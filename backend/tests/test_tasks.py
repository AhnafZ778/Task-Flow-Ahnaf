import os
import tempfile
import pytest
from fastapi.testclient import TestClient

## Temp DB must be set BEFORE app import
_test_db_fd, _test_db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_PATH"] = _test_db_path

from app.database import init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db(_test_db_path)
    yield
    os.close(_test_db_fd)
    os.unlink(_test_db_path)


@pytest.fixture()
def client():
    return TestClient(app)


def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_task_success(client):
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
    response = client.post("/api/tasks", json={"title": "Walk the dog"})
    assert response.status_code == 201
    assert response.json()["task"]["title"] == "Walk the dog"
    assert response.json()["task"]["description"] is None


def test_create_task_empty_title(client):
    response = client.post("/api/tasks", json={"title": ""})
    assert response.status_code == 400
    assert "error" in response.json()


def test_create_task_whitespace_title(client):
    response = client.post("/api/tasks", json={"title": "   "})
    assert response.status_code == 400
    assert "error" in response.json()


def test_create_task_missing_title(client):
    response = client.post("/api/tasks", json={})
    assert response.status_code == 400


def test_create_task_with_priority(client):
    response = client.post(
        "/api/tasks",
        json={"title": "Urgent fix", "priority": 3},
    )
    assert response.status_code == 201
    assert response.json()["task"]["priority"] == 3


def test_create_task_default_priority(client):
    response = client.post("/api/tasks", json={"title": "Normal task"})
    assert response.status_code == 201
    assert response.json()["task"]["priority"] == 2


def test_create_task_invalid_priority(client):
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
    create_resp = client.post("/api/tasks", json={"title": "Change my priority"})
    task_id = create_resp.json()["task"]["id"]
    assert create_resp.json()["task"]["priority"] == 2

    update_resp = client.put(f"/api/tasks/{task_id}", json={"priority": 1})
    assert update_resp.status_code == 200
    assert update_resp.json()["task"]["priority"] == 1


def test_list_tasks(client):
    response = client.get("/api/tasks")
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert isinstance(data["tasks"], list)
    assert len(data["tasks"]) >= 1


def test_list_tasks_filter_pending(client):
    response = client.get("/api/tasks?status=pending")
    assert response.status_code == 200
    for task in response.json()["tasks"]:
        assert task["status"] == "pending"


def test_list_tasks_filter_invalid(client):
    response = client.get("/api/tasks?status=invalid")
    assert response.status_code == 400
    assert "error" in response.json()


def test_toggle_task(client):
    create_resp = client.post("/api/tasks", json={"title": "Toggle me"})
    task_id = create_resp.json()["task"]["id"]
    original_updated = create_resp.json()["task"]["updated_at"]

    ## pending → completed
    toggle_resp = client.patch(f"/api/tasks/{task_id}/toggle")
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["task"]["status"] == "completed"
    assert toggle_resp.json()["task"]["updated_at"] != original_updated

    ## completed → pending
    toggle_resp2 = client.patch(f"/api/tasks/{task_id}/toggle")
    assert toggle_resp2.status_code == 200
    assert toggle_resp2.json()["task"]["status"] == "pending"


def test_toggle_nonexistent(client):
    response = client.patch("/api/tasks/99999/toggle")
    assert response.status_code == 404


def test_update_task(client):
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
    create_resp = client.post("/api/tasks", json={"title": "Status test"})
    task_id = create_resp.json()["task"]["id"]

    update_resp = client.put(f"/api/tasks/{task_id}", json={"status": "completed"})
    assert update_resp.status_code == 200
    assert update_resp.json()["task"]["status"] == "completed"


def test_update_task_invalid_status(client):
    create_resp = client.post("/api/tasks", json={"title": "Bad status"})
    task_id = create_resp.json()["task"]["id"]

    update_resp = client.put(f"/api/tasks/{task_id}", json={"status": "invalid"})
    assert update_resp.status_code == 400


def test_update_nonexistent(client):
    response = client.put("/api/tasks/99999", json={"title": "Nope"})
    assert response.status_code == 404


def test_delete_task(client):
    create_resp = client.post("/api/tasks", json={"title": "Delete me"})
    task_id = create_resp.json()["task"]["id"]

    delete_resp = client.delete(f"/api/tasks/{task_id}")
    assert delete_resp.status_code == 200
    assert "deleted" in delete_resp.json()["message"].lower()

    ## Verify it's actually gone
    get_resp = client.get("/api/tasks")
    task_ids = [t["id"] for t in get_resp.json()["tasks"]]
    assert task_id not in task_ids


def test_delete_nonexistent(client):
    response = client.delete("/api/tasks/99999")
    assert response.status_code == 404
