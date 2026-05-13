# Task-Flow

A clean, full-stack personal task manager built as a technical assignment. The app supports full CRUD operations on tasks with a FastAPI backend, SQLite database, and a vanilla HTML/CSS/JavaScript frontend.

## Tech Stack

| Layer    | Technology                     |
|----------|--------------------------------|
| Backend  | Python 3.10+, FastAPI, Uvicorn |
| Database | SQLite (file-based, local)     |
| Frontend | HTML5, CSS3, Vanilla JavaScript|
| Testing  | pytest, FastAPI TestClient     |

## Features

- **View** all tasks in a clean list UI
- **Add** a task with title (required) and optional description
- **Edit** title and description inline
- **Toggle** task status between pending and completed
- **Delete** task with confirmation dialog
- **Filter** tasks by All, Pending, or Completed
- **Validation** — empty/whitespace-only titles rejected on both frontend and backend
- **Persistent storage** — SQLite database, auto-created on startup
- **Mobile responsive** — works on any screen size
- **Completed task styling** — strikethrough, muted color, status badge

## Folder Structure

```
task-flow/
├── backend/
│   ├── app/
│   │   ├── __init__.py        # Package marker
│   │   ├── main.py            # FastAPI app, CORS, lifespan, health route
│   │   ├── database.py        # SQLite connection, table creation
│   │   ├── schemas.py         # Pydantic request/response models
│   │   ├── crud.py            # Database operations (SELECT, INSERT, UPDATE, DELETE)
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── tasks.py       # API endpoint handlers
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_tasks.py      # Automated tests
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Environment variable template
├── frontend/
│   ├── index.html             # Main page
│   ├── styles.css             # Custom styles
│   └── app.js                 # Application logic
└── README.md                  # This file
```

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- A modern web browser
- No external database service needed — SQLite is built into Python

## Backend Setup

```bash
# Navigate to backend directory
cd task-flow/backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# (Optional) Copy and configure environment
cp .env.example .env

# Start the server
uvicorn app.main:app --reload --port 8000
```

The database file (`taskflow.db`) is created automatically on first startup. No manual migration or seeding needed.

## Frontend Setup

In a separate terminal:

```bash
cd task-flow/frontend
python3 -m http.server 3000
```

Open **http://localhost:3000** in your browser.

> The frontend expects the backend API at `http://localhost:8000`. If you change the backend port, update `API_BASE` in `frontend/app.js`.

## API Endpoints

| Method | Endpoint                | Description              | Success | Error Codes |
|--------|-------------------------|--------------------------|---------|-------------|
| GET    | `/`                     | Health check             | 200     | —           |
| GET    | `/api/tasks`            | List all tasks           | 200     | 400 (bad filter) |
| GET    | `/api/tasks?status=X`   | Filter by pending/completed/all | 200 | 400       |
| POST   | `/api/tasks`            | Create a task            | 201     | 400         |
| PUT    | `/api/tasks/{id}`       | Update task (title, description, status) | 200 | 400, 404 |
| PATCH  | `/api/tasks/{id}/toggle`| Toggle pending/completed | 200     | 404         |
| DELETE | `/api/tasks/{id}`       | Delete a task            | 200     | 404         |

### Request/Response Examples

**Create a task:**
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy groceries", "description": "Milk, eggs, bread"}'
```
```json
{
  "task": {
    "id": 1,
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "status": "pending",
    "created_at": "2025-01-01 12:00:00",
    "updated_at": "2025-01-01 12:00:00"
  }
}
```

**Validation error (empty title):**
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": ""}'
```
```json
{"error": "title: Value error, Title cannot be empty or whitespace only"}
```
Status: `400 Bad Request`

## Running Tests

```bash
cd task-flow/backend
source venv/bin/activate

pytest tests/ -v
```

Tests use an isolated temporary database file — your development database is not touched.

## Technical Decisions

1. **Plain sqlite3 over SQLAlchemy** — The app has a single table with straightforward queries. Using raw `sqlite3` with parameterized queries keeps the codebase simple and easy to explain without ORM abstraction overhead.

2. **DATABASE_PATH over DATABASE_URL** — Since we only use SQLite (a file path), a simple path variable is cleaner than a connection URL that would need parsing.

3. **Pydantic validation → 400 (not 422)** — FastAPI defaults to HTTP 422 for validation errors. Custom exception handlers override this to return 400, which is more conventional for "bad user input."

4. **updated_at refreshed on every mutation** — Both edits and toggles update the `updated_at` timestamp to accurately reflect when the task was last modified.

5. **Vanilla frontend** — No React, Vue, or build tools. The app is a single HTML page with plain CSS and JavaScript, runnable with any static file server.

6. **Inline editing** — Tasks are edited in-place by replacing the content area with input fields, rather than opening a separate modal. This keeps the interaction lightweight.

7. **No authentication** — The assignment calls for a personal task manager. Auth would add complexity without value for a single-user local app.

## AI Assistance Disclosure

AI assistance (Claude) was used for planning, code generation, and debugging support during this project. All generated code was reviewed, understood, and validated by the developer. The architectural decisions, project structure, and implementation logic reflect the developer's own understanding and judgment.
# Task-Flow-Ahnaf
