import glob
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_dialogue(client, sid, text, answer_fn):
    req = {"session_id": sid, "text": text, "answers": []}
    for _ in range(10):
        st = client.post("/api/diagnose", json=req).get_json()
        if st["status"] != "question":
            return st
        q = st["question"]["symptom_id"]
        req["answers"].append({"symptom_id": q, "answer": answer_fn(q)})
    raise AssertionError("dialogue did not finish")


def test_pages_render(client):
    assert client.get("/").status_code == 200
    assert client.get("/expert").status_code == 200
    assert client.get("/sw.js").status_code == 200
    assert client.get("/manifest.webmanifest").status_code == 200


def test_meta(client):
    m = client.get("/api/meta").get_json()
    assert m["kg"]["diseases"] == 17
    assert m["backend"]["backend"] == "embedded"
    assert sum(len(g["items"]) for g in m["symptom_groups"]) == m["kg"]["symptoms"]


def test_full_dialogue_whitefly(client):
    st = run_dialogue(client, "session-whitefly-1", "இலையில் வெள்ளை தூள் போல இருக்கு",
                      lambda q: "yes" if q in ("pests_seen", "insects_fly_up", "sticky_sooty") else "no")
    r = st["result"]
    assert r["disease_id"] == "whitefly"
    assert r["disease"]["treatments"]["organic"]
    assert r["explanation"]["evidence"]


def test_feedback_learns_once(client, app):
    st = run_dialogue(client, "session-feedback-1", "செடியின் ஒரு பக்கம் மட்டும் வாடுது",
                      lambda q: "yes" if q in ("brown_inside_stem", "leaf_yellowing", "starts_lower_leaves") else "no")
    svc = app.extensions["tomatodoc"]
    d = st["result"]["disease_id"]
    before = svc.kg.theta(d, "one_side_wilt")
    r = client.post("/api/feedback", json={"session_id": "session-feedback-1", "outcome": "confirmed", "disease_id": d}).get_json()
    assert r["learned"] and r["updates"] > 0
    assert svc.kg.theta(d, "one_side_wilt") > before
    again = client.post("/api/feedback", json={"session_id": "session-feedback-1", "outcome": "confirmed", "disease_id": d}).get_json()
    assert again["status"] == "already_recorded"


def test_learning_survives_restart(tmp_path, monkeypatch):
    monkeypatch.delenv("NEO4J_URI", raising=False)
    from tomatodoc import create_app
    cfg = {"DATABASE_PATH": str(tmp_path / "p.db"), "KG_BACKEND": "embedded", "NEO4J_URI": None}
    a1 = create_app(cfg)
    c = a1.test_client()
    run_dialogue(c, "session-persist-1", "white powder on leaves", lambda q: "no")
    c.post("/api/feedback", json={"session_id": "session-persist-1", "outcome": "confirmed", "disease_id": "powdery_mildew"})
    w = a1.extensions["tomatodoc"].kg.theta("powdery_mildew", "white_powder")
    a2 = create_app(cfg)
    assert a2.extensions["tomatodoc"].kg.theta("powdery_mildew", "white_powder") == pytest.approx(w)


def test_rejection_without_correction_does_not_change_weights(client, app):
    run_dialogue(client, "session-reject-1", "white powder on leaves", lambda q: "no")
    svc = app.extensions["tomatodoc"]
    before = dict((k, dict(v)) for k, v in svc.kg.edges.items())
    client.post("/api/feedback", json={"session_id": "session-reject-1", "outcome": "rejected", "disease_id": "powdery_mildew"})
    assert {k: dict(v) for k, v in svc.kg.edges.items()} == before


def test_unmatched_text_is_queued_and_can_be_taught(client):
    phrase = "இலையில் கண்ணாடி மாதிரி பளிங்கு"
    assert client.post("/api/analyze", json={"text": phrase}).get_json()["understood"] is False
    row = [u for u in client.get("/api/expert/unmatched").get_json() if u["text"] == phrase][0]
    r = client.post(f"/api/expert/unmatched/{row['id']}/resolve", json={"symptom_id": "bronze_dry_leaves", "lang": "ta"})
    assert r.status_code == 200
    got = client.post("/api/analyze", json={"text": phrase}).get_json()
    assert "bronze_dry_leaves" in [m["symptom_id"] for m in got["matches"]]


@pytest.mark.parametrize("payload", [
    {"session_id": "x"},
    {"session_id": "../../etc/passwd"},
])
def test_bad_session_rejected(client, payload):
    assert client.post("/api/diagnose", json=payload).status_code == 400


def test_malformed_lists_are_ignored(client):
    r = client.post("/api/diagnose", json={"session_id": "session-malformed-1", "answers": [1, "x", {"symptom_id": 5}],
                                            "text_matches": "zz", "picked": {"a": 1}, "photo": "nope"})
    assert r.status_code == 200 and r.get_json()["status"] == "need_input"


def test_non_json_body(client):
    assert client.post("/api/diagnose", data="hello", content_type="text/plain").status_code == 400


def test_expert_requires_token_when_configured(tmp_path, monkeypatch):
    monkeypatch.delenv("NEO4J_URI", raising=False)
    from tomatodoc import create_app
    app = create_app({"DATABASE_PATH": str(tmp_path / "e.db"), "KG_BACKEND": "embedded", "NEO4J_URI": None, "EXPERT_TOKEN": "s3cret"})
    c = app.test_client()
    assert c.get("/api/expert/stats").status_code == 401
    assert c.get("/api/expert/stats", headers={"X-Expert-Token": "s3cret"}).status_code == 200


VAL = glob.glob(os.path.join(ROOT, "tomato", "val", "Tomato___Late_blight", "*"))


@pytest.mark.skipif(not VAL or not os.path.exists(os.path.join(ROOT, "models", "leaf_classifier.onnx")), reason="no model/data")
def test_photo_endpoint(client):
    with open(VAL[0], "rb") as f:
        r = client.post("/api/photo", data={"photo": (f, "leaf.jpg")}, content_type="multipart/form-data")
    p = r.get_json()
    assert r.status_code == 200 and p["top"] == "late_blight"
    st = client.post("/api/diagnose", json={"session_id": "session-photo-1", "photo": p}).get_json()
    assert st["posterior"][0]["id"] == "late_blight"


def test_photo_rejects_non_image(client):
    r = client.post("/api/photo", data={"photo": (open(__file__, "rb"), "x.jpg")}, content_type="multipart/form-data")
    assert r.status_code in (400, 503)
