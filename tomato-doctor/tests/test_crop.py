"""My field: crop stage, harvest safety (pre-harvest intervals), prevention alerts."""
from datetime import date, datetime, timedelta

import pytest

from tomatodoc import advisory, crop

TODAY = date(2026, 10, 13)


def days_ago(n):
    return (TODAY - timedelta(days=n)).isoformat()


@pytest.mark.parametrize("dat,stage", [(0, "establishment"), (19, "establishment"), (20, "vegetative"),
                                       (40, "flowering"), (60, "fruiting"), (95, "harvest")])
def test_stage_from_transplanting_date(dat, stage):
    f = crop.clean_field({"planting_date": days_ago(dat)}, TODAY)
    assert crop.stage_info(f, TODAY)["stage"] == stage


def test_clean_field_rejects_bad_input():
    assert crop.clean_field({"planting_date": days_ago(400)}, TODAY) is None          # last season's crop
    assert crop.clean_field({"planting_date": "2027-01-01"}, TODAY) is None           # future
    assert crop.clean_field("x") is None
    f = crop.clean_field({"harvesting": "yes", "pick_every": 99}, TODAY)
    assert f["pick_every"] == 10 and f["harvesting"] == "yes"


def test_stage_factors_rule_out_fruit_problems_on_young_plants():
    assert crop.stage_factors("vegetative")["blossom_end_rot"] < 0.5
    assert crop.stage_factors("fruiting")["blossom_end_rot"] > 1
    assert crop.stage_factors(None) == {}


def test_harvest_context_next_picking():
    f = crop.clean_field({"planting_date": days_ago(90), "last_pick": days_ago(1), "pick_every": 4}, TODAY)
    h = crop.harvest_context(f, "harvest", TODAY)
    assert h == {"picking": True, "every": 4, "next_pick": (TODAY + timedelta(days=3)).isoformat(), "days_to_pick": 3}
    assert crop.harvest_context(crop.clean_field({"planting_date": days_ago(40)}, TODAY), "flowering", TODAY) == {"picking": False}


def test_phi_check_statuses():
    h = {"picking": True, "every": 4, "next_pick": "2026-10-16", "days_to_pick": 3}
    assert crop.phi_check(3, h, TODAY)["status"] == "ok"
    assert crop.phi_check(4, h, TODAY)["status"] == "after_pick"
    r = crop.phi_check(7, h, TODAY)
    assert r["status"] == "blocks_pick" and r["safe_from"] == "2026-10-20"
    assert crop.phi_check(7, {"picking": False}, TODAY)["status"] == "ok"
    assert crop.phi_check(None, h) is None


def test_every_sprayable_treatment_has_a_phi(kg):
    missing = [t for t, v in kg.treatments.items()
               if (v.get("application") or {}).get("mode") in advisory.SPRAYABLE and (v.get("application") or {}).get("phi_days") is None]
    assert missing == []


def test_plan_moves_long_phi_product_down_while_picking(kg):
    from tomatodoc.services import Services  # noqa: F401 (import check)
    treatments = [t for t in kg.treatments_for("early_blight")]
    disease = {"id": "early_blight", "type": "fungal", "severity": 3}
    base = advisory.plan(disease, treatments, "severe")
    h = {"picking": True, "every": 4, "next_pick": (date.today() + timedelta(days=3)).isoformat(), "days_to_pick": 3}
    picked = advisory.plan(disease, treatments, "severe", harvest=h)
    assert base["order"][0] == "mancozeb_75wp"                       # 5-day PHI
    assert picked["order"].index("mancozeb_75wp") > picked["order"].index("copper_hydroxide")
    assert {"picking", "phi_avoid"} <= {n["code"] for n in picked["notes"]}
    assert all(x["treatment_id"] != "mancozeb_75wp" for x in picked["schedule"])
    assert all(x["safe_from"] for x in picked["schedule"])


