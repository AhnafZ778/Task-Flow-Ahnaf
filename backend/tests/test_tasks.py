## Tests for the Task-Flow API
## uses an isolated temporary SQLite database for each test session
## so the real production data never gets touched

import os
import tempfile
import pytest
from fastapi.testclient import TestClient

## setting up a temp database BEFORE importing the app
## this way when the app loads it'll use our test DB instead of the real one
_test_db_fd, _test_db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_PATH"] = _test_db_path

from app.database import init_db  # noqa: E402
from app.main import app  # noqa: E402


## creates the tables in the test database once per session
## cleans up the temp file after all tests are done
@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db(_test_db_path)
    yield
    os.close(_test_db_fd)
    os.unlink(_test_db_path)


## provides a fresh TestClient for each individual test
@pytest.fixture()
def client():
    return TestClient(app)


## ---- Health Check ----

def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


## ---- Create Task ----

def test_create_task_success(client):
    ## standard task creation with title and description
    response = client.post(
        "/api/tasks",
        json={"title": "Buy groceries", "description": "Milk, eggs, bread"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["task"]["title"] == "Buy groceries"
    assert data["task"]["description"] == "Milk, eggs, bread"
    assert data["task"]["status"] == "pending"


def test_create_task_title_only(client):
    ## should work with just a title, description should be None
    response = client.post("/api/tasks", json={"title": "Walk the dog"})
    assert response.status_code == 201
    data = response.json()
    assert data["task"]["title"] == "Walk the dog"
    assert data["task"]["description"] is None


def test_create_task_empty_title(client):
    ## empty title should get rejected
    response = client.post("/api/tasks", json={"title": ""})
    assert response.status_code == 400
    assert "error" in response.json()


def test_create_task_whitespace_title(client):
    ## whitespace only title should also get rejected
    response = client.post("/api/tasks", json={"title": "   "})
    assert response.status_code == 400
    assert "error" in response.json()


def test_create_task_missing_title(client):
    ## no title at all should fail
    response = client.post("/api/tasks", json={})
    assert response.status_code == 400


## ---- Priority Tests ----

def test_create_task_with_priority(client):
    ## creating a task with an explicit priority should store and return it
    response = client.post(
        "/api/tasks",
        json={"title": "Urgent fix", "priority": 3},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["task"]["priority"] == 3


def test_create_task_default_priority(client):
    ## if no priority is specified it should default to 2 (Medium)
    response = client.post(
        "/api/tasks",
        json={"title": "Normal task"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["task"]["priority"] == 2


def test_create_task_invalid_priority(client):
    ## priority outside 1-3 range should get rejected
    response = client.post(
        "/api/tasks",
        json={"title": "Bad priority", "priority": 0},
    )
    assert response.status_code == 400

    response2 = client.post(
        "/api/tasks",
        json={"title": "Bad priority high", "priority": 4},
    )
    assert response2.status_code == 400


def test_update_task_priority(client):
    ## priority should be changeable via PUT
    create_resp = client.post(
        "/api/tasks",
        json={"title": "Change my priority"},
    )
    task_id = create_resp.json()["task"]["id"]
    assert create_resp.json()["task"]["priority"] == 2

    update_resp = client.put(
        f"/api/tasks/{task_id}",
        json={"priority": 1},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["task"]["priority"] == 1


## ---- List Tasks ----

def test_list_tasks(client):
    ## should return a list with at least 1 task since we created some above
    response = client.get("/api/tasks")
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert isinstance(data["tasks"], list)
    assert len(data["tasks"]) >= 1


def test_list_tasks_filter_pending(client):
    ## filtering by pending should only return pending tasks
    response = client.get("/api/tasks?status=pending")
    assert response.status_code == 200
    tasks = response.json()["tasks"]
    for task in tasks:
        assert task["status"] == "pending"


def test_list_tasks_filter_invalid(client):
    ## invalid filter should get rejected
    response = client.get("/api/tasks?status=invalid")
    assert response.status_code == 400
    assert "error" in response.json()


## ---- Toggle Task ----

def test_toggle_task(client):
    ## create a task first then toggle it back and forth
    create_resp = client.post("/api/tasks", json={"title": "Toggle me"})
    task_id = create_resp.json()["task"]["id"]
    original_updated = create_resp.json()["task"]["updated_at"]

    ## first toggle: pending → completed
    toggle_resp = client.patch(f"/api/tasks/{task_id}/toggle")
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["task"]["status"] == "completed"
    assert toggle_resp.json()["task"]["updated_at"] != original_updated

    ## second toggle: completed → back to pending
    toggle_resp2 = client.patch(f"/api/tasks/{task_id}/toggle")
    assert toggle_resp2.status_code == 200
    assert toggle_resp2.json()["task"]["status"] == "pending"


def test_toggle_nonexistent(client):
    ## toggling a task that doesn't exist should 404
    response = client.patch("/api/tasks/99999/toggle")
    assert response.status_code == 404


## ---- Update Task ----

def test_update_task(client):
    ## create then update title and description
    create_resp = client.post("/api/tasks", json={"title": "Old title"})
    task_id = create_resp.json()["task"]["id"]
    original_updated = create_resp.json()["task"]["updated_at"]

    update_resp = client.put(
        f"/api/tasks/{task_id}",
        json={"title": "New title", "description": "Added description"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["task"]["title"] == "New title"
    assert update_resp.json()["task"]["description"] == "Added description"
    assert update_resp.json()["task"]["updated_at"] != original_updated


def test_update_task_with_status(client):
    ## should be able to change status via PUT as well
    create_resp = client.post("/api/tasks", json={"title": "Status test"})
    task_id = create_resp.json()["task"]["id"]

    update_resp = client.put(
        f"/api/tasks/{task_id}",
        json={"status": "completed"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["task"]["status"] == "completed"


def test_update_task_invalid_status(client):
    ## invalid status should get rejected
    create_resp = client.post("/api/tasks", json={"title": "Bad status"})
    task_id = create_resp.json()["task"]["id"]

    update_resp = client.put(
        f"/api/tasks/{task_id}",
        json={"status": "invalid"},
    )
    assert update_resp.status_code == 400


def test_update_nonexistent(client):
    ## updating a task that doesn't exist should 404
    response = client.put("/api/tasks/99999", json={"title": "Nope"})
    assert response.status_code == 404


## ---- Delete Task ----

def test_delete_task(client):
    ## create a task, delete it, then verify its actually gone
    create_resp = client.post("/api/tasks", json={"title": "Delete me"})
    task_id = create_resp.json()["task"]["id"]

    delete_resp = client.delete(f"/api/tasks/{task_id}")
    assert delete_resp.status_code == 200
    assert "deleted" in delete_resp.json()["message"].lower()

    ## making sure it's actually removed from the database
    get_resp = client.get("/api/tasks")
    all_ids = []
    for t in get_resp.json()["tasks"]:
        all_ids.append(t["id"])
    assert task_id not in all_ids


def test_delete_nonexistent(client):
    ## deleting a task that doesn't exist should 404
    response = client.delete("/api/tasks/99999")
    assert response.status_code == 404
