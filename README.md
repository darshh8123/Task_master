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