def test_diagnose_with_field(client):
    today = date.today()
    field = {"planting_date": (today - timedelta(days=85)).isoformat(), "last_pick": (today - timedelta(days=1)).isoformat(), "pick_every": 4}
    r = client.post("/api/diagnose", json={"session_id": "croptest01", "text": "இலையில் வளையம் போன்ற புள்ளி, கீழ் இலையில் தான்",
                                           "field": field, "severity": "severe", "finish": True}).get_json()
    assert r["crop"]["stage"] == "harvest" and r["crop"]["harvest"]["picking"]
    adv = r["result"]["advisory"]
    assert adv["harvest_safety"]["mancozeb_75wp"]["status"] == "blocks_pick"
    assert adv["plan"]["harvest"]["every"] == 4


def test_young_crop_lowers_fruit_disorder(client):
    today = date.today()
    text = "பழத்தின் அடியில் கருப்பு புள்ளி, பழம் அழுகுது"

    def p_ber(field):
        r = client.post("/api/diagnose", json={"session_id": "croptest02", "text": text, "field": field}).get_json()
        return next(p["p"] for p in r["posterior"] if p["id"] == "blossom_end_rot")
    young = p_ber({"planting_date": (today - timedelta(days=15)).isoformat()})
    fruiting = p_ber({"planting_date": (today - timedelta(days=60)).isoformat()})
    assert fruiting > young


def test_prevention_alert_is_harvest_safe(app):
    svc = app.extensions["tomatodoc"]
    ranked = [{"disease_id": "early_blight", "name_en": "Early Blight", "name_ta": "x", "type": "fungal", "level": "high",
               "explain_en": None, "explain_ta": None},
              {"disease_id": "late_blight", "name_en": "Late Blight", "name_ta": "y", "type": "fungal", "level": "low"}]
    h = {"picking": True, "every": 4, "next_pick": (date.today() + timedelta(days=3)).isoformat(), "days_to_pick": 3}
    alerts = svc.prevention_alerts(ranked, None, h)
    assert [a["disease_id"] for a in alerts] == ["early_blight"]
    tr = alerts[0]["treatment"]
    assert tr["id"] != "mancozeb_75wp" and tr["phi"]["status"] != "blocks_pick"
    assert alerts[0]["window"] is None                                   # no weather -> no window claimed


def test_phi_counts_from_the_spray_day_not_today():
    h = {"picking": True, "every": 4, "next_pick": "2026-10-16", "days_to_pick": 3}
    assert crop.phi_check(3, h, TODAY)["status"] == "ok"                     # spray today: safe by Fri
    late = crop.phi_check(3, h, spray_day=TODAY + timedelta(days=1))          # spray tomorrow: not safe by Fri
    assert late["status"] == "after_pick" and late["safe_from"] == "2026-10-17"


def test_repeat_sprays_follow_picking_days(kg, monkeypatch):
    start = datetime(2026, 10, 14, 8, 0)
    monkeypatch.setattr(advisory, "next_spray_time", lambda w: start)
    disease = {"id": "early_blight", "type": "fungal", "severity": 3}
    h = {"picking": True, "every": 4, "next_pick": "2026-10-16", "days_to_pick": 2}
    sched = advisory.plan(disease, kg.treatments_for("early_blight"), "severe", harvest=h)["schedule"]
    assert len(sched) == 3
    # copper (PHI 3) cannot wait for the picking in 2 days: pick first, and the rhythm restarts today
    assert sched[0]["after_pick"]
    picks = {start.date() + timedelta(days=4 * j) for j in range(12)}
    for x in sched:
        sd = datetime.fromisoformat(x["date"]).date()
        assert sd in picks and x["after_pick"]                  # every spray follows a picking
        assert x["phi"] is None or x["phi"] <= 4                # ...and is clear before the next one


def test_warns_when_no_spray_fits_the_picking_interval(kg, monkeypatch):
    monkeypatch.setattr(advisory, "next_spray_time", lambda w: datetime(2026, 10, 14, 8, 0))
    disease = {"id": "leaf_curl_virus", "type": "viral", "severity": 4}
    h = {"picking": True, "every": 4, "next_pick": "2026-10-16", "days_to_pick": 2}
    notes = [n["code"] for n in advisory.plan(disease, kg.treatments_for("leaf_curl_virus"), "severe", harvest=h)["notes"]]
    assert "phi_no_safe_option" in notes
