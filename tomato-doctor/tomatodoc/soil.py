"""
soil.py - soil-test reports: reading them, rating them, and making the diagnosis
and the treatment plan soil-aware.

A soil test is optional. When the farmer provides one (typed in, or read from a
photo / PDF of the Soil Health Card), it is used in three places:

  1. prior     - soil conditions that are known to favour a problem raise its
                 prior a little (e.g. low calcium or salty soil -> blossom-end rot,
                 acidic or sandy soil -> Fusarium wilt, sandy soil -> root-knot
                 nematode). Bounded, so symptoms still decide the diagnosis.
  2. advice    - the diagnosed problem is checked against the soil: root causes to
                 fix (lime, gypsum, calcium, salts, organic matter), fertiliser
                 to hold back (excess nitrogen feeds many foliar diseases and
                 sucking pests), and product cautions (copper in acidic soil).
  3. nutrition - a soil-test-adjusted NPK + micronutrient plan for tomato,
                 converted to bags of common fertilisers per acre.

Ratings follow the classes printed on India's Soil Health Card (sources in
data/agronomy/sources.json); the thresholds live in PARAMS below so an
agronomist can review them in one place.
"""
import re

HA_PER_ACRE = 0.4047

# id: unit, plausible range, rating bands [(upper_bound, rating), ...] (last band open-ended),
#     what each rating means for tomato ("ok" | "watch" | "problem")
PARAMS = {
    "ph": {"unit": "", "range": (3.0, 11.0), "decimals": 1,
           "bands": [(5.5, "strongly_acidic"), (6.0, "acidic"), (7.5, "suitable"), (8.5, "alkaline"), (None, "strongly_alkaline")],
           "status": {"strongly_acidic": "problem", "acidic": "watch", "suitable": "ok", "alkaline": "watch", "strongly_alkaline": "problem"},
           "source": "shc"},
    "ec": {"unit": "dS/m", "range": (0.0, 20.0), "decimals": 2,
           "bands": [(1.0, "normal"), (2.0, "critical"), (None, "saline")],
           "status": {"normal": "ok", "critical": "watch", "saline": "problem"}, "source": "shc"},
    "oc": {"unit": "%", "range": (0.0, 10.0), "decimals": 2,
           "bands": [(0.5, "low"), (0.75, "medium"), (None, "high")],
           "status": {"low": "problem", "medium": "ok", "high": "ok"}, "source": "shc"},
    "n": {"unit": "kg/ha", "range": (0.0, 2000.0), "decimals": 0,
          "bands": [(280, "low"), (560, "medium"), (None, "high")],
          "status": {"low": "watch", "medium": "ok", "high": "watch"}, "source": "shc"},
    "p": {"unit": "kg/ha", "range": (0.0, 500.0), "decimals": 1,
          "bands": [(10, "low"), (25, "medium"), (None, "high")],
          "status": {"low": "watch", "medium": "ok", "high": "ok"}, "source": "shc"},
    "k": {"unit": "kg/ha", "range": (0.0, 3000.0), "decimals": 0,
          "bands": [(108, "low"), (280, "medium"), (None, "high")],
          "status": {"low": "watch", "medium": "ok", "high": "ok"}, "source": "shc"},
    "s": {"unit": "ppm", "range": (0.0, 500.0), "decimals": 1,
          "bands": [(10, "deficient"), (None, "sufficient")], "status": {"deficient": "watch", "sufficient": "ok"}, "source": "shc"},
    "zn": {"unit": "ppm", "range": (0.0, 100.0), "decimals": 2,
           "bands": [(0.6, "deficient"), (None, "sufficient")], "status": {"deficient": "watch", "sufficient": "ok"}, "source": "dtpa"},
    "fe": {"unit": "ppm", "range": (0.0, 500.0), "decimals": 2,
           "bands": [(4.5, "deficient"), (None, "sufficient")], "status": {"deficient": "watch", "sufficient": "ok"}, "source": "dtpa"},
    "mn": {"unit": "ppm", "range": (0.0, 500.0), "decimals": 2,
           "bands": [(2.0, "deficient"), (None, "sufficient")], "status": {"deficient": "watch", "sufficient": "ok"}, "source": "shc"},
    "cu": {"unit": "ppm", "range": (0.0, 200.0), "decimals": 2,
           "bands": [(0.2, "deficient"), (None, "sufficient")], "status": {"deficient": "watch", "sufficient": "ok"}, "source": "dtpa"},
    "b": {"unit": "ppm", "range": (0.0, 50.0), "decimals": 2,
          "bands": [(0.5, "deficient"), (None, "sufficient")], "status": {"deficient": "watch", "sufficient": "ok"}, "source": "shc"},
    "ca": {"unit": "cmol/kg", "range": (0.0, 100.0), "decimals": 1,
           "bands": [(1.5, "deficient"), (None, "sufficient")], "status": {"deficient": "problem", "sufficient": "ok"}, "source": "general"},
    "mg": {"unit": "cmol/kg", "range": (0.0, 60.0), "decimals": 1,
           "bands": [(1.0, "deficient"), (None, "sufficient")], "status": {"deficient": "watch", "sufficient": "ok"}, "source": "general"},
}
ORDER = list(PARAMS)
TEXTURES = ("sandy", "loamy", "clayey")

