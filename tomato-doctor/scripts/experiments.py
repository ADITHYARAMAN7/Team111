"""
experiments.py - every number reported in the paper (docs/paper) is produced here.

    python scripts/experiments.py            # all experiments (~5 min on a laptop CPU)
    python scripts/experiments.py e1 e4      # selected experiments

Outputs: docs/paper/results/<experiment>.json

E1  diagnostic accuracy + ablations on the 85 held-out farmer descriptions
E1b out-of-scope problems: abstention with / without the UNKNOWN hypothesis
E2  accuracy as a function of the question budget, per question-selection strategy
E3  leaf-photo classifier: clean vs. degraded images, alone and fused with the dialogue
E4  online learning from farmer confirmations, starting from a corrupted graph
E5  latency of one dialogue step
E6  weather-driven risk case study for four Tamil Nadu districts (live weather)
E7  field context: soil report + crop stage that agree with, or mislead about, the true problem
E8  harvest safety: pre-harvest-interval conflicts of the spray plan with the farmer's picking rhythm
"""
import copy
import glob
import io
import json
import math
import os
import random
import statistics
import sys
import time
import zlib
from datetime import datetime, timedelta

# String hashing (set/dict iteration order) is randomised per process; fix it so that every
# number in the paper is reproduced exactly on re-run.
if os.environ.get("PYTHONHASHSEED") != "0":
    import subprocess
    sys.exit(subprocess.call([sys.executable] + sys.argv, env={**os.environ, "PYTHONHASHSEED": "0"}))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from tomatodoc import advisory, crop, inference, risk, soil, weather  # noqa: E402
from tomatodoc.inference import CONFIDENT, MAX_QUESTIONS, UNKNOWN, DiagnosisEngine, report_likelihood  # noqa: E402
from tomatodoc.kg.graph import PRIOR_STRENGTH, KnowledgeGraph, load_seed, seed_to_data  # noqa: E402
from tomatodoc.learning import plan_updates  # noqa: E402
from tomatodoc.nlu import SymptomMatcher  # noqa: E402

OUT = os.path.join(ROOT, "docs", "paper", "results")
CASES = json.load(open(os.path.join(ROOT, "data", "eval", "test_cases.json"), encoding="utf-8"))
N_RUNS = 20
LEAK_ANSWER = 0.02


def save(name, obj):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"{name}.json"), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    print(f"  -> results/{name}.json")


def fresh_kg():
    return KnowledgeGraph(seed_to_data(load_seed()))


def bootstrap_ci(per_case, n=2000, seed=1):
    rng = random.Random(seed)
    k = len(per_case)
    means = sorted(sum(per_case[rng.randrange(k)] for _ in range(k)) / k for _ in range(n))
    return [round(means[int(0.025 * n)], 4), round(means[int(0.975 * n)], 4)]


# ------------------------------------------------------------------ dialogue simulation
def answer(kg, truth, s, rng):
    th = kg.theta(truth, s)
    return "yes" if rng.random() < (th if th is not None else LEAK_ANSWER) else "no"


def choose_variance(engine, kg, post, observed):
    """v1 heuristic: among the top-3 candidates, prefer a symptom absent for some
    candidate (score 1), else the variance of its weights across candidates."""
    top = [h for h, _ in sorted(((h, p) for h, p in post.items() if h != UNKNOWN), key=lambda kv: -kv[1])[:3]]
    best, best_s = None, -1
    for s in kg.symptoms:
        if s in observed:
            continue
        ws = [kg.theta(d, s) for d in top]
        if all(w is None for w in ws):
            continue
        if any(w is None for w in ws):
            score = 1.0
        else:
            m = sum(ws) / len(ws)
            score = sum((w - m) ** 2 for w in ws) / len(ws)
        if score > best_s:
            best, best_s = s, score
    return best


def dialogue(engine, kg, text_matches, truth, rng, strategy="eig", budget=MAX_QUESTIONS, photo=None, factors=None):
    answers = []
    while True:
        ev = engine.build_evidence(text_matches, answers)
        post, _ = engine.posterior(ev, photo=photo, factors=factors)
        top_p = max(p for h, p in post.items() if h != UNKNOWN)
        if len(answers) >= budget or (ev or photo) and top_p >= CONFIDENT:
            break
        observed = {e["symptom_id"] for e in ev} | {a["symptom_id"] for a in answers}
        if strategy == "eig":
            ranked = engine.rank_questions(post, observed)
            if not ranked or ranked[0][1] < inference.MIN_EIG:
                break
            s = ranked[0][2]
        elif strategy == "variance":
            s = choose_variance(engine, kg, post, observed)
        else:
            pool = [s for s in kg.symptoms if s not in observed and any(post[d] > 0.01 for d in kg.diseases_of[s])]
            s = rng.choice(pool) if pool else None
        if s is None:
            break
        answers.append({"symptom_id": s, "answer": answer(kg, truth, s, rng)})
    ev = engine.build_evidence(text_matches, answers)
    post, _ = engine.posterior(ev, photo=photo, factors=factors)
    ranked = sorted(((h, p) for h, p in post.items() if h != UNKNOWN), key=lambda kv: -kv[1])
    return ranked, len(answers)


