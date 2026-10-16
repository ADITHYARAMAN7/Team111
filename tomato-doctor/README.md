# தக்காளி டாக்டர் · Tomato Doctor

A Tamil-first crop doctor for tomato growers. The farmer describes the problem
in their own words — typed or spoken, in Tamil, English or Tanglish — and can
add a leaf photo. The system reasons over a **knowledge graph** of diseases,
symptoms, farmer phrases and treatments, asks only the few follow-up questions
that best separate the remaining candidates, confirms the diagnosis against
reference photos, and gives cited treatment, dosage and prevention advice.
Every confirmed diagnosis teaches the graph.

## Quick start

```bash
pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:5000 (farmer app) and http://127.0.0.1:5000/expert
(expert console). No database setup is needed: by default the graph is
loaded from `tomatodoc/kg/seed/tomato_kg.json` and learning is stored in
`instance/tomatodoc.db`.

To open the app on a phone on the same Wi-Fi: set `HOST=0.0.0.0` and
`EXPERT_TOKEN=<something>` in `.env`, then browse to `http://<laptop-ip>:5000`.
(Voice input and "install app" need HTTPS or localhost in most browsers.)

### Using Neo4j (AuraDB or local)

```bash
cp .env.example .env           # fill in NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD
python scripts/seed_neo4j.py   # MERGE the curated graph (add --reset to wipe first)
python run.py                  # KG_BACKEND=auto picks Neo4j when it is seeded
```

Learned weights are written back onto the relationships (`alpha`, `beta`,
`weight`), so the live graph can be explored in Neo4j Browser. No database at
all? `python scripts/seed_neo4j.py --export-cypher docs/tomato_kg.cypher` writes
a script you can paste into the Aura query window. If Neo4j is unreachable (Aura
Free pauses idle instances), the app falls back to the embedded graph instead of
failing — important for a live demo.

## What the farmer gets

| Feature | Detail |
|---|---|
| Describe in any language | Tamil, English, Tanglish, mixed; typos and Tamil inflections handled; negation understood ("பூச்சி இல்லை", "no insects") |
| Voice in / voice out | Browser speech recognition (`ta-IN`) and read-aloud of questions and results |
| Photo | Leaf photo classifier (97.6 % on held-out PlantVillage images) with blur / darkness / "no leaf" checks; fused with the graph, never trusted alone |
| Tap-to-pick symptoms | 45 symptoms grouped by plant part, for low-literacy users or when text is not understood |
| Smart questions | 2.1 questions on average; Yes / No / Not sure; live probability bars |
| Honest uncertainty | An explicit "something else" hypothesis; uncertain results show photo comparisons instead of a guess |
| Result | Disease in Tamil + English, probability, urgency, contagion warning, reference photos, "why this diagnosis" chain, things to check next |
| Treatment | Organic / field-practice / chemical tabs, dosages, source citation per item, pesticide safety note |
| Context | Season from calendar, local weather (Open-Meteo, via the browser) or the farmer's choice — shifts the prior via `FAVORED_BY` edges |
| Feedback | "Yes, this is it" / "No" → pick the right one from photos → the graph learns |
| Also | Disease library, consultation history, WhatsApp share, print, installable PWA, dark mode, Kisan Call Centre number |

## Location- and weather-aware advice (v2.1)

Share a location (GPS or pick a district) and the app uses **the weather your
plants actually experienced**:

| Feature | How |
|---|---|
| Disease-risk early warning | Published forecast models run on 7 days of hourly local weather: **Hutton criteria** (late blight), **TOM-CAST** (early blight), plus dataset rules for 11 other diseases — shown on the home screen before symptoms appear |
| Weather-driven diagnosis | The risk scores replace the calendar season as the Bayesian **prior**, so the same symptoms are read in the light of local conditions |
| Spray-window finder | Next hours that are rain-free for the product's rain-fast period, wind < 15–20 km/h and below its heat limit; every treatment gets "OK now" / "wait — rain in 3 h" / "too hot, spray after 4 PM" |
| Rain-aware ranking | Systemic products rank above contact ones when rain is coming |
| Severity-adaptive plan | Mild → field practice + organic first; severe → effective chemical now; field scope from how many plants are affected |
| Resistance rotation | Products the farmer already sprayed are matched to FRAC/IRAC groups; the plan switches group and the schedule alternates groups |
| Dose calculator + calendar | Per 16 L tank and per cents/acres; dated schedule exported as a calendar file with reminders |
| Community outbreak alerts | Farmer-confirmed diagnoses (location rounded to ~5 km) become reports; cases within 30 km in 3 weeks alert neighbours and raise that disease's prior; expert outbreak map |