# Report labels (English, abbreviations, Tamil) -> parameter. Longest/most specific first.
LABELS = [
    ("ec", r"electrical\s+conductivity|\bE\.?\s?C\.?\b|மின்\s*கடத்து\w*"),
    ("oc", r"organic\s+carbon|\bO\.?\s?C\.?\b|கரிமக?\s*கரி\w*|அங்கக\s*கரி\w*"),
    ("ph", r"\bp\.?\s?H\b|கார\s*அமில\w*"),
    ("n", r"(?:available\s+)?nitrogen|\bN\b(?!\s*/)|தழைச்\s*சத்து|நைட்ரஜன்"),
    ("p", r"(?:available\s+)?phosph\w*|\bP\s*2\s*O\s*5\b|\bP\b|மணிச்\s*சத்து|பாஸ்பரஸ்"),
    ("k", r"(?:available\s+)?potass\w*|potash|\bK\s*2\s*O\b|\bK\b|சாம்பல்\s*சத்து|பொட்டாஷ்"),
    ("zn", r"zinc|\bZn\b|துத்தநாகம்"),
    ("fe", r"\biron\b|\bFe\b|இரும்பு"),
    ("mn", r"manganese|\bMn\b|மாங்கனீசு"),
    ("cu", r"copper|\bCu\b|தாமிரம்"),
    ("b", r"boron|\bB\b|போரான்"),
    ("s", r"sulph\w*|sulf\w*|\bS\b|கந்தகம்"),
    ("ca", r"calcium|\bCa\b|கால்சியம்"),
    ("mg", r"magnesium|\bMg\b|மெக்னீசியம்"),
]
_LABEL_RE = [(p, re.compile(rx, re.I)) for p, rx in LABELS]
_NUM = re.compile(r"(?<![\w.])(\d{1,4}(?:\.\d+)?)(?![\d.])")
_P2O5 = re.compile(r"P\s*2\s*O\s*5|P₂O₅", re.I)
_K2O = re.compile(r"K\s*2\s*O|K₂O", re.I)
P2O5_TO_P = 0.4364
K2O_TO_K = 0.8301


def rate(param, value):
    spec = PARAMS[param]
    for upper, rating in spec["bands"]:
        if upper is None or value < upper:
            return rating, spec["status"][rating]
    raise AssertionError("unreachable")


def clean(raw):
    """Untrusted dict (form, Gemini, parser) -> {values: {param: float}, texture, sample_date}."""
    if not isinstance(raw, dict):
        return None
    src = raw.get("values") if isinstance(raw.get("values"), dict) else raw
    values = {}
    for p in ORDER:
        v = src.get(p)
        if isinstance(v, bool) or v is None or v == "":
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        lo, hi = PARAMS[p]["range"]
        if v < 0 or not lo <= v <= hi:
            continue
        values[p] = round(v, 3)
    texture = raw.get("texture") if raw.get("texture") in TEXTURES else None
    date = str(raw.get("sample_date") or "")[:20] or None
    if not values and not texture:
        return None
    return {"values": values, "texture": texture, "sample_date": date}


def interpret(soil):
    """Per-parameter rating for display, plus the list of soil problems."""
    rows = []
    for p in ORDER:
        if p in soil["values"]:
            rating, status = rate(p, soil["values"][p])
            rows.append({"param": p, "value": soil["values"][p], "unit": PARAMS[p]["unit"],
                         "rating": rating, "status": status, "source": PARAMS[p]["source"]})
    return {"params": rows, "texture": soil.get("texture"),
            "problems": [r["param"] for r in rows if r["status"] == "problem"],
            "watch": [r["param"] for r in rows if r["status"] == "watch"]}


def _r(soil, p):
    return rate(p, soil["values"][p])[0] if p in soil["values"] else None


# ---------------------------------------------------------------- 1. prior
FOLIAR_LUSH = {"late_blight", "bacterial_spot", "leaf_mold", "septoria_leaf_spot", "target_spot", "powdery_mildew"}
SUCKING_PESTS = {"whitefly", "spider_mite", "leaf_miner"}
MAX_FACTOR = 2.0


