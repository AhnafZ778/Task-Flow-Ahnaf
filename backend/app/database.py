import os
import sqlite3

DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "..", "taskflow.db"))

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER   PRIMARY KEY AUTOINCREMENT,
    title       TEXT      NOT NULL,
    description TEXT,
    status      TEXT      NOT NULL DEFAULT 'pending'
                          CHECK (status IN ('pending', 'completed')),
    priority    INTEGER   NOT NULL DEFAULT 2
                          CHECK (priority BETWEEN 1 AND 3),
    deadline    TEXT      DEFAULT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db(db_path: str | None = None) -> sqlite3.Connection:
    ## Row factory so rows behave like dicts, WAL for concurrent reads
    path = db_path or DATABASE_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(db_path: str | None = None) -> None:
    conn = get_db(db_path)
    try:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()
    finally:
        conn.close()
