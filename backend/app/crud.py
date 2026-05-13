from datetime import datetime, timezone
from typing import Optional
from app.database import get_db


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")


def _row_to_dict(row) -> dict:
    return dict(row)


def get_all_tasks(status_filter: Optional[str] = None, db_path: str | None = None) -> list[dict]:
    conn = get_db(db_path)
    try:
        if status_filter and status_filter != "all":
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY priority DESC, created_at DESC",
                (status_filter,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY priority DESC, created_at DESC"
            ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_task_by_id(task_id: int, db_path: str | None = None) -> Optional[dict]:
    conn = get_db(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def get_tasks_grouped_by_deadline(db_path: str | None = None) -> dict:
    ## Groups tasks by date portion of deadline for the calendar popup
    conn = get_db(db_path)
    try:
        rows = conn.execute(
            """
            SELECT * FROM tasks
            WHERE deadline IS NOT NULL AND deadline != ''
            ORDER BY deadline ASC, priority DESC
            """
        ).fetchall()

        grouped = {}
        for row in rows:
            task = _row_to_dict(row)
            date_key = task["deadline"][:10] if task["deadline"] else None
            if date_key:
                if date_key not in grouped:
                    grouped[date_key] = []
                grouped[date_key].append(task)

        return grouped
    finally:
        conn.close()


def create_task(
    title: str,
    description: Optional[str] = None,
    priority: int = 2,
    deadline: Optional[str] = None,
    db_path: str | None = None,
) -> dict:
    now = _now()
    conn = get_db(db_path)
    try:
        cursor = conn.execute(
            """
            INSERT INTO tasks (title, description, status, priority, deadline, created_at, updated_at)
            VALUES (?, ?, 'pending', ?, ?, ?, ?)
            """,
            (title, description, priority, deadline, now, now),
        )
        conn.commit()
        return get_task_by_id(cursor.lastrowid, db_path)
    finally:
        conn.close()


def update_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[int] = None,
    deadline: Optional[str] = None,
    db_path: str | None = None,
) -> Optional[dict]:
    existing = get_task_by_id(task_id, db_path)
    if existing is None:
        return None

    ## Fallback to existing values for any field not provided
    new_title = title if title is not None else existing["title"]
    new_desc = description if description is not None else existing["description"]
    new_status = status if status is not None else existing["status"]
    new_priority = priority if priority is not None else existing["priority"]
    new_deadline = deadline if deadline is not None else existing["deadline"]
    now = _now()

    conn = get_db(db_path)
    try:
        conn.execute(
            """
            UPDATE tasks
               SET title = ?, description = ?, status = ?, priority = ?, deadline = ?, updated_at = ?
             WHERE id = ?
            """,
            (new_title, new_desc, new_status, new_priority, new_deadline, now, task_id),
        )
        conn.commit()
    finally:
        conn.close()

    return get_task_by_id(task_id, db_path)


def toggle_task_status(task_id: int, db_path: str | None = None) -> Optional[dict]:
    existing = get_task_by_id(task_id, db_path)
    if existing is None:
        return None

    new_status = "completed" if existing["status"] == "pending" else "pending"
    now = _now()

    conn = get_db(db_path)
    try:
        conn.execute(
            "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, now, task_id),
        )
        conn.commit()
    finally:
        conn.close()

    return get_task_by_id(task_id, db_path)


def delete_task(task_id: int, db_path: str | None = None) -> bool:
    conn = get_db(db_path)
    try:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
