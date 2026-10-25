"""
store.py - where the knowledge graph is persisted.

  EmbeddedStore : seed JSON + learned state in SQLite. Zero setup; the default.
  Neo4jStore    : the graph lives in Neo4j (AuraDB or local). Learned weights
                  are written back onto the relationships as alpha/beta/weight,
                  so the live graph can be inspected in Neo4j Browser.

Both produce the same in-memory KnowledgeGraph, so the reasoning engine does
not care which one is used.
"""
import json
import logging
import time

from .graph import PRIOR_STRENGTH, KnowledgeGraph, flatten_layterms, load_seed, seed_to_data

log = logging.getLogger(__name__)


class EmbeddedStore:
    name = "embedded"

    def __init__(self, db, seed_path=None):
        self.db = db
        self.seed_path = seed_path

    def describe(self):
        return {"backend": "embedded", "detail": "seed JSON + SQLite learned state"}

    def load(self):
        seed = load_seed(self.seed_path) if self.seed_path else load_seed()
        data = seed_to_data(seed)
        for row in self.db.query("SELECT * FROM edge_extra"):
            if not any(e["d"] == row["d"] and e["s"] == row["s"] for e in data["has_symptom"]):
                w = row["weight"]
                data["has_symptom"].append({"d": row["d"], "s": row["s"], "seed": w,
                                            "alpha": w * PRIOR_STRENGTH, "beta": (1 - w) * PRIOR_STRENGTH})
        for row in self.db.query("SELECT * FROM layterm_extra"):
            data["layterms"].append({"id": row["id"], "text": row["text"], "lang": row["lang"],
                                     "symptom_id": row["symptom_id"], "weight": row["weight"], "origin": "expert"})
        kg = KnowledgeGraph(data)
        for row in self.db.query("SELECT * FROM edge_state"):
            if row["rel"] == "HAS_SYMPTOM" and (row["src"], row["dst"]) in kg.edges:
                e = kg.edges[(row["src"], row["dst"])]
                e["alpha"], e["beta"] = row["alpha"], row["beta"]
            elif row["rel"] == "LAYTERM_MAPS_TO" and row["src"] in kg.layterms:
                lt = kg.layterms[row["src"]]
                lt["alpha"], lt["beta"] = row["alpha"], row["beta"]
                lt["weight"] = row["alpha"] / (row["alpha"] + row["beta"])
        # load expert-added diseases
        dis_rows, sym_rows, trt_rows = self.db.get_disease_extras()
        for row in dis_rows:
            dd = json.loads(row["data_json"])
            syms = [(r["s"], r["weight"]) for r in sym_rows if r["d"] == row["id"]]
            trts = [(r["t"], r["efficacy"]) for r in trt_rows if r["d"] == row["id"]]
            kg.add_disease(dd, syms, trts)
        kg._index()
        return kg

    def apply_updates(self, kg, updates):
        applied = []
        for u in updates:
            if not kg.apply_edge_delta(u["rel"], u["src"], u["dst"], u["d_alpha"], u["d_beta"]):
                continue
            if u["rel"] == "HAS_SYMPTOM":
                e = kg.edges[(u["src"], u["dst"])]
                a, b = e["alpha"], e["beta"]
            else:
                lt = kg.layterms[u["src"]]
                a, b = lt["alpha"], lt["beta"]
            with self.db.tx() as c:
                c.execute("INSERT INTO edge_state (rel, src, dst, alpha, beta, updated_at) VALUES (?, ?, ?, ?, ?, ?) "
                          "ON CONFLICT(rel, src, dst) DO UPDATE SET alpha=excluded.alpha, beta=excluded.beta, "
                          "updated_at=excluded.updated_at", (u["rel"], u["src"], u["dst"], a, b, time.time()))
            applied.append(u)
        return applied

    def add_layterm(self, kg, lt):
        with self.db.tx() as c:
            c.execute("INSERT OR REPLACE INTO layterm_extra (id, text, lang, symptom_id, weight, created_at, created_by) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?)", (lt["id"], lt["text"], lt["lang"], lt["symptom_id"], lt["weight"],
                                                       time.time(), lt.get("created_by", "expert")))
        kg.add_layterm({**lt, "origin": "expert"})

    def add_edge(self, kg, d, s, weight):
        with self.db.tx() as c:
            c.execute("INSERT OR REPLACE INTO edge_extra (d, s, weight, created_at) VALUES (?, ?, ?, ?)",
                      (d, s, weight, time.time()))
        kg.add_edge(d, s, weight)

    def add_disease(self, kg, disease_dict, symptoms, treatments, created_by="expert"):
        """Persist a new disease (and its edges) to SQLite, then mirror into the live KG."""
        self.db.add_disease_extra(
            disease_dict["id"],
            json.dumps(disease_dict, ensure_ascii=False),
            symptoms, treatments, created_by
        )
        kg.add_disease(disease_dict, symptoms, treatments)


