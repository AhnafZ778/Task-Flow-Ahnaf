# Task-Flow

Task-Flow is a small full-stack personal task manager built for the ACME AI Fellowship technical assignment.

The goal was to keep the app simple, functional, and easy to run locally. It supports normal task CRUD operations, stores data in SQLite, and uses a plain frontend that talks to the backend through HTTP API calls.

## Tech Stack

**Backend:** Python, FastAPI, SQLite  
**Frontend:** HTML, CSS, Vanilla JavaScript  
**Testing:** Pytest, FastAPI TestClient

## Features

- View all tasks
- Add a task with title and optional description
- Edit task title/description
- Mark tasks as pending or completed
- Delete tasks with confirmation
- Filter tasks by All, Pending, and Completed
- Frontend and backend validation for empty titles
- SQLite database persistence
- Responsive café-style UI

Extra features added after the required ones were working:

- Priority field
- Deadline field
- Simple natural-language deadline detection, for example `tomorrow at 6am`
- Upcoming tasks calendar view
- Backend test suite

## Project Structure

```text
task-flow/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── schemas.py
│   │   ├── crud.py
│   │   └── routes/tasks.py
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── icons/
└── README.md
```

## Prerequisites

- Python 3.10 or newer
- pip
- A modern browser

## Backend Setup

From the project root:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The backend will run at:

```text
http://localhost:8000
```

## Frontend Setup

Open a second terminal:

```bash
cd frontend
python3 -m http.server 3000
```

Then open:

```text
http://localhost:3000
```

## Database Setup

No manual database setup is needed.

The app uses SQLite. When the backend starts, it creates the `tasks` table automatically if it does not already exist.

The database path can be configured through `backend/.env.example`:

```env
DATABASE_PATH=./taskflow.db
HOST=0.0.0.0
PORT=8000
```

Task data is stored in the backend SQLite database file, not in browser `localStorage` or hardcoded JavaScript arrays.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/tasks` | Get all tasks |
| POST | `/api/tasks` | Create a task |
| PUT | `/api/tasks/{id}` | Update a task |
| PATCH | `/api/tasks/{id}/toggle` | Toggle pending/completed |
| DELETE | `/api/tasks/{id}` | Delete a task |

Validation errors return `400`, missing tasks return `404`, and successful task creation returns `201`.

## Running Tests

From the `backend` folder:

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

## Technical Decisions

I chose FastAPI because I am more comfortable with Python than with JavaScript frameworks, and it allowed me to keep the backend clear and explainable. I used raw SQLite instead of an ORM because the project is small and the database logic is easier to follow this way.

The frontend is plain HTML, CSS, and JavaScript. I avoided React or other frameworks because the assignment did not require them, and I wanted the app to stay simple.

## AI Assistance Note

I used AI assistance while building this project. My Python fundamentals are stronger, and I have some basic HTML/CSS experience, but my JavaScript basics and frontend fundamentals are still weak. Because of that, I used AI mainly to help with the JavaScript flow, DOM handling, frontend polish, and reviewing whether the project matched the assignment requirements.

I have gone through the code, tested the main flows, and made sure I understand how the backend, database, API routes, and frontend connect together.

## Current Limitations

- No authentication, since the assignment is for a single-user task manager
- No deployment link included
- The date parser is a small helper feature, not a full natural-language engine