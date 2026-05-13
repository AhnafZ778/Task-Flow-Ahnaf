## Pydantic schemas for request validation and response serialization
## basically these define what the API expects when you create or update a task
## if any of the validation fails it gets caught by a custom exception handler
## in main.py and returned as a 400 error instead of FastAPI's default 422

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


## Schema for creating a new task
## title is required, everything else is optional
## priority defaults to 2 (Medium) if not specified
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int = 2
    deadline: Optional[str] = None

    ## making sure the title isn't empty or just whitespace
    ## because that would be pretty useless as a task
    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, title):
        stripped = title.strip()
        if len(stripped) == 0:
            raise ValueError("Title cannot be empty or whitespace only")
        return stripped

    ## cleaning up the description, if its just whitespace treat it as None
    @field_validator("description")
    @classmethod
    def clean_description(cls, description):
        if description is not None:
            description = description.strip()
            if description == "":
                return None
        return description

    ## priority has to be between 1 and 3 (Low, Medium, Hard)
    @field_validator("priority")
    @classmethod
    def priority_must_be_valid(cls, priority):
        if priority < 1 or priority > 3:
            raise ValueError("Priority must be between 1 and 3")
        return priority

    ## deadline validation, I'm accepting both ISO date (2026-05-13) and
    ## ISO datetime (2026-05-13T17:00) because the frontend can send either
    ## depending on whether the user typed a time keyword or just a date
    @field_validator("deadline")
    @classmethod
    def deadline_must_be_valid_iso(cls, deadline):
        if deadline is not None:
            deadline = deadline.strip()
            if deadline == "":
                return None
            valid = False
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M"):
                try:
                    datetime.strptime(deadline, fmt)
                    valid = True
                    break
                except ValueError:
                    continue
            if valid == False:
                raise ValueError("Deadline must be in ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM")
        return deadline


## Schema for updating an existing task, all fields are optional here
## because the user might only want to change the title or just the status
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    deadline: Optional[str] = None

    ## same title validation as TaskCreate but allows None since its optional
    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, title):
        if title is not None:
            stripped = title.strip()
            if len(stripped) == 0:
                raise ValueError("Title cannot be empty or whitespace only")
            return stripped
        return title

    ## same description cleanup
    @field_validator("description")
    @classmethod
    def clean_description(cls, description):
        if description is not None:
            description = description.strip()
            if description == "":
                return None
        return description

    ## status can only be 'pending' or 'completed', anything else gets rejected
    @field_validator("status")
    @classmethod
    def status_must_be_valid(cls, status):
        if status is not None:
            if status not in ("pending", "completed"):
                raise ValueError("Status must be 'pending' or 'completed'")
        return status

    ## priority validation, same range check as TaskCreate
    @field_validator("priority")
    @classmethod
    def priority_must_be_valid(cls, priority):
        if priority is not None:
            if priority < 1 or priority > 3:
                raise ValueError("Priority must be between 1 and 3")
        return priority

    ## same deadline format validation as TaskCreate
    @field_validator("deadline")
    @classmethod
    def deadline_must_be_valid_iso(cls, deadline):
        if deadline is not None:
            deadline = deadline.strip()
            if deadline == "":
                return None
            valid = False
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M"):
                try:
                    datetime.strptime(deadline, fmt)
                    valid = True
                    break
                except ValueError:
                    continue
            if valid == False:
                raise ValueError("Deadline must be in ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM")
        return deadline