**Gemini voice understanding** (`GEMINI_API_KEY` in `.env`): the farmer
speaks; Gemini transcribes the Tamil and *links it to the graph's own
vocabulary* — symptom ids, severity ("கொஞ்சம்" → mild), % of plants affected,
duration, crop stage, products already sprayed. It never diagnoses: the
knowledge graph still reasons, asks and explains. Without a key, the browser's
speech recognition and the built-in matcher are used, and severity/extent are
still extracted from plain words.

The data and sources behind these features: [`data/agronomy/`](data/agronomy/README.md).
Demo the outbreak map with `python scripts/simulate_outbreaks.py`
(rows are labelled *simulated*; remove with `--clear`).

**Automatic location.** On first open the app asks the browser for location
(permission prompt), names the nearest district ("Near Krishnagiri") and loads
the field's weather and risk forecast straight away. A GPS location is refreshed
on each visit; a district picked by hand is kept. If permission is refused, the
home screen offers the district picker instead. Browsers only share location on
`https://` or `localhost` pages.

## My field: crop stage, harvest safety, early warnings (v2.3)

The leaf-and-soil icon in the top bar opens **My field** (optional; saved on the
phone once, then sent with every diagnosis). It holds the transplanting date,
variety, hybrid/variety, area, picking rhythm, field location and soil report.

| Feature | How |
|---|---|
| Crop stage | Days after transplanting → establishment, vegetative, flowering, fruit set, harvest (typical 135–150-day crop). The stage adjusts the prior: fruit disorders and fruit borer are unlikely before there is fruit; early blight builds up on older plants; leaf curl hits young plants hardest |
| Harvest safety | Every sprayable product has a pre-harvest interval (PHI). While fruit is being picked (by stage, or set by the farmer with last-picked date and interval), each treatment shows from when picking is safe, counted from the day it will actually be sprayed; products whose PHI is longer than the picking interval move down the plan with the reason, and the schedule shows "pick from …" for every spray |
| Early warning | When the weather risk for a disease is high, the home screen proposes a preventive spray from the graph (protectants/bio-agents preferred, harvest-safe while picking) with the next good spray window |
| Field-aware tools | Dose calculator uses the field area; the fertiliser plan dates the day-30 top dressing |

PHI values are conservative defaults (≥ typical tomato label intervals); the
product label is final — see `data/agronomy/`.

### Soil test report (optional, v2.2)

The soil report is part of My field. It is never required, and nothing about it
appears on the diagnosis screen itself. The farmer can:

* **upload** the report: a text PDF (e.g. a downloaded Soil Health Card) is read
  locally; a photo or scanned PDF is read by Gemini (values only, validated
  against plausible ranges, P₂O₅/K₂O converted); or
* **type** the values (pH, EC, organic carbon, N, P, K, S, Zn, Fe, Mn, Cu, B, Ca,
  Mg, soil type).

The values are kept on the phone and sent along with each diagnosis, where they:

| Use | How |
|---|---|
| Soil-aware diagnosis | Documented soil links raise the prior (bounded ×2): low Ca / salinity / acidity → blossom-end rot; acidic or sandy soil → Fusarium wilt; sandy, low-organic soil → root-knot nematode; low N/K → early blight; excess N → lush-growth diseases and sucking pests |
| Root-cause treatment | The result gets a *Soil-aware advice* card: gypsum/calcium and lime for blossom-end rot, lime + nitrate-N for Fusarium wilt, salinity management, hold back urea, copper caution in strongly acidic soil, enriched FYM for bio-agents |
| Fertiliser plan | TNAU tomato recommendation adjusted by the soil test (Low +25 %, High −25 %), as bags of urea / SSP / MOP (SOP on salty soil) per acre, basal vs. day-30 top dressing, plus micronutrients that test deficient |

Ratings use the Soil Health Card classes; thresholds and rules are in
[`tomatodoc/soil.py`](tomatodoc/soil.py), sources in `data/agronomy/sources.json`.

## Expert console (`/expert`)

Overview analytics · interactive knowledge-graph explorer · **outbreak map** · **Teach language**
(phrases the system did not understand, mapped to a symptom in one click — the
LayTerm layer grows from real usage) · **Learning** audit (seed vs learned
weight of every edge, suggested new edges) · evaluation report · photo-model
confusion matrix.

## How it works

```
farmer text ─► NLU (concepts + IDF coverage + negation) ─► symptom evidence ─┐
leaf photo  ─► ONNX classifier + quality checks ─► tempered likelihood ──────┤
season / weather ─► FAVORED_BY prior ────────────────────────────────────────┤
                                                                             ▼
                 Bayesian posterior over 17 diseases + "unknown"   (Neo4j / embedded KG)
                         │                         │
            top < 85 % and useful question?        └─► result + explanation + treatments
                         ▼                                          │
       ask symptom with max expected information gain        farmer confirms / corrects
                                                                    ▼
                                         Beta updates on HAS_SYMPTOM / LAYTERM_MAPS_TO
```

