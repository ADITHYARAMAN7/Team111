"""
services.py - wires the knowledge graph, language matcher, reasoning engine,
photo model and databases together, and implements the use-cases the HTTP
layer exposes. Kept free of Flask so it can be tested and scripted directly.
"""
import json
import logging
import math
import re
import threading
import time
from datetime import date, datetime

from . import advisory, crop, risk, soil as soil_mod, weather
from .context import resolve_season, season_from_weather
from .db import Database
from .inference import UNKNOWN, DiagnosisEngine
from .kg.store import Neo4jStore, make_store
from .learning import plan_updates
from .llm import LLMError, make_client
from .nlu import SymptomMatcher, extract_modifiers
from .vision import load_classifier

log = logging.getLogger(__name__)
SESSION_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
URGENCY = {5: "urgent", 4: "high", 3: "normal", 2: "low", 1: "low"}
PREVENT_MODES = {"contact", "systemic", "biological", "botanical", "contact_insect", "nutrient"}  # nutrient: calcium vs blossom-end rot


def _dicts(value, limit):
    """Untrusted JSON list -> list of dicts (anything else dropped)."""
    if not isinstance(value, list):
        return []
    return [v for v in value[:limit] if isinstance(v, dict)]


def _location(value):
    if isinstance(value, dict) and weather.valid_location(value.get("lat"), value.get("lon")):
        return weather.grid(value["lat"], value["lon"])          # never store more precise than ~5 km
    return None


def haversine_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