def v1_matches(kg, text):
    """v1 language layer (token_sort_ratio >= 55, last match wins) as evidence for the v2 engine."""
    from rapidfuzz import fuzz
    rel = {}
    for lt in kg.layterm_list():
        sc = fuzz.token_sort_ratio(text, lt["text"])
        if sc >= 55:
            rel[lt["symptom_id"]] = {"symptom_id": lt["symptom_id"], "present": True, "strength": lt["weight"] * sc / 100,
                                     "layterm_id": lt["id"], "phrase": lt["text"]}
    return list(rel.values())


def v1_rank(kg, text):
    from rapidfuzz import fuzz
    rel = {}
    for lt in kg.layterm_list():
        sc = fuzz.token_sort_ratio(text, lt["text"])
        if sc >= 55:
            rel[lt["symptom_id"]] = lt["weight"] * sc / 100
    scores = {}
    for (d, s), e in kg.edges.items():
        if s in rel:
            scores[d] = scores.get(d, 0) + rel[s] * e["seed"]
    return sorted(scores.items(), key=lambda kv: -kv[1]), bool(rel)


# ------------------------------------------------------------------ E1
def e1():
    print("E1 diagnostic accuracy + ablations")
    kg = fresh_kg()
    matcher = SymptomMatcher(kg.layterm_list())
    eng = DiagnosisEngine(kg)
    methods = [
        ("v1", "v1 prototype (fuzzy match + additive score)"),
        ("v1nlu_bayes_eig", "v1 matching + Bayesian + EIG"),
        ("text_only", "v2 matching + Bayesian, no questions"),
        ("random", "v2 + random questions"),
        ("variance", "v2 + variance heuristic (v1 rule)"),
        ("eig", "v2 + EIG (proposed)"),
        ("eig_symmetric", "proposed, symmetric noise"),
        ("eig_no_unknown", "proposed, no UNKNOWN hypothesis"),
    ]
    rows = {m: [] for m, _ in methods}
    for truth, lang, text in CASES:
        ranked, understood = v1_rank(kg, text)
        top = ranked[0][0] if ranked else None
        amb = len(ranked) > 1 and ranked[1][1] > 0.8 * ranked[0][1]
        rows["v1"].append({"truth": truth, "lang": lang, "text": text, "understood": understood, "top1": [top == truth],
                           "top3": [truth in [d for d, _ in ranked[:3]]], "q": [None],
                           "wrong_conf": [bool(ranked) and not amb and top != truth]})
        tm = matcher.match(text)["matches"]
        v1tm = v1_matches(kg, text)
        for m, _ in methods[1:]:
            r = {"truth": truth, "lang": lang, "text": text, "understood": bool(tm if m != "v1nlu_bayes_eig" else v1tm),
                 "top1": [], "top3": [], "q": [], "wrong_conf": []}
            saved = (inference.FALSE_ALARM, inference.UNKNOWN_PRIOR)
            if m == "eig_symmetric":
                inference.FALSE_ALARM = 1.0
            if m == "eig_no_unknown":
                inference.UNKNOWN_PRIOR = 1e-9
            rng = random.Random(zlib.crc32(f"{text}|{m}".encode("utf-8")))   # stable across runs
            for _ in range(N_RUNS if m != "text_only" else 1):
                strategy = {"random": "random", "variance": "variance"}.get(m, "eig")
                budget = 0 if m == "text_only" else MAX_QUESTIONS
                ranked2, nq = dialogue(eng, kg, v1tm if m == "v1nlu_bayes_eig" else tm, truth, rng, strategy, budget)
                r["top1"].append(ranked2[0][0] == truth)
                r["top3"].append(truth in [d for d, _ in ranked2[:3]])
                r["q"].append(nq)
                r["wrong_conf"].append(ranked2[0][0] != truth and ranked2[0][1] >= CONFIDENT)
            inference.FALSE_ALARM, inference.UNKNOWN_PRIOR = saved
            rows[m].append(r)

    def agg(rs):
        per_case = [sum(r["top1"]) / len(r["top1"]) for r in rs]
        qs = [q for r in rs for q in r["q"] if q is not None]
        out = {"top1": round(statistics.mean(per_case), 4), "top1_ci95": bootstrap_ci(per_case),
               "top3": round(statistics.mean(sum(r["top3"]) / len(r["top3"]) for r in rs), 4),
               "understood": round(sum(r["understood"] for r in rs) / len(rs), 4),
               "wrong_confident": round(statistics.mean(sum(r["wrong_conf"]) / len(r["wrong_conf"]) for r in rs), 4),
               "avg_questions": round(statistics.mean(qs), 3) if qs else None,
               "by_lang": {}}
        for l in ("ta", "en", "tl"):
            lr = [sum(r["top1"]) / len(r["top1"]) for r in rs if r["lang"] == l]
            out["by_lang"][l] = {"n": len(lr), "top1": round(statistics.mean(lr), 4)}
        return out

    res = {"n_cases": len(CASES), "n_runs": N_RUNS, "languages": {l: sum(1 for c in CASES if c[1] == l) for l in ("ta", "en", "tl")},
           "methods": [{"id": m, "name": n, **agg(rows[m])} for m, n in methods]}
    per_d = {}
    for m in ("v1", "eig"):
        for r in rows[m]:
            per_d.setdefault(r["truth"], {})[m] = per_d.get(r["truth"], {}).get(m, []) + [sum(r["top1"]) / len(r["top1"])]
    res["per_disease"] = [{"disease": d, "name": kg.diseases[d]["name_en"], "v1": round(statistics.mean(v["v1"]), 4),
                           "eig": round(statistics.mean(v["eig"]), 4)} for d, v in per_d.items()]
    # confusions of the proposed system
    conf = {}
    rng = random.Random(5)
    for truth, lang, text in CASES:
        tm = matcher.match(text)["matches"]
        for _ in range(N_RUNS):
            ranked2, _ = dialogue(eng, kg, tm, truth, rng)
            if ranked2[0][0] != truth:
                k = f"{truth}->{ranked2[0][0]}"
                conf[k] = conf.get(k, 0) + 1
    res["top_confusions"] = sorted(({"pair": k, "count": v} for k, v in conf.items()), key=lambda x: -x["count"])[:6]
    save("e1_accuracy", res)
    for m in res["methods"]:
        print(f"   {m['name']:<42} top1={m['top1']:.3f} {m['top1_ci95']} Q={m['avg_questions']} wrongconf={m['wrong_confident']}")


