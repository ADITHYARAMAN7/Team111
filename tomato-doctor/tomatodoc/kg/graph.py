"""
graph.py - in-memory snapshot of the knowledge graph.

The graph lives in Neo4j (or the embedded store); at start-up it is loaded once
into this structure so that inference (a few thousand multiplications per
request) never waits on the database. Writes (feedback learning, new lay-terms)
go to the store first and are then mirrored here.

Edge weights on HAS_SYMPTOM and LAYTERM_MAPS_TO are Beta(alpha, beta) posteriors:
    weight = alpha / (alpha + beta)
The seed weight w becomes alpha = w*K, beta = (1-w)*K, with K = PRIOR_STRENGTH
pseudo-observations. Each farmer confirmation adds evidence, so the graph
learns gradually and every change is reversible and auditable.
"""
import json
import os
import threading

PRIOR_STRENGTH = 20.0
SEED_PATH = os.path.join(os.path.dirname(__file__), "seed", "tomato_kg.json")


def layterm_id(symptom_id, lang, idx):
    return f"lt_{symptom_id}_{lang}{idx}"


def load_seed(path=SEED_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def flatten_layterms(seed):
    """symptoms[].lay -> flat list of LayTerm dicts (stable ids)."""
    out = []
    for s in seed["symptoms"]:
        for i, entry in enumerate(s.get("lay", [])):
            lang, text, w = entry[0], entry[1], entry[2]
            lid = entry[3] if len(entry) > 3 else layterm_id(s["id"], lang, i)
            out.append({"id": lid, "text": text, "lang": lang, "symptom_id": s["id"], "weight": w,
                        "origin": "seed"})
    return out


class KnowledgeGraph:
    def __init__(self, data):
        """data: dict with keys meta, seasons, diseases, symptoms, layterms,
        has_symptom (list of dicts d,s,alpha,beta,seed), treatments, treated_by."""
        self.lock = threading.RLock()
        self.meta = data["meta"]
        self.seasons = {s["id"]: s for s in data["seasons"]}
        self.diseases = {d["id"]: d for d in data["diseases"]}
        self.symptoms = {s["id"]: {k: v for k, v in s.items() if k != "lay"} for s in data["symptoms"]}
        self.treatments = {t["id"]: t for t in data["treatments"]}
        self.layterms = {lt["id"]: dict(lt) for lt in data["layterms"]}
        self.edges = {}          # (d, s) -> {"alpha","beta","seed"}
        for e in data["has_symptom"]:
            self.edges[(e["d"], e["s"])] = {"alpha": e["alpha"], "beta": e["beta"], "seed": e["seed"]}
        self.treated_by = {}
        for d, t, eff in data["treated_by"]:
            self.treated_by.setdefault(d, []).append((t, eff))
        for d in self.treated_by:
            self.treated_by[d].sort(key=lambda x: -x[1])
        self._index()

    def _index(self):
        self.symptoms_of = {d: {} for d in self.diseases}
        self.diseases_of = {s: {} for s in self.symptoms}
        for (d, s), e in self.edges.items():
            w = e["alpha"] / (e["alpha"] + e["beta"])
            self.symptoms_of[d][s] = w
            self.diseases_of[s][d] = w

    # ---- reads -------------------------------------------------------------
    def theta(self, d, s):
        return self.symptoms_of.get(d, {}).get(s)

    def layterm_list(self):
        return [{**lt, "weight": self.layterm_weight(lt)} for lt in self.layterms.values()]

    @staticmethod
    def layterm_weight(lt):
        if "alpha" in lt and "beta" in lt:
            return lt["alpha"] / (lt["alpha"] + lt["beta"])
        return lt["weight"]

    def treatments_for(self, d):
        out = []
        for tid, eff in self.treated_by.get(d, []):
            t = self.treatments.get(tid)
            if t:
                out.append({**t, "efficacy": eff})
        return out

    def stats(self):
        return {"diseases": len(self.diseases), "symptoms": len(self.symptoms), "layterms": len(self.layterms),
                "treatments": len(self.treatments), "has_symptom_edges": len(self.edges),
                "treated_by_edges": sum(len(v) for v in self.treated_by.values()),
                "languages": sorted({lt.get("lang", "ta") for lt in self.layterms.values()})}

    # ---- writes (called by the store after persisting) ---------------------
    def apply_edge_delta(self, rel, src, dst, d_alpha, d_beta):
        with self.lock:
            if rel == "HAS_SYMPTOM":
                e = self.edges.get((src, dst))
                if e is None:
                    return False
                e["alpha"] += d_alpha
                e["beta"] += d_beta
                w = e["alpha"] / (e["alpha"] + e["beta"])
                self.symptoms_of[src][dst] = w
                self.diseases_of[dst][src] = w
                return True
            if rel == "LAYTERM_MAPS_TO":
                lt = self.layterms.get(src)
                if lt is None:
                    return False
                if "alpha" not in lt:
                    lt["alpha"], lt["beta"] = lt["weight"] * PRIOR_STRENGTH, (1 - lt["weight"]) * PRIOR_STRENGTH
                lt["alpha"] += d_alpha
                lt["beta"] += d_beta
                lt["weight"] = lt["alpha"] / (lt["alpha"] + lt["beta"])
                return True
        return False

    def add_layterm(self, lt):
        with self.lock:
            self.layterms[lt["id"]] = dict(lt)

    def add_edge(self, d, s, weight):
        with self.lock:
            self.edges[(d, s)] = {"alpha": weight * PRIOR_STRENGTH, "beta": (1 - weight) * PRIOR_STRENGTH, "seed": weight}
            self._index()


def seed_to_data(seed):
    """Convert the seed JSON into the KnowledgeGraph constructor format."""
    return {
        "meta": seed["meta"],
        "seasons": seed["seasons"],
        "diseases": seed["diseases"],
        "symptoms": seed["symptoms"],
        "treatments": seed["treatments"],
        "treated_by": seed["treated_by"],
        "layterms": flatten_layterms(seed),
        "has_symptom": [{"d": d, "s": s, "seed": w, "alpha": w * PRIOR_STRENGTH, "beta": (1 - w) * PRIOR_STRENGTH}
                        for d, s, w in seed["has_symptom"]],
    }


def validate_seed(seed):
    """Referential integrity check - used by tests and the seeding script."""
    errors = []
    dids = {d["id"] for d in seed["diseases"]}
    sids = {s["id"] for s in seed["symptoms"]}
    tids = {t["id"] for t in seed["treatments"]}
    seasons = {s["id"] for s in seed["seasons"]}
    for d, s, w in seed["has_symptom"]:
        if d not in dids:
            errors.append(f"has_symptom: unknown disease {d}")
        if s not in sids:
            errors.append(f"has_symptom: unknown symptom {s}")
        if not 0 < w < 1:
            errors.append(f"has_symptom: weight out of range {d}->{s}={w}")
    for d, t, e in seed["treated_by"]:
        if d not in dids:
            errors.append(f"treated_by: unknown disease {d}")
        if t not in tids:
            errors.append(f"treated_by: unknown treatment {t}")
    for d in seed["diseases"]:
        for sc in d.get("favored_by", {}):
            if sc not in seasons:
                errors.append(f"{d['id']}: unknown season {sc}")
        if not any(x[0] == d["id"] for x in seed["has_symptom"]):
            errors.append(f"{d['id']}: has no symptoms")
        if not any(x[0] == d["id"] for x in seed["treated_by"]):
            errors.append(f"{d['id']}: has no treatments")
    ids = [lt["id"] for lt in flatten_layterms(seed)]
    if len(ids) != len(set(ids)):
        errors.append("duplicate layterm ids")
    pairs = [(d, s) for d, s, _ in seed["has_symptom"]]
    if len(pairs) != len(set(pairs)):
        errors.append("duplicate has_symptom edges")
    for s in seed["symptoms"]:
        if not any(x[1] == s["id"] for x in seed["has_symptom"]):
            errors.append(f"symptom {s['id']} is not linked to any disease")
    return errors
