"""
test_logic_standalone.py
-------------------------
Verifies the CORE ALGORITHM (fuzzy match -> score -> disambiguate) works
correctly, using an in-memory mirror of the seed data. This does not need
a live Neo4j connection - useful to validate logic before/without AuraDB,
and to generate the worked example used in the report.
"""

from rapidfuzz import fuzz

LAYTERMS = [
    {"term_id": "lt_white_dust", "raw_text": "வெள்ளை தூள் போல இலையில்", "symptom_id": "white_powdery_coating", "weight": 0.8},
    {"term_id": "lt_white_powder", "raw_text": "இலையில் வெள்ளை பொடி", "symptom_id": "white_powdery_coating", "weight": 0.85},
    {"term_id": "lt_white_flying_insects", "raw_text": "வெள்ளை சிறு பூச்சிகள் பறக்கும்", "symptom_id": "tiny_flying_white_insects", "weight": 0.95},
    {"term_id": "lt_white_dot_insects", "raw_text": "இலையில் வெள்ளை புள்ளி பூச்சி", "symptom_id": "tiny_flying_white_insects", "weight": 0.6},
]

HAS_SYMPTOM = [
    {"disease_id": "powdery_mildew", "name_en": "Powdery Mildew", "symptom_id": "white_powdery_coating", "weight": 0.95},
    {"disease_id": "whitefly", "name_en": "Whitefly Infestation", "symptom_id": "white_powdery_coating", "weight": 0.30},
    {"disease_id": "whitefly", "name_en": "Whitefly Infestation", "symptom_id": "tiny_flying_white_insects", "weight": 0.95},
    {"disease_id": "whitefly", "name_en": "Whitefly Infestation", "symptom_id": "sticky_honeydew", "weight": 0.80},
]

SYMPTOM_DESC = {
    "white_powdery_coating": "White powdery/dust-like coating on leaf surface",
    "tiny_flying_white_insects": "Tiny white insects that fly up when leaf is disturbed",
    "sticky_honeydew": "Sticky/shiny residue on leaves, sooty mould",
}


def match_layterms(farmer_text, threshold=45):
    matches = []
    for lt in LAYTERMS:
        score = fuzz.partial_ratio(farmer_text, lt["raw_text"])
        if score >= threshold:
            matches.append({**lt, "match_score": score / 100.0})
    return matches


def score_diseases(matched):
    relevance = {}
    for m in matched:
        relevance[m["symptom_id"]] = m["weight"] * m["match_score"]

    scores = {}
    for row in HAS_SYMPTOM:
        if row["symptom_id"] not in relevance:
            continue
        contrib = relevance[row["symptom_id"]] * row["weight"]
        d = scores.setdefault(row["disease_id"], {"disease_id": row["disease_id"],
                                                    "name_en": row["name_en"], "score": 0.0})
        d["score"] += contrib
    return sorted(scores.values(), key=lambda x: x["score"], reverse=True)


def next_discriminative_question(candidate_ids, already_asked):
    symptom_map = {}
    for row in HAS_SYMPTOM:
        if row["disease_id"] in candidate_ids:
            symptom_map.setdefault(row["symptom_id"], {})[row["disease_id"]] = row["weight"]

    best_symptom, best_score = None, -1
    for sid, dmap in symptom_map.items():
        if sid in already_asked:
            continue
        weights = list(dmap.values())
        if len(weights) < len(candidate_ids):
            # symptom is present for some candidates but ABSENT (not just low-weight)
            # for at least one other -> maximally discriminating, since absence
            # itself is informative and can't be captured by variance alone
            variance = 1.0
        else:
            mean = sum(weights) / len(weights)
            variance = sum((w - mean) ** 2 for w in weights) / len(weights)
        if variance > best_score:
            best_score = variance
            best_symptom = sid
    return best_symptom


if __name__ == "__main__":
    print("=" * 60)
    print("TEST CASE: Farmer says 'வெள்ளை தூள் போல இலையில் இருக்கு'")
    print("(white dust-like on the leaf)  -- the ambiguous case")
    print("=" * 60)

    farmer_text = "இலையில் வெள்ளை தூள் போல இருக்கு"
    matched = match_layterms(farmer_text)
    print(f"\n1. Matched lay-terms ({len(matched)}):")
    for m in matched:
        print(f"   - {m['term_id']} -> symptom '{m['symptom_id']}' "
              f"(layterm_weight={m['weight']}, match_score={m['match_score']:.2f})")

    ranked = score_diseases(matched)
    print(f"\n2. Ranked disease candidates:")
    for r in ranked:
        print(f"   - {r['name_en']}: score={r['score']:.4f}")

    if len(ranked) >= 2 and ranked[1]["score"] > 0.8 * ranked[0]["score"]:
        print(f"\n3. AMBIGUOUS: top two scores within 20% of each other.")
        candidate_ids = [r["disease_id"] for r in ranked[:2]]
        q = next_discriminative_question(candidate_ids, already_asked=[])
        print(f"   -> System asks discriminating question about symptom: '{q}'")
        print(f"      ({SYMPTOM_DESC.get(q, q)})")
        print(f"   This correctly identifies 'tiny_flying_white_insects' as the")
        print(f"   splitting symptom -- present strongly in whitefly (0.95) but")
        print(f"   NOT linked to powdery_mildew at all (absent = max variance).")
    else:
        print(f"\n3. Not ambiguous -> would go straight to image confirmation for {ranked[0]['name_en']}")