# ------------------------------------------------------------------ E1b
def e1b():
    """Out-of-scope problems (not in the graph): does the system abstain instead of
    confidently naming a disease? Simulated farmer answers 'yes' with p=0.15."""
    print("E1b out-of-scope abstention")
    oos = json.load(open(os.path.join(ROOT, "data", "eval", "out_of_scope.json"), encoding="utf-8"))
    kg = fresh_kg()
    matcher = SymptomMatcher(kg.layterm_list())
    eng = DiagnosisEngine(kg)
    out = {"n_cases": len(oos), "n_runs": N_RUNS, "variants": {}}
    for variant in ("with_unknown", "no_unknown"):
        saved = inference.UNKNOWN_PRIOR
        if variant == "no_unknown":
            inference.UNKNOWN_PRIOR = 1e-9
        abstain = conf_wrong = no_input = total = 0
        rng = random.Random(9)
        for lang, text in oos:
            tm = matcher.match(text)["matches"]
            for _ in range(N_RUNS):
                total += 1
                answers = []
                while True:
                    ev = eng.build_evidence(tm, answers)
                    st = eng.step(ev, asked=[a["symptom_id"] for a in answers])
                    if st["status"] != "question":
                        break
                    answers.append({"symptom_id": st["question"]["symptom_id"], "answer": "yes" if rng.random() < 0.15 else "no"})
                if st["status"] == "need_input":
                    no_input += 1
                    abstain += 1
                elif st["result"]["confidence"] == "uncertain":
                    abstain += 1
                elif st["result"]["probability"] >= CONFIDENT:
                    conf_wrong += 1
        inference.UNKNOWN_PRIOR = saved
        out["variants"][variant] = {"abstain_rate": round(abstain / total, 4), "no_symptom_matched_rate": round(no_input / total, 4),
                                    "confidently_wrong_rate": round(conf_wrong / total, 4)}
        print(f"   {variant}: {out['variants'][variant]}")
    save("e1b_out_of_scope", out)


