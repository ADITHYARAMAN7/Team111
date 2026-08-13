"""
kg_engine.py
------------
Core logic for the Tomato Disease Knowledge Graph diagnosis system.

Implements two novel components described in the project report:
1. Weighted lay-term matching -> candidate disease scoring
2. Discriminative Question Selection - when top candidates are close,
   pick the symptom question that best splits them (entropy-style),
   instead of guessing or asking a random follow-up.

This module is UI-agnostic - app.py (Flask) calls into it.
"""

from neo4j import GraphDatabase
from rapidfuzz import fuzz
import math


class TomatoKGEngine:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    # -----------------------------------------------------
    # STEP 1: Match farmer's free-text Tamil input to LayTerms
    # -----------------------------------------------------
    def match_layterms(self, farmer_text, threshold=60):
        """
        Fuzzy-matches farmer_text against all LayTerm.raw_text in the graph.
        Returns list of (term_id, symptom_id, layterm_weight, match_score).
        NOTE: this is a placeholder for a proper Tamil NLU model - see report
        section "NLP limitations / future work".

        IMPORTANT: uses token_sort_ratio (whole-phrase similarity after
        sorting tokens), NOT partial_ratio. partial_ratio scores the best-
        matching SUBSTRING, which badly over-matches short Tamil phrases
        that share common words like "இலையில்" (on the leaf) or "புள்ளி"
        (spot) even when the overall meaning is unrelated - e.g. it was
        cross-matching "ring spot" input against "spider mite webbing"
        lay-terms purely because both phrases contain "புள்ளி". Whole-
        phrase comparison is far less prone to this false-positive pattern.
        """
        with self.driver.session() as session:
            rows = session.run("""
                MATCH (l:LayTerm)-[r:LAYTERM_MAPS_TO]->(s:Symptom)
                RETURN l.term_id AS term_id, l.raw_text AS raw_text,
                       s.symptom_id AS symptom_id, r.weight AS weight
            """)
            candidates = [dict(row) for row in rows]

        matches = []
        for c in candidates:
            score = fuzz.token_sort_ratio(farmer_text, c["raw_text"])
            if score >= threshold:
                matches.append({
                    "term_id": c["term_id"],
                    "symptom_id": c["symptom_id"],
                    "layterm_weight": c["weight"],
                    "match_score": score / 100.0
                })
        return matches

    # -----------------------------------------------------
    # STEP 2: Score candidate diseases from matched symptoms
    # -----------------------------------------------------
    def score_diseases(self, matched_symptoms):
        """
        matched_symptoms: list of dicts from match_layterms()
        score(disease) = sum( layterm_weight * match_score * has_symptom_weight )
        """
        if not matched_symptoms:
            return []

        symptom_ids = list({m["symptom_id"] for m in matched_symptoms})
        relevance = {m["symptom_id"]: m["layterm_weight"] * m["match_score"]
                     for m in matched_symptoms}

        with self.driver.session() as session:
            rows = session.run("""
                MATCH (d:Disease)-[r:HAS_SYMPTOM]->(s:Symptom)
                WHERE s.symptom_id IN $symptom_ids
                RETURN d.disease_id AS disease_id, d.name_en AS name_en,
                       d.name_ta AS name_ta, d.type AS type,
                       s.symptom_id AS symptom_id, r.weight AS weight
            """, symptom_ids=symptom_ids)
            rows = [dict(r) for r in rows]

        scores = {}
        for r in rows:
            did = r["disease_id"]
            contribution = relevance[r["symptom_id"]] * r["weight"]
            if did not in scores:
                scores[did] = {"disease_id": did, "name_en": r["name_en"],
                                "name_ta": r["name_ta"], "type": r["type"],
                                "score": 0.0, "matched_symptoms": set()}
            scores[did]["score"] += contribution
            scores[did]["matched_symptoms"].add(r["symptom_id"])

        ranked = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
        for r in ranked:
            r["matched_symptoms"] = list(r["matched_symptoms"])
        return ranked

    # -----------------------------------------------------
    # STEP 3: Discriminative Question Selection (novelty #1)
    # -----------------------------------------------------
    def next_discriminative_question(self, top_candidates, already_asked_symptoms):
        """
        If the top 2+ candidate diseases are close in score, find the
        symptom that best SPLITS them - i.e. present in one candidate's
        symptom set but not (or weakly) in the other's - and return it
        as the next question to ask the farmer.

        This mirrors information-gain-based splitting in a decision tree,
        but walked over the weighted KG instead of a flat feature table.
        """
        if len(top_candidates) < 2:
            return None

        candidate_ids = [c["disease_id"] for c in top_candidates[:3]]

        with self.driver.session() as session:
            rows = session.run("""
                MATCH (d:Disease)-[r:HAS_SYMPTOM]->(s:Symptom)
                WHERE d.disease_id IN $ids
                RETURN d.disease_id AS disease_id, s.symptom_id AS symptom_id,
                       s.description_en AS description_en, r.weight AS weight
            """, ids=candidate_ids)
            rows = [dict(r) for r in rows]

        # Build symptom -> {disease: weight}
        symptom_map = {}
        for r in rows:
            symptom_map.setdefault(r["symptom_id"], {})[r["disease_id"]] = r["weight"]
            symptom_map[r["symptom_id"]]["_desc"] = r["description_en"]

        best_symptom, best_split_score = None, -1
        for sid, dmap in symptom_map.items():
            if sid in already_asked_symptoms:
                continue
            weights = [w for k, w in dmap.items() if k != "_desc"]
            if len(weights) < len(candidate_ids):
                # symptom absent entirely for at least one candidate disease
                # (not just low-weight) -> maximally discriminating, since
                # absence is itself informative and variance alone can't see it
                split_score = 1.0
            else:
                # variance across candidates = how well it splits them
                mean = sum(weights) / len(weights)
                split_score = sum((w - mean) ** 2 for w in weights) / len(weights)
            if split_score > best_split_score:
                best_split_score = split_score
                best_symptom = {"symptom_id": sid, "description_en": dmap["_desc"]}

        return best_symptom

    # -----------------------------------------------------
    # STEP 4: Fetch treatment + confirmation image for a disease
    # -----------------------------------------------------
    def get_diagnosis_detail(self, disease_id):
        with self.driver.session() as session:
            row = session.run("""
                MATCH (d:Disease {disease_id:$did})
                OPTIONAL MATCH (d)-[tr:TREATED_BY]->(t:Treatment)
                OPTIONAL MATCH (d)-[:CONFIRMED_BY]->(i:ConfirmationImage)
                RETURN d.name_en AS name_en, d.name_ta AS name_ta,
                       d.type AS type,
                       collect(DISTINCT {name: t.name_en, dosage: t.dosage,
                                         type: t.type, efficacy: tr.efficacy}) AS treatments,
                       i.url AS image_url
            """, did=disease_id).single()
            return dict(row) if row else None

    # -----------------------------------------------------
    # STEP 5: Feedback loop - update weights on confirmation (novelty #2)
    # -----------------------------------------------------
    def record_confirmation(self, disease_id, matched_symptom_ids, confirmed, learning_rate=0.03):
        """
        On farmer confirmation (yes/no), nudge LAYTERM_MAPS_TO and
        HAS_SYMPTOM weights along the path that led to this diagnosis.
        Confirmed=True -> increase weight (bounded at 1.0)
        Confirmed=False -> decay weight (bounded at 0.05 floor)
        """
        delta = learning_rate if confirmed else -learning_rate
        with self.driver.session() as session:
            session.run("""
                MATCH (d:Disease {disease_id:$did})-[r:HAS_SYMPTOM]->(s:Symptom)
                WHERE s.symptom_id IN $sids
                SET r.weight = CASE
                    WHEN r.weight + $delta > 1.0 THEN 1.0
                    WHEN r.weight + $delta < 0.05 THEN 0.05
                    ELSE r.weight + $delta END
            """, did=disease_id, sids=matched_symptom_ids, delta=delta)

            if confirmed:
                session.run("""
                    MATCH (d:Disease {disease_id:$did})-[:CONFIRMED_BY]->(i:ConfirmationImage)
                    SET i.verified_count = coalesce(i.verified_count, 0) + 1
                """, did=disease_id)
        return {"disease_id": disease_id, "confirmed": confirmed, "delta_applied": delta}