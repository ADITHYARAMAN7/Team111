import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tomatodoc.inference import DiagnosisEngine  # noqa: E402
from tomatodoc.kg.graph import KnowledgeGraph, load_seed, seed_to_data  # noqa: E402
from tomatodoc.nlu import SymptomMatcher  # noqa: E402


@pytest.fixture(scope="session")
def seed():
    return load_seed()


@pytest.fixture()
def kg(seed):
    return KnowledgeGraph(seed_to_data(seed))


@pytest.fixture(scope="session")
def matcher(seed):
    return SymptomMatcher(KnowledgeGraph(seed_to_data(seed)).layterm_list())


@pytest.fixture()
def engine(kg):
    return DiagnosisEngine(kg)


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.delenv("NEO4J_URI", raising=False)
    from tomatodoc import create_app
    return create_app({"DATABASE_PATH": str(tmp_path / "t.db"), "KG_BACKEND": "embedded", "NEO4J_URI": None, "EXPERT_TOKEN": None})


@pytest.fixture()
def client(app):
    return app.test_client()