**Knowledge graph** (`tomatodoc/kg/seed/tomato_kg.json`): 17 diseases, 45
symptoms, 247 lay-terms (Tamil, English, Tanglish), 30 treatments, 3 seasons,
131 weighted `HAS_SYMPTOM` + 65 `TREATED_BY` edges. Treatments are cited to
Jagtap et al. 2025 (Mendeley Data, DOI 10.17632/ztncd79yhk.1) or marked as
general extension guidance.

**Language layer** (`nlu.py`, `lexicon.py`): words are mapped to
language-independent concepts (தூள் / பொடி / powder / podi → POWDER) with
Tamil stem matching. A lay-term phrase matches when the IDF-weighted share of
its concepts found in the input passes a threshold, and its most informative
concepts must be present. This fixes the v1 failure where shared filler words
("இலையில்", "போல") made "white dust on the leaf" match Target Spot.

**Reasoning** (`inference.py`):
`P(d | E) ∝ P(d) · Π P(report | d) · L_photo(d)`, where each report has a
reliability `c` and asymmetric noise (`P(present | d) = cθ + 0.3(1−c)(1−θ)`), so
a weak language match moves the posterior only a little. The next question
maximises `EIG(s) = H(D) − Σ P(a) H(D | a)` discounted by an observation cost
(cutting a stem, uprooting a plant).

**Learning** (`learning.py`): edge weights are Beta(α, β) posteriors seeded
with 20 pseudo-observations. Only confirmed or corrected outcomes update them;
a bare "no" is logged but changes nothing. Symptoms reported for a confirmed
disease that has no such edge become *suggested edges* for expert review.

## Evaluation

85 farmer descriptions written independently of the lay-terms, each followed by 20 simulated
noisy dialogues (`python scripts/experiments.py`, seeds fixed; full results and ablations in
the paper, `docs/paper/`).

| Metric | v1 prototype | v2 + random questions | **v2** |
|---|---:|---:|---:|
| Top-1 accuracy, description only | 63.5 % | 92.9 % | 92.9 % |
| Top-1 accuracy after dialogue | 63.5 % | 94.6 % | **96.5 %** |
| Confidently wrong | 10.6 % | 0.8 % | 1.1 % |
| Avg. follow-up questions | — | 3.49 | **2.05** |

Field profile (soil report + crop stage, E7): a consistent profile halves confidently wrong
answers (1.1 % → 0.6 %); a misleading one costs no accuracy after dialogue. Harvest safety
(E8, 741 picking scenarios): spray schedules that clash with the next picking fall from
49.3 % to 4.9 %.

The test sentences were written by the authors and the simulated farmer
answers from the graph's own probabilities, so this measures the reasoning
pipeline, not field accuracy. Weakest pair: Bacterial Spot vs Target Spot,
which genuinely share early symptoms; a photo resolves most of these.
`python scripts/evaluate.py` writes a quick benchmark to `docs/evaluation.md`, shown in the
expert console.

## Project layout

```
run.py                      start the web app
tomatodoc/
  kg/seed/tomato_kg.json    the curated knowledge graph (single source of truth)
  kg/graph.py, kg/store.py  in-memory graph + embedded / Neo4j stores
  lexicon.py, nlu.py        Tamil/English/Tanglish understanding
  inference.py              Bayesian diagnosis + information-gain questions
  learning.py               feedback → graph updates
  vision.py, context.py     photo model, season
  weather.py, risk.py       local weather + disease-risk models (Hutton, TOM-CAST, ...)
  advisory.py               spray windows, severity plan, FRAC/IRAC rotation, schedule
  soil.py                   soil report reading, ratings, soil-aware prior/advice, fertiliser plan
  crop.py                   crop stage from transplanting date, picking rhythm, pre-harvest intervals
  llm.py                    Gemini voice/text understanding (entity linking to the KG)
  services.py, __init__.py  use-cases + HTTP API (Flask)
  templates/, static/       farmer app (PWA) and expert console
scripts/  train_vision.py · seed_neo4j.py · evaluate.py · simulate_outbreaks.py
models/   leaf_classifier.onnx + metrics          tests/   pytest suite
data/     Mendeley dataset + parser, evaluation cases
tomato/   PlantVillage tomato images (train/val)   legacy/  the v1 prototype
```

## Development

```bash
python -m pytest                                      # 111 tests (3 need Neo4j)
TEST_NEO4J_URI=bolt://localhost:7687 TEST_NEO4J_PASSWORD=... python -m pytest tests/test_neo4j.py
python scripts/train_vision.py                        # retrain photo model (needs torch)
```

Add a disease or symptom by editing `tomato_kg.json`; `validate_seed` (run by
the tests and the seeder) checks referential integrity.

*Guidance only — for severe damage consult your agricultural officer / KVK.
Kisan Call Centre: 1800-180-1551.*
