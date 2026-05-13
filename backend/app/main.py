from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.database import init_db
from app.routes.tasks import router as tasks_router


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


## Overriding 422 → 400 for cleaner frontend error handling
@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request: Request, exc: ValidationError):
    errors = exc.errors()
    first = errors[0]
    field = " → ".join(str(loc) for loc in first.get("loc", []))
    message = first.get("msg", "Validation error")
    detail = f"{field}: {message}" if field else message
    return JSONResponse(status_code=400, content={"error": detail})


@app.exception_handler(RequestValidationError)
async def fastapi_validation_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first = errors[0]
    field = " → ".join(str(loc) for loc in first.get("loc", []) if loc != "body")
    message = first.get("msg", "Validation error")
    detail = f"{field}: {message}" if field else message
    return JSONResponse(status_code=400, content={"error": detail})


app.include_router(tasks_router)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Task-Flow API is running"}