def disease_factors(soil):
    """disease -> (factor, [reasons]). Only diseases with a documented soil link appear."""
    if not soil:
        return {}
    v, tex = soil["values"], soil.get("texture")
    out = {}

    def add(d, f, reason):
        cur, why = out.get(d, (1.0, []))
        out[d] = (min(MAX_FACTOR, cur * f), why + [reason])

    if _r(soil, "ca") == "deficient":
        add("blossom_end_rot", 1.5, "ca_low")
    if _r(soil, "ec") in ("critical", "saline"):
        add("blossom_end_rot", 1.4 if _r(soil, "ec") == "saline" else 1.2, "ec_high")
    if "ph" in v and v["ph"] < 5.5:
        add("blossom_end_rot", 1.2, "ph_acidic")
    if "ph" in v and v["ph"] < 6.0:
        add("fusarium_wilt", 1.3, "ph_acidic")
    if tex == "sandy":
        add("fusarium_wilt", 1.15, "sandy")
        add("root_knot_nematode", 1.4, "sandy")
    if _r(soil, "oc") == "low":
        add("root_knot_nematode", 1.15, "oc_low")
    if _r(soil, "n") == "low":
        add("early_blight", 1.2, "n_low")
    if _r(soil, "k") == "low":
        add("early_blight", 1.1, "k_low")
    if _r(soil, "n") == "high":
        for d in FOLIAR_LUSH | SUCKING_PESTS:
            add(d, 1.15, "n_high")
    return out


# ---------------------------------------------------------------- 2. advice for the diagnosed problem
COPPER = {"copper_hydroxide", "copper_oxychloride"}
BIO_SOIL = {"trichoderma", "pseudomonas_bacillus"}


def advise(disease_id, soil, treatment_ids):
    """Soil findings that matter for this diagnosis -> list of action codes (+ vars)."""
    if not soil:
        return []
    v, tex = soil["values"], soil.get("texture")
    acts = []

    def act(code, why, **kw):
        acts.append({"code": code, "because": why, **kw})

    ph, ec = v.get("ph"), _r(soil, "ec")
    # root causes of the diagnosed problem
    if disease_id == "blossom_end_rot":
        if _r(soil, "ca") == "deficient":
            act("ber_calcium", ["ca"])
        if ph is not None and ph < 6.0:
            act("lime", ["ph"])
        if ec in ("critical", "saline"):
            act("salinity_water", ["ec"])
        if _r(soil, "n") == "high":
            act("ber_ammonium", ["n"])
    if disease_id == "fusarium_wilt":
        if ph is not None and ph < 6.5:
            act("fusarium_lime", ["ph"])
        else:
            act("fusarium_nitrate", [])
        if tex == "sandy":
            act("organic_matter", ["texture"])
    if disease_id == "root_knot_nematode" and (tex == "sandy" or _r(soil, "oc") == "low"):
        act("nematode_organic", ["texture" if tex == "sandy" else "oc"])
    if disease_id == "early_blight":
        if _r(soil, "n") == "low":
            act("eb_nitrogen", ["n"])
        if _r(soil, "k") == "low":
            act("potash", ["k"])
    if _r(soil, "n") == "high" and disease_id in FOLIAR_LUSH | SUCKING_PESTS:
        act("hold_nitrogen", ["n"])
    # treatment-specific cautions
    if ph is not None and ph < 5.5 and COPPER & set(treatment_ids):
        act("copper_acid", ["ph"])
    if _r(soil, "oc") == "low" and BIO_SOIL & set(treatment_ids):
        act("enrich_fym", ["oc"])
    # general soil problems worth fixing whatever the disease (once each)
    done = {a["code"] for a in acts}
    if ph is not None and ph < 5.5 and not done & {"lime", "fusarium_lime"}:
        act("lime", ["ph"])
    if ph is not None and ph >= 8.5:
        act("gypsum_sodic", ["ph"])
    elif ph is not None and ph >= 7.5 and any(_r(soil, m) == "deficient" for m in ("zn", "fe", "mn")):
        act("alkaline_micros", ["ph"])
    if ec == "saline" and "salinity_water" not in done:
        act("salinity_water", ["ec"])
    if _r(soil, "oc") == "low" and not done & {"organic_matter", "nematode_organic", "enrich_fym"}:
        act("organic_matter", ["oc"])
    if disease_id is None and _r(soil, "n") == "high":
        act("hold_nitrogen_general", ["n"])
    return acts


