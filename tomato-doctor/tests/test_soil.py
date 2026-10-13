"""Soil test report: parsing, ratings, soil-aware prior and advice, API."""
import io

import pytest

from tomatodoc import soil

REPORT = """SOIL HEALTH CARD
Sample No: 45  Survey No 112/3
Soil texture: Sandy loam
1 pH 5.2 Strongly acidic
2 EC 2.6 dS/m
3 Organic Carbon (OC) 0.38 %
4 Available Nitrogen (N) 198 kg/ha Low
5 Available Phosphorus (P2O5) 52 kg/ha
6 Available Potassium (K) 310 kg/ha High
7 Available Sulphur (S) 8.2 ppm
8 Available Zinc (Zn) 0.42 ppm
9 Available Boron (B) 0.61 ppm
Exchangeable Calcium 1.1 cmol/kg
"""
POOR = {"values": {"ph": 5.2, "ec": 2.6, "ca": 1.1, "n": 198, "oc": 0.38}, "texture": "sandy"}


def test_parse_report_text():
    r = soil.parse_text(REPORT)
    v = r["values"]
    assert v["ph"] == 5.2 and v["ec"] == 2.6 and v["oc"] == 0.38 and v["n"] == 198
    assert v["p"] == pytest.approx(52 * 0.4364, abs=0.01)      # P2O5 converted to P
    assert r["converted"] == {"p": "P2O5"}
    assert v["k"] == 310 and v["s"] == 8.2 and v["zn"] == 0.42 and v["b"] == 0.61 and v["ca"] == 1.1
    assert r["texture"] == "sandy"
    assert "fe" not in v                                        # not on the report -> not invented


def test_clean_rejects_implausible_and_junk():
    c = soil.clean({"values": {"ph": 25, "ec": -1, "oc": "abc", "n": True, "k": "150"}, "texture": "rocky"})
    assert c == {"values": {"k": 150.0}, "texture": None, "sample_date": None}
    assert soil.clean({"values": {}}) is None
    assert soil.clean("nope") is None


@pytest.mark.parametrize("param,value,rating", [
    ("ph", 5.4, "strongly_acidic"), ("ph", 6.5, "suitable"), ("ph", 8.6, "strongly_alkaline"),
    ("ec", 0.5, "normal"), ("ec", 1.5, "critical"), ("ec", 3, "saline"),
    ("n", 279, "low"), ("n", 280, "medium"), ("n", 561, "high"),
    ("k", 100, "low"), ("zn", 0.59, "deficient"), ("zn", 0.6, "sufficient"),
])
def test_soil_health_card_ratings(param, value, rating):
    assert soil.rate(param, value)[0] == rating


def test_soil_factors_are_bounded_and_specific():
    f = soil.disease_factors(soil.clean(POOR))
    assert f["blossom_end_rot"][0] == soil.MAX_FACTOR
    assert set(f["blossom_end_rot"][1]) == {"ca_low", "ec_high", "ph_acidic"}
    assert f["fusarium_wilt"][0] > 1 and f["root_knot_nematode"][0] > 1
    assert "late_blight" not in f
    assert soil.disease_factors(soil.clean({"values": {"ph": 6.8, "ec": 0.3}})) == {}


def test_advice_targets_root_cause():
    c = soil.clean(POOR)
    codes = [a["code"] for a in soil.advise("blossom_end_rot", c, ["calcium_spray"])]
    assert codes[:3] == ["ber_calcium", "lime", "salinity_water"]
    codes = [a["code"] for a in soil.advise("late_blight", c, ["copper_hydroxide"])]
    assert "copper_acid" in codes and "ber_calcium" not in codes
    rich = soil.clean({"values": {"n": 650, "ph": 6.8}})
    assert [a["code"] for a in soil.advise("whitefly", rich, [])] == ["hold_nitrogen"]


def test_nutrient_plan_adjusts_by_soil_test():
    plan = soil.nutrient_plan(soil.clean({"values": {"n": 198, "p": 18, "k": 310, "ec": 2.6, "zn": 0.4}}))
    assert plan["nutrients"]["n"]["kg_ha"] == 187.5        # low N  -> +25 %
    assert plan["nutrients"]["p"]["kg_ha"] == 100.0        # medium -> as recommended
    assert plan["nutrients"]["k"]["kg_ha"] == 37.5         # high K -> -25 %
    assert plan["potash_form"] == "sop"                    # salty soil -> no muriate of potash
    urea = plan["products"][0]
    assert urea["product"] == "urea" and urea["kg_acre"] == urea["basal_kg"] + urea["top_kg"]
    assert urea["kg_acre"] == round(187.5 * soil.HA_PER_ACRE / 0.46 / 2) * 2
    assert [m["element"] for m in plan["micros"]] == ["zn"]
    std = soil.nutrient_plan(None, "hybrid")
    assert std["nutrients"]["k"]["kg_ha"] == 250 and not std["adjusted"]


