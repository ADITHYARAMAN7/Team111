"""Neo4j store integration test. Runs only against a THROWAWAY database:
    TEST_NEO4J_URI=bolt://localhost:7687 TEST_NEO4J_PASSWORD=... pytest tests/test_neo4j.py
(the test wipes the database)."""
import os

import pytest

from tomatodoc.kg.graph import KnowledgeGraph, seed_to_data
from tomatodoc.kg.store import Neo4jStore

URI = os.environ.get("TEST_NEO4J_URI")
pytestmark = pytest.mark.skipif(not URI, reason="set TEST_NEO4J_URI to run against a throwaway Neo4j")


@pytest.fixture()
def store():
    s = Neo4jStore(URI, os.environ.get("TEST_NEO4J_USER", "neo4j"), os.environ.get("TEST_NEO4J_PASSWORD", ""))
    yield s
    s.close()


def test_seed_load_roundtrip(store, seed):
    store.seed(seed, reset=True)
    kg = store.load()
    ref = KnowledgeGraph(seed_to_data(seed))
    assert kg.stats() == ref.stats()
    for key, e in ref.edges.items():
        assert kg.edges[key]["alpha"] == pytest.approx(e["alpha"])
    assert set(kg.layterms) == set(ref.layterms)
    assert kg.treatments_for("late_blight")[0]["id"] == ref.treatments_for("late_blight")[0]["id"]


def test_seed_is_idempotent_and_keeps_learning(store, seed):
    store.seed(seed, reset=True)
    kg = store.load()
    store.apply_updates(kg, [{"rel": "HAS_SYMPTOM", "src": "whitefly", "dst": "insects_fly_up", "d_alpha": 2.0, "d_beta": 0.0},
                             {"rel": "LAYTERM_MAPS_TO", "src": "lt_white_dust", "dst": "white_powder", "d_alpha": 0.0, "d_beta": 1.0}])
    store.seed(seed)                      # re-seed without reset must not overwrite learned weights
    kg2 = store.load()
    assert kg2.edges[("whitefly", "insects_fly_up")]["alpha"] == pytest.approx(kg.edges[("whitefly", "insects_fly_up")]["alpha"])
    assert kg2.layterms["lt_white_dust"]["beta"] == pytest.approx(kg.layterms["lt_white_dust"]["beta"])


def test_expert_additions_persist(store, seed):
    store.seed(seed, reset=True)
    kg = store.load()
    store.add_layterm(kg, {"id": "lt_x_test", "text": "இலை மேல மாவு", "lang": "ta", "symptom_id": "white_powder", "weight": 0.8})
    store.add_edge(kg, "early_blight", "leaf_tunnels", 0.3)
    kg2 = store.load()
    assert "lt_x_test" in kg2.layterms
    assert kg2.theta("early_blight", "leaf_tunnels") == pytest.approx(0.3)
