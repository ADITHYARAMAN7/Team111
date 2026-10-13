"""Weather risk models, spray advisory, outbreak alerts and the Gemini adapter -
all offline (synthetic weather, mocked Gemini transport)."""
import json
from datetime import datetime, timedelta

import pytest

from tomatodoc import advisory, risk
from tomatodoc.llm import GeminiClient, LLMError, clean
from tomatodoc.nlu import extract_modifiers


def synth(days_past=7, days_future=3, temp=(15, 22), rh_night=95, rh_day=70, rain_hours=(), wind=8, start_hour=12):
    """Hourly weather; night = 20:00-07:00. rain_hours: offsets from 'now' (+ = future) with 2 mm rain."""
    t0 = datetime(2026, 10, 1, 0)
    total = (days_past + days_future) * 24
    hours = []
    for i in range(total):
        ts = t0 + timedelta(hours=i)
        night = ts.hour >= 20 or ts.hour < 7
        hot = 10 <= ts.hour < 16
        hours.append({"time": ts.strftime("%Y-%m-%dT%H:00"), "temp": temp[1] if hot else temp[0],
                      "rh": rh_night if night else rh_day, "rain": 0.0, "rain_prob": 5, "wind": wind})
    now = days_past * 24 - 24 + start_hour
    for off in rain_hours:
        hours[now + off]["rain"] = 2.0
        hours[now + off]["rain_prob"] = 90
    return {"hours": hours, "now": now}


# ---------------------------------------------------------------- risk models
def test_cool_wet_week_gives_high_late_blight():
    r = risk.assess(synth(temp=(14, 20), rh_night=96))
    assert r["late_blight"]["level"] == "high"
    assert r["late_blight"]["facts"]["hutton_periods_7d"] >= 2


def test_hot_dry_week_gives_mites_not_blight():
    r = risk.assess(synth(temp=(27, 37), rh_night=45, rh_day=25))
    assert r["late_blight"]["level"] == "low"
    assert r["spider_mite"]["score"] > r["late_blight"]["score"]
    assert r["spider_mite"]["level"] == "high"


def test_tropical_heat_damps_hutton():
    cool = risk.assess(synth(temp=(15, 21), rh_night=96))["late_blight"]["score"]
    hot = risk.assess(synth(temp=(26, 33), rh_night=96))["late_blight"]["score"]
    assert hot < cool * 0.6


def test_tomcast_dsv_table():
    wet_day = [{"temp": 22, "rh": 95}] * 14 + [{"temp": 28, "rh": 60}] * 10
    assert risk.tomcast_dsv(wet_day) == 3          # 21-25 °C band, 14 wet hours -> 3
    assert risk.tomcast_dsv([{"temp": 22, "rh": 60}] * 24) == 0


def test_risk_prior_factors_shift_posterior(engine):
    ev = [{"symptom_id": "leaf_spots", "present": True, "c": 0.85, "source": "text"}]
    wet = risk.prior_factors(risk.assess(synth(temp=(15, 21), rh_night=96)))
    post_plain = engine.posterior(ev)[0]
    post_wet = engine.posterior(ev, factors=wet)[0]
    assert post_wet["late_blight"] > post_plain["late_blight"]


# ---------------------------------------------------------------- spray advisory
MANCOZEB = {"mode": "contact", "rainfast_h": 4, "max_temp_c": 35, "timing": "any"}
SULFUR = {"mode": "contact", "rainfast_h": 3, "max_temp_c": 32, "timing": "morning_evening"}


def test_rain_soon_blocks_contact_spray():
    w = synth(rain_hours=(2, 3))
    s = advisory.suitability(w, MANCOZEB)
    assert s["status"] in ("later", "not_soon")
    assert any(r["code"] == "rain_soon" for r in s["reasons"])


def test_dry_calm_day_is_ok_now():
    s = advisory.suitability(synth(temp=(18, 26)), MANCOZEB)
    assert s["status"] == "now"


def test_heat_blocks_sulfur_and_finds_evening_window():
    w = synth(temp=(24, 36), start_hour=13)
    s = advisory.suitability(w, SULFUR)
    assert s["status"] == "later"
    assert any(r["code"] == "hot" for r in s["reasons"])
    assert int(s["window"]["start"][11:13]) >= 16 or int(s["window"]["start"][11:13]) <= 10


def test_wind_blocks_spraying():
    s = advisory.suitability(synth(wind=25), MANCOZEB)
    assert any(r["code"] == "wind" for r in s["reasons"])


