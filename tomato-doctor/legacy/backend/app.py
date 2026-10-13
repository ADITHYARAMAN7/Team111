"""
app.py - Flask web app for the Tomato Disease Diagnosis demo.

Env vars expected (set these before running, see SETUP_GUIDE.md):
  NEO4J_URI       e.g. neo4j+s://xxxx.databases.neo4j.io
  NEO4J_USER      e.g. neo4j
  NEO4J_PASSWORD  your AuraDB password
"""

import os
from flask import Flask, request, jsonify, render_template
from kg_engine import TomatoKGEngine

app = Flask(__name__)

engine = TomatoKGEngine(
    uri=os.environ.get("NEO4J_URI", "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"),
    user=os.environ.get("NEO4J_USER", "neo4j"),
    password=os.environ.get("NEO4J_PASSWORD", "YOUR_PASSWORD"),
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/diagnose", methods=["POST"])
def diagnose():
    data = request.get_json()
    farmer_text = data.get("text", "").strip()
    already_asked = data.get("already_asked_symptoms", [])

    if not farmer_text:
        return jsonify({"error": "empty input"}), 400

    matched = engine.match_layterms(farmer_text)
    ranked = engine.score_diseases(matched)

    if not ranked:
        return jsonify({
            "status": "no_match",
            "message": "எந்த நோயையும் கண்டறிய முடியவில்லை. மேலும் விவரமாக கூறுங்கள்."
            # "Could not identify a disease. Please describe in more detail."
        })

    top = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None

    # Ambiguous if top two scores are close (within 20% of top score)
    is_ambiguous = second is not None and second["score"] > 0.8 * top["score"]

    if is_ambiguous:
        # Only treat a symptom as "already stated" (and exclude it from
        # being asked as a follow-up) if the farmer's input matched it with
        # HIGH confidence. A weak/borderline match (e.g. score just over the
        # matching threshold) is NOT strong enough grounds to skip asking
        # about it directly - in fact it's often exactly the symptom worth
        # confirming explicitly, since it's what's actually splitting the
        # ambiguous candidates apart.
        HIGH_CONFIDENCE = 0.75
        confidently_stated_symptoms = list({
            m["symptom_id"] for m in matched if m["match_score"] >= HIGH_CONFIDENCE
        })
        exclude = list(set(already_asked) | set(confidently_stated_symptoms))
        question = engine.next_discriminative_question(ranked, exclude)
        return jsonify({
            "status": "clarify",
            "candidates": [{"name_en": c["name_en"], "name_ta": c["name_ta"],
                             "score": round(c["score"], 3)} for c in ranked[:3]],
            "next_question": question
        })

    detail = engine.get_diagnosis_detail(top["disease_id"])
    symptom_descriptions = engine.get_symptom_descriptions(top["matched_symptoms"])
    return jsonify({
        "status": "confirm",
        "disease_id": top["disease_id"],
        "matched_symptoms": top["matched_symptoms"],
        "matched_symptom_descriptions": symptom_descriptions,
        "score": round(top["score"], 3),
        "detail": detail
    })


@app.route("/api/confirm", methods=["POST"])
def confirm():
    data = request.get_json()
    result = engine.record_confirmation(
        disease_id=data["disease_id"],
        matched_symptom_ids=data["matched_symptoms"],
        confirmed=bool(data["confirmed"])
    )
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
