"""
Task Master - A simple task management app built with Flask + SQLite.

Run with:
    python app.py

This project has two halves that share the same database:

1. A REST API under /api/tasks (JSON in/out) - this is the piece worth
   putting on a resume as a "Flask REST API" project.
2. A plain server-rendered website (Jinja2 templates + HTML forms) under
   / - no JavaScript at all. Every action (add/complete/delete/filter)
   is a normal form submission or link, and the page reloads with the
   result, the old-school way.

Uses Python's built-in sqlite3 module with raw parameterized SQL
(no ORM) to keep the project lightweight and SQL-focused.
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, render_template, redirect, url_for, g

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
# Website routes (server-rendered, no JavaScript)
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """Show all tasks. Supports ?filter=pending / ?filter=completed."""
    db = get_db()
    task_filter = request.args.get("filter", "all")

    if task_filter == "pending":
        rows = db.execute(
            "SELECT * FROM tasks WHERE completed = 0 ORDER BY created_at DESC"
        ).fetchall()
    elif task_filter == "completed":
        rows = db.execute(
            "SELECT * FROM tasks WHERE completed = 1 ORDER BY created_at DESC"
        ).fetchall()
    else:
        task_filter = "all"
        rows = db.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()

    tasks = [row_to_dict(r) for r in rows]
    total = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    pending = db.execute("SELECT COUNT(*) FROM tasks WHERE completed = 0").fetchone()[0]

    return render_template(
        "index.html",
        tasks=tasks,
        current_filter=task_filter,
        total=total,
        pending=pending,
    )


@app.route("/add", methods=["POST"])
def add_task_form():
    """Handle the 'add task' HTML form (regular POST, page reload)."""
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "medium")
    if priority not in ("low", "medium", "high"):
        priority = "medium"

    if title:
        db = get_db()
        db.execute(
            "INSERT INTO tasks (title, description, priority, completed, created_at) "
            "VALUES (?, ?, ?, 0, ?)",
            (title, description, priority, datetime.utcnow().strftime("%Y-%m-%d %H:%M")),
        )
        db.commit()

    return redirect(url_for("index"))


@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle_task_form(task_id):
    """Flip a task between completed / not completed."""
    db = get_db()
    row = db.execute("SELECT completed FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is not None:
        new_value = 0 if row["completed"] else 1
        db.execute("UPDATE tasks SET completed = ? WHERE id = ?", (new_value, task_id))
        db.commit()

    return redirect(request.referrer or url_for("index"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task_form(task_id):
    """Delete a task via a plain HTML form button."""
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()

    return redirect(request.referrer or url_for("index"))


# ---------------------------------------------------------------------------
# REST API routes (JSON) - this is the part to reference on a resume as
# "Flask REST API with SQLite backend, full CRUD".
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
