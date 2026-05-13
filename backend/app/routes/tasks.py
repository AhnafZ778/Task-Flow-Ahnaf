from typing import Optional
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.schemas import TaskCreate, TaskUpdate
from app import crud

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

VALID_STATUS_FILTERS = {"all", "pending", "completed"}


@router.get("/upcoming")
def upcoming_tasks():
    grouped = crud.get_tasks_grouped_by_deadline()
    return {"groups": grouped}


@router.get("")
def list_tasks(status: Optional[str] = Query(default=None)):
    if status is not None and status not in VALID_STATUS_FILTERS:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Invalid status filter '{status}'. Must be one of: all, pending, completed"
            },
        )

    tasks = crud.get_all_tasks(status_filter=status)
    return {"tasks": tasks}


@router.post("", status_code=201)
def create_task(payload: TaskCreate):
    task = crud.create_task(
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        deadline=payload.deadline,
    )
    return {"task": task}


@router.put("/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    task = crud.update_task(
        task_id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        deadline=payload.deadline,
    )
    if task is None:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return {"task": task}


@router.patch("/{task_id}/toggle")
def toggle_task(task_id: int):
    task = crud.toggle_task_status(task_id)
    if task is None:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return {"task": task}


@router.delete("/{task_id}")
def delete_task(task_id: int):
    deleted = crud.delete_task(task_id)
    if not deleted:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return {"message": "Task deleted successfully"}
