"""
db.py - operational SQLite database.

Holds what is NOT domain knowledge: consultation logs, feedback events, phrases
the system failed to understand, and (for the embedded graph store) the learned
edge state. The knowledge graph itself lives in Neo4j or the seed file.
"""
import json
import os
import sqlite3
import threading
import time
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS consultations (
    id TEXT PRIMARY KEY,
    created_at REAL, updated_at REAL,
    input_text TEXT, lang TEXT, season TEXT,
    evidence_json TEXT, posterior_json TEXT,
    top_disease TEXT, top_prob REAL, status TEXT,
    questions_asked INTEGER DEFAULT 0, photo_used INTEGER DEFAULT 0,
    outcome TEXT, final_disease TEXT
);
CREATE TABLE IF NOT EXISTS feedback_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consultation_id TEXT, created_at REAL,
    outcome TEXT, disease_id TEXT, corrected_to TEXT, updates_json TEXT
);
CREATE TABLE IF NOT EXISTS unmatched (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT UNIQUE, count INTEGER DEFAULT 1,
    first_seen REAL, last_seen REAL,
    resolved INTEGER DEFAULT 0, resolved_symptom TEXT
);
CREATE TABLE IF NOT EXISTS edge_state (
    rel TEXT, src TEXT, dst TEXT, alpha REAL, beta REAL, updated_at REAL,
    PRIMARY KEY (rel, src, dst)
);
CREATE TABLE IF NOT EXISTS layterm_extra (
    id TEXT PRIMARY KEY, text TEXT, lang TEXT, symptom_id TEXT, weight REAL,
    created_at REAL, created_by TEXT
);
CREATE TABLE IF NOT EXISTS edge_extra (
    d TEXT, s TEXT, weight REAL, created_at REAL, PRIMARY KEY (d, s)
);
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at REAL, disease TEXT, lat REAL, lon REAL, source TEXT DEFAULT 'farmer', consultation_id TEXT
);
CREATE INDEX IF NOT EXISTS reports_time ON reports (created_at);
CREATE TABLE IF NOT EXISTS edge_suggestions (
    d TEXT, s TEXT, count REAL DEFAULT 0, last_seen REAL, status TEXT DEFAULT 'open',
    PRIMARY KEY (d, s)
);
"""


class Database:
    def __init__(self, path):
        self.path = path
        if path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self._lock = threading.Lock()
        # one shared connection; sqlite3 serialises access via our lock
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        if path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(SCHEMA)
        cols = {r[1] for r in self._conn.execute("PRAGMA table_info(consultations)")}
        for col, typ in (("lat", "REAL"), ("lon", "REAL"), ("severity", "TEXT"), ("extent", "INTEGER"), ("voice_ai", "INTEGER"),
                         ("soil_used", "INTEGER")):
            if col not in cols:                      # migrate databases created by v2.0
                self._conn.execute(f"ALTER TABLE consultations ADD COLUMN {col} {typ}")
        self._conn.commit()

    @contextmanager
    def tx(self):
        with self._lock:
            try:
                yield self._conn
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise

    def query(self, sql, args=()):
        with self._lock:
            return [dict(r) for r in self._conn.execute(sql, args).fetchall()]

    # ---- consultations -----------------------------------------------------
    def upsert_consultation(self, cid, **f):
        now = time.time()
        cols = ["input_text", "lang", "season", "evidence_json", "posterior_json", "top_disease", "top_prob",
                "status", "questions_asked", "photo_used", "lat", "lon", "severity", "extent", "voice_ai", "soil_used"]
        vals = [f.get(c) for c in cols]
        with self.tx() as c:
            exists = c.execute("SELECT 1 FROM consultations WHERE id=?", (cid,)).fetchone()
            if exists:
                c.execute(f"UPDATE consultations SET {', '.join(f'{k}=?' for k in cols)}, updated_at=? WHERE id=?",
                          (*vals, now, cid))
            else:
                c.execute(f"INSERT INTO consultations (id, created_at, updated_at, {', '.join(cols)}) "
                          f"VALUES (?, ?, ?, {', '.join('?' for _ in cols)})", (cid, now, now, *vals))

    def get_consultation(self, cid):
        rows = self.query("SELECT * FROM consultations WHERE id=?", (cid,))
        return rows[0] if rows else None

    def record_feedback(self, cid, outcome, disease_id, corrected_to, updates):
        with self.tx() as c:
            c.execute("INSERT INTO feedback_events (consultation_id, created_at, outcome, disease_id, corrected_to, updates_json) "
                      "VALUES (?, ?, ?, ?, ?, ?)", (cid, time.time(), outcome, disease_id, corrected_to, json.dumps(updates)))
            c.execute("UPDATE consultations SET outcome=?, final_disease=? WHERE id=?",
                      (outcome, corrected_to or (disease_id if outcome == "confirmed" else None), cid))

    # ---- unmatched phrases (the "teach me" queue) --------------------------
    def log_unmatched(self, text):
        text = (text or "").strip()[:500]
        if not text:
            return
        now = time.time()
        with self.tx() as c:
            c.execute("INSERT INTO unmatched (text, first_seen, last_seen) VALUES (?, ?, ?) "
                      "ON CONFLICT(text) DO UPDATE SET count=count+1, last_seen=excluded.last_seen", (text, now, now))

    def resolve_unmatched(self, uid, symptom_id):
        with self.tx() as c:
            c.execute("UPDATE unmatched SET resolved=1, resolved_symptom=? WHERE id=?", (symptom_id, uid))

    # ---- edge suggestions (graph growth from field evidence) ---------------
    def suggest_edge(self, d, s, amount):
        with self.tx() as c:
            c.execute("INSERT INTO edge_suggestions (d, s, count, last_seen) VALUES (?, ?, ?, ?) "
                      "ON CONFLICT(d, s) DO UPDATE SET count=count+excluded.count, last_seen=excluded.last_seen",
                      (d, s, amount, time.time()))

    def set_suggestion_status(self, d, s, status):
        with self.tx() as c:
            c.execute("UPDATE edge_suggestions SET status=? WHERE d=? AND s=?", (status, d, s))

    # ---- community outbreak reports ----------------------------------------
    def add_report(self, disease, lat, lon, source="farmer", consultation_id=None, created_at=None):
        with self.tx() as c:
            c.execute("INSERT INTO reports (created_at, disease, lat, lon, source, consultation_id) VALUES (?, ?, ?, ?, ?, ?)",
                      (created_at or time.time(), disease, lat, lon, source, consultation_id))

    def reports_since(self, since):
        return self.query("SELECT * FROM reports WHERE created_at >= ? ORDER BY created_at DESC", (since,))