class Neo4jStore:
    name = "neo4j"

    def __init__(self, uri, user, password, database=None):
        from neo4j import GraphDatabase
        self.uri = uri
        self.database = database or None
        self.driver = GraphDatabase.driver(uri, auth=(user, password), connection_timeout=10)

    def describe(self):
        return {"backend": "neo4j", "detail": self.uri}

    def close(self):
        self.driver.close()

    def _run(self, cypher, **params):
        with self.driver.session(database=self.database) as s:
            return [r.data() for r in s.run(cypher, **params)]

    def ping(self):
        self.driver.verify_connectivity()
        rows = self._run("MATCH (m:KGMeta {id:'meta'}) RETURN m.version AS version")
        return rows[0]["version"] if rows else None

    # ---- seeding -----------------------------------------------------------
    def seed(self, seed, reset=False):
        """Idempotent load of the seed JSON (MERGE everywhere). reset=True wipes
        every node first - this also erases learned weights."""
        if reset:
            self._run("MATCH (n) DETACH DELETE n")
        for label, key in [("Crop", "crop_id"), ("Disease", "disease_id"), ("Symptom", "symptom_id"),
                           ("LayTerm", "term_id"), ("Treatment", "treatment_id"),
                           ("ConfirmationImage", "image_id"), ("SeasonCondition", "condition_id")]:
            self._run(f"CREATE CONSTRAINT {label.lower()}_key IF NOT EXISTS FOR (n:{label}) REQUIRE n.{key} IS UNIQUE")

        crop = seed["meta"]["crop"]
        self._run("MERGE (m:KGMeta {id:'meta'}) SET m.version=$v, m.sources_json=$src, m.notes=$notes",
                  v=seed["meta"]["version"], src=json.dumps(seed["meta"]["sources"]), notes=seed["meta"].get("notes", ""))
        self._run("MERGE (c:Crop {crop_id:$id}) SET c.name_en=$en, c.name_ta=$ta", id=crop["id"], en=crop["name_en"], ta=crop["name_ta"])
        self._run("""UNWIND $rows AS r MERGE (s:SeasonCondition {condition_id:r.id})
                     SET s.name_en=r.name_en, s.name_ta=r.name_ta, s.temp_range=r.temp_range,
                         s.humidity_range=r.humidity_range, s.months=r.months""", rows=seed["seasons"])
        diseases = [{**d, "source_citation": seed["meta"]["sources"].get(d["source"], d["source"])} for d in seed["diseases"]]
        self._run("""UNWIND $rows AS r MERGE (d:Disease {disease_id:r.id})
                     SET d.name_en=r.name_en, d.name_ta=r.name_ta, d.type=r.type, d.severity_scale=r.severity,
                         d.contagious=r.contagious, d.source=r.source, d.source_citation=r.source_citation,
                         d.summary_en=r.summary_en, d.summary_ta=r.summary_ta,
                         d.prevention_en=r.prevention_en, d.prevention_ta=r.prevention_ta, d.images=r.images
                     WITH d MATCH (c:Crop {crop_id:$crop}) MERGE (c)-[:SUSCEPTIBLE_TO]->(d)""",
                  rows=diseases, crop=crop["id"])
        fav = [{"d": d["id"], "s": s, "b": b} for d in seed["diseases"] for s, b in d.get("favored_by", {}).items()]
        self._run("""UNWIND $rows AS r MATCH (d:Disease {disease_id:r.d}), (s:SeasonCondition {condition_id:r.s})
                     MERGE (d)-[f:FAVORED_BY]->(s) SET f.boost=r.b""", rows=fav)
        imgs = [{"d": d["id"], "id": f"img_{img.rsplit('.', 1)[0]}", "url": f"/static/img/diseases/{img}"}
                for d in seed["diseases"] for img in d.get("images", [])]
        self._run("""UNWIND $rows AS r MATCH (d:Disease {disease_id:r.d})
                     MERGE (i:ConfirmationImage {image_id:r.id}) ON CREATE SET i.verified_count=0
                     SET i.url=r.url, i.disease_id=r.d MERGE (d)-[:CONFIRMED_BY]->(i)""", rows=imgs)
        syms = [{k: v for k, v in s.items() if k != "lay"} for s in seed["symptoms"]]
        self._run("""UNWIND $rows AS r MERGE (s:Symptom {symptom_id:r.id})
                     SET s.part=r.part, s.group=r.group, s.cost=r.cost, s.label_en=r.label_en, s.label_ta=r.label_ta,
                         s.description_en=r.label_en, s.question_en=r.question_en, s.question_ta=r.question_ta""", rows=syms)
        lts = flatten_layterms(seed)
        self._run("""UNWIND $rows AS r MATCH (s:Symptom {symptom_id:r.symptom_id})
                     MERGE (l:LayTerm {term_id:r.id}) SET l.raw_text=r.text, l.lang=r.lang, l.region_tag='general', l.origin='seed'
                     MERGE (l)-[m:LAYTERM_MAPS_TO]->(s)
                     ON CREATE SET m.alpha=r.weight*$k, m.beta=(1-r.weight)*$k, m.weight=r.weight, m.seed_weight=r.weight""",
                  rows=lts, k=PRIOR_STRENGTH)
        hs = [{"d": d, "s": s, "w": w} for d, s, w in seed["has_symptom"]]
        self._run("""UNWIND $rows AS r MATCH (d:Disease {disease_id:r.d}), (s:Symptom {symptom_id:r.s})
                     MERGE (d)-[h:HAS_SYMPTOM]->(s)
                     ON CREATE SET h.alpha=r.w*$k, h.beta=(1-r.w)*$k, h.weight=r.w, h.seed_weight=r.w""",
                  rows=hs, k=PRIOR_STRENGTH)
        self._run("""UNWIND $rows AS r MERGE (t:Treatment {treatment_id:r.id})
                     SET t.name_en=r.name_en, t.name_ta=r.name_ta, t.type=r.type, t.dosage=r.dosage_en,
                         t.dosage_en=r.dosage_en, t.dosage_ta=r.dosage_ta, t.source=r.source""", rows=seed["treatments"])
        tb = [{"d": d, "t": t, "e": e} for d, t, e in seed["treated_by"]]
        self._run("""UNWIND $rows AS r MATCH (d:Disease {disease_id:r.d}), (t:Treatment {treatment_id:r.t})
                     MERGE (d)-[x:TREATED_BY]->(t) SET x.efficacy=r.e""", rows=tb)
        return self._run("MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY label")

    # ---- load --------------------------------------------------------------
    def load(self):
        meta_rows = self._run("MATCH (m:KGMeta {id:'meta'}) RETURN m.version AS version, m.sources_json AS sources, m.notes AS notes")
        if not meta_rows:
            raise RuntimeError("Neo4j graph is not seeded - run: python scripts/seed_neo4j.py")
        crop = self._run("MATCH (c:Crop) RETURN c.crop_id AS id, c.name_en AS name_en, c.name_ta AS name_ta LIMIT 1")[0]
        meta = {"version": meta_rows[0]["version"], "sources": json.loads(meta_rows[0]["sources"] or "{}"),
                "notes": meta_rows[0]["notes"], "crop": crop}
        seasons = self._run("""MATCH (s:SeasonCondition) RETURN s.condition_id AS id, s.name_en AS name_en, s.name_ta AS name_ta,
                               s.temp_range AS temp_range, s.humidity_range AS humidity_range, s.months AS months""")
        diseases = self._run("""MATCH (d:Disease)
                                WITH d, [(d)-[f:FAVORED_BY]->(s:SeasonCondition) | [s.condition_id, f.boost]] AS fav
                                RETURN d.disease_id AS id, d.name_en AS name_en, d.name_ta AS name_ta, d.type AS type,
                                       d.severity_scale AS severity, d.contagious AS contagious, d.source AS source,
                                       d.summary_en AS summary_en, d.summary_ta AS summary_ta,
                                       d.prevention_en AS prevention_en, d.prevention_ta AS prevention_ta,
                                       d.images AS images, fav""")
        for d in diseases:
            d["favored_by"] = {k: v for k, v in d.pop("fav")}
            for k in ("prevention_en", "prevention_ta", "images"):
                d[k] = d.get(k) or []
            d["contagious"] = bool(d.get("contagious"))
            d["severity"] = d.get("severity") or 3
        symptoms = self._run("""MATCH (s:Symptom) RETURN s.symptom_id AS id, s.part AS part, s.group AS group, s.cost AS cost,
                                coalesce(s.label_en, s.description_en) AS label_en, coalesce(s.label_ta, s.description_en) AS label_ta,
                                coalesce(s.question_en, s.description_en) AS question_en,
                                coalesce(s.question_ta, s.description_en) AS question_ta""")
        for s in symptoms:
            s["cost"] = s["cost"] or 0
            s["part"] = s["part"] or "leaf"
            s["group"] = s["group"] or "other"
        lts = self._run("""MATCH (l:LayTerm)-[m:LAYTERM_MAPS_TO]->(s:Symptom)
                           RETURN l.term_id AS id, l.raw_text AS text, coalesce(l.lang,'ta') AS lang,
                                  coalesce(l.origin,'seed') AS origin, s.symptom_id AS symptom_id,
                                  m.weight AS weight, m.alpha AS alpha, m.beta AS beta""")
        seen = set()
        for lt in lts:
            if lt["id"] in seen:                       # one phrase mapped to several symptoms
                lt["id"] = f"{lt['id']}@{lt['symptom_id']}"
            seen.add(lt["id"])
            if lt["alpha"] is None:
                lt.pop("alpha"), lt.pop("beta")
        hs = self._run("""MATCH (d:Disease)-[h:HAS_SYMPTOM]->(s:Symptom)
                          RETURN d.disease_id AS d, s.symptom_id AS s, h.weight AS w, h.alpha AS alpha, h.beta AS beta,
                                 coalesce(h.seed_weight, h.weight) AS seed""")
        has_symptom = []
        for e in hs:
            a = e["alpha"] if e["alpha"] is not None else e["w"] * PRIOR_STRENGTH
            b = e["beta"] if e["beta"] is not None else (1 - e["w"]) * PRIOR_STRENGTH
            has_symptom.append({"d": e["d"], "s": e["s"], "alpha": a, "beta": b, "seed": e["seed"]})
        treatments = self._run("""MATCH (t:Treatment) RETURN t.treatment_id AS id, t.name_en AS name_en,
                                  coalesce(t.name_ta, t.name_en) AS name_ta, t.type AS type,
                                  coalesce(t.dosage_en, t.dosage) AS dosage_en, coalesce(t.dosage_ta, t.dosage_en, t.dosage) AS dosage_ta,
                                  coalesce(t.source, 'general') AS source""")
        tb = self._run("MATCH (d:Disease)-[x:TREATED_BY]->(t:Treatment) RETURN d.disease_id AS d, t.treatment_id AS t, x.efficacy AS e")
        return KnowledgeGraph({
            "meta": meta, "seasons": seasons, "diseases": diseases, "symptoms": symptoms, "layterms": lts,
            "has_symptom": has_symptom, "treatments": treatments, "treated_by": [[r["d"], r["t"], r["e"]] for r in tb],
        })

    # ---- writes ------------------------------------------------------------
    def apply_updates(self, kg, updates):
        hs = [u for u in updates if u["rel"] == "HAS_SYMPTOM"]
        lt = [u for u in updates if u["rel"] == "LAYTERM_MAPS_TO"]
        if hs:
            self._run("""UNWIND $rows AS u MATCH (d:Disease {disease_id:u.src})-[h:HAS_SYMPTOM]->(s:Symptom {symptom_id:u.dst})
                         SET h.alpha = coalesce(h.alpha, h.weight*$k) + u.d_alpha,
                             h.beta = coalesce(h.beta, (1-h.weight)*$k) + u.d_beta
                         SET h.weight = h.alpha / (h.alpha + h.beta)""", rows=hs, k=PRIOR_STRENGTH)
        if lt:
            rows = [{**u, "src": u["src"].split("@")[0]} for u in lt]
            self._run("""UNWIND $rows AS u MATCH (l:LayTerm {term_id:u.src})-[m:LAYTERM_MAPS_TO]->(s:Symptom {symptom_id:u.dst})
                         SET m.alpha = coalesce(m.alpha, m.weight*$k) + u.d_alpha,
                             m.beta = coalesce(m.beta, (1-m.weight)*$k) + u.d_beta
                         SET m.weight = m.alpha / (m.alpha + m.beta)""", rows=rows, k=PRIOR_STRENGTH)
        return [u for u in updates if kg.apply_edge_delta(u["rel"], u["src"], u["dst"], u["d_alpha"], u["d_beta"])]

    def add_layterm(self, kg, lt):
        self._run("""MATCH (s:Symptom {symptom_id:$sid})
                     MERGE (l:LayTerm {term_id:$id}) SET l.raw_text=$text, l.lang=$lang, l.region_tag='general', l.origin='expert'
                     MERGE (l)-[m:LAYTERM_MAPS_TO]->(s) SET m.weight=$w, m.alpha=$w*$k, m.beta=(1-$w)*$k, m.seed_weight=$w""",
                  sid=lt["symptom_id"], id=lt["id"], text=lt["text"], lang=lt["lang"], w=lt["weight"], k=PRIOR_STRENGTH)
        kg.add_layterm({**lt, "origin": "expert"})

    def add_edge(self, kg, d, s, weight):
        self._run("""MATCH (d:Disease {disease_id:$d}), (s:Symptom {symptom_id:$s})
                     MERGE (d)-[h:HAS_SYMPTOM]->(s) SET h.weight=$w, h.alpha=$w*$k, h.beta=(1-$w)*$k, h.seed_weight=$w""",
                  d=d, s=s, w=weight, k=PRIOR_STRENGTH)
        kg.add_edge(d, s, weight)

    def record_image_confirmation(self, disease_id):
        self._run("""MATCH (d:Disease {disease_id:$d})-[:CONFIRMED_BY]->(i:ConfirmationImage)
                     SET i.verified_count = coalesce(i.verified_count, 0) + 1""", d=disease_id)


def make_store(config, db):
    """Pick the graph store from config. KG_BACKEND = auto | neo4j | embedded."""
    backend = (config.get("KG_BACKEND") or "auto").lower()
    uri = config.get("NEO4J_URI")
    if backend in ("neo4j", "auto") and uri:
        try:
            store = Neo4jStore(uri, config.get("NEO4J_USER") or "neo4j", config.get("NEO4J_PASSWORD") or "",
                               config.get("NEO4J_DATABASE"))
            version = store.ping()
            if version is None:
                raise RuntimeError("graph not seeded (run scripts/seed_neo4j.py)")
            log.info("Using Neo4j knowledge graph at %s (version %s)", uri, version)
            return store
        except Exception as e:  # noqa: BLE001 - any driver/network error -> fall back
            if backend == "neo4j":
                raise
            log.warning("Neo4j unavailable (%s) - falling back to embedded graph store", e)
    return EmbeddedStore(db, config.get("KG_SEED_PATH"))
