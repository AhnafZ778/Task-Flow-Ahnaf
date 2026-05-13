## Task API Routes
## these are all the endpoints the frontend calls to manage tasks
##
## GET    /api/tasks              — list tasks (optional ?status= filter)
## GET    /api/tasks/upcoming     — tasks grouped by deadline date
## POST   /api/tasks              — create a task
## PUT    /api/tasks/{id}         — update a task
## PATCH  /api/tasks/{id}/toggle  — toggle pending/completed
## DELETE /api/tasks/{id}         — delete a task

from typing import Optional
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.schemas import TaskCreate, TaskUpdate
from app import crud

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

## the only valid status filters, anything else gets rejected
VALID_STATUS_FILTERS = {"all", "pending", "completed"}


## returns tasks grouped by their deadline date
## this is what the calendar popup uses to know which dates have tasks
@router.get("/upcoming")
def upcoming_tasks():
    grouped = crud.get_tasks_grouped_by_deadline()
    return {"groups": grouped}


## returns all tasks, can optionally filter by status using ?status=pending etc
## if an invalid status is passed it returns a 400 error
@router.get("")
def list_tasks(status: Optional[str] = Query(default=None)):
    if status is not None:
        if status not in VALID_STATUS_FILTERS:
            return JSONResponse(
                status_code=400,
                content={
                    "error": f"Invalid status filter '{status}'. Must be one of: all, pending, completed"
                },
            )

    tasks = crud.get_all_tasks(status_filter=status)
    return {"tasks": tasks}


## creates a new task, title is required and can't be blank
## everything else is optional, priority defaults to Medium (2)
@router.post("", status_code=201)
def create_task(payload: TaskCreate):
    task = crud.create_task(
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        deadline=payload.deadline,
    )
    return {"task": task}


## updates an existing task, you can change any combination of fields
## only the fields you include in the request body get changed
## returns 404 if the task doesn't exist
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


## toggles a task between pending and completed
## basically just flips the status to the opposite of whatever it is
@router.patch("/{task_id}/toggle")
def toggle_task(task_id: int):
    task = crud.toggle_task_status(task_id)
    if task is None:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return {"task": task}


## permanently deletes a task, no undo
## returns 404 if the task doesn't exist
@router.delete("/{task_id}")
def delete_task(task_id: int):
    deleted = crud.delete_task(task_id)
    if not deleted:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return {"message": "Task deleted successfully"}
