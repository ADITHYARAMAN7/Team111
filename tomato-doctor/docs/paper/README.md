# Paper: Tomato Doctor (IEEE conference format)

`main.pdf` is the compiled paper (10 pages, IEEEtran conference class); `main.tex` is its source.
`Tomato_Doctor_IEEE.docx` is the same paper as an editable Word document (IEEE US-Letter two-column
layout, native Word equations, full-width figures floating to the top of the page).

## Reproduce everything

```bash
# 1. experiments -> results/*.json   (all numbers in the paper)
python scripts/experiments.py
# 2. charts -> figures/*.pdf
python docs/paper/make_figures.py
# 3. app screenshots -> figures/screens/  (app running on :5057 with demo data)
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
Edit `main.tex`, not the .docx, if you want the two versions to stay in sync.

## Where each result comes from

| Paper item | Experiment | File |
|---|---|---|
| Table III, Fig. 6, language breakdown | E1 | `results/e1_accuracy.json` |
| Out-of-scope abstention | E1b | `results/e1b_out_of_scope.json` |
| Fig. 7, Fig. 8 | E2 | `results/e2_budget.json` |
| Fig. 9 | E3 | `results/e3_vision.json` |
| Fig. 10 | E4 | `results/e4_learning.json` |
| Table IV | E5 | `results/e5_latency.json` |
| Fig. 11 | E6 (live weather, 13 Oct 2026) | `results/e6_weather.json` |

E6 uses live weather, so re-running it on another day gives different values;
update the date in Section X-G if you regenerate it.

## Before submission

* Replace the author names, affiliations and e-mails in the `\author` block, and edit the acknowledgment.
* Check the target venue's page limit (many IEEE conferences allow 6 pages + extra paid pages).
* Re-run `scripts/experiments.py` if the knowledge graph or code changes, and update the numbers.
