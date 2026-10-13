"""
llm.py - Gemini as a *listening and entity-linking* front end to the knowledge graph.

Division of labour (deliberate, and part of the design):
  Gemini        hears the farmer (Tamil speech -> transcript), and links what was
                said to the graph's own vocabulary: symptom ids, severity, how
                much of the field is affected, how long, crop stage, products
                already sprayed. It is told NOT to diagnose.
  Knowledge graph + Bayesian engine
                does the diagnosis, asks the questions, explains, and learns.
So the AI can never invent a disease or a dosage; everything shown to the
farmer still comes from the curated, cited graph.

API: the Gemini Interactions API (POST /v1beta/interactions) with a JSON schema in
response_format; if that endpoint is unavailable we fall back to the classic
models/{model}:generateContent. Configure with GEMINI_API_KEY / GEMINI_MODEL.
"""
import base64
import json
import logging
import re
import urllib.error
import urllib.request

log = logging.getLogger(__name__)
BASE = "https://generativelanguage.googleapis.com/v1beta"
SEVERITIES = ["mild", "moderate", "severe", "unknown"]
STAGES = ["nursery", "vegetative", "flowering", "fruiting", "harvest", "unknown"]
PARTS = ["leaf", "stem", "fruit", "flower", "root", "whole_plant"]


class LLMError(Exception):
    pass


def build_schema(symptom_ids, treatment_ids, with_transcript):
    props = {
        "language": {"type": "string", "enum": ["ta", "en", "mixed", "other"]},
        "english_summary": {"type": "string", "description": "One-sentence English summary of what the farmer observed."},
        "symptoms": {"type": "array", "items": {"type": "object", "properties": {
            "symptom_id": {"type": "string", "enum": symptom_ids},
            "present": {"type": "boolean", "description": "false if the farmer says this is NOT seen"},
            "confidence": {"type": "number", "description": "0-1: how clearly the farmer described this symptom"},
            "evidence_quote": {"type": "string", "description": "the farmer's own words for it, original script"}},
            "required": ["symptom_id", "present", "confidence", "evidence_quote"]}},
        "severity": {"type": "string", "enum": SEVERITIES},
        "affected_percent": {"type": "integer", "description": "estimated % of plants affected; -1 if not said"},
        "duration_days": {"type": "integer", "description": "days since the problem started; -1 if not said"},
        "plant_parts": {"type": "array", "items": {"type": "string", "enum": PARTS}},
        "crop_stage": {"type": "string", "enum": STAGES},
        "sprays_done": {"type": "array", "items": {"type": "object", "properties": {
            "product": {"type": "string"},
            "treatment_id": {"type": "string", "enum": treatment_ids + ["other"]},
            "days_ago": {"type": "integer", "description": "-1 if not said"}},
            "required": ["product", "treatment_id", "days_ago"]}},
        "weather_mentioned": {"type": "string", "description": "any weather the farmer mentions, else empty"},
    }
    required = ["language", "english_summary", "symptoms", "severity", "affected_percent", "duration_days",
                "plant_parts", "crop_stage", "sprays_done", "weather_mentioned"]
    if with_transcript:
        props = {"transcript": {"type": "string", "description": "verbatim transcript in the original language and script"}, **props}
        required = ["transcript"] + required
    return {"type": "object", "properties": props, "required": required}


def build_prompt(symptoms, treatments, from_audio):
    sym = "\n".join(f"- {s['id']}: {s['label_en']}" for s in symptoms)
    tr = "\n".join(f"- {t['id']}: {t['name_en']}" for t in treatments)
    task = ("First transcribe the recording exactly, in the language and script spoken (Tamil in Tamil script). "
            if from_audio else "")
    return f"""You are the intake assistant of a tomato crop-doctor app used by farmers in Tamil Nadu, India.
{task}Then extract structured facts from what the farmer said.

Rules:
- Do NOT diagnose a disease and do NOT recommend treatments - another system does that.
- Map every observation the farmer describes to the closest symptom_id from the list below.
  Use present=false only when the farmer explicitly says something is NOT there.
  Leave out symptoms the farmer did not talk about.
- Severity: words like கொஞ்சம், லேசா, slight -> mild; அதிகமா, ரொம்ப, முழுக்க, badly, whole field -> severe.
- affected_percent: e.g. "ஒன்னு ரெண்டு செடி" (one or two plants) ~ 5; "பாதி வயல்" (half the field) ~ 50; -1 if unknown.
- sprays_done: products the farmer already applied; map to the closest treatment_id, or "other".
- If the audio has no speech, return an empty transcript and empty lists.

Symptom vocabulary:
{sym}

Treatment vocabulary:
{tr}"""


