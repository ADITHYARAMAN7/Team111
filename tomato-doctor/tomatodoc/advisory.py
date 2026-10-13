"""
advisory.py - location- and weather-aware treatment advice.

Given the diagnosis, the farmer's local forecast, how bad the problem is, and
what was already sprayed, it produces:
  * spray windows    - hours in the next 3 days that are dry for long enough for
                       the product to become rain-fast, not too windy (drift) and
                       not too hot (leaf burn / evaporation)
  * suitability      - per treatment: "OK now" or why to wait, and when
  * plan             - severity-adaptive order (mild -> cultural/organic first,
                       severe -> effective chemical first), field scope from how
                       many plants are affected, systemic products preferred when
                       rain is coming, FRAC/IRAC rotation away from what was
                       already used
  * schedule         - dated repeat applications that alternate resistance groups
  * harvest safety   - while fruit is being picked, products whose pre-harvest
                       interval does not fit the picking rhythm move down, and
                       every spray says from when picking is safe again
Rules and thresholds are cited in the knowledge graph (meta.sources).
"""
from datetime import datetime, timedelta

from rapidfuzz import fuzz, process

from .crop import phi_check
from .weather import hour_of

WIND_OK, WIND_MAX = 15, 20         # km/h: ideal ≤15, avoid ≥20 (spray_wind)
RAIN_MM, RAIN_PROB = 0.3, 60       # an hour counts as "wet" above these
GENERAL_MAX_TEMP = 35
SPRAY_HOURS = {"any": range(6, 19), "morning_evening": list(range(6, 11)) + list(range(16, 19)),
               "evening": range(16, 19), "morning": range(6, 11)}
SPRAYABLE = {"contact", "systemic", "biological", "botanical", "contact_insect", "nutrient"}


def _wet(h):
    return h["rain"] >= RAIN_MM or (h["rain_prob"] is not None and h["rain_prob"] >= RAIN_PROB)


def hour_check(hours, i, app):
    """Reasons why hour i is NOT good for this application ([] = good)."""
    h = hours[i]
    reasons = []
    if hour_of(h["time"]) not in SPRAY_HOURS.get(app.get("timing") or "any", SPRAY_HOURS["any"]):
        reasons.append(("time", None))
    if h["rain"] >= 0.1:
        reasons.append(("raining", None))
    need = max(2, int(app.get("rainfast_h") or 0))
    for k in range(1, need + 1):
        if i + k < len(hours) and _wet(hours[i + k]):
            reasons.append(("rain_soon", k))
            break
    if h["wind"] >= WIND_MAX:
        reasons.append(("wind", round(h["wind"])))
    maxt = app.get("max_temp_c") or GENERAL_MAX_TEMP
    if h["temp"] > maxt:
        reasons.append(("hot", round(h["temp"])))
    if h["rh"] >= 97:
        reasons.append(("leaves_wet", None))
    return reasons


def find_window(weather, app, horizon=72, min_len=2):
    """First run of >= min_len good hours in the forecast -> dict or None."""
    hours, n = weather["hours"], weather["now"]
    run = []
    for i in range(n, min(len(hours), n + horizon)):
        if not hour_check(hours, i, app):
            run.append(i)
            if len(run) >= min_len and (i + 1 >= len(hours) or hour_check(hours, i + 1, app)):
                break
        else:
            if len(run) >= min_len:
                break
            run = []
    if len(run) < min_len:
        return None
    a, b = hours[run[0]], hours[run[-1]]
    return {"start": a["time"], "end": b["time"][:11] + f"{hour_of(b['time']) + 1:02d}:00",
            "temp": round(sum(hours[i]["temp"] for i in run) / len(run), 1),
            "wind": round(max(hours[i]["wind"] for i in run), 1), "in_hours": run[0] - n}


def suitability(weather, app):
    if app.get("mode") not in SPRAYABLE:
        return {"status": "anytime"}
    if not weather:
        return {"status": "unknown"}
    n = weather["now"]
    reasons = hour_check(weather["hours"], n, app)
    window = find_window(weather, app)
    status = "now" if not reasons else ("later" if window else "not_soon")
    cur = weather["hours"][n]
    warnings = []
    if status == "now" and cur["wind"] >= WIND_OK:
        warnings.append({"code": "breezy", "value": round(cur["wind"])})
    if status == "now" and rain_expected(weather, 12):
        warnings.append({"code": "rain_later", "value": None})
    return {"status": status, "warnings": warnings, "reasons": [{"code": c, "value": v} for c, v in reasons if c != "time" or not window or window["in_hours"] > 0],
            "window": window}


def rain_expected(weather, hours=24):
    if not weather:
        return False
    n = weather["now"]
    return any(_wet(h) for h in weather["hours"][n + 1:n + 1 + hours])


def match_sprays(sprays, treatments):
    """Free-text product names the farmer already used -> treatment ids (+ group)."""
    names = {}
    for t in treatments.values():
        for k in ("name_en", "name_ta"):
            names[t[k].lower()] = t["id"]
    out = []
    for s in sprays or []:
        tid = s.get("treatment_id")
        if tid not in treatments:
            hit = process.extractOne((s.get("product") or "").lower(), list(names), scorer=fuzz.partial_ratio, score_cutoff=80)
            tid = names[hit[0]] if hit else None
        grp = (treatments[tid].get("application") or {}).get("group") if tid else None
        out.append({"product": s.get("product"), "treatment_id": tid, "group": grp, "days_ago": s.get("days_ago")})
    return out