def test_soil_shifts_diagnosis_towards_soil_linked_disorder(client):
    text = "பழத்தின் அடியில் கருப்பு புள்ளி, பழம் அழுகுது"
    def p_ber(s):
        r = client.post("/api/diagnose", json={"session_id": "soiltest01", "text": text, "soil": s}).get_json()
        return next(p["p"] for p in r["posterior"] if p["id"] == "blossom_end_rot"), r
    without, _ = p_ber(None)
    with_soil, r = p_ber(POOR)
    assert with_soil > without
    assert r["soil_used"] is True


def test_result_carries_soil_advice(client):
    r = client.post("/api/diagnose", json={"session_id": "soiltest02", "text": "பழத்தின் அடியில் கருப்பு புள்ளி",
                                           "soil": POOR, "finish": True}).get_json()
    assert r["status"] == "result"
    s = r["result"]["advisory"]["soil"]
    assert s["plan"]["products"] and s["interpretation"]["params"]
    if r["result"]["disease_id"] == "blossom_end_rot":
        assert "ber_calcium" in [a["code"] for a in s["actions"]]
    plain = client.post("/api/diagnose", json={"session_id": "soiltest03", "text": "இலையில் வெள்ளை தூள்", "finish": True}).get_json()
    assert plain["result"]["advisory"]["soil"] is None     # soil is optional


def test_soil_summary_api(client):
    r = client.post("/api/soil", json={"soil": POOR})
    assert r.status_code == 200
    j = r.get_json()
    assert j["risks"][0]["disease_id"] == "blossom_end_rot"
    assert all(x["factor"] >= 1.2 for x in j["risks"])
    assert client.post("/api/soil", json={"soil": {}}).status_code == 400


def test_soil_report_upload_pdf_and_photo_without_ai(client):
    fitz = pytest.importorskip("fitz")
    doc = fitz.open()
    doc.new_page().insert_text((50, 70), "pH 6.8\nEC 0.4 dS/m\nOrganic Carbon 0.62 %\nAvailable Nitrogen 300 kg/ha", fontsize=11)
    r = client.post("/api/soil/report", data={"report": (io.BytesIO(doc.tobytes()), "r.pdf", "application/pdf")},
                    content_type="multipart/form-data")
    assert r.status_code == 200
    j = r.get_json()
    assert j["method"] == "pdf_text" and j["soil"]["values"] == {"ph": 6.8, "ec": 0.4, "oc": 0.62, "n": 300.0}
    r = client.post("/api/soil/report", data={"report": (io.BytesIO(b"\xff\xd8\xff" + b"0" * 2000), "r.jpg", "image/jpeg")},
                    content_type="multipart/form-data")
    assert r.status_code == 503 and r.get_json()["error"] == "needs_ai"
    r = client.post("/api/soil/report", data={"report": (io.BytesIO(b"hello"), "r.txt", "text/plain")},
                    content_type="multipart/form-data")
    assert r.status_code == 400


def test_gemini_soil_reader_is_validated():
    from tomatodoc.llm import GeminiClient
    calls = []

    def transport(url, body):
        calls.append(body)
        return 200, {"output_text": '{"is_soil_report": true, "texture": "clayey", "sample_date": "12/03/2026", '
                                    '"ph": 7.9, "ec": 0.3, "oc": 0.5, "n": -1, "p": 12, "k": 200, "s": -1, "zn": 0.3, '
                                    '"fe": -1, "mn": -1, "cu": -1, "b": -1, "ca": -1, "mg": -1}'}
    g = GeminiClient("k", transport=transport)
    raw = g.read_soil_report(b"%PDF-1.4", "application/pdf")
    assert calls[0]["input"][1]["type"] == "document"
    c = soil.clean(raw)
    assert c["values"] == {"ph": 7.9, "ec": 0.3, "oc": 0.5, "p": 12.0, "k": 200.0, "zn": 0.3}
    assert c["texture"] == "clayey"
