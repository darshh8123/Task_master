"""
Task Master - A simple task management REST API built with Flask + SQLite.

Run with:
    python app.py

The API is served under /api/tasks, and a small HTML/CSS/JS frontend
is served at / for interacting with it in the browser.

Uses Python's built-in sqlite3 module with raw parameterized SQL
(no ORM) to keep the project lightweight and SQL-focused.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, render_template, g

app = Flask(__name__)

DB_PATH = Path(__file__).parent / "tasks.db"


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db():
    """Open (or reuse) a SQLite connection for the current request."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create the tasks table if it doesn't already exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT NOT NULL DEFAULT 'medium'
                    CHECK (priority IN ('low', 'medium', 'high')),
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def row_to_dict(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "priority": row["priority"],
        "completed": bool(row["completed"]),
        "created_at": row["created_at"],
    }


# ---------------------------------------------------------------------------
# Frontend route
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# REST API routes
# ---------------------------------------------------------------------------
@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    """Return all tasks. Optional ?completed=true/false filter."""
    db = get_db()
    completed_param = request.args.get("completed")

    if completed_param is not None:
        is_completed = 1 if completed_param.lower() == "true" else 0
        rows = db.execute(
            "SELECT * FROM tasks WHERE completed = ? ORDER BY created_at DESC",
            (is_completed,),
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()

    return jsonify([row_to_dict(r) for r in rows]), 200


@app.route("/api/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    db = get_db()
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(row_to_dict(row)), 200


@app.route("/api/tasks", methods=["POST"])
def create_task():
    data = request.get_json(silent=True)
    if not data or not data.get("title", "").strip():
        return jsonify({"error": "Title is required"}), 400

    title = data["title"].strip()
    description = data.get("description", "").strip()
    priority = data.get("priority", "medium")
    if priority not in ("low", "medium", "high"):
        priority = "medium"
    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

    db = get_db()
    cursor = db.execute(
        "INSERT INTO tasks (title, description, priority, completed, created_at) "
        "VALUES (?, ?, ?, 0, ?)",
        (title, description, priority, created_at),
    )
    db.commit()

    row = db.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(row_to_dict(row)), 201


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    db = get_db()
    existing = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if existing is None:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json(silent=True) or {}

    title = existing["title"]
    if "title" in data:
        if not data["title"].strip():
            return jsonify({"error": "Title cannot be empty"}), 400
        title = data["title"].strip()

    description = existing["description"]
    if "description" in data:
        description = data["description"].strip()

    priority = existing["priority"]
    if "priority" in data and data["priority"] in ("low", "medium", "high"):
        priority = data["priority"]

    completed = existing["completed"]
    if "completed" in data:
        completed = 1 if bool(data["completed"]) else 0

    db.execute(
        "UPDATE tasks SET title = ?, description = ?, priority = ?, completed = ? "
        "WHERE id = ?",
        (title, description, priority, completed, task_id),
    )
    db.commit()

    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return jsonify(row_to_dict(row)), 200


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    db = get_db()
    existing = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if existing is None:
        return jsonify({"error": "Task not found"}), 404

    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return jsonify({"message": "Task deleted"}), 200


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