def _extract_text(data):
    """Pull the model's text out of either API's response."""
    if isinstance(data.get("output_text"), str):
        return data["output_text"]
    texts = []
    for step in data.get("steps") or []:
        if step.get("type") in (None, "model_output"):
            for c in step.get("content") or []:
                if c.get("type") == "text" and c.get("text"):
                    texts.append(c["text"])
    for o in data.get("outputs") or []:
        if o.get("type") == "text" and o.get("text"):
            texts.append(o["text"])
    for cand in data.get("candidates") or []:
        for p in (cand.get("content") or {}).get("parts") or []:
            if p.get("text"):
                texts.append(p["text"])
    if not texts:
        raise LLMError("no text in Gemini response")
    return "".join(texts)


def _parse_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            return json.loads(m.group(0))
        raise LLMError("Gemini did not return JSON")


class GeminiClient:
    def __init__(self, api_key, model="gemini-3.8-flash", timeout=45, transport=None):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.transport = transport or self._http
        self.api_style = "interactions"

    def _http(self, url, body):
        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                     headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                detail = json.loads(e.read().decode("utf-8"))
            except Exception:  # noqa: BLE001
                detail = {}
            return e.code, detail
        except Exception as e:  # noqa: BLE001
            raise LLMError(f"Gemini unreachable: {e}") from e

    def _call(self, prompt, schema, audio=None):
        """audio: (base64, mime) - any media the model accepts inline (audio, image, PDF)."""
        if self.api_style == "interactions":
            inp = [{"type": "text", "text": prompt}]
            if audio:
                kind = "image" if audio[1].startswith("image/") else "document" if audio[1] == "application/pdf" else "audio"
                inp.append({"type": kind, "data": audio[0], "mime_type": audio[1]})
            body = {"model": self.model, "input": inp,
                    "response_format": {"type": "text", "mime_type": "application/json", "schema": schema}}
            status, data = self.transport(f"{BASE}/interactions", body)
            if status == 200:
                return _parse_json(_extract_text(data))
            if status in (401, 403):
                raise LLMError("Gemini API key rejected")
            if status not in (400, 404):
                raise LLMError(f"Gemini error {status}: {str(data)[:200]}")
            log.info("Interactions API returned %s - falling back to generateContent", status)
            self.api_style = "generate_content"
        parts = [{"text": prompt}]
        if audio:
            parts.append({"inline_data": {"mime_type": audio[1], "data": audio[0]}})
        body = {"contents": [{"role": "user", "parts": parts}],
                "generationConfig": {"responseMimeType": "application/json", "responseJsonSchema": schema, "temperature": 0.1}}
        status, data = self.transport(f"{BASE}/models/{self.model}:generateContent", body)
        if status != 200:
            raise LLMError(f"Gemini error {status}: {str(data)[:200]}")
        return _parse_json(_extract_text(data))

    def understand(self, symptoms, treatments, text=None, audio_bytes=None, mime="audio/wav"):
        from_audio = audio_bytes is not None
        schema = build_schema([s["id"] for s in symptoms], [t["id"] for t in treatments], from_audio)
        prompt = build_prompt(symptoms, treatments, from_audio)
        if not from_audio:
            prompt += f"\n\nFarmer's message:\n\"\"\"{text}\"\"\""
        audio = (base64.b64encode(audio_bytes).decode("ascii"), mime) if from_audio else None
        return clean(self._call(prompt, schema, audio), {s["id"] for s in symptoms}, {t["id"] for t in treatments})


    def read_soil_report(self, data, mime):
        """Photo / PDF of a soil test report -> raw values (validated later by soil.clean)."""
        raw = self._call(SOIL_PROMPT, soil_schema(), (base64.b64encode(data).decode("ascii"), mime))
        values = {}
        for p in SOIL_PARAMS:
            v = raw.get(p)
            if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0:
                values[p] = float(v)
        return {"values": values, "texture": raw.get("texture") if raw.get("texture") in ("sandy", "loamy", "clayey") else None,
                "sample_date": str(raw.get("sample_date") or "")[:20] or None,
                "is_soil_report": bool(raw.get("is_soil_report", True))}


