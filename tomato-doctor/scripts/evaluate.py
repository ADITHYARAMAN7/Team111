"""
evaluate.py - benchmark the diagnosis pipeline on held-out farmer descriptions.

Methods compared (all on the SAME knowledge graph, so only the algorithm differs):
  v1     : the original prototype - whole-phrase fuzzy matching (token_sort_ratio
           >= 55), additive scoring, variance-based follow-up question whose answer
           is not fed back into scoring (as in the v1 code), so its final answer is
           its text-only answer.
  random : v2 language layer + Bayesian inference, but follow-up questions chosen
           at random (ablation: what does information-gain selection buy us?)
  v2     : full system - concept-level Tamil/English/Tanglish matching, Bayesian
           posterior with an explicit "unknown" hypothesis, expected-information-gain
           question selection.

Simulated farmer: answers "yes" to a question about symptom s with probability
theta(true disease, s) (or 0.02 if the graph has no such edge), so answers are
noisy and realistic rather than oracle-perfect. Each case is run N_RUNS times.

Usage:  python scripts/evaluate.py          -> docs/evaluation.json + docs/evaluation.md
"""
import json
import os
import random
import sys
import time
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rapidfuzz import fuzz  # noqa: E402

from tomatodoc.inference import CONFIDENT, MAX_QUESTIONS, UNKNOWN, DiagnosisEngine  # noqa: E402
from tomatodoc.kg.graph import KnowledgeGraph, load_seed, seed_to_data  # noqa: E402
from tomatodoc.nlu import SymptomMatcher  # noqa: E402

N_RUNS = 20
CASES = os.path.join(ROOT, "data", "eval", "test_cases.json")
OUT_JSON = os.path.join(ROOT, "docs", "evaluation.json")
OUT_MD = os.path.join(ROOT, "docs", "evaluation.md")


# ----------------------------------------------------------------- v1 baseline
def v1_rank(kg, text):
    """Faithful re-implementation of the v1 kg_engine.match_layterms + score_diseases."""
    matched = []
    for lt in kg.layterm_list():
        score = fuzz.token_sort_ratio(text, lt["text"])
        if score >= 55:
            matched.append((lt["symptom_id"], lt["weight"] * score / 100.0))
    relevance = {}
    for sid, rel in matched:          # v1 used a dict comprehension: last match wins
        relevance[sid] = rel
    scores = defaultdict(float)
    for (d, s), e in kg.edges.items():
        if s in relevance:
            scores[d] += relevance[s] * e["seed"]
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    return ranked, bool(matched)


# ----------------------------------------------------------------- v2 dialogue
def simulate(engine, kg, text_matches, truth, rng, chooser="eig"):
    answers = []
    for _ in range(MAX_QUESTIONS + 1):
        ev = engine.build_evidence(text_matches, answers)
        if chooser == "eig":
            st = engine.step(ev, asked=[a["symptom_id"] for a in answers])
            if st["status"] != "question":
                break
            s = st["question"]["symptom_id"]
        else:
            post, _ = engine.posterior(ev)
            top = max(post.values()) if ev else 0
            if ev and (top >= CONFIDENT or len(answers) >= MAX_QUESTIONS):
                break
            if not ev and len(answers) >= MAX_QUESTIONS:
                break
            seen = {e["symptom_id"] for e in ev} | {a["symptom_id"] for a in answers}
            pool = [s for s in kg.symptoms if s not in seen and any(post[d] > 0.01 for d in kg.diseases_of[s])]
            if not pool:
                break
            s = rng.choice(pool)
        th = kg.theta(truth, s)
        p_yes = th if th is not None else 0.02
        answers.append({"symptom_id": s, "answer": "yes" if rng.random() < p_yes else "no"})
    ev = engine.build_evidence(text_matches, answers)
    post, _ = engine.posterior(ev)
    ranked = sorted(((h, p) for h, p in post.items() if h != UNKNOWN), key=lambda kv: -kv[1])
    return ranked, len(answers)


