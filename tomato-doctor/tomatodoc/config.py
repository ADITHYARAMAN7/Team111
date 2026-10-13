"""
config.py - settings from environment variables (and an optional .env file in
the project root). Nothing is required: with no configuration the app runs on
the embedded knowledge graph with a local SQLite database.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_dotenv(path):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load_config(overrides=None):
    _load_dotenv(os.path.join(ROOT, ".env"))
    env = os.environ.get
    cfg = {
        "KG_BACKEND": env("KG_BACKEND", "auto"),               # auto | neo4j | embedded
        "NEO4J_URI": env("NEO4J_URI"),
        "NEO4J_USER": env("NEO4J_USER") or env("NEO4J_USERNAME") or "neo4j",
        "NEO4J_PASSWORD": env("NEO4J_PASSWORD"),
        "NEO4J_DATABASE": env("NEO4J_DATABASE"),
        "DATABASE_PATH": env("DATABASE_PATH", os.path.join(ROOT, "instance", "tomatodoc.db")),
        "MODEL_DIR": env("MODEL_DIR", os.path.join(ROOT, "models")),
        "KG_SEED_PATH": env("KG_SEED_PATH"),
        "EXPERT_TOKEN": env("EXPERT_TOKEN"),                     # unset -> expert pages only from this computer
        "ENABLE_VISION": env("ENABLE_VISION", "1") != "0",
        "MAX_UPLOAD_MB": float(env("MAX_UPLOAD_MB", "8")),
        "GEMINI_API_KEY": env("GEMINI_API_KEY"),
        "GEMINI_MODEL": env("GEMINI_MODEL", "gemini-3.8-flash"),
        "GEMINI_FOR_TEXT": env("GEMINI_FOR_TEXT", "1") != "0",   # also use Gemini on typed text when a key is set
        "ENABLE_WEATHER": env("ENABLE_WEATHER", "1") != "0",
        "OUTBREAK_RADIUS_KM": float(env("OUTBREAK_RADIUS_KM", "30")),
        "OUTBREAK_DAYS": int(env("OUTBREAK_DAYS", "21")),
        "EVALUATION_PATH": os.path.join(ROOT, "docs", "evaluation.json"),
    }
    if overrides:
        cfg.update(overrides)
    return cfg