# ---------------------------------------------------------------- 3. nutrient plan
# Tomato blanket recommendation, kg/ha (TNAU Crop Production Guide, Horticulture):
#   varieties 150:100:50 N:P2O5:K2O (N half basal, half top-dressed at 30 days), hybrids 200:250:250.
# Soil-test adjustment (Low +25 %, Medium as is, High -25 %) as used for Soil Health Card advice.
BLANKET = {"variety": {"n": 150, "p": 100, "k": 50}, "hybrid": {"n": 200, "p": 250, "k": 250}}
ADJUST = {"low": 1.25, "medium": 1.0, "high": 0.75}
FERTILISERS = {"urea": 0.46, "ssp": 0.16, "mop": 0.60, "sop": 0.50}
MICRO = {  # deficient -> product, soil dose kg/ha, foliar g/L (None = soil only)
    "zn": ("zinc_sulphate", 25, 5.0),
    "b": ("borax", 10, None),
    "fe": ("ferrous_sulphate", None, 5.0),
    "mn": ("manganese_sulphate", None, 5.0),
    "s": ("gypsum_s", None, None),
}


def nutrient_plan(soil, crop="variety"):
    crop = crop if crop in BLANKET else "variety"
    base = BLANKET[crop]
    v = soil["values"] if soil else {}
    nut = {}
    for el in ("n", "p", "k"):
        rating = rate(el, v[el])[0] if el in v else None
        f = ADJUST.get(rating, 1.0)
        nut[el] = {"rating": rating, "factor": f, "kg_ha": round(base[el] * f, 1)}
    saline = "ec" in v and rate("ec", v["ec"])[0] != "normal"
    potash = "sop" if saline else "mop"
    per_acre = lambda kg_ha: round(kg_ha * HA_PER_ACRE, 1)  # noqa: E731
    n_ac, p_ac, k_ac = (per_acre(nut[e]["kg_ha"]) for e in ("n", "p", "k"))
    urea_half = round(n_ac / 2 / FERTILISERS["urea"])
    products = [
        {"product": "urea", "kg_acre": 2 * urea_half, "basal_kg": urea_half, "top_kg": urea_half, "top_day": 30},
        {"product": "ssp", "kg_acre": round(p_ac / FERTILISERS["ssp"]), "basal_kg": round(p_ac / FERTILISERS["ssp"])},
        {"product": potash, "kg_acre": round(k_ac / FERTILISERS[potash]), "basal_kg": round(k_ac / FERTILISERS[potash])},
    ]
    micros = []
    for el, (prod, soil_kg_ha, foliar_g_l) in MICRO.items():
        if el in v and rate(el, v[el])[0] == "deficient":
            micros.append({"element": el, "product": prod,
                           "kg_acre": per_acre(soil_kg_ha) if soil_kg_ha else None, "foliar_g_l": foliar_g_l})
    return {"crop": crop, "nutrients": nut, "products": products, "potash_form": potash, "saline": saline,
            "fym_t_acre": per_acre(25), "micros": micros, "adjusted": any(nut[e]["rating"] for e in nut),
            "sources": ["tnau_tomato", "shc"]}


# ---------------------------------------------------------------- reading report text (PDF / pasted)
def parse_text(text):
    """Best-effort extraction of soil values from report text. Each line is searched
    for a known label followed by a number in the plausible range."""
    found, basis = {}, {}
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        for p, rx in _LABEL_RE:
            if p in found:
                continue
            m = rx.search(line)
            if not m:
                continue
            after = line[m.end():m.end() + 60]
            nm = _NUM.search(after)
            if not nm:
                continue
            val = float(nm.group(1))
            if p == "p" and _P2O5.search(line):
                val, basis["p"] = val * P2O5_TO_P, "P2O5"
            if p == "k" and _K2O.search(line):
                val, basis["k"] = val * K2O_TO_K, "K2O"
            lo, hi = PARAMS[p]["range"]
            if lo <= val <= hi:
                found[p] = round(val, 3)
                break                       # one parameter per line
    low = (text or "").lower()
    texture = next((t for t, words in (("clayey", ("clay", "களிமண்")), ("sandy", ("sandy", "sand", "மணல்")),
                                       ("loamy", ("loam", "வண்டல்"))) if any(w in low for w in words)), None)
    return {"values": found, "texture": texture, "converted": basis}


def pdf_text(data):
    try:
        from io import BytesIO
        from pypdf import PdfReader
    except ImportError:
        return ""
    try:
        reader = PdfReader(BytesIO(data))
        return "\n".join((pg.extract_text() or "") for pg in reader.pages[:4])
    except Exception:  # noqa: BLE001 - malformed / scanned PDF
        return ""