def main():
    seed = load_seed()
    kg = KnowledgeGraph(seed_to_data(seed))
    matcher = SymptomMatcher(kg.layterm_list())
    engine = DiagnosisEngine(kg)
    with open(CASES, encoding="utf-8") as f:
        cases = json.load(f)

    methods = {
        "v1": {"name": "v1 prototype", "rows": []},
        "random": {"name": "v2 + random questions", "rows": []},
        "v2": {"name": "v2 (this system)", "rows": []},
    }
    t0 = time.time()
    for truth, lang, text in cases:
        # ---- v1
        ranked, understood = v1_rank(kg, text)
        top = ranked[0][0] if ranked else None
        ambiguous = len(ranked) > 1 and ranked[1][1] > 0.8 * ranked[0][1]
        methods["v1"]["rows"].append({
            "truth": truth, "lang": lang, "understood": understood, "top1_text": top == truth, "top1": top == truth,
            "top3": truth in [d for d, _ in ranked[:3]], "questions": None,
            "wrong_confident": bool(ranked) and not ambiguous and top != truth})
        # ---- v2 / random
        tm = matcher.match(text)["matches"]
        post0, _ = engine.posterior(engine.build_evidence(tm))
        top_text = max((h for h in post0 if h != UNKNOWN), key=post0.get)
        for mid in ("v2", "random"):
            rng = random.Random(hash((text, mid)) & 0xFFFFFFFF)
            for _ in range(N_RUNS):
                ranked, nq = simulate(engine, kg, tm, truth, rng, "eig" if mid == "v2" else "random")
                methods[mid]["rows"].append({
                    "truth": truth, "lang": lang, "understood": bool(tm), "top1_text": bool(tm) and top_text == truth,
                    "top1": ranked[0][0] == truth, "top3": truth in [d for d, _ in ranked[:3]], "questions": nq,
                    "wrong_confident": ranked[0][0] != truth and ranked[0][1] >= CONFIDENT})

    def agg(rows):
        n = len(rows)
        mean = lambda k: sum(1 for r in rows if r[k]) / n if n else None  # noqa: E731
        qs = [r["questions"] for r in rows if r["questions"] is not None]
        by_lang = {}
        for l in ("ta", "en", "tl"):
            lr = [r for r in rows if r["lang"] == l]
            by_lang[l] = sum(1 for r in lr if r["top1"]) / len(lr) if lr else None
        return {"text_understood": mean("understood"), "top1_text_only": mean("top1_text"), "top1_final": mean("top1"),
                "top3_final": mean("top3"), "wrong_confident": mean("wrong_confident"),
                "avg_questions": sum(qs) / len(qs) if qs else None, "by_lang": by_lang}

    out_methods = [{"id": mid, "name": m["name"], **agg(m["rows"])} for mid, m in methods.items()]
    per_disease = []
    for d in kg.diseases:
        row = {"disease": d, "name": kg.diseases[d]["name_en"], "n": sum(1 for c in cases if c[0] == d)}
        for mid, m in methods.items():
            rows = [r for r in m["rows"] if r["truth"] == d]
            row[mid] = sum(1 for r in rows if r["top1"]) / len(rows) if rows else None
        per_disease.append(row)

    result = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M"), "n_cases": len(cases), "n_runs": N_RUNS,
        "description": "Free-text farmer descriptions (Tamil, English, Tanglish) of all 17 diseases, written independently "
                       "of the knowledge graph's lay-term phrases, followed by a simulated noisy dialogue.",
        "caveat": "The test descriptions were written by the system's authors, and the simulated farmer answers according to "
                  "the knowledge graph's own probabilities - so these numbers measure the reasoning pipeline, not field "
                  "accuracy. A field study with real farmer descriptions is the next validation step.",
        "methods": out_methods, "per_disease": per_disease, "runtime_s": round(time.time() - t0, 1),
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    p = lambda v: "—" if v is None else f"{v * 100:.1f}%"  # noqa: E731
    lines = [f"# Evaluation ({result['generated_at']})", "", result["description"], "",
             f"{len(cases)} cases × {N_RUNS} simulated dialogues.", "",
             "| Metric | " + " | ".join(m["name"] for m in out_methods) + " |", "|---|" + "---:|" * len(out_methods)]
    for k, label in [("text_understood", "Input understood"), ("top1_text_only", "Top-1, description only"),
                     ("top1_final", "Top-1 after dialogue"), ("top3_final", "Top-3 after dialogue"),
                     ("wrong_confident", "Confidently wrong")]:
        lines.append(f"| {label} | " + " | ".join(p(m[k]) for m in out_methods) + " |")
    lines.append("| Avg. questions | " + " | ".join("—" if m["avg_questions"] is None else f"{m['avg_questions']:.2f}" for m in out_methods) + " |")
    for l, name in (("ta", "Tamil"), ("en", "English"), ("tl", "Tanglish")):
        lines.append(f"| Top-1 after dialogue, {name} | " + " | ".join(p(m["by_lang"][l]) for m in out_methods) + " |")
    lines += ["", "## Per disease (top-1 after dialogue)", "", "| Disease | " + " | ".join(m["name"] for m in out_methods) + " |",
              "|---|" + "---:|" * len(out_methods)]
    for r in per_disease:
        lines.append(f"| {r['name']} | " + " | ".join(p(r[m['id']]) for m in out_methods) + " |")
    lines += ["", f"> {result['caveat']}", ""]
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines[:16]))
    print(f"\nwrote {OUT_JSON} ({result['runtime_s']}s)")


if __name__ == "__main__":
    main()