# ------------------------------------------------------------------ E2
def e2():
    print("E2 accuracy vs question budget")
    kg = fresh_kg()
    matcher = SymptomMatcher(kg.layterm_list())
    eng = DiagnosisEngine(kg)
    tms = [(t, matcher.match(x)["matches"]) for t, _, x in CASES]
    out = {"budgets": list(range(0, 7)), "curves": {}}
    for strategy in ("eig", "variance", "random"):
        accs = []
        for b in out["budgets"]:
            rng = random.Random(100 + b)
            hits = n = 0
            for truth, tm in tms:
                for _ in range(10):
                    ranked, _ = dialogue(eng, kg, tm, truth, rng, strategy, b)
                    hits += ranked[0][0] == truth
                    n += 1
            accs.append(round(hits / n, 4))
        out["curves"][strategy] = accs
        print(f"   {strategy:<9} {accs}")
    # the motivating "white dust" example, step by step
    text = "இலையில் வெள்ளை தூள் போல இருக்கு"
    tm = matcher.match(text)["matches"]
    trace = []
    for truth in ("powdery_mildew", "whitefly"):
        answers, steps = [], []
        while True:
            ev = eng.build_evidence(tm, answers)
            st = eng.step(ev, asked=[a["symptom_id"] for a in answers])
            steps.append({"posterior": st["posterior"][:4], "question": st.get("question", {}).get("symptom_id"),
                          "eig": st.get("question", {}).get("eig")})
            if st["status"] != "question":
                steps[-1]["result"] = st["result"]["disease_id"]
                break
            q = st["question"]["symptom_id"]
            th = kg.theta(truth, q)
            answers.append({"symptom_id": q, "answer": "yes" if th and th >= 0.5 else "no"})
            steps[-1]["answer"] = answers[-1]["answer"]
        trace.append({"truth": truth, "steps": steps})
    out["white_dust_trace"] = {"text": text, "matches": [m["symptom_id"] for m in tm], "traces": trace}
    save("e2_budget", out)


# ------------------------------------------------------------------ E3
def degrade(data, rng):
    """Field-like degradation: off-centre crop, defocus blur, under-exposure,
    colour cast, sensor noise, heavy JPEG compression."""
    from PIL import Image, ImageEnhance, ImageFilter
    import numpy as np
    img = Image.open(io.BytesIO(data)).convert("RGB")
    w, h = img.size
    s = int(min(w, h) * rng.uniform(0.6, 0.8))
    x, y = rng.randint(0, w - s), rng.randint(0, h - s)
    img = img.crop((x, y, x + s, y + s)).resize((w, h))
    img = img.filter(ImageFilter.GaussianBlur(rng.uniform(1.5, 2.5)))
    img = ImageEnhance.Brightness(img).enhance(rng.uniform(0.45, 0.7))
    arr = np.asarray(img).astype(np.float32)
    arr *= np.array([rng.uniform(0.9, 1.15), 1.0, rng.uniform(0.85, 1.1)], dtype=np.float32)
    arr += np.random.default_rng(rng.randint(0, 10 ** 6)).normal(0, 10, arr.shape)
    img = Image.fromarray(arr.clip(0, 255).astype("uint8"))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=20)
    return buf.getvalue()


