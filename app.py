import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

import mysql.connector

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "taskflow-local-secret-key")

# Render can use SQLite.
# Local development continues to use MySQL unless USE_SQLITE=true.
USE_SQLITE = os.environ.get("USE_SQLITE", "false").lower() == "true"
SQLITE_DATABASE = os.environ.get("SQLITE_DATABASE", "/tmp/taskflow.db")


def get_db_connection():
    """Connect to SQLite for the hosted demo or MySQL locally."""

    if USE_SQLITE:
        connection = sqlite3.connect(SQLITE_DATABASE)
        connection.row_factory = sqlite3.Row
        return connection

    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "taskflow")
    )


def initialize_database():
    """Create the SQLite table when running the hosted demo."""

    if USE_SQLITE:
        connection = get_db_connection()

        try:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(100) NOT NULL,
                    description TEXT,
                    priority VARCHAR(20) DEFAULT 'Medium',
                    status VARCHAR(20) DEFAULT 'Pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            connection.commit()
        finally:
            connection.close()


def execute_query(connection, query, values=()):
    """Execute a query using the correct placeholder for the database."""

    if USE_SQLITE:
        query = query.replace("%s", "?")
        return connection.execute(query, values)

    cursor = connection.cursor()
    cursor.execute(query, values)
    return cursor


def get_task_rows(cursor):
    """Return task records as dictionaries for the HTML templates."""

    rows = cursor.fetchall()

    if USE_SQLITE:
        return [dict(row) for row in rows]

    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


@app.route("/")
def home():
    connection = get_db_connection()

    try:
        tasks_cursor = execute_query(
            connection,
            """
            SELECT id, title, description, priority, status, created_at
            FROM tasks
            ORDER BY id DESC
            """
        )
        tasks = get_task_rows(tasks_cursor)

        total_cursor = execute_query(
            connection, "SELECT COUNT(*) FROM tasks"
        )
        total_tasks = total_cursor.fetchone()[0]

        pending_cursor = execute_query(
            connection,
            "SELECT COUNT(*) FROM tasks WHERE status = %s",
            ("Pending",)
        )
        pending_tasks = pending_cursor.fetchone()[0]

        completed_cursor = execute_query(
            connection,
            "SELECT COUNT(*) FROM tasks WHERE status = %s",
            ("Completed",)
        )
        completed_tasks = completed_cursor.fetchone()[0]

        return render_template(
            "index.html",
            tasks=tasks,
            total_tasks=total_tasks,
            pending_tasks=pending_tasks,
            completed_tasks=completed_tasks
        )

    finally:
        connection.close()


@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "Medium").strip()

    if not title:
        flash("Please enter a task title.", "error")
        return redirect(url_for("home"))

    if len(title) > 100:
        flash("Task title must be 100 characters or fewer.", "error")
        return redirect(url_for("home"))

    if priority not in ("Low", "Medium", "High"):
        priority = "Medium"

    connection = get_db_connection()

    try:
        existing_cursor = execute_query(
            connection,
            "SELECT id FROM tasks WHERE LOWER(title) = LOWER(%s)",
            (title,)
        )
        existing_task = existing_cursor.fetchone()

        if existing_task:
            return render_template(
                "confirm_duplicate.html",
                title=title,
                description=description,
                priority=priority
            )

        execute_query(
            connection,
            """
            INSERT INTO tasks (title, description, priority, status)
            VALUES (%s, %s, %s, %s)
            """,
            (title, description, priority, "Pending")
        )

        connection.commit()
        flash("Task added successfully!", "success")

    finally:
        connection.close()

    return redirect(url_for("home"))


@app.route("/add-confirmed", methods=["POST"])
def add_task_confirmed():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "Medium").strip()

    if not title or len(title) > 100:
        flash("Please enter a valid task title.", "error")
        return redirect(url_for("home"))

    if priority not in ("Low", "Medium", "High"):
        priority = "Medium"

    connection = get_db_connection()

    try:
        execute_query(
            connection,
            """
            INSERT INTO tasks (title, description, priority, status)
            VALUES (%s, %s, %s, %s)
            """,
            (title, description, priority, "Pending")
        )

        connection.commit()
        flash("Task added successfully!", "success")

    finally:
        connection.close()

    return redirect(url_for("home"))


@app.route("/complete/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    connection = get_db_connection()

    try:
        execute_query(
            connection,
            "UPDATE tasks SET status = %s WHERE id = %s",
            ("Completed", task_id)
        )
        connection.commit()
        flash("Task marked as completed!", "success")

    finally:
        connection.close()

    return redirect(url_for("home"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    connection = get_db_connection()

    try:
        execute_query(
            connection,
            "DELETE FROM tasks WHERE id = %s",
            (task_id,)
        )
        connection.commit()
        flash("Task deleted successfully!", "success")

    finally:
        connection.close()

    return redirect(url_for("home"))


# Create the SQLite table automatically when the hosted app starts.
initialize_database()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)