def test_cultural_treatments_are_anytime():
    assert advisory.suitability(synth(), {"mode": "cultural"})["status"] == "anytime"


def _treatments(app_svc, d):
    det = app_svc.disease_detail(d)
    return det, [t for k in ("organic", "cultural", "chemical") for t in det["treatments"][k]]


def test_plan_severity_orders_options(app):
    svc = app.extensions["tomatodoc"]
    det, trs = _treatments(svc, "early_blight")
    mild = advisory.plan(det, trs, "mild")
    severe = advisory.plan(det, trs, "severe")
    typ = {t["id"]: t["type"] for t in trs}
    assert typ[mild["order"][0]] != "chemical"
    assert typ[severe["order"][0]] == "chemical"
    assert len(severe["schedule"]) == 3 and len(mild["schedule"]) == 1


def test_plan_rotates_away_from_used_group(app):
    svc = app.extensions["tomatodoc"]
    det, trs = _treatments(svc, "early_blight")
    sprays = advisory.match_sprays([{"product": "Mancozeb", "days_ago": 5}], svc.kg.treatments)
    assert sprays[0]["treatment_id"] == "mancozeb_75wp" and sprays[0]["group"] == "FRAC M3"
    p = advisory.plan(det, trs, "severe", sprays=sprays)
    assert any(n["code"] == "rotate" for n in p["notes"])
    assert p["schedule"][0]["group"] != "FRAC M3"
    groups = [x["group"] for x in p["schedule"]]
    assert all(a != b for a, b in zip(groups, groups[1:]))   # consecutive sprays alternate groups


def test_plan_scope_from_extent(app):
    svc = app.extensions["tomatodoc"]
    det, trs = _treatments(svc, "late_blight")
    assert advisory.plan(det, trs, extent=5)["scope"] == "spot"
    assert advisory.plan(det, trs, extent=80)["scope"] == "field"


def test_viral_plan_says_no_cure(app):
    svc = app.extensions["tomatodoc"]
    det, trs = _treatments(svc, "leaf_curl_virus")
    assert any(n["code"] == "viral_no_cure" for n in advisory.plan(det, trs)["notes"])


# ---------------------------------------------------------------- modifiers without AI
@pytest.mark.parametrize("text,sev,ext", [
    ("இலையில் கொஞ்சம் வெள்ளை தூள்", "mild", None),
    ("வயல் முழுக்க ரொம்ப அதிகமா பரவிடுச்சு", "severe", 90),
    ("only a few plants, slightly yellow", "mild", 5),
    ("about 30% of plants are affected", None, 30),
])
def test_extract_modifiers(text, sev, ext):
    m = extract_modifiers(text)
    assert m["severity"] == sev and m["affected_percent"] == ext


# ---------------------------------------------------------------- Gemini adapter
SYMS = [{"id": "white_powder", "label_en": "White powder"}, {"id": "insects_fly_up", "label_en": "Insects"}]
TRS = [{"id": "neem_oil", "name_en": "Neem oil"}]
AI_JSON = {"transcript": "இலையில் கொஞ்சம் வெள்ளை தூள், பூச்சி இல்லை", "language": "ta", "english_summary": "a little white powder, no insects",
           "symptoms": [{"symptom_id": "white_powder", "present": True, "confidence": 0.9, "evidence_quote": "வெள்ளை தூள்"},
                        {"symptom_id": "insects_fly_up", "present": False, "confidence": 0.8, "evidence_quote": "பூச்சி இல்லை"},
                        {"symptom_id": "made_up", "present": True, "confidence": 1, "evidence_quote": "x"}],
           "severity": "mild", "affected_percent": 5, "duration_days": 3, "plant_parts": ["leaf", "moon"],
           "crop_stage": "flowering", "sprays_done": [{"product": "neem", "treatment_id": "neem_oil", "days_ago": 4}],
           "weather_mentioned": ""}


def test_gemini_interactions_request_and_parsing():
    calls = []

    def transport(url, body):
        calls.append((url, body))
        return 200, {"id": "x", "steps": [{"type": "model_output", "content": [{"type": "text", "text": json.dumps(AI_JSON, ensure_ascii=False)}]}]}
    c = GeminiClient("k", transport=transport)
    out = c.understand(SYMS, TRS, audio_bytes=b"RIFF....", mime="audio/wav")
    url, body = calls[0]
    assert url.endswith("/interactions")
    assert body["input"][1]["type"] == "audio" and body["input"][1]["mime_type"] == "audio/wav"
    assert body["response_format"]["mime_type"] == "application/json"
    assert "transcript" in body["response_format"]["schema"]["properties"]
    assert [s["symptom_id"] for s in out["symptoms"]] == ["white_powder", "insects_fly_up"]   # unknown id dropped
    assert out["plant_parts"] == ["leaf"] and out["severity"] == "mild"


