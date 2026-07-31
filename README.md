# Task Master

A simple task management app built with **Flask** + **SQLite** on the backend
and a lightweight **HTML/CSS/JS** frontend. Built as a small, resume-friendly
example of a REST API project.

## Features

- Full REST API for tasks (Create, Read, Update, Delete)
- SQLite database via Flask-SQLAlchemy (no separate DB server needed)
- Filter tasks by completion status
- Priority levels (low / medium / high)
- Simple, responsive UI that talks to the API via `fetch()`

## Project structure

```
task_master/
├── app.py                # Flask app + REST API routes + DB model
├── requirements.txt
├── templates/
│   └── index.html        # Frontend page
└── static/
    ├── style.css          # Styling
    └── script.js          # Frontend logic (calls the API)
```

## Setup

1. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate      # on Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   python app.py
   ```

4. Open your browser at `http://127.0.0.1:5000`

The SQLite database file (`tasks.db`) is created automatically on first run.

## REST API Reference

| Method | Endpoint             | Description                          |
|--------|-----------------------|--------------------------------------|
| GET    | `/api/tasks`           | Get all tasks (optional `?completed=true/false`) |
| GET    | `/api/tasks/<id>`      | Get a single task                    |
| POST   | `/api/tasks`           | Create a new task                    |
| PUT    | `/api/tasks/<id>`      | Update an existing task              |
| DELETE | `/api/tasks/<id>`      | Delete a task                        |

### Example: create a task

```bash
curl -X POST http://127.0.0.1:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Finish resume", "description": "Add this project", "priority": "high"}'
```

### Example: mark a task complete

```bash
curl -X PUT http://127.0.0.1:5000/api/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'
```

### Task object shape

```json
{
  "id": 1,
  "title": "Finish resume",
  "description": "Add this project",
  "priority": "high",
  "completed": false,
  "created_at": "2026-07-29 09:15"
}
```

## Notes / ideas for extending it

- Add user accounts + login (Flask-Login) so each user has their own tasks
- Add due dates and sort/filter by them
- Swap SQLite for PostgreSQL for a "production-style" setup
- Add pagination to the `GET /api/tasks` endpoint
- Write tests with `pytest` + Flask's test client

## For your resume

Something like:

> **Task Master** – Built a full-stack task management app with a Flask REST
> API and SQLite database, supporting full CRUD operations, and a
> vanilla JS/HTML/CSS frontend consuming the API via `fetch`.