class Services:
    def __init__(self, config):
        self.config = config
        self.db = Database(config["DATABASE_PATH"])
        self.store = make_store(config, self.db)
        self.kg = self.store.load()
        self.engine = DiagnosisEngine(self.kg)
        self.matcher = SymptomMatcher(self.kg.layterm_list())
        self.vision = load_classifier(config["MODEL_DIR"]) if config.get("ENABLE_VISION", True) else None
        self.llm = make_client(config)
        self.weather_fn = weather.fetch if config.get("ENABLE_WEATHER", True) else (lambda lat, lon: None)
        self._lock = threading.Lock()
        log.info("Knowledge graph loaded from %s: %s", self.store.name, self.kg.stats())

    def rebuild_matcher(self):
        with self._lock:
            self.matcher.build(self.kg.layterm_list())

    # ---- public views of graph objects -------------------------------------
    def image_urls(self, d):
        return [f"/static/img/diseases/{img}" for img in self.kg.diseases[d].get("images", [])]

    def disease_card(self, d):
        dd = self.kg.diseases[d]
        imgs = self.image_urls(d)
        return {"id": d, "name_en": dd["name_en"], "name_ta": dd["name_ta"], "type": dd["type"],
                "severity": dd.get("severity", 3), "urgency": URGENCY.get(dd.get("severity", 3), "normal"),
                "contagious": bool(dd.get("contagious")), "image": imgs[0] if imgs else None}

    def disease_detail(self, d):
        dd = self.kg.diseases[d]
        sources = self.kg.meta.get("sources", {})
        treatments = {"organic": [], "chemical": [], "cultural": []}
        for t in self.kg.treatments_for(d):
            treatments.setdefault(t["type"], []).append({
                "id": t["id"], "name_en": t["name_en"], "name_ta": t["name_ta"], "type": t["type"],
                "dosage_en": t["dosage_en"], "dosage_ta": t["dosage_ta"], "efficacy": t["efficacy"],
                "source": t["source"], "source_citation": sources.get(t["source"], t["source"]),
                "application": t.get("application")})
        symptoms = sorted(({"symptom_id": s, "theta": round(w, 3), "label_en": self.kg.symptoms[s]["label_en"],
                            "label_ta": self.kg.symptoms[s]["label_ta"]} for s, w in self.kg.symptoms_of[d].items()),
                          key=lambda x: -x["theta"])
        return {**self.disease_card(d), "summary_en": dd.get("summary_en"), "summary_ta": dd.get("summary_ta"),
                "prevention_en": dd.get("prevention_en", []), "prevention_ta": dd.get("prevention_ta", []),
                "images": self.image_urls(d), "treatments": treatments, "symptoms": symptoms,
                "source": dd.get("source"), "source_citation": sources.get(dd.get("source"), dd.get("source")),
                "favored_by": dd.get("favored_by", {})}

    def meta(self):
        groups = {}
        order = ["spots", "colour", "shape", "fungus", "pests", "pattern", "wilt", "stem_root", "growth", "fruit"]
        for s in self.kg.symptoms.values():
            groups.setdefault(s.get("group", "other"), []).append(
                {"id": s["id"], "label_en": s["label_en"], "label_ta": s["label_ta"], "part": s.get("part")})
        season, src = resolve_season(self.kg)
        v = self.vision
        return {
            "kg": self.kg.stats(), "kg_version": self.kg.meta.get("version"), "backend": self.store.describe(),
            "vision": {"available": v is not None,
                       "val_accuracy": v.meta.get("val_accuracy") if v else None,
                       "labels": v.labels if v else []},
            "seasons": [{"id": s["id"], "name_en": s["name_en"], "name_ta": s["name_ta"]} for s in self.kg.seasons.values()],
            "season_suggestion": {"id": season, "source": src},
            "symptom_groups": [{"group": g, "items": groups[g]} for g in sorted(groups, key=lambda g: order.index(g) if g in order else 99)],
            "diseases": [self.disease_card(d) for d in self.kg.diseases],
            "voice_ai": {"available": self.llm is not None, "model": self.llm.model if self.llm else None},
            "weather": {"available": self.config.get("ENABLE_WEATHER", True)},
        }

    # ---- location, weather, outbreaks --------------------------------------
    def outbreaks_near(self, loc, radius_km=None, days=None):
        radius_km = radius_km or self.config.get("OUTBREAK_RADIUS_KM", 30)
        days = days or self.config.get("OUTBREAK_DAYS", 21)
        counts = {}
        for r in self.db.reports_since(time.time() - days * 86400):
            dist = haversine_km(loc, (r["lat"], r["lon"]))
            if dist <= radius_km and r["disease"] in self.kg.diseases:
                c = counts.setdefault(r["disease"], {"disease_id": r["disease"], "n": 0, "simulated": 0, "nearest_km": dist})
                c["n"] += 1
                c["simulated"] += 1 if r["source"] == "simulated" else 0
                c["nearest_km"] = round(min(c["nearest_km"], dist), 1)
        out = sorted(counts.values(), key=lambda x: -x["n"])
        for o in out:
            card = self.disease_card(o["disease_id"])
            o.update({k: card[k] for k in ("name_en", "name_ta", "type")})
        return {"radius_km": radius_km, "days": days, "diseases": out}

    def context(self, loc, field=None):
        """Everything location tells us: weather now, disease-risk forecast, outbreaks nearby,
        and preventive-spray alerts for diseases the weather now strongly favours."""
        w = self.weather_fn(*loc)
        risks = risk.assess(w)
        ranked = []
        for d, r in risks.items():
            card = self.disease_card(d)
            ranked.append({"disease_id": d, **r, "name_en": card["name_en"], "name_ta": card["name_ta"], "type": card["type"]})
        ranked.sort(key=lambda x: -x["score"])
        summ = weather.summary(w)
        season = season_from_weather(summ["mean_temp_3d"], summ["mean_rh_3d"]) if summ else None
        stage = crop.stage_info(field)
        harvest = crop.harvest_context(field, stage["stage"] if stage else None)
        return {"location": {"lat": loc[0], "lon": loc[1]}, "weather": summ, "risks": ranked,
                "outbreaks": self.outbreaks_near(loc), "season": season,
                "alerts": self.prevention_alerts(ranked, w, harvest), "crop": stage, "_raw": w, "_risks": risks}

    def prevention_alerts(self, ranked, w, harvest=None, limit=2):
        """High weather risk -> the best preventive spray from the graph (protectants and
        bio-agents preferred, harvest-safe while picking) and the next good spray window."""
        out = []
        for r in ranked:
            if r["level"] != "high" or len(out) >= limit:
                continue
            best = None
            for t in self.kg.treatments_for(r["disease_id"]):
                app = t.get("application") or {}
                if app.get("mode") not in PREVENT_MODES:
                    continue
                window = advisory.find_window(w, app) if w else None
                spray_day = datetime.fromisoformat(window["start"]).date() if window else advisory.next_spray_time(None).date()
                ph = crop.phi_check(app.get("phi_days"), harvest, spray_day=spray_day)
                if ph and ph["status"] == "blocks_pick":
                    continue
                score = t["efficacy"] + (0.1 if app.get("mode") in ("contact", "biological", "botanical") else 0) \
                    - (0.05 if ph and ph["status"] == "after_pick" else 0)
                if best is None or score > best[0]:
                    best = (score, t, app, ph, window)
            alert = {k: r.get(k) for k in ("disease_id", "name_en", "name_ta", "type", "level", "explain_en", "explain_ta")}
            if best:
                _, t, app, ph, window = best
                alert["treatment"] = {"id": t["id"], "name_en": t["name_en"], "name_ta": t["name_ta"],
                                      "dosage_en": t["dosage_en"], "dosage_ta": t["dosage_ta"], "phi": ph}
                alert["window"] = window
            out.append(alert)
        return out

    def prior_factors(self, ctx):
        if not ctx:
            return None
        f = risk.prior_factors(ctx["_risks"]) or {}
        for o in ctx["outbreaks"]["diseases"]:
            base = f.get(o["disease_id"], f.get("_default", 1.0))
            f[o["disease_id"]] = base * (1 + 0.2 * min(o["n"], 5))
        return f or None

    def public_context(self, ctx):
        return {k: v for k, v in ctx.items() if not k.startswith("_")} if ctx else None

    # ---- voice / AI understanding ------------------------------------------
    def _ai_vocab(self):
        syms = [{"id": s, "label_en": v["label_en"]} for s, v in self.kg.symptoms.items()]
        trs = [{"id": t, "name_en": v["name_en"]} for t, v in self.kg.treatments.items()]
        return syms, trs

    def voice(self, audio, mime):
        if not self.llm:
            raise LLMError("voice AI is not configured (set GEMINI_API_KEY)")
        syms, trs = self._ai_vocab()
        ai = self.llm.understand(syms, trs, audio_bytes=audio, mime=mime)
        if ai["transcript"]:
            res = self.analyze(ai["transcript"], ai=ai)
        else:
            res = {"matches": [], "understood": False, "modifiers": {"severity": None, "affected_percent": None}}
            res["ai"] = self._label_ai(ai)
        res["transcript"] = ai["transcript"]
        return res

    def _label_ai(self, ai):
        for s in ai.get("symptoms", []):
            s["label_en"] = self.kg.symptoms[s["symptom_id"]]["label_en"]
            s["label_ta"] = self.kg.symptoms[s["symptom_id"]]["label_ta"]
        return ai

    # ---- use-cases ---------------------------------------------------------
    def analyze(self, text, ai=None):
        res = self.matcher.match(text)
        for m in res["matches"]:
            s = self.kg.symptoms[m["symptom_id"]]
            m["label_en"], m["label_ta"] = s["label_en"], s["label_ta"]
        res["modifiers"] = extract_modifiers(text)
        if ai is None and self.llm and self.config.get("GEMINI_FOR_TEXT") and text.strip():
            try:
                syms, trs = self._ai_vocab()
                ai = self.llm.understand(syms, trs, text=text)
            except LLMError as e:
                log.warning("Gemini text understanding failed: %s", e)
                res["ai_error"] = str(e)
        if ai is not None:
            res["ai"] = self._label_ai(ai)
            mods = res["modifiers"]
            res["modifiers"] = {"severity": ai.get("severity") or mods["severity"],
                                "affected_percent": ai["affected_percent"] if ai.get("affected_percent") is not None
                                else mods["affected_percent"]}
        res["understood"] = bool(res["matches"]) or bool(ai and ai.get("symptoms"))
        if not res["understood"] and text.strip():
            self.db.log_unmatched(text)
        return res

    def photo(self, data):
        if not self.vision:
            return None
        r = self.vision.predict(data)
        ranked = sorted(r["probs"].items(), key=lambda kv: -kv[1])
        r["ranked"] = [{"id": k, "p": v, **({"name_en": self.kg.diseases[k]["name_en"], "name_ta": self.kg.diseases[k]["name_ta"]}
                                           if k in self.kg.diseases else {"name_en": "Healthy", "name_ta": "ஆரோக்கியம்"})}
                       for k, v in ranked[:4]]
        return r

    def diagnose(self, req):
        sid = req.get("session_id") or ""
        if not SESSION_RE.match(sid):
            raise ValueError("invalid session_id")
        text = str(req.get("text") or "")[:1000]
        text_matches = req.get("text_matches")
        if text_matches is None:
            text_matches = self.matcher.match(text)["matches"] if text else []
        text_matches = [{"symptom_id": m["symptom_id"], "present": bool(m.get("present", True)),
                         "strength": max(0.0, min(1.0, float(m.get("strength", 0.6)))),
                         "layterm_id": m.get("layterm_id") if m.get("layterm_id") in self.kg.layterms else None,
                         "phrase": str(m.get("phrase") or "")[:200], "removed": bool(m.get("removed"))}
                        for m in _dicts(text_matches, 40) if m.get("symptom_id") in self.kg.symptoms]
        answers = [a for a in _dicts(req.get("answers"), 20) if a.get("symptom_id") in self.kg.symptoms]
        picked = [p for p in _dicts(req.get("picked"), 40) if p.get("symptom_id") in self.kg.symptoms]
        skipped = [s for s in (req.get("skipped") or [])[:20] if isinstance(s, str)]
        photo = req.get("photo")
        if photo and not (isinstance(photo, dict) and isinstance(photo.get("probs"), dict)):
            photo = None
        if photo:
            photo = {"probs": {k: float(v) for k, v in photo["probs"].items()},
                     "temperature": max(0.0, min(1.0, float(photo.get("temperature", 0.5))))}
        ai_symptoms = []
        for a in _dicts(req.get("ai_symptoms"), 20):
            if a.get("symptom_id") in self.kg.symptoms:
                try:
                    conf = max(0.0, min(1.0, float(a.get("confidence", 0.6))))
                except (TypeError, ValueError):
                    conf = 0.6
                ai_symptoms.append({"symptom_id": a["symptom_id"], "present": bool(a.get("present", True)),
                                    "confidence": conf, "evidence_quote": str(a.get("evidence_quote") or "")[:200]})
        severity = req.get("severity") if req.get("severity") in ("mild", "moderate", "severe") else None
        extent = req.get("extent")
        extent = int(extent) if isinstance(extent, (int, float)) and not isinstance(extent, bool) and 0 <= extent <= 100 else None
        sprays = [{"product": str(x.get("product") or "")[:80], "treatment_id": x.get("treatment_id"),
                   "days_ago": x.get("days_ago") if isinstance(x.get("days_ago"), int) else None}
                  for x in _dicts(req.get("sprays"), 10) if x.get("product") or x.get("treatment_id")]
        loc = _location(req.get("location"))
        ctx = self.context(loc) if loc else None
        if ctx and ctx["season"] and not req.get("season"):
            season, season_src = ctx["season"], "weather"
        else:
            season, season_src = resolve_season(self.kg, req.get("season"), req.get("weather"))
        weather_f = self.prior_factors(ctx) if ctx and ctx["_risks"] and not req.get("season") else None
        soil = soil_mod.clean(req.get("soil"))
        soil_f = soil_mod.disease_factors(soil)
        field = crop.clean_field(req.get("field"))
        stage = crop.stage_info(field)
        harvest = crop.harvest_context(field, stage["stage"] if stage else None)
        factors = self.combine_factors(weather_f, season, {d: f for d, (f, _) in soil_f.items()},
                                       crop.stage_factors(stage["stage"]) if stage else {})

        evidence = self.engine.build_evidence(text_matches, answers, picked, ai_symptoms)
        state = self.engine.step(evidence, season=season, photo=photo,
                                 asked=[a["symptom_id"] for a in answers], skipped=skipped,
                                 finish=bool(req.get("finish")), factors=factors)
        state["season"] = {"id": season, "source": "weather_models" if weather_f else season_src}
        state["soil_used"] = bool(soil)
        state["crop"] = {**(stage or {}), "harvest": harvest} if field else None
        state["context"] = self.public_context(ctx)
        state["evidence"] = [{**e, "label_en": self.kg.symptoms[e["symptom_id"]]["label_en"],
                              "label_ta": self.kg.symptoms[e["symptom_id"]]["label_ta"]} for e in evidence]
        for p in state["posterior"]:
            p.update(self.disease_card(p["id"]) if p["id"] != UNKNOWN else
                     {"name_en": "Something else", "name_ta": "வேறு ஏதோ பிரச்சனை"})
        if state["status"] == "result":
            r = state["result"]
            r["disease"] = self.disease_detail(r["disease_id"])
            for a in r["alternatives"]:
                a.update(self.disease_card(a["disease_id"]))
            r["advisory"] = self.advise(r["disease"], ctx, severity, extent, sprays, soil, soil_f,
                                        (field or {}).get("crop_type") or req.get("crop_type"), harvest)
        top = state["posterior"][0]
        self.db.upsert_consultation(
            sid, input_text=text, lang=req.get("lang"), season=season,
            evidence_json=json.dumps(evidence, ensure_ascii=False),
            posterior_json=json.dumps(state["posterior"][:4], ensure_ascii=False),
            top_disease=top["id"], top_prob=top["p"], status=state["status"],
            questions_asked=len(answers), photo_used=1 if photo else 0,
            lat=loc[0] if loc else None, lon=loc[1] if loc else None, severity=severity, extent=extent,
            voice_ai=1 if ai_symptoms else 0, soil_used=1 if soil else 0)
        return state

    def combine_factors(self, weather_f, season, *extra):
        """Soil and crop-stage factors ({disease: factor}) multiply onto the weather
        factors, or onto the calendar-season boost when there is no weather (the
        engine then uses these instead of the season)."""
        extra = [e for e in extra if e]
        if not extra:
            return weather_f
        if weather_f:
            base = {d: weather_f.get(d, weather_f.get("_default", 1.0)) for d in self.kg.diseases}
        else:
            base = {d: 1.0 + (dd.get("favored_by", {}).get(season, 0.0) if season else 0.0) for d, dd in self.kg.diseases.items()}
        out = {}
        for d, f in base.items():
            for e in extra:
                f *= e.get(d, 1.0)
            out[d] = f
        return out

    # ---- soil test report ----------------------------------------------------
    def soil_summary(self, soil, crop=None):
        """Ratings, soil-linked disease risks and the fertiliser plan for a soil profile."""
        risks = [{"disease_id": d, "factor": round(f, 2), "reasons": why, **self.disease_card(d)}
                 for d, (f, why) in sorted(soil_mod.disease_factors(soil).items(), key=lambda kv: -kv[1][0])
                 if f >= 1.2]            # weak links (e.g. excess N alone) are shown as a soil fix instead
        return {"soil": soil, "interpretation": soil_mod.interpret(soil), "risks": risks,
                "plan": soil_mod.nutrient_plan(soil, crop), "general": soil_mod.advise(None, soil, [])}

    def read_soil_report(self, data, mime):
        """Uploaded report -> soil values. PDFs with a text layer are read locally;
        photos and scanned PDFs need the AI reader (Gemini)."""
        method, parsed = None, None
        if mime == "application/pdf":
            text = soil_mod.pdf_text(data)
            if text.strip():
                parsed, method = soil_mod.parse_text(text), "pdf_text"
        if (parsed is None or len(parsed["values"]) < 3) and self.llm:
            ai = self.llm.read_soil_report(data, mime)
            if not ai["is_soil_report"]:
                raise ValueError("not_a_soil_report")
            if parsed is None or len(ai["values"]) > len(parsed["values"]):
                parsed, method = ai, "ai"
        if parsed is None:
            raise LookupError("needs_ai")
        soil = soil_mod.clean(parsed)
        if not soil or len(soil["values"]) < 1:
            raise ValueError("no_values")
        return {"method": method, "found": len(soil["values"]), **self.soil_summary(soil)}

    def advise(self, disease, ctx, severity, extent, sprays, soil=None, soil_f=None, crop_type=None, harvest=None):
        w = ctx["_raw"] if ctx else None
        treatments = [t for typ in ("organic", "cultural", "chemical") for t in disease["treatments"].get(typ, [])]
        matched = advisory.match_sprays(sprays, self.kg.treatments)
        d = disease["id"]
        d_risk = ctx["_risks"].get(d) if ctx else None
        return {
            "weather": weather.summary(w),
            "risk": d_risk,
            "general_window": advisory.find_window(w, {"timing": "any", "rainfast_h": 4}) if w else None,
            "suitability": {t["id"]: advisory.suitability(w, t.get("application") or {}) for t in treatments},
            "plan": (p := advisory.plan(disease, treatments, severity, extent, matched, w, d_risk, harvest)),
            "harvest_safety": {t["id"]: crop.phi_check((t.get("application") or {}).get("phi_days"), harvest,
                                                       spray_day=date.fromisoformat(p["spray_day"])) for t in treatments},
            "outbreak": next((o for o in ctx["outbreaks"]["diseases"] if o["disease_id"] == d), None) if ctx else None,
            "severity": severity, "extent": extent,
            "soil": {"actions": soil_mod.advise(d, soil, [t["id"] for t in treatments]),
                     "prior": (soil_f or {}).get(d, (1.0, []))[1],
                     "interpretation": soil_mod.interpret(soil),
                     "plan": soil_mod.nutrient_plan(soil, crop_type)} if soil else None,
        }

    def feedback(self, req):
        sid = req.get("session_id") or ""
        outcome = req.get("outcome")
        if not SESSION_RE.match(sid) or outcome not in ("confirmed", "corrected", "rejected", "unsure"):
            raise ValueError("invalid feedback")
        cons = self.db.get_consultation(sid)
        if not cons:
            raise LookupError("unknown session")
        if cons.get("outcome"):
            return {"status": "already_recorded", "outcome": cons["outcome"]}
        disease_id = req.get("disease_id")
        corrected_to = req.get("corrected_to")
        truth = disease_id if outcome == "confirmed" else corrected_to if outcome == "corrected" else None
        if truth is not None and truth not in self.kg.diseases:
            raise ValueError("unknown disease")
        evidence = json.loads(cons["evidence_json"] or "[]")
        applied, suggestions = [], []
        if truth:
            updates, suggestions = plan_updates(self.kg, evidence, truth)
            applied = self.store.apply_updates(self.kg, updates)
            for s in suggestions:
                self.db.suggest_edge(s["d"], s["s"], s["amount"])
            if isinstance(self.store, Neo4jStore):
                try:
                    self.store.record_image_confirmation(truth)
                except Exception as e:  # noqa: BLE001
                    log.warning("could not update verified_count: %s", e)
            self.rebuild_matcher()
        if truth and cons.get("lat") is not None:
            self.db.add_report(truth, cons["lat"], cons["lon"], "farmer", sid)
        self.db.record_feedback(sid, outcome, disease_id, corrected_to, applied)
        return {"status": "recorded", "learned": bool(truth), "updates": len(applied), "suggestions": len(suggestions)}

    # ---- expert use-cases --------------------------------------------------
    def expert_stats(self):
        q = self.db.query
        total = q("SELECT COUNT(*) n FROM consultations")[0]["n"]
        fb = {r["outcome"]: r["n"] for r in q("SELECT outcome, COUNT(*) n FROM consultations WHERE outcome IS NOT NULL GROUP BY outcome")}
        top = q("""SELECT COALESCE(final_disease, top_disease) d, COUNT(*) n FROM consultations
                   WHERE status='result' GROUP BY d ORDER BY n DESC LIMIT 8""")
        avg_q = q("SELECT AVG(questions_asked) a FROM consultations WHERE status='result'")[0]["a"]
        since = time.time() - 14 * 86400
        daily = q("""SELECT date(created_at, 'unixepoch') day, COUNT(*) n FROM consultations
                     WHERE created_at > ? GROUP BY day ORDER BY day""", (since,))
        recent = q("""SELECT id, created_at, input_text, top_disease, top_prob, status, questions_asked, photo_used, outcome, final_disease
                      FROM consultations ORDER BY updated_at DESC LIMIT 25""")
        unmatched_open = q("SELECT COUNT(*) n FROM unmatched WHERE resolved=0")[0]["n"]
        judged = sum(fb.values()) - fb.get("unsure", 0)
        return {
            "consultations": total, "feedback": fb,
            "accuracy_feedback": round(fb.get("confirmed", 0) / judged, 3) if judged else None,
            "avg_questions": round(avg_q, 2) if avg_q is not None else None,
            "top_diseases": [{**r, "name_en": self.kg.diseases[r["d"]]["name_en"] if r["d"] in self.kg.diseases else r["d"]} for r in top],
            "daily": daily, "recent": recent, "unmatched_open": unmatched_open,
            "kg": self.kg.stats(), "backend": self.store.describe(),
            "photo_rate": round(q("SELECT AVG(photo_used) a FROM consultations")[0]["a"] or 0, 3),
        }

    def expert_graph(self, include_layterms=False):
        nodes, edges = [], []
        for d, dd in self.kg.diseases.items():
            nodes.append({"id": f"d:{d}", "label": dd["name_en"], "label_ta": dd["name_ta"], "kind": "disease", "type": dd["type"]})
        for s, ss in self.kg.symptoms.items():
            nodes.append({"id": f"s:{s}", "label": ss["label_en"], "label_ta": ss["label_ta"], "kind": "symptom", "part": ss.get("part")})
        for (d, s), e in self.kg.edges.items():
            edges.append({"from": f"d:{d}", "to": f"s:{s}", "rel": "HAS_SYMPTOM", "weight": round(e["alpha"] / (e["alpha"] + e["beta"]), 3)})
        for t, tt in self.kg.treatments.items():
            nodes.append({"id": f"t:{t}", "label": tt["name_en"], "label_ta": tt["name_ta"], "kind": "treatment", "type": tt["type"]})
        for d, lst in self.kg.treated_by.items():
            for t, eff in lst:
                edges.append({"from": f"d:{d}", "to": f"t:{t}", "rel": "TREATED_BY", "weight": eff})
        if include_layterms:
            for lt in self.kg.layterm_list():
                nodes.append({"id": f"l:{lt['id']}", "label": lt["text"], "kind": "layterm", "lang": lt.get("lang")})
                edges.append({"from": f"l:{lt['id']}", "to": f"s:{lt['symptom_id']}", "rel": "LAYTERM_MAPS_TO", "weight": round(lt["weight"], 3)})
        return {"nodes": nodes, "edges": edges}

    def expert_edges(self):
        from .kg.graph import PRIOR_STRENGTH
        rows = []
        for (d, s), e in self.kg.edges.items():
            w = e["alpha"] / (e["alpha"] + e["beta"])
            rows.append({"d": d, "s": s, "disease": self.kg.diseases[d]["name_en"], "symptom": self.kg.symptoms[s]["label_en"],
                         "seed": round(e["seed"], 3), "current": round(w, 3), "drift": round(w - e["seed"], 3),
                         "observations": round(e["alpha"] + e["beta"] - PRIOR_STRENGTH, 2)})
        rows.sort(key=lambda r: (-r["observations"], -abs(r["drift"])))
        return rows

    def add_layterm(self, symptom_id, text, lang="ta", weight=0.8, created_by="expert"):
        if symptom_id not in self.kg.symptoms:
            raise ValueError("unknown symptom")
        text = (text or "").strip()
        if not 2 <= len(text) <= 200:
            raise ValueError("phrase must be 2-200 characters")
        lang = lang if lang in ("ta", "en", "tl") else "ta"
        weight = max(0.3, min(0.95, float(weight)))
        lid = f"lt_x_{int(time.time() * 1000)}"
        self.store.add_layterm(self.kg, {"id": lid, "text": text, "lang": lang, "symptom_id": symptom_id,
                                         "weight": weight, "created_by": created_by})
        self.rebuild_matcher()
        return lid

    def accept_suggestion(self, d, s, weight=0.3):
        if d not in self.kg.diseases or s not in self.kg.symptoms:
            raise ValueError("unknown disease or symptom")
        if (d, s) not in self.kg.edges:
            self.store.add_edge(self.kg, d, s, max(0.05, min(0.95, float(weight))))
        self.db.set_suggestion_status(d, s, "accepted")

    def add_disease(self, data):
        """Expert creates a new disease and wires it into the live knowledge graph.

        Required keys: id, name_en, name_ta, type, severity, contagious,
                       summary_en, summary_ta, symptoms (list of {symptom_id, weight}),
                       treatments (list of {treatment_id, efficacy})
        Optional keys: prevention_en[], prevention_ta[], favored_by{}, images[]
        """
        import re as _re
        did = (data.get("id") or "").strip().lower()
        if not _re.match(r"^[a-z][a-z0-9_]{1,59}$", did):
            raise ValueError("id must be 2-60 lowercase letters/digits/underscores, starting with a letter")
        if did in self.kg.diseases:
            raise ValueError(f"disease '{did}' already exists")
        name_en = (data.get("name_en") or "").strip()
        name_ta = (data.get("name_ta") or "").strip()
        if not name_en or not name_ta:
            raise ValueError("name_en and name_ta are required")
        d_type = data.get("type")
        if d_type not in ("fungal", "bacterial", "viral", "pest", "physiological", "other"):
            raise ValueError("type must be one of: fungal, bacterial, viral, pest, physiological, other")
        severity = int(data.get("severity", 3))
        if not 1 <= severity <= 5:
            raise ValueError("severity must be 1-5")
        # validate symptom links
        raw_syms = data.get("symptoms") or []
        symptoms = []
        for item in raw_syms:
            sid = item.get("symptom_id") or ""
            if sid not in self.kg.symptoms:
                raise ValueError(f"unknown symptom: {sid}")
            w = max(0.05, min(0.95, float(item.get("weight", 0.5))))
            symptoms.append((sid, w))
        if not symptoms:
            raise ValueError("at least one symptom link is required")
        # validate treatment links
        raw_trts = data.get("treatments") or []
        treatments = []
        for item in raw_trts:
            tid = item.get("treatment_id") or ""
            if tid not in self.kg.treatments:
                raise ValueError(f"unknown treatment: {tid}")
            eff = max(0.01, min(1.0, float(item.get("efficacy", 0.5))))
            treatments.append((tid, eff))
        if not treatments:
            raise ValueError("at least one treatment link is required")
        # build favored_by from seasons
        favored_by = {}
        for s, b in (data.get("favored_by") or {}).items():
            if s in self.kg.seasons:
                favored_by[s] = max(0.0, min(2.0, float(b)))
        disease_dict = {
            "id": did, "name_en": name_en, "name_ta": name_ta, "type": d_type,
            "severity": severity, "contagious": bool(data.get("contagious")),
            "source": "expert", "summary_en": (data.get("summary_en") or "").strip(),
            "summary_ta": (data.get("summary_ta") or "").strip(),
            "prevention_en": [p for p in (data.get("prevention_en") or []) if isinstance(p, str) and p.strip()],
            "prevention_ta": [p for p in (data.get("prevention_ta") or []) if isinstance(p, str) and p.strip()],
            "images": [], "favored_by": favored_by,
        }
        self.store.add_disease(self.kg, disease_dict, symptoms, treatments)
        self.rebuild_matcher()
        log.info("Expert added new disease: %s (%s)", did, name_en)
        return did

    def expert_outbreaks(self, days=60):
        rows = self.db.reports_since(time.time() - days * 86400)
        for r in rows:
            r["name_en"] = self.kg.diseases.get(r["disease"], {}).get("name_en", r["disease"])
            r["type"] = self.kg.diseases.get(r["disease"], {}).get("type")
        return rows