def _groups(g):
    return {x.strip() for x in (g or "").replace("FRAC", "").replace("IRAC", "").split("+") if x.strip()}


def next_spray_time(weather):
    """When the next spray will realistically happen: the first good forecast window,
    else the next daylight spraying hour."""
    w = find_window(weather, {"timing": "any", "rainfast_h": 4}) if weather else None
    if w:
        return datetime.fromisoformat(w["start"])
    start = datetime.now().replace(minute=0, second=0, microsecond=0)
    if start.hour >= 18:
        start = (start + timedelta(days=1)).replace(hour=7)
    elif start.hour < 6:
        start = start.replace(hour=7)
    return start


def plan(disease, treatments, severity=None, extent=None, sprays=None, weather=None, risk=None, harvest=None):
    """disease: detail dict; treatments: list (with efficacy + application);
    harvest: crop.harvest_context() or None."""
    severity = severity if severity in ("mild", "moderate", "severe") else None
    level = severity or ("severe" if disease.get("severity", 3) >= 5 else "moderate")
    used = [s for s in (sprays or []) if s.get("group")]
    used_groups = set().union(*[_groups(s["group"]) for s in used]) if used else set()
    rainy = rain_expected(weather)

    picking = bool(harvest and harvest.get("picking"))
    spray_at = next_spray_time(weather)

    def phi_status(t):
        ph = phi_check((t.get("application") or {}).get("phi_days"), harvest, spray_day=spray_at.date())
        return ph["status"] if ph else None

    def score(t, with_harvest=True):
        app = t.get("application") or {}
        s = t["efficacy"]
        typ = t["type"]
        if level == "mild":
            s += {"cultural": 0.3, "organic": 0.2, "chemical": -0.3}[typ]
        elif level == "severe":
            s += {"chemical": 0.25, "cultural": 0.1, "organic": -0.1}[typ]
        if rainy and app.get("mode") == "systemic":
            s += 0.1
        if rainy and app.get("mode") == "contact":
            s -= 0.05
        if used_groups and _groups(app.get("group")) & used_groups:
            s -= 0.4
        if with_harvest and picking:
            s -= {"blocks_pick": 0.5, "after_pick": 0.05}.get(phi_status(t), 0)
        return s

    ranked = sorted(treatments, key=score, reverse=True)
    notes = []
    if picking:
        notes.append({"code": "picking", "next_pick": harvest["next_pick"], "every": harvest["every"]})
        first_spray = next((t for t in sorted(treatments, key=lambda t: score(t, False), reverse=True)
                            if (t.get("application") or {}).get("mode") in SPRAYABLE), None)
        if first_spray and phi_status(first_spray) == "blocks_pick":
            notes.append({"code": "phi_avoid", "treatment_id": first_spray["id"],
                          "phi": first_spray["application"]["phi_days"], "every": harvest["every"]})
    for s in used:
        same = [t for t in treatments if _groups((t.get("application") or {}).get("group")) & _groups(s["group"])]
        if same:
            alt = next((t for t in ranked if t["type"] == "chemical" and not (_groups((t.get("application") or {}).get("group")) & used_groups)), None)
            notes.append({"code": "rotate", "product": s["product"], "group": s["group"], "alternative": alt["id"] if alt else None})
        elif s.get("treatment_id") and s["treatment_id"] not in {t["id"] for t in treatments}:
            notes.append({"code": "wrong_product", "product": s["product"]})
    if disease.get("type") == "viral":
        notes.append({"code": "viral_no_cure"})
    if rainy:
        notes.append({"code": "rain_prefer_systemic"})
    if risk and risk.get("level") == "high":
        notes.append({"code": "weather_favours", "explain_en": risk.get("explain_en"), "explain_ta": risk.get("explain_ta")})

    scope = None
    if extent is not None:
        scope = "spot" if extent < 10 else "patch" if extent < 40 else "field"

    # dated schedule: alternate resistance groups among sprayable products
    sprayable = [t for t in ranked if (t.get("application") or {}).get("mode") in SPRAYABLE and (t.get("application") or {}).get("interval_days")]
    if level == "mild":
        sprayable = [t for t in sprayable if t["type"] != "chemical"] or sprayable
    if picking:
        sprayable = [t for t in sprayable if phi_status(t) != "blocks_pick"] or sprayable
    schedule = []
    if sprayable:
        first = suitability(weather, sprayable[0]["application"]).get("window") if weather else None
        start = datetime.fromisoformat(first["start"]) if first else next_spray_time(None)
        rounds = 1 if level == "mild" else 3
        day = start
        last_groups = set(used_groups)
        pool = list(sprayable)
        for k in range(rounds):
            pick = next((t for t in pool if not (_groups(t["application"].get("group")) & last_groups)), pool[0])
            phi = pick["application"].get("phi_days")
            schedule.append({"date": day.isoformat(timespec="minutes"), "treatment_id": pick["id"], "group": pick["application"].get("group"),
                             "forecast_checked": k == 0 and bool(first), "phi": phi,
                             "safe_from": (day + timedelta(days=phi)).date().isoformat() if phi is not None else None})
            last_groups = _groups(pick["application"].get("group"))
            day = day + timedelta(days=pick["application"]["interval_days"])
    return {"level": level, "scope": scope, "order": [t["id"] for t in ranked], "notes": notes, "schedule": schedule,
            "rain_expected": rainy, "sprays_matched": sprays or [], "harvest": harvest,
            "spray_day": spray_at.date().isoformat()}
