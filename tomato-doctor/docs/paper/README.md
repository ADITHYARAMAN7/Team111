# Paper: Tomato Doctor (IEEE conference format)

`main.pdf` is the compiled paper (13 pages, IEEEtran conference class); `main.tex` is its source.
`Tomato_Doctor_IEEE.docx` is the same paper as an editable Word document (IEEE US-Letter two-column
layout, native Word equations, full-width figures floating to the top of the page).

## Reproduce everything

```bash
# 1. experiments -> results/*.json   (all numbers in the paper; seeds are fixed, so re-runs match exactly)
python scripts/experiments.py                 # E6 uses live weather: skip it to keep the 13 Oct 2026 case study
# 2. charts -> figures/*.pdf
python docs/paper/make_figures.py
# 3. app screenshots -> figures/screens/  (desktop layout; demo app on :5057 with a throw-away database)
export DATABASE_PATH=/tmp/paper_demo.db       # never the real database
python scripts/simulate_outbreaks.py
PORT=5057 python run.py &
python docs/paper/capture_screens.py
# 4. PDF (XeLaTeX engine required for Tamil script)
cd docs/paper && tectonic main.tex          # or: latexmk -xelatex main.tex
```

Architecture, schema and worked-example diagrams are TikZ (`figures/*.tex`).
The Tamil font (Noto Sans Tamil, SIL Open Font License) is in `fonts/`.

## Word version

The Word file is generated from `main.tex`, so both stay identical:

```bash
npm install -g docx          # once
bash docs/paper/word/build.sh   # tex2json.py -> build_docx.js -> finalize.py
```

`word/tex2json.py` parses the LaTeX (text, numbering, citations, tables, algorithm, equations as
Office Math), `word/build_docx.js` lays out the document, `word/finalize.py` inserts the equations.
The diagram and chart images it uses are in `word/assets/` (TikZ compiled from `word/tikz/`, charts
rendered from `figures/*.pdf` at 300 dpi). Edit `main.tex`, not the .docx.

## Where each result comes from

| Paper item | Experiment | File |
|---|---|---|
| Table IV, Fig. 8, language breakdown | E1 | `results/e1_accuracy.json` |
| Out-of-scope abstention | E1b | `results/e1b_out_of_scope.json` |
| Fig. 9, Fig. 10 | E2 | `results/e2_budget.json` |
| Fig. 11 | E3 | `results/e3_vision.json` |
| Fig. 12 | E4 | `results/e4_learning.json` |
| Table V (field profile) | E7 | `results/e7_field_context.json` |
| Table VI (harvest safety) | E8 | `results/e8_harvest_safety.json` |
| Fig. 13 | E6 (live weather, 13 Oct 2026) | `results/e6_weather.json` |
| Table VII | E5 | `results/e5_latency.json` |

E5 (latency) depends on the machine, and E6 uses live weather, so re-running those two gives
different values; update the text if you regenerate them.

## Before submission

* Replace the author names, affiliations and e-mails in the `\author` block, and edit the acknowledgment.
* Check the target venue's page limit (many IEEE conferences allow 6 pages + extra paid pages).
* Run the text through your institution's similarity checker (e.g. Turnitin / iThenticate).
* Re-run `scripts/experiments.py` if the knowledge graph or code changes, and update the numbers.