def test_gemini_falls_back_to_generate_content():
    calls = []

    def transport(url, body):
        calls.append(url)
        if url.endswith("/interactions"):
            return 404, {"error": {"message": "not found"}}
        return 200, {"candidates": [{"content": {"parts": [{"text": "```json\n" + json.dumps(AI_JSON) + "\n```"}]}}]}
    out = GeminiClient("k", transport=transport).understand(SYMS, TRS, text="white powder")
    assert calls[-1].endswith(":generateContent") and out["affected_percent"] == 5


def test_gemini_bad_key_raises():
    with pytest.raises(LLMError):
        GeminiClient("k", transport=lambda u, b: (403, {})).understand(SYMS, TRS, text="x")


def test_clean_clamps_values():
    out = clean({"affected_percent": 250, "duration_days": -1, "severity": "apocalyptic"}, set(), set())
    assert out["affected_percent"] == 100 and out["duration_days"] is None and out["severity"] is None


# ---------------------------------------------------------------- end to end with location
def test_diagnose_with_location_weather_and_outbreaks(app, client):
    svc = app.extensions["tomatodoc"]
    svc.weather_fn = lambda lat, lon: synth(temp=(15, 21), rh_night=96)
    for _ in range(3):
        svc.db.add_report("late_blight", 11.40, 76.70, "simulated")
    ctx = client.post("/api/context", json={"lat": 11.41, "lon": 76.69}).get_json()
    assert ctx["risks"][0]["disease_id"] == "late_blight"
    assert ctx["outbreaks"]["diseases"][0]["n"] == 3
    req = {"session_id": "session-field-01", "text": "இலையில் கருப்பு திட்டு, வேகமா பரவுது", "answers": [],
           "location": {"lat": 11.41, "lon": 76.69}, "severity": "severe", "extent": 60,
           "sprays": [{"product": "copper oxychloride", "days_ago": 4}]}
    for _ in range(8):
        st = client.post("/api/diagnose", json=req).get_json()
        if st["status"] != "question":
            break
        q = st["question"]["symptom_id"]
        req["answers"].append({"symptom_id": q, "answer": "yes" if svc.kg.theta("late_blight", q) else "no"})
    r = st["result"]
    assert r["disease_id"] == "late_blight"
    assert st["season"]["source"] == "weather_models"
    adv = r["advisory"]
    assert adv["outbreak"]["n"] == 3 and adv["plan"]["scope"] == "field"
    assert any(n["code"] == "rotate" for n in adv["plan"]["notes"])
    assert set(adv["suitability"]) >= {"cyazofamid", "remove_destroy_plants"}
    fb = client.post("/api/feedback", json={"session_id": "session-field-01", "outcome": "confirmed", "disease_id": "late_blight"})
    assert fb.status_code == 200
    assert len([x for x in svc.db.reports_since(0) if x["source"] == "farmer"]) == 1   # confirmed case joins the community map


def test_location_is_coarsened_for_privacy(app, client):
    svc = app.extensions["tomatodoc"]
    svc.weather_fn = lambda lat, lon: None
    client.post("/api/diagnose", json={"session_id": "session-privacy-1", "text": "white powder on leaves",
                                       "location": {"lat": 11.123456, "lon": 77.987654}})
    row = svc.db.get_consultation("session-privacy-1")
    assert (row["lat"], row["lon"]) == (11.1, 78.0)


def test_voice_endpoint_without_key(client):
    r = client.post("/api/voice", data={"audio": (open(__file__, "rb"), "a.wav")}, content_type="multipart/form-data")
    assert r.status_code == 503


def test_voice_endpoint_with_mocked_gemini(app, client):
    svc = app.extensions["tomatodoc"]
    svc.llm = GeminiClient("k", transport=lambda u, b: (200, {"output_text": json.dumps(AI_JSON, ensure_ascii=False)}))
    r = client.post("/api/voice", data={"audio": (__import__("io").BytesIO(b"RIFF" + b"\0" * 4000), "a.wav", "audio/wav")},
                    content_type="multipart/form-data").get_json()
    assert r["transcript"].startswith("இலையில்")
    assert r["modifiers"]["severity"] == "mild"
    assert {m["symptom_id"] for m in r["matches"]} >= {"white_powder"}
    assert r["ai"]["sprays_done"][0]["treatment_id"] == "neem_oil"
