"""
learning.py - turns farmer feedback into knowledge-graph updates.

Only CONFIRMED outcomes teach the graph (the farmer said "yes, this is it", or
picked the right disease after rejecting ours). A bare "no" without a correct
answer is logged but changes no weights - it tells us we were wrong, not what
is right, so decaying weights on it (as the v1 prototype did) would punish
edges that may be perfectly correct.

For a confirmed disease d* and each piece of symptom evidence e (reliability c):
  * HAS_SYMPTOM(d*, s) exists : present -> alpha += w,  absent -> beta += w
  * no edge, symptom present  : record a suggested new edge for expert review
  * LAYTERM_MAPS_TO(l, s) used by the text match:
        s is a symptom of d* -> alpha += w/2   (phrase mapping was useful)
        s is not             -> beta  += w/2   (phrase probably mis-mapped)
where w = 2(c − 0.5) ∈ (0, 1] is how sure we were about that observation.
Weights are Beta posteriors, so each update is small, bounded and reversible.
"""


def evidence_weight(c):
    return max(0.0, min(1.0, 2 * (c - 0.5)))


def plan_updates(kg, evidence, true_disease):
    updates, suggestions = [], []
    for e in evidence:
        s = e["symptom_id"]
        w = evidence_weight(e["c"])
        if w <= 0:
            continue
        theta = kg.theta(true_disease, s)
        if theta is not None:
            updates.append({"rel": "HAS_SYMPTOM", "src": true_disease, "dst": s,
                            "d_alpha": w if e["present"] else 0.0, "d_beta": 0.0 if e["present"] else w})
        elif e["present"] and w >= 0.6:
            suggestions.append({"d": true_disease, "s": s, "amount": w})
        if e.get("source") == "text" and e.get("layterm_id") and e["present"]:
            useful = theta is not None
            updates.append({"rel": "LAYTERM_MAPS_TO", "src": e["layterm_id"], "dst": s,
                            "d_alpha": w / 2 if useful else 0.0, "d_beta": 0.0 if useful else w / 2})
    return updates, suggestions
