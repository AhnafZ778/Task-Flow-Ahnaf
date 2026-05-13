## Pydantic schemas for request validation and response serialization
## Validation errors get caught and returned as HTTP 400 instead of FastAPI's
## default 422, that's handled by a custom exception handler in main.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


## Schema for creating a new task
## Title is required, everything else is optional
## Priority defaults to 2 (Medium) if not specified
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int = 2
    deadline: Optional[str] = None

    ## Making sure the title isn't empty or just whitespace
    ## because that would be pretty useless as a task
    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title cannot be empty or whitespace only")
        return stripped

    ## Cleaning up the description, if it's just whitespace treat it as None
    @field_validator("description")
    @classmethod
    def clean_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    ## Priority has to be between 1 and 3 (Low, Medium, Hard)
    @field_validator("priority")
    @classmethod
    def priority_must_be_valid(cls, v: int) -> int:
        if v < 1 or v > 3:
            raise ValueError("Priority must be between 1 and 3")
        return v

    ## Deadline validation, I'm accepting both ISO date (2026-05-13) and
    ## ISO datetime (2026-05-13T17:00) because the frontend can send either
    ## depending on whether the user typed a time keyword or just a date
    @field_validator("deadline")
    @classmethod
    def deadline_must_be_valid_iso(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M"):
                try:
                    datetime.strptime(v, fmt)
                    return v
                except ValueError:
                    continue
            raise ValueError("Deadline must be in ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM")
        return v


## Schema for updating an existing task, all fields are optional here
## because the user might only want to change the title or just the status
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    deadline: Optional[str] = None

    ## Same title validation as TaskCreate but allows None since it's optional
    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Title cannot be empty or whitespace only")
            return stripped
        return v

    ## Same description cleanup
    @field_validator("description")
    @classmethod
    def clean_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    ## Status can only be 'pending' or 'completed', anything else gets rejected
    @field_validator("status")
    @classmethod
    def status_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("pending", "completed"):
            raise ValueError("Status must be 'pending' or 'completed'")
        return v

    ## Priority validation, same range check
    @field_validator("priority")
    @classmethod
    def priority_must_be_valid(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 3):
            raise ValueError("Priority must be between 1 and 3")
        return v

    ## Same deadline format validation as TaskCreate
    @field_validator("deadline")
    @classmethod
    def deadline_must_be_valid_iso(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M"):
                try:
                    datetime.strptime(v, fmt)
                    return v
                except ValueError:
                    continue
            raise ValueError("Deadline must be in ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM")
        return v


