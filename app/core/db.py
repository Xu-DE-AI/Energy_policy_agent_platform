"""Small persistence layer for auditable request, tool, and cost events."""
from pathlib import Path
from sqlalchemy import create_engine, text
from app.core.config import settings

# SQLite is a zero-ops default. Production deployments should use managed Postgres.
if settings.database_url.startswith("sqlite:///"):
    db_path = settings.database_url.replace("sqlite:///", "", 1)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(settings.database_url, future=True, pool_pre_ping=True)

DDL = """
CREATE TABLE IF NOT EXISTS agent_runs (
  run_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, question TEXT NOT NULL,
  status TEXT NOT NULL, answer TEXT, model TEXT, input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0, llm_cost_usd REAL DEFAULT 0, tool_cost_usd REAL DEFAULT 0,
  total_cost_usd REAL DEFAULT 0, duration_ms REAL DEFAULT 0, tool_call_count INTEGER DEFAULT 0,
  error TEXT
);
CREATE TABLE IF NOT EXISTS tool_events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, sequence_no INTEGER NOT NULL,
  tool_name TEXT NOT NULL, status TEXT NOT NULL, started_at TEXT NOT NULL, duration_ms REAL DEFAULT 0,
  estimated_cost_usd REAL DEFAULT 0, input_summary TEXT, output_summary TEXT, error TEXT,
  FOREIGN KEY(run_id) REFERENCES agent_runs(run_id)
);
CREATE TABLE IF NOT EXISTS retrieved_chunks (
  chunk_id TEXT PRIMARY KEY, source_file TEXT NOT NULL, title TEXT NOT NULL, topic TEXT,
  source_url TEXT, text TEXT NOT NULL, content_hash TEXT NOT NULL
);
"""

def init_db():
    with engine.begin() as conn:
        for statement in DDL.strip().split(';'):
            if statement.strip(): conn.execute(text(statement))

def query_df(sql: str, params: dict | None = None):
    import pandas as pd
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})
