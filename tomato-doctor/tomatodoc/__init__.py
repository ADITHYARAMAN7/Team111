"""
TomatoDoc - Tamil-first, knowledge-graph-based tomato crop doctor.

    from tomatodoc import create_app
    app = create_app()
"""
import json
import logging
import os
from functools import wraps

from flask import Flask, abort, jsonify, render_template, request, send_from_directory

from .config import load_config
from .services import Services

__version__ = "2.4.0"


def create_app(overrides=None):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = load_config(overrides)
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = int(config["MAX_UPLOAD_MB"] * 1024 * 1024)
    app.config["JSON_AS_ASCII"] = False
    app.json.ensure_ascii = False
    svc = Services(config)
    app.extensions["tomatodoc"] = svc

    def body():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            abort(400, "expected a JSON object")
        return data

    def expert_only(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            token = config.get("EXPERT_TOKEN")
            if token:
                given = request.headers.get("X-Expert-Token") or request.args.get("token")
                if given != token:
                    abort(401, "expert token required")
            elif request.remote_addr not in ("127.0.0.1", "::1", None):
                abort(403, "set EXPERT_TOKEN to use the expert console from another device")
            return fn(*a, **kw)
        return wrapper

    @app.errorhandler(400)
    @app.errorhandler(401)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def http_error(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": getattr(e, "description", str(e))}), e.code
        return e

    # ---- pages -------------------------------------------------------------
    @app.get("/")
    def index():
        return render_template("index.html", version=__version__)

    @app.get("/expert")
    def expert_page():
        return render_template("expert.html", version=__version__)

    @app.get("/sw.js")
    def service_worker():
        resp = send_from_directory(app.static_folder, "sw.js", mimetype="application/javascript")
        resp.headers["Cache-Control"] = "no-cache"
        return resp

    @app.get("/manifest.webmanifest")
    def manifest():
        return send_from_directory(app.static_folder, "manifest.webmanifest", mimetype="application/manifest+json")

    # ---- farmer API --------------------------------------------------------
    @app.get("/api/meta")
    def api_meta():
        return jsonify({**svc.meta(), "version": __version__})

    @app.post("/api/analyze")
    def api_analyze():
        text = str(body().get("text", ""))[:1000]
        return jsonify(svc.analyze(text))

    @app.post("/api/photo")
    def api_photo():
        if not svc.vision:
            return jsonify({"error": "photo diagnosis is not available on this server"}), 503
        f = request.files.get("photo")
        if not f:
            abort(400, "no photo uploaded")
        try:
            return jsonify(svc.photo(f.read()))
        except Exception:  # noqa: BLE001 - corrupt / unsupported image
            abort(400, "could not read this image")

    @app.post("/api/context")
    def api_context():
        from .services import _location
        from .crop import clean_field
        data = body()
        loc = _location(data)
        if not loc:
            abort(400, "lat/lon required")
        return jsonify(svc.public_context(svc.context(loc, clean_field(data.get("field")))))

    @app.post("/api/voice")
    def api_voice():
        from .llm import LLMError
        if not svc.llm:
            return jsonify({"error": "voice AI is not configured on this server"}), 503
        f = request.files.get("audio")
        if not f:
            abort(400, "no audio uploaded")
        mime = (f.mimetype or "audio/wav").split(";")[0]
        if mime not in ("audio/wav", "audio/x-wav", "audio/webm", "audio/ogg", "audio/mpeg", "audio/mp3", "audio/mp4", "audio/m4a", "audio/flac"):
            abort(400, "unsupported audio type")
        data = f.read()
        if len(data) < 1000:
            abort(400, "recording too short")
        try:
            return jsonify(svc.voice(data, "audio/wav" if mime == "audio/x-wav" else mime))
        except LLMError as e:
            return jsonify({"error": str(e)}), 502

    @app.post("/api/soil")
    def api_soil():
        from .soil import clean
        data = body()
        soil = clean(data.get("soil"))
        if not soil:
            abort(400, "no soil values")
        return jsonify(svc.soil_summary(soil, data.get("crop_type")))

    @app.post("/api/soil/report")
    def api_soil_report():
        from .llm import LLMError
        f = request.files.get("report")
        if not f:
            abort(400, "no report uploaded")
        mime = (f.mimetype or "").split(";")[0]
        if mime not in ("application/pdf", "image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"):
            abort(400, "upload a PDF or a photo of the report")
        try:
            return jsonify(svc.read_soil_report(f.read(), mime))
        except LookupError:
            return jsonify({"error": "needs_ai"}), 503
        except ValueError as e:
            return jsonify({"error": str(e)}), 422
        except LLMError as e:
            return jsonify({"error": str(e)}), 502

    @app.post("/api/diagnose")
    def api_diagnose():
        try:
            return jsonify(svc.diagnose(body()))
        except ValueError as e:
            abort(400, str(e))

    @app.post("/api/feedback")
    def api_feedback():
        try:
            return jsonify(svc.feedback(body()))
        except ValueError as e:
            abort(400, str(e))
        except LookupError as e:
            abort(404, str(e))

    @app.get("/api/diseases")
    def api_diseases():
        return jsonify([svc.disease_card(d) for d in svc.kg.diseases])

    @app.get("/api/disease/<disease_id>")
    def api_disease(disease_id):
        if disease_id not in svc.kg.diseases:
            abort(404, "unknown disease")
        return jsonify(svc.disease_detail(disease_id))

    # ---- expert API --------------------------------------------------------
    @app.get("/api/expert/stats")
    @expert_only
    def ex_stats():
        return jsonify(svc.expert_stats())

    @app.get("/api/expert/graph")
    @expert_only
    def ex_graph():
        return jsonify(svc.expert_graph(request.args.get("layterms") == "1"))

    @app.get("/api/expert/edges")
    @expert_only
    def ex_edges():
        return jsonify(svc.expert_edges())

    @app.get("/api/expert/unmatched")
    @expert_only
    def ex_unmatched():
        return jsonify(svc.db.query("SELECT * FROM unmatched WHERE resolved=0 ORDER BY count DESC, last_seen DESC LIMIT 200"))

    @app.post("/api/expert/unmatched/<int:uid>/resolve")
    @expert_only
    def ex_resolve(uid):
        data = body()
        rows = svc.db.query("SELECT * FROM unmatched WHERE id=?", (uid,))
        if not rows:
            abort(404, "not found")
        try:
            lid = svc.add_layterm(data.get("symptom_id"), data.get("text") or rows[0]["text"],
                                  data.get("lang", "ta"), data.get("weight", 0.8))
        except ValueError as e:
            abort(400, str(e))
        svc.db.resolve_unmatched(uid, data.get("symptom_id"))
        return jsonify({"status": "ok", "layterm_id": lid})

    @app.post("/api/expert/unmatched/<int:uid>/dismiss")
    @expert_only
    def ex_dismiss(uid):
        svc.db.resolve_unmatched(uid, None)
        return jsonify({"status": "ok"})

    @app.post("/api/expert/layterm")
    @expert_only
    def ex_layterm():
        data = body()
        try:
            lid = svc.add_layterm(data.get("symptom_id"), data.get("text"), data.get("lang", "ta"), data.get("weight", 0.8))
        except ValueError as e:
            abort(400, str(e))
        return jsonify({"status": "ok", "layterm_id": lid})

    @app.get("/api/expert/suggestions")
    @expert_only
    def ex_suggestions():
        rows = svc.db.query("SELECT * FROM edge_suggestions WHERE status='open' ORDER BY count DESC")
        for r in rows:
            r["disease"] = svc.kg.diseases.get(r["d"], {}).get("name_en", r["d"])
            r["symptom"] = svc.kg.symptoms.get(r["s"], {}).get("label_en", r["s"])
        return jsonify(rows)

    @app.post("/api/expert/suggestions/<action>")
    @expert_only
    def ex_suggestion_action(action):
        data = body()
        if action == "accept":
            try:
                svc.accept_suggestion(data.get("d"), data.get("s"), data.get("weight", 0.3))
            except ValueError as e:
                abort(400, str(e))
        elif action == "reject":
            svc.db.set_suggestion_status(data.get("d"), data.get("s"), "rejected")
        else:
            abort(404)
        return jsonify({"status": "ok"})

    @app.get("/api/expert/evaluation")
    @expert_only
    def ex_evaluation():
        path = config["EVALUATION_PATH"]
        if not os.path.exists(path):
            return jsonify(None)
        with open(path, encoding="utf-8") as f:
            return jsonify(json.load(f))

    @app.get("/api/expert/vision")
    @expert_only
    def ex_vision():
        return jsonify(svc.vision.meta if svc.vision else None)

    @app.get("/api/expert/outbreaks")
    @expert_only
    def ex_outbreaks():
        return jsonify(svc.expert_outbreaks())

    @app.get("/api/expert/symptoms")
    @expert_only
    def ex_symptoms():
        return jsonify([{"id": s, "label_en": v["label_en"], "label_ta": v["label_ta"]} for s, v in svc.kg.symptoms.items()])

    @app.get("/api/expert/treatments")
    @expert_only
    def ex_treatments():
        return jsonify([{"id": t, "name_en": v["name_en"], "name_ta": v["name_ta"], "type": v["type"]}
                        for t, v in svc.kg.treatments.items()])

    @app.post("/api/expert/disease")
    @expert_only
    def ex_add_disease():
        try:
            did = svc.add_disease(body())
        except ValueError as e:
            abort(400, str(e))
        return jsonify({"status": "ok", "disease_id": did})

    return app
