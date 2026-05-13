## Task-Flow — FastAPI application entry point
## this is where everything starts, it initializes the database on startup
## registers the CORS middleware so the frontend can talk to it
## and hooks up all the task routes

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.database import init_db
from app.routes.tasks import router as tasks_router


## lifespan event handler, this runs the DB init when the app first starts up
## so I don't have to manually run any setup scripts
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Task-Flow API",
    description="A simple personal task manager API",
    version="1.0.0",
    lifespan=lifespan,
)

## CORS is set to allow everything because the frontend runs on a different
## port (3000) while the API runs on 8000, without this the browser
## would block all the fetch requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


## FastAPI normally returns 422 for validation errors which is technically
## correct but 400 is more standard and easier for the frontend to handle
## so I'm catching both Pydantic's ValidationError and FastAPI's own
## RequestValidationError and converting them to 400 with a clean message

@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request: Request, exc: ValidationError):
    errors = exc.errors()
    first = errors[0]
    field = " → ".join(str(loc) for loc in first.get("loc", []))
    message = first.get("msg", "Validation error")
    if field:
        detail = f"{field}: {message}"
    else:
        detail = message
    return JSONResponse(status_code=400, content={"error": detail})


@app.exception_handler(RequestValidationError)
async def fastapi_validation_handler(request: Request, exc: RequestValidationError):
    ## same thing but filtering out "body" from the location path
    ## since that part isn't useful info for the frontend
    errors = exc.errors()
    first = errors[0]
    locations = []
    for loc in first.get("loc", []):
        if loc != "body":
            locations.append(str(loc))
    field = " → ".join(locations)
    message = first.get("msg", "Validation error")
    if field:
        detail = f"{field}: {message}"
    else:
        detail = message
    return JSONResponse(status_code=400, content={"error": detail})


## hooking up the task routes
app.include_router(tasks_router)


## simple health check endpoint to verify the API is running
@app.get("/")
def health_check():
    return {"status": "ok", "message": "Task-Flow API is running"}
