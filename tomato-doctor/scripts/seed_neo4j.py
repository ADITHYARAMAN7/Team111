"""
seed_neo4j.py - load the curated knowledge graph into Neo4j (AuraDB or local).

    python scripts/seed_neo4j.py            # idempotent MERGE; keeps learned weights
    python scripts/seed_neo4j.py --reset    # wipe the database first (erases learning!)
    python scripts/seed_neo4j.py --export-cypher docs/tomato_kg.cypher   # no DB needed

Connection settings come from .env / environment: NEO4J_URI, NEO4J_USER
(or NEO4J_USERNAME), NEO4J_PASSWORD, NEO4J_DATABASE.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tomatodoc.config import load_config  # noqa: E402
from tomatodoc.kg.graph import PRIOR_STRENGTH, flatten_layterms, load_seed, validate_seed  # noqa: E402
from tomatodoc.kg.store import Neo4jStore  # noqa: E402


def q(v):
    return json.dumps(v, ensure_ascii=False)


def export_cypher(seed, path):
    """Plain Cypher script (paste into Neo4j Browser / Aura Query) - same graph the seeder builds."""
    out = ["// Tomato Doctor knowledge graph - generated from tomatodoc/kg/seed/tomato_kg.json", ""]
    for label, key in [("Crop", "crop_id"), ("Disease", "disease_id"), ("Symptom", "symptom_id"), ("LayTerm", "term_id"),
                       ("Treatment", "treatment_id"), ("ConfirmationImage", "image_id"), ("SeasonCondition", "condition_id")]:
        out.append(f"CREATE CONSTRAINT {label.lower()}_key IF NOT EXISTS FOR (n:{label}) REQUIRE n.{key} IS UNIQUE;")
    crop = seed["meta"]["crop"]
    out.append(f"MERGE (m:KGMeta {{id:'meta'}}) SET m.version={q(seed['meta']['version'])}, m.sources_json={q(json.dumps(seed['meta']['sources']))};")
    out.append(f"MERGE (c:Crop {{crop_id:{q(crop['id'])}}}) SET c.name_en={q(crop['name_en'])}, c.name_ta={q(crop['name_ta'])};")
    for s in seed["seasons"]:
        out.append(f"MERGE (s:SeasonCondition {{condition_id:{q(s['id'])}}}) SET s.name_en={q(s['name_en'])}, s.name_ta={q(s['name_ta'])}, "
                   f"s.temp_range={q(s['temp_range'])}, s.humidity_range={q(s['humidity_range'])}, s.months={q(s['months'])};")
    for d in seed["diseases"]:
        out.append(f"MERGE (d:Disease {{disease_id:{q(d['id'])}}}) SET d.name_en={q(d['name_en'])}, d.name_ta={q(d['name_ta'])}, "
                   f"d.type={q(d['type'])}, d.severity_scale={d['severity']}, d.contagious={str(d['contagious']).lower()}, d.source={q(d['source'])}, "
                   f"d.summary_en={q(d['summary_en'])}, d.summary_ta={q(d['summary_ta'])}, d.prevention_en={q(d['prevention_en'])}, "
                   f"d.prevention_ta={q(d['prevention_ta'])}, d.images={q(d['images'])};")
        out.append(f"MATCH (c:Crop {{crop_id:{q(crop['id'])}}}), (d:Disease {{disease_id:{q(d['id'])}}}) MERGE (c)-[:SUSCEPTIBLE_TO]->(d);")
        for sc, b in d.get("favored_by", {}).items():
            out.append(f"MATCH (d:Disease {{disease_id:{q(d['id'])}}}), (s:SeasonCondition {{condition_id:{q(sc)}}}) MERGE (d)-[f:FAVORED_BY]->(s) SET f.boost={b};")
        for img in d.get("images", []):
            iid = "img_" + img.rsplit(".", 1)[0]
            out.append(f"MATCH (d:Disease {{disease_id:{q(d['id'])}}}) MERGE (i:ConfirmationImage {{image_id:{q(iid)}}}) "
                       f"SET i.url={q('/static/img/diseases/' + img)}, i.disease_id={q(d['id'])}, i.verified_count=coalesce(i.verified_count,0) MERGE (d)-[:CONFIRMED_BY]->(i);")
    for s in seed["symptoms"]:
        out.append(f"MERGE (s:Symptom {{symptom_id:{q(s['id'])}}}) SET s.part={q(s['part'])}, s.group={q(s['group'])}, s.cost={s['cost']}, "
                   f"s.label_en={q(s['label_en'])}, s.label_ta={q(s['label_ta'])}, s.description_en={q(s['label_en'])}, "
                   f"s.question_en={q(s['question_en'])}, s.question_ta={q(s['question_ta'])};")
    for lt in flatten_layterms(seed):
        w = lt["weight"]
        out.append(f"MATCH (s:Symptom {{symptom_id:{q(lt['symptom_id'])}}}) MERGE (l:LayTerm {{term_id:{q(lt['id'])}}}) "
                   f"SET l.raw_text={q(lt['text'])}, l.lang={q(lt['lang'])}, l.region_tag='general', l.origin='seed' "
                   f"MERGE (l)-[m:LAYTERM_MAPS_TO]->(s) ON CREATE SET m.weight={w}, m.seed_weight={w}, m.alpha={w * PRIOR_STRENGTH:.4f}, m.beta={(1 - w) * PRIOR_STRENGTH:.4f};")
    for d, s, w in seed["has_symptom"]:
        out.append(f"MATCH (d:Disease {{disease_id:{q(d)}}}), (s:Symptom {{symptom_id:{q(s)}}}) MERGE (d)-[h:HAS_SYMPTOM]->(s) "
                   f"ON CREATE SET h.weight={w}, h.seed_weight={w}, h.alpha={w * PRIOR_STRENGTH:.4f}, h.beta={(1 - w) * PRIOR_STRENGTH:.4f};")
    for t in seed["treatments"]:
        out.append(f"MERGE (t:Treatment {{treatment_id:{q(t['id'])}}}) SET t.name_en={q(t['name_en'])}, t.name_ta={q(t['name_ta'])}, "
                   f"t.type={q(t['type'])}, t.dosage={q(t['dosage_en'])}, t.dosage_en={q(t['dosage_en'])}, t.dosage_ta={q(t['dosage_ta'])}, t.source={q(t['source'])};")
    for d, t, e in seed["treated_by"]:
        out.append(f"MATCH (d:Disease {{disease_id:{q(d)}}}), (t:Treatment {{treatment_id:{q(t)}}}) MERGE (d)-[x:TREATED_BY]->(t) SET x.efficacy={e};")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"wrote {len(out)} statements to {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reset", action="store_true", help="delete every node first (erases learned weights)")
    ap.add_argument("--export-cypher", metavar="PATH", help="write a .cypher script instead of connecting")
    args = ap.parse_args()

    seed = load_seed()
    errors = validate_seed(seed)
    if errors:
        sys.exit("seed is invalid:\n  " + "\n  ".join(errors))
    if args.export_cypher:
        return export_cypher(seed, args.export_cypher)

    cfg = load_config()
    if not cfg.get("NEO4J_URI"):
        sys.exit("NEO4J_URI is not set (put it in .env - see .env.example)")
    store = Neo4jStore(cfg["NEO4J_URI"], cfg["NEO4J_USER"], cfg["NEO4J_PASSWORD"] or "", cfg.get("NEO4J_DATABASE"))
    store.driver.verify_connectivity()
    if args.reset:
        print("Resetting database (all nodes, including learned weights, will be deleted)...")
    counts = store.seed(seed, reset=args.reset)
    for row in counts:
        print(f"  {row['label']:<18} {row['n']}")
    kg = store.load()
    print("loaded back:", kg.stats())
    store.close()


if __name__ == "__main__":
    main()
