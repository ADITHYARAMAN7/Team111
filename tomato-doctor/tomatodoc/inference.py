"""
inference.py - probabilistic reasoning over the knowledge graph.

Model
-----
Hypotheses H = every Disease node + an explicit UNKNOWN hypothesis ("something
not in the graph"), so the system can say "I am not sure" instead of forcing a
wrong answer.

Prior        P(d) ∝ 1 · (1 + boost(d, season))          [FAVORED_BY edges]
Symptom      θ(d,s) = HAS_SYMPTOM weight, or LEAK if no edge
Observation  every piece of evidence is a report "s present/absent" with a
             reliability c (how much we trust the report). Noise is asymmetric:
             farmers miss symptoms far more often than they invent a specific
             one, so the false-alarm rate is a fraction of the miss rate:
               P(report present | d) = c·θ + FA·(1−c)·(1−θ)
               P(report absent  | d) = c·(1−θ) + (1−c)·θ
             c comes from the lay-term match strength (text), or is fixed for
             direct answers / tapped symptoms. A weak NLU match therefore moves
             the posterior only a little - robust to language-matching errors.
Photo        leaf classifier probabilities enter as a tempered likelihood
             p(d | image)^τ (τ<1 because lab-trained models over-trust).
Posterior    P(d | E) ∝ P(d) · Π_e P(e | d) · L_photo(d)

Question selection (Discriminative Question Selection, v2)
----------------------------------------------------------
For each unobserved symptom s the expected information gain is
    EIG(s) = H(D) − Σ_{a∈{yes,no}} P(a) · H(D | a)
and the next question maximises EIG(s)·(1 − cost(s)); cost penalises
destructive checks (cutting a stem, uprooting a plant). Asking stops when the
top hypothesis is confident, the best question is uninformative, or the
question budget is used up.
"""
import math

LEAK = 0.02              # P(symptom | disease) when the graph has no edge
UNKNOWN_THETA = 0.12     # P(symptom | "unknown problem")
UNKNOWN_PRIOR = 0.6      # relative to 1.0 per disease
ANSWER_RELIABILITY = {"yes": 0.92, "no": 0.9}
PICKER_RELIABILITY = 0.9
PHOTO_TEMPERATURE = 0.5
PHOTO_FLOOR = 0.02
PHOTO_OTHER = 0.05       # likelihood for diseases the photo model cannot recognise
CONFIDENT = 0.85
MAX_QUESTIONS = 6
MIN_EIG = 0.03
UNKNOWN = "unknown"


def entropy(p):
    return -sum(v * math.log2(v) for v in p.values() if v > 0)


FALSE_ALARM = 0.3       # false-alarm rate as a fraction of the miss rate


def report_likelihood(theta, present, c):
    if present:
        return c * theta + FALSE_ALARM * (1 - c) * (1 - theta)
    return c * (1 - theta) + (1 - c) * theta


def text_reliability(strength):
    """lay-term match strength (0.36..1) -> report reliability (0.66..0.95)"""
    return max(0.55, min(0.95, 0.5 + 0.45 * strength))