SOIL_PARAMS = ["ph", "ec", "oc", "n", "p", "k", "s", "zn", "fe", "mn", "cu", "b", "ca", "mg"]
SOIL_PROMPT = """You read soil test reports for farmers in India (Soil Health Card, private or university lab reports;
English or Tamil). Extract the measured values printed on this report.

Rules:
- Copy numbers exactly as printed; do not estimate or fill in typical values. Use -1 for anything not on the report.
- Units to return: ph (no unit), ec in dS/m (mS/cm is the same; convert µS/cm by /1000), oc in % (organic carbon,
  not organic matter: if only organic matter % is given, divide by 1.724), n, p, k as available kg/ha, s, zn, fe, mn,
  cu, b in ppm (= mg/kg), ca and mg exchangeable in cmol/kg (= meq/100 g).
- If phosphorus is reported as P2O5 multiply by 0.436 to give P; if potassium is reported as K2O multiply by 0.830 to give K.
  If they are given in ppm / mg/kg, multiply by 2.24 to give kg/ha.
- texture: sandy, loamy or clayey if the report states a soil texture/type, else "unknown".
- is_soil_report: false if the image is not a soil test report at all."""


def soil_schema():
    props = {p: {"type": "number"} for p in SOIL_PARAMS}
    props.update({"texture": {"type": "string", "enum": ["sandy", "loamy", "clayey", "unknown"]},
                  "sample_date": {"type": "string", "description": "date the sample was taken/tested, as printed, else empty"},
                  "is_soil_report": {"type": "boolean"}})
    return {"type": "object", "properties": props, "required": ["is_soil_report", "texture", "sample_date", *SOIL_PARAMS]}


def clean(raw, symptom_ids, treatment_ids):
    """Never trust model output blindly: keep only known ids, clamp numbers."""
    def num(v, lo, hi):
        try:
            v = int(v)
        except (TypeError, ValueError):
            return None
        return None if v < 0 else max(lo, min(hi, v))
    syms = []
    for s in raw.get("symptoms") or []:
        if isinstance(s, dict) and s.get("symptom_id") in symptom_ids:
            try:
                conf = max(0.0, min(1.0, float(s.get("confidence", 0.6))))
            except (TypeError, ValueError):
                conf = 0.6
            syms.append({"symptom_id": s["symptom_id"], "present": bool(s.get("present", True)), "confidence": conf,
                         "evidence_quote": str(s.get("evidence_quote") or "")[:200]})
    sprays = []
    for s in raw.get("sprays_done") or []:
        if isinstance(s, dict) and s.get("product"):
            sprays.append({"product": str(s["product"])[:80],
                           "treatment_id": s.get("treatment_id") if s.get("treatment_id") in treatment_ids else None,
                           "days_ago": num(s.get("days_ago"), 0, 365)})
    sev = raw.get("severity")
    return {
        "transcript": str(raw.get("transcript") or "")[:2000],
        "language": raw.get("language") if raw.get("language") in ("ta", "en", "mixed", "other") else None,
        "english_summary": str(raw.get("english_summary") or "")[:400],
        "symptoms": syms,
        "severity": sev if sev in ("mild", "moderate", "severe") else None,
        "affected_percent": num(raw.get("affected_percent"), 0, 100),
        "duration_days": num(raw.get("duration_days"), 0, 365),
        "plant_parts": [p for p in raw.get("plant_parts") or [] if p in PARTS],
        "crop_stage": raw.get("crop_stage") if raw.get("crop_stage") in STAGES[:-1] else None,
        "sprays_done": sprays,
        "weather_mentioned": str(raw.get("weather_mentioned") or "")[:200],
    }


def make_client(config):
    key = config.get("GEMINI_API_KEY")
    if not key:
        return None
    return GeminiClient(key, config.get("GEMINI_MODEL") or "gemini-3.8-flash")
