# Task-Flow

Task-Flow is a personal task management platform that been developed to be a small full stack task manager for the ACME AI Fellowship assignment.

The aim was to have a simple, functional and easily run locally application. It has a plain front end that communicate with the (backend) data via HTTP API operations, stores data in SQLite, and it is able to handle task CRUD operations.

## Tech Stack

This project comprises two parts: frontend (using JavaScript) and backend (using Python and FastAPI).  
Fronted language(s): HTML, CSS, Vanilla JS 

## Features

View, add, edit, delete and change (toggle) tasks
Search task by the categories: All, Pending and Completed.
There is no need to create a title that is empty.Empty titles don't have to be created either in front-end or behind.
- SQLite database persistence
- Responsive café-style UI
- Extra: Pattern is a priority, a deadline, a simple deadline detection, an upcoming tasks view and a backend test with adding extra priority and deadlines.

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

### Linux / macOS

In the root directory

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Windows PowerShell

In the root directory

```powershell
cd backend
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

If PowerShell doesn't allow for activation script to be run, then run this once in the same terminal, and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```cmd
cd backend
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The compression should be performed by the back end at:

```text
http://localhost:8000
```

## Frontend Setup

Run another terminal.Go back to terminal.

### Linux / macOS

```bash
cd frontend
python3 -m http.server 3000
```

### Windows

```powershell
cd frontend
py -m http.server 3000
```

Then open:

```text
http://localhost:3000
```

## Database Setup

No need for hand setup of the databases.

Utilised to store data for this app is SQLite. The `tasks` table is automatically created on the backend when it is started, if it doesn't exist.

They can be found in the backend/ .env.example:

```env
DATABASE_PATH=./taskflow.db
HOST=0.0.0.0
PORT=8000
```

Task data stored in a SQLite database file that is on the backend.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/tasks` | Get all tasks |
| POST | `/api/tasks` | Create a task |
| PUT | `/api/tasks/{id}` | Update a task |
This operation changes the pending/completed status of a task.When using this operation, a task's ESA is has been toggled between pending and completed statuses.
| DELETE | `/api/tasks/{id}` | Delete a task |

The following are the validation errors: 400, These errors indicate that the task system does not exist: 404, These errors indicate that task system(s) have been created successfully: 201.

## Running Tests

### Linux / macOS

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```

### Windows PowerShell

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m pytest tests/ -v
```

### Windows Command Prompt

```cmd
cd backend
venv\Scripts\activate
python -m pytest tests/ -v
```

## Technical Decisions

I had some preference for FastAPI since I  prefer to work with Python as I have spent my entire academic journey coding in Python and have had little to no exposure to Javascript, which is why I maintained a simple and easy to explain backend. Since it was a small project, I used SQLite as my Database of choice.

Frontend was done using just HTML, CSS and JavaScript. Sticking with smaller frontent frameworks was due to the fact that I didn't need them for the assignment, and I did not want to turn the project into a full stack project which included a front end framework.

## AI Assistance Note

Obtained help from AI when creating this project. My python knowledge is good, I have experience with HTML and CSS since I completed the course on it by the Odin Project, but my JavaScript background and basic experience with frontend is weak. Therefore, I took AI's help primarily for the JavaScript flow logic, DOM manipulation, finishing up the site and validation of the project with the assignment requirements.

However, I have ensured that I know how the codebase works which allowed me to learn a little about JS and also understand a lot of core concepts about Python from scratch again since I have become a little rusty with it.

## Current Limitations

- No authentication
- Since It’s my Finals Week and I have very little time I couldn’t manage to deploy the website
- Potentially would love to scale it into a Habit tracker of sorts which accumulates all the productivity tools I need in one place and will utilize automations and other shenanigans to make this an actual productivity tool that I can potentially use moving forward instead of being a dead project which just sits in my github repository.