def e3():
    print("E3 photo model: clean vs degraded, alone vs fused")
    from tomatodoc.vision import load_classifier
    clf = load_classifier(os.path.join(ROOT, "models"))
    kg = fresh_kg()
    eng = DiagnosisEngine(kg)
    folder_to_id = {"Tomato___Bacterial_spot": "bacterial_spot", "Tomato___Early_blight": "early_blight",
                    "Tomato___Late_blight": "late_blight", "Tomato___Leaf_Mold": "leaf_mold",
                    "Tomato___Septoria_leaf_spot": "septoria_leaf_spot",
                    "Tomato___Spider_mites Two-spotted_spider_mite": "spider_mite", "Tomato___Target_Spot": "target_spot",
                    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": "leaf_curl_virus", "Tomato___Tomato_mosaic_virus": "mosaic_virus"}
    rng = random.Random(42)
    res = {}
    for cond in ("clean", "degraded"):
        n = c_clf = c_photo = c_fused = 0
        qs, flagged, temps = [], 0, []
        for folder, did in folder_to_id.items():
            for f in sorted(glob.glob(os.path.join(ROOT, "tomato", "val", folder, "*"))):
                data = open(f, "rb").read()
                if cond == "degraded":
                    data = degrade(data, rng)
                pred = clf.predict(data)
                n += 1
                c_clf += pred["top"] == did
                flagged += bool(pred["quality"]["issues"]) or pred["top_p"] < 0.5
                temps.append(pred["temperature"])
                photo = {"probs": pred["probs"], "temperature": pred["temperature"]}
                post, _ = eng.posterior([], photo=photo)
                c_photo += max((h for h in post if h != UNKNOWN), key=post.get) == did
                ranked, nq = dialogue(eng, kg, [], did, rng, "eig", MAX_QUESTIONS, photo=photo)
                c_fused += ranked[0][0] == did
                qs.append(nq)
        res[cond] = {"n": n, "classifier_top1": round(c_clf / n, 4), "photo_only_engine_top1": round(c_photo / n, 4),
                     "photo_plus_dialogue_top1": round(c_fused / n, 4), "avg_questions": round(statistics.mean(qs), 3),
                     "flagged_low_quality_or_unsure": round(flagged / n, 4), "mean_temperature": round(statistics.mean(temps), 3)}
        print(f"   {cond}: {res[cond]}")
    meta = json.load(open(os.path.join(ROOT, "models", "leaf_classifier.json")))
    res["classifier_meta"] = {k: meta[k] for k in ("val_accuracy", "temperature", "per_class", "confusion_matrix", "labels",
                                                   "backbone", "train_images", "val_images")}
    save("e3_vision", res)


# ------------------------------------------------------------------ E4
def simulate_case(kg_true, rng, n_text=2):
    """Sample a farmer: a disease, its true symptoms, and a description of n_text of them."""
    d = rng.choice(list(kg_true.diseases))
    present = [s for s, w in kg_true.symptoms_of[d].items() if rng.random() < w]
    if not present:
        present = [max(kg_true.symptoms_of[d], key=kg_true.symptoms_of[d].get)]
    described = rng.sample(present, min(n_text, len(present)))
    tm = [{"symptom_id": s, "present": True, "strength": 0.85} for s in described]
    return d, set(present), tm


def run_learning(rule, seed, n=1500, window=100, noise=0.25, drop=0.15):
    rng = random.Random(seed)
    kg_true = fresh_kg()
    kg = fresh_kg()
    # corrupt: perturb weights, and remove some true edges entirely (knowledge gaps)
    for key, e in list(kg.edges.items()):
        w = e["alpha"] / (e["alpha"] + e["beta"])
        if rng.random() < drop:
            w = 0.05
        else:
            w = min(0.95, max(0.05, w + rng.gauss(0, noise)))
        e["alpha"], e["beta"] = w * PRIOR_STRENGTH, (1 - w) * PRIOR_STRENGTH
    kg._index()
    eng = DiagnosisEngine(kg)
    keys = list(kg_true.edges)

    def mae():
        return statistics.mean(abs(kg.theta(d, s) - kg_true.theta(d, s)) for d, s in keys)
    curve, hits, maes = [], 0, [round(mae(), 4)]
    for i in range(1, n + 1):
        d, present, tm = simulate_case(kg_true, rng)
        answers = []
        for _ in range(MAX_QUESTIONS + 1):
            ev = eng.build_evidence(tm, answers)
            st = eng.step(ev, asked=[a["symptom_id"] for a in answers])
            if st["status"] != "question":
                break
            q = st["question"]["symptom_id"]
            truly = q in present or (kg_true.theta(d, q) is None and rng.random() < LEAK_ANSWER)
            answers.append({"symptom_id": q, "answer": "yes" if truly else "no"})
        ev = eng.build_evidence(tm, answers)
        pred = st["result"]["disease_id"] if st["status"] == "result" else st["posterior"][0]["id"]
        hits += pred == d
        # farmer feedback: confirms when right; picks the right disease from photos 70 % of the time when wrong
        if rule == "beta":
            truth = d if pred == d or rng.random() < 0.7 else None
            if truth:
                ups, _ = plan_updates(kg, ev, truth)
                for u in ups:
                    if u["rel"] == "HAS_SYMPTOM":
                        kg.apply_edge_delta("HAS_SYMPTOM", u["src"], u["dst"], u["d_alpha"], u["d_beta"])
        elif rule == "v1":
            # v1 prototype: +0.03 on confirmation, -0.03 on rejection, on the edges of the predicted disease
            delta = 0.03 if pred == d else -0.03
            for e in ev:
                if e["present"] and kg.theta(pred, e["symptom_id"]) is not None:
                    w = min(1.0, max(0.05, kg.theta(pred, e["symptom_id"]) + delta))
                    ed = kg.edges[(pred, e["symptom_id"])]
                    tot = ed["alpha"] + ed["beta"]
                    ed["alpha"], ed["beta"] = w * tot, (1 - w) * tot
                    kg._index()
        if i % window == 0:
            curve.append(round(hits / window, 4))
            maes.append(round(mae(), 4))
            hits = 0
    return curve, maes


def e4():
    print("E4 online learning from confirmations")
    out = {"window": 100, "n": 1500, "seeds": 5, "rules": {}}
    for rule in ("beta", "v1", "none"):
        curves, maes = [], []
        for seed in range(5):
            c, m = run_learning(rule, seed)
            curves.append(c)
            maes.append(m)
        out["rules"][rule] = {"accuracy_mean": [round(statistics.mean(x), 4) for x in zip(*curves)],
                              "accuracy_sd": [round(statistics.pstdev(x), 4) for x in zip(*curves)],
                              "mae_mean": [round(statistics.mean(x), 4) for x in zip(*maes)]}
        r = out["rules"][rule]
        print(f"   {rule:<5} acc first {r['accuracy_mean'][0]} last {r['accuracy_mean'][-1]} | MAE {r['mae_mean'][0]} -> {r['mae_mean'][-1]}")
    save("e4_learning", out)


# ------------------------------------------------------------------ E5
def e5():
    print("E5 latency")
    import tempfile
    from tomatodoc import create_app
    app = create_app({"DATABASE_PATH": os.path.join(tempfile.mkdtemp(), "lat.db"), "KG_BACKEND": "embedded",
                      "NEO4J_URI": None, "ENABLE_WEATHER": False, "GEMINI_API_KEY": None})
    c = app.test_client()
    svc = app.extensions["tomatodoc"]
    t_nlu, t_step, t_api = [], [], []
    for i, (truth, lang, text) in enumerate(CASES):
        t0 = time.perf_counter()
        tm = svc.matcher.match(text)["matches"]
        t_nlu.append(time.perf_counter() - t0)
        ev = svc.engine.build_evidence(tm)
        t0 = time.perf_counter()
        svc.engine.step(ev)
        t_step.append(time.perf_counter() - t0)
        t0 = time.perf_counter()
        c.post("/api/diagnose", json={"session_id": f"latency-session-{i:03d}", "text": text})
        t_api.append(time.perf_counter() - t0)
    img = sorted(glob.glob(os.path.join(ROOT, "tomato", "val", "Tomato___Late_blight", "*")))[:20]
    t_img = []
    for f in img:
        data = open(f, "rb").read()
        t0 = time.perf_counter()
        svc.vision.predict(data)
        t_img.append(time.perf_counter() - t0)
    q = lambda xs: {"median_ms": round(1000 * statistics.median(xs), 2), "p95_ms": round(1000 * sorted(xs)[int(0.95 * len(xs)) - 1], 2)}  # noqa: E731
    import platform
    out = {"nlu": q(t_nlu), "inference_step": q(t_step), "api_diagnose": q(t_api), "photo": q(t_img),
           "cpu": platform.processor(), "cores": os.cpu_count(), "python": platform.python_version()}
    print("  ", out)
    save("e5_latency", out)


# ------------------------------------------------------------------ E6
def e6():
    print("E6 weather risk case study (live)")
    sites = [("The Nilgiris (Ooty)", 11.41, 76.70), ("Coimbatore", 11.02, 76.96), ("Krishnagiri", 12.52, 78.21), ("Madurai", 9.93, 78.12)]
    out = {"fetched_at": time.strftime("%Y-%m-%d %H:%M"), "sites": []}
    for name, lat, lon in sites:
        w = None
        for _ in range(3):
            w = weather.fetch(lat, lon)
            if w:
                break
            time.sleep(2)
        if not w:
            print("   weather unavailable for", name)
            continue
        r = risk.assess(w)
        out["sites"].append({"name": name, "lat": lat, "lon": lon, "summary": weather.summary(w),
                             "risks": {d: {"score": v["score"], "level": v["level"], "facts": v["facts"], "model": v["model"]} for d, v in r.items()}})
        top = sorted(r.items(), key=lambda kv: -kv[1]["score"])[:3]
        print(f"   {name}: {[(d, v['level'], v['score']) for d, v in top]}")
    save("e6_weather", out)


# ------------------------------------------------------------------ E7
NEUTRAL_SOIL = {"ph": 6.8, "ec": 0.4, "oc": 0.62, "n": 350, "p": 18, "k": 200, "ca": 4.0}
LINKED = ["blossom_end_rot", "fusarium_wilt", "root_knot_nematode", "early_blight", "fruit_borer", "leaf_curl_virus"]
TYPICAL_STAGE = {"blossom_end_rot": "fruiting", "fruit_borer": "fruiting", "early_blight": "harvest", "leaf_curl_virus": "vegetative"}


def field_context(d):
    """A plausible soil report + crop stage for a field where disease d occurs. Soil values
    are changed only where the system's rules link soil to d; everything else is a typical,
    unremarkable loam, so the context carries no information about unlinked diseases."""
    v, texture = dict(NEUTRAL_SOIL), "loamy"
    if d == "blossom_end_rot":
        v.update(ca=1.1, ec=2.6)
    elif d == "fusarium_wilt":
        v.update(ph=5.6)
        texture = "sandy"
    elif d == "root_knot_nematode":
        v.update(oc=0.40)
        texture = "sandy"
    elif d == "early_blight":
        v.update(n=220)
    elif d in soil.FOLIAR_LUSH | soil.SUCKING_PESTS:
        v.update(n=620)
    return soil.clean({"values": v, "texture": texture}), TYPICAL_STAGE.get(d, "flowering")


def context_factors(kg, ctx):
    soil_profile, stage = ctx
    sf = {d: f for d, (f, _) in soil.disease_factors(soil_profile).items()}
    stf = crop.stage_factors(stage)
    return {d: sf.get(d, 1.0) * stf.get(d, 1.0) for d in kg.diseases}


def e7():
    """Does a consistent field profile help, and how much does a misleading one hurt?"""
    print("E7 field context (soil report + crop stage)")
    kg = fresh_kg()
    matcher = SymptomMatcher(kg.layterm_list())
    eng = DiagnosisEngine(kg)
    conds = ["none", "consistent", "misleading"]
    rows = {c: [] for c in conds}
    for truth, lang, text in CASES:
        tm = matcher.match(text)["matches"]
        seed = zlib.crc32(text.encode("utf-8"))
        decoy = random.Random(seed).choice([d for d in LINKED if d != truth])
        ctxs = {"none": None, "consistent": context_factors(kg, field_context(truth)),
                "misleading": context_factors(kg, field_context(decoy))}
        for c in conds:
            r = {"truth": truth, "linked": truth in LINKED or truth in (soil.FOLIAR_LUSH | soil.SUCKING_PESTS)}
            ranked0, _ = dialogue(eng, kg, tm, truth, random.Random(seed), budget=0, factors=ctxs[c])
            r["desc_top1"] = ranked0[0][0] == truth
            rng = random.Random(zlib.crc32(f"{text}|eig".encode("utf-8")))   # same dialogues as E1 "eig"
            t1, wc, qs = [], [], []
            for _ in range(N_RUNS):
                ranked2, nq = dialogue(eng, kg, tm, truth, rng, factors=ctxs[c])
                t1.append(ranked2[0][0] == truth)
                wc.append(ranked2[0][0] != truth and ranked2[0][1] >= CONFIDENT)
                qs.append(nq)
            r.update(top1=sum(t1) / len(t1), wrong=sum(wc) / len(wc), q=statistics.mean(qs))
            rows[c].append(r)

    def agg(rs):
        return {"n": len(rs), "desc_top1": round(statistics.mean(r["desc_top1"] for r in rs), 4),
                "top1": round(statistics.mean(r["top1"] for r in rs), 4),
                "top1_ci95": bootstrap_ci([r["top1"] for r in rs]),
                "wrong_confident": round(statistics.mean(r["wrong"] for r in rs), 4),
                "avg_questions": round(statistics.mean(r["q"] for r in rs), 3)}
    out = {"n_cases": len(CASES), "n_runs": N_RUNS, "neutral_soil": NEUTRAL_SOIL, "conditions": {}}
    for c in conds:
        out["conditions"][c] = {"all": agg(rows[c]),
                                "linked": agg([r for r in rows[c] if r["linked"]]),
                                "unlinked": agg([r for r in rows[c] if not r["linked"]])}
        a = out["conditions"][c]["all"]
        print(f"   {c:<11} desc-only={a['desc_top1']:.3f} dialogue={a['top1']:.3f} {a['top1_ci95']} "
              f"Q={a['avg_questions']} wrongconf={a['wrong_confident']}  linked={out['conditions'][c]['linked']['top1']:.3f}")
    save("e7_field_context", out)


# ------------------------------------------------------------------ E8
def e8():
    """Harvest safety audit. For every disease x severity x picking interval x days to the
    next picking, compare the first scheduled spray (and the whole schedule) of the
    harvest-unaware plan with the harvest-aware plan."""
    print("E8 harvest safety (pre-harvest intervals vs. picking rhythm)")
    kg = fresh_kg()
    day0 = datetime(2026, 10, 14, 8, 0)
    saved = advisory.next_spray_time
    advisory.next_spray_time = lambda w: day0          # deterministic spray day (no forecast)

    def detail(d):
        tr = []
        for t in kg.treatments_for(d):
            tr.append({**t, "application": t.get("application")})
        return {"id": d, "type": kg.diseases[d]["type"], "severity": kg.diseases[d].get("severity", 3)}, tr

    def picks(anchor, every, horizon=60):
        return [anchor + j * every for j in range(horizon // every + 2)]

    def conflicts(schedule, k, every):
        """(any spray whose PHI overlaps the next picking after it, any PHI longer than the interval).
        The farmer picks on schedule; when the plan says 'pick the ripe fruit first' for the
        first spray, that extra picking happens before spraying and the rhythm restarts there."""
        overlap = longer = False
        ps = picks(0 if schedule and schedule[0].get("after_pick") else k, every)
        for x in schedule:
            if not x.get("phi"):
                continue
            sd = (datetime.fromisoformat(x["date"]).date() - day0.date()).days
            nxt = min(p for p in ps if p > sd)                # a picking on the spray day happens first
            if nxt < sd + x["phi"]:
                overlap = True
            if x["phi"] > every:
                longer = True
        return overlap, longer

    stats = {"baseline": {"first_overlap": [], "first_longer": [], "sched_overlap": [], "sched_longer": [], "eff": []},
             "aware": {"first_overlap": [], "first_longer": [], "sched_overlap": [], "sched_longer": [], "eff": []}}
    n_scen, no_spray = 0, 0
    for d in kg.diseases:
        disease, treatments = detail(d)
        if not any((t["application"] or {}).get("phi_days") is not None for t in treatments):
            no_spray += 1
            continue
        for sev in ("mild", "moderate", "severe"):
            base = advisory.plan(disease, treatments, sev)
            for every in (3, 4, 5, 7):
                for k in range(1, every + 1):
                    h = {"picking": True, "every": every, "next_pick": (day0.date() + timedelta(days=k)).isoformat(), "days_to_pick": k}
                    aware = advisory.plan(disease, treatments, sev, harvest=h)
                    n_scen += 1
                    for name, pl in (("baseline", base), ("aware", aware)):
                        sch = pl["schedule"]
                        if not sch:
                            continue
                        first = sch[0]
                        first_next = every if first.get("after_pick") else k
                        stats[name]["first_overlap"].append(bool(first.get("phi")) and first["phi"] > first_next)
                        stats[name]["first_longer"].append(bool(first.get("phi")) and first["phi"] > every)
                        o, lg = conflicts(sch, k, every)
                        stats[name]["sched_overlap"].append(o)
                        stats[name]["sched_longer"].append(lg)
                        eff = next(t["efficacy"] for t in treatments if t["id"] == first["treatment_id"])
                        stats[name]["eff"].append(eff)
    advisory.next_spray_time = saved
    out = {"scenarios": n_scen, "diseases_without_sprays": no_spray, "intervals": [3, 4, 5, 7],
           "phi_days": {t: v["application"]["phi_days"] for t, v in kg.treatments.items() if (v.get("application") or {}).get("phi_days") is not None}}
    for name, st in stats.items():
        out[name] = {k: round(statistics.mean(v), 4) for k, v in st.items()}
        print(f"   {name:<9} first spray overlaps next picking={out[name]['first_overlap']:.3f}  PHI>interval={out[name]['first_longer']:.3f}  "
              f"schedule overlap={out[name]['sched_overlap']:.3f}  mean efficacy={out[name]['eff']:.3f}")
    save("e8_harvest_safety", out)


if __name__ == "__main__":
    which = sys.argv[1:] or ["e1", "e1b", "e2", "e3", "e4", "e5", "e6", "e7", "e8"]
    t0 = time.time()
    for name in which:
        globals()[name]()
    print(f"done in {time.time() - t0:.0f}s")
