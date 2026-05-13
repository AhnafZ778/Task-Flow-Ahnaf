## This handles all the database stuff for Task-Flow
## I'm using sqlite3 because its simple and doesn't need a whole server setup
## the path for where the db file lives comes from an environment variable
## but if thats not set it'll just make a taskflow.db in the backend folder

import os
import sqlite3

## grabbing the path from env or defaulting to local
DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "..", "taskflow.db"))

## the SQL for creating the tasks table
## status can only be pending or completed, priority goes from 1-3
## deadline is optional and the timestamps fill themselves in
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

def get_db(db_path = None):
    ## row_factory makes it so the rows come back as dict-like objects
    ## instead of plain tuples which is way easier to work with
    ## also WAL mode is for better performance when reading concurrently
    path = db_path if db_path else DATABASE_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(db_path = None):
    ## just runs the create table SQL, nothing fancy
    conn = get_db(db_path)
    try:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()
    finally:
        conn.close()