class DiagnosisEngine:
    def __init__(self, kg):
        self.kg = kg

    # ---- evidence assembly -------------------------------------------------
    def build_evidence(self, text_matches=(), answers=(), picked=(), ai_symptoms=()):
        """Merge the three evidence sources. Later sources override earlier ones
        for the same symptom: a direct answer beats an inferred text match."""
        ev = {}
        for m in text_matches:
            if m.get("removed") or m["symptom_id"] not in self.kg.symptoms:
                continue
            ev[m["symptom_id"]] = {"symptom_id": m["symptom_id"], "present": bool(m["present"]),
                                   "c": text_reliability(m["strength"]), "source": "text",
                                   "layterm_id": m.get("layterm_id"), "phrase": m.get("phrase"),
                                   "strength": m["strength"]}
        for a in ai_symptoms:          # Gemini entity links - used only where text matching found nothing
            sid = a.get("symptom_id")
            if sid in self.kg.symptoms and sid not in ev:
                c = max(0.55, min(0.9, 0.5 + 0.4 * float(a.get("confidence", 0.6))))
                ev[sid] = {"symptom_id": sid, "present": bool(a.get("present", True)), "c": c, "source": "ai",
                           "phrase": a.get("evidence_quote"), "strength": round(c, 3)}
        for p in picked:
            if p["symptom_id"] in self.kg.symptoms:
                ev[p["symptom_id"]] = {"symptom_id": p["symptom_id"], "present": bool(p.get("present", True)),
                                       "c": PICKER_RELIABILITY, "source": "picker"}
        for a in answers:
            if a["symptom_id"] in self.kg.symptoms and a.get("answer") in ANSWER_RELIABILITY:
                ev[a["symptom_id"]] = {"symptom_id": a["symptom_id"], "present": a["answer"] == "yes",
                                       "c": ANSWER_RELIABILITY[a["answer"]], "source": "answer"}
        return list(ev.values())

    # ---- likelihood pieces -------------------------------------------------
    def theta(self, h, s):
        if h == UNKNOWN:
            return UNKNOWN_THETA
        t = self.kg.theta(h, s)
        return LEAK if t is None else t

    def hypotheses(self):
        return list(self.kg.diseases) + [UNKNOWN]

    def prior(self, season=None, factors=None):
        """Weather-driven factors (risk.prior_factors x outbreak factors) replace the
        coarse calendar-season boost when the farmer's location is known."""
        p = {}
        for d, dd in self.kg.diseases.items():
            if factors:
                p[d] = factors.get(d, factors.get("_default", 1.0))
            else:
                boost = dd.get("favored_by", {}).get(season, 0.0) if season else 0.0
                p[d] = 1.0 + boost
        p[UNKNOWN] = UNKNOWN_PRIOR
        z = sum(p.values())
        return {h: v / z for h, v in p.items()}

    @staticmethod
    def photo_likelihood(photo, h):
        if not photo:
            return 1.0
        probs = photo["probs"]
        tau = photo.get("temperature", PHOTO_TEMPERATURE)
        if h in probs:
            v = max(probs[h], PHOTO_FLOOR)
        else:
            v = PHOTO_OTHER
        return v ** tau

    def log_likelihoods(self, evidence, photo=None):
        """h -> list of (evidence key, log-likelihood) - kept itemised for explanations."""
        out = {}
        for h in self.hypotheses():
            items = [(e["symptom_id"], math.log(report_likelihood(self.theta(h, e["symptom_id"]), e["present"], e["c"])))
                     for e in evidence]
            if photo:
                items.append(("__photo__", math.log(self.photo_likelihood(photo, h))))
            out[h] = items
        return out

    def posterior(self, evidence, season=None, photo=None, factors=None):
        prior = self.prior(season, factors)
        ll = self.log_likelihoods(evidence, photo)
        logp = {h: math.log(prior[h]) + sum(v for _, v in ll[h]) for h in prior}
        m = max(logp.values())
        z = sum(math.exp(v - m) for v in logp.values())
        return {h: math.exp(v - m) / z for h, v in logp.items()}, ll

    # ---- question selection ------------------------------------------------
    def expected_information_gain(self, post, s, c=0.92):
        p_yes_h = {h: report_likelihood(self.theta(h, s), True, c) for h in post}
        p_yes = sum(post[h] * p_yes_h[h] for h in post)
        p_no = 1 - p_yes
        if p_yes <= 1e-9 or p_no <= 1e-9:
            return 0.0
        post_yes = {h: post[h] * p_yes_h[h] / p_yes for h in post}
        post_no = {h: post[h] * (1 - p_yes_h[h]) / p_no for h in post}
        return entropy(post) - p_yes * entropy(post_yes) - p_no * entropy(post_no)

    def rank_questions(self, post, exclude):
        ranked = []
        for s, sym in self.kg.symptoms.items():
            if s in exclude:
                continue
            eig = self.expected_information_gain(post, s)
            score = eig * (1 - sym.get("cost", 0))
            ranked.append((score, eig, s))
        ranked.sort(reverse=True)
        return ranked

    # ---- one dialogue step -------------------------------------------------
    def step(self, evidence, season=None, photo=None, asked=(), skipped=(), finish=False,
             max_questions=MAX_QUESTIONS, factors=None):
        post, ll = self.posterior(evidence, season, photo, factors)
        ranked_h = sorted(post.items(), key=lambda kv: -kv[1])
        top, top_p = ranked_h[0]
        n_asked = len(asked)
        observed = {e["symptom_id"] for e in evidence} | set(asked) | set(skipped)

        state = {"posterior": [{"id": h, "p": round(p, 4)} for h, p in ranked_h[:6]],
                 "entropy": round(entropy(post), 3), "questions_asked": n_asked}

        if not evidence and not photo:
            state["status"] = "need_input"
            return state

        question = None
        if not finish and top_p < CONFIDENT and n_asked < max_questions:
            ranked_q = self.rank_questions(post, observed)
            if ranked_q and ranked_q[0][1] >= MIN_EIG:
                score, eig, s = ranked_q[0]
                question = {"symptom_id": s, "eig": round(eig, 3), **self._symptom_public(s),
                            "alternatives": [{"symptom_id": x[2], "eig": round(x[1], 3)} for x in ranked_q[1:4]]}

        if question:
            state["status"] = "question"
            state["question"] = question
            return state

        state["status"] = "result"
        state["result"] = self.result(post, ll, evidence, photo)
        return state

    # ---- result + explanation ----------------------------------------------
    def result(self, post, ll, evidence, photo=None):
        ranked = sorted(((h, p) for h, p in post.items() if h != UNKNOWN), key=lambda kv: -kv[1])
        best, best_p = ranked[0]
        p_unknown = post[UNKNOWN]
        if p_unknown > best_p or best_p < 0.35:
            confidence = "uncertain"
        elif best_p >= CONFIDENT:
            confidence = "confident"
        elif best_p >= 0.6:
            confidence = "likely"
        else:
            confidence = "possible"
        runner = ranked[1][0] if len(ranked) > 1 else None
        return {
            "disease_id": best, "probability": round(best_p, 4), "confidence": confidence,
            "p_unknown": round(p_unknown, 4),
            "alternatives": [{"disease_id": h, "probability": round(p, 4)} for h, p in ranked[1:4] if p >= 0.02],
            "explanation": self.explain(best, runner, ll, evidence, photo),
            "check_next": self.unobserved_key_symptoms(best, evidence),
        }

    def explain(self, d, runner, ll, evidence, photo=None):
        ev_by = {e["symptom_id"]: e for e in evidence}
        lines = []
        for (key, v), (_, vr) in zip(ll[d], ll[runner] if runner else [(k, 0.0) for k, _ in ll[d]]):
            if key == "__photo__":
                lines.append({"kind": "photo", "llr": round(v - vr, 3),
                              "photo_p": round(photo["probs"].get(d, 0.0), 3) if photo else None})
                continue
            e = ev_by[key]
            lines.append({"kind": e["source"], "symptom_id": key, "present": e["present"],
                          "phrase": e.get("phrase"), "layterm_id": e.get("layterm_id"),
                          "theta": round(self.theta(d, key), 3), "theta_runner": round(self.theta(runner, key), 3) if runner else None,
                          "llr": round(v - vr, 3), **self._symptom_public(key)})
        lines.sort(key=lambda x: -abs(x["llr"]))
        return {"versus": runner, "evidence": lines}

    def unobserved_key_symptoms(self, d, evidence, k=3):
        seen = {e["symptom_id"] for e in evidence}
        strong = sorted(((s, w) for s, w in self.kg.symptoms_of.get(d, {}).items() if s not in seen and w >= 0.6),
                        key=lambda x: -x[1])
        return [{"symptom_id": s, "theta": round(w, 3), **self._symptom_public(s)} for s, w in strong[:k]]

    def _symptom_public(self, s):
        sym = self.kg.symptoms[s]
        return {"label_en": sym["label_en"], "label_ta": sym["label_ta"], "question_en": sym["question_en"],
                "question_ta": sym["question_ta"], "part": sym.get("part"), "cost": sym.get("cost", 0)}
