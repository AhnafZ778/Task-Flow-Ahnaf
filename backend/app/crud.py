## All the database operations for tasks live here
## every function takes an optional db_path so the tests can use
## their own separate database and not mess with the real one
## also every mutation updates the updated_at timestamp automatically

from datetime import datetime, timezone
from app.database import get_db


def _now():
    ## gets current UTC time as a string with microsecond precision
    ## the microseconds are important because without them the
    ## updated_at comparisons in the tests don't work properly
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")


def _row_to_dict(row):
    ## sqlite3 Row objects arent JSON serializable on their own
    ## so I need to convert them to regular dicts first
    return dict(row)


## fetches all tasks, can optionally filter by status
## results are ordered by priority (highest first) then by newest
## if status_filter is None or "all" it just returns everything
def get_all_tasks(status_filter = None, db_path = None):
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

        result = []
        for row in rows:
            result.append(_row_to_dict(row))
        return result
    finally:
        conn.close()


## fetches a single task by its ID, returns None if it doesn't exist
def get_task_by_id(task_id, db_path = None):
    conn = get_db(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row:
            return _row_to_dict(row)
        else:
            return None
    finally:
        conn.close()


## returns tasks that have a deadline, grouped by date
## the result looks like: { "2026-05-13": [task, ...], "2026-05-14": [task, ...] }
## this is what powers the calendar popup on the frontend
def get_tasks_grouped_by_deadline(db_path = None):
    conn = get_db(db_path)
    try:
        rows = conn.execute(
            """
            SELECT * FROM tasks
            WHERE deadline IS NOT NULL AND deadline != ''
            ORDER BY deadline ASC, priority DESC
            """
        ).fetchall()

        ## grouping tasks by the date portion of their deadline
        ## some deadlines include time like 2026-05-13T17:00 so I just
        ## take the first 10 characters to get the YYYY-MM-DD part
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


## inserts a new task into the database and returns the created row
## status always starts as 'pending' and timestamps are set to now
def create_task(title, description = None, priority = 2, deadline = None, db_path = None):
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
        new_id = cursor.lastrowid
        return get_task_by_id(new_id, db_path)
    finally:
        conn.close()


## updates a task's fields, only the ones that are provided get changed
## if a field is None it just keeps the existing value
## returns the updated task or None if it wasn't found
def update_task(task_id, title = None, description = None, status = None, priority = None, deadline = None, db_path = None):
    existing = get_task_by_id(task_id, db_path)
    if existing is None:
        return None

    ## using the existing values as fallbacks for anything that wasn't provided
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


## flips a task between 'pending' and 'completed'
## returns None if the task doesn't exist
def toggle_task_status(task_id, db_path = None):
    existing = get_task_by_id(task_id, db_path)
    if existing is None:
        return None

    current_status = existing["status"]
    if current_status == "pending":
        new_status = "completed"
    else:
        new_status = "pending"
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


## deletes a task by ID
## returns True if something was actually deleted, False if it didn't exist
def delete_task(task_id, db_path = None):
    conn = get_db(db_path)
    try:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return True
        else:
            return False
    finally:
        conn.close()
