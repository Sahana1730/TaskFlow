from flask import Flask, render_template, request, redirect
import mysql.connector
import os

app = Flask(__name__)


# Connect to the MySQL database
def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.environ.get("DB_PASSWORD"),
        database="taskflow"
    )
    return connection


# Display all tasks
@app.route("/")
def home():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
    tasks = cursor.fetchall()
    total_tasks = len(tasks)
    pending_tasks = sum(1 for task in tasks if task[4] == "Pending")
    completed_tasks = sum(1 for task in tasks if task[4] == "Completed")

    cursor.close()
    connection.close()

    return render_template(
    "index.html",
    tasks=tasks,
    total_tasks=total_tasks,
    pending_tasks=pending_tasks,
    completed_tasks=completed_tasks
)


# Add a new task and check for duplicate titles
@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "Medium")

    # Validate the task title
    if not title:
        return "Task title cannot be empty.", 400

    if len(title) > 100:
        return "Task title cannot exceed 100 characters.", 400

    if len(description) > 500:
        return "Description cannot exceed 500 characters.", 400

    # Connect to the database
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Check whether a task with the same title already exists
        cursor.execute(
            "SELECT id FROM tasks WHERE LOWER(title) = LOWER(%s)",
            (title,)
        )

        duplicate = cursor.fetchone()

        # If a duplicate exists, ask the user whether to continue
        if duplicate:
            cursor.close()
            connection.close()

            return render_template(
                "confirm_duplicate.html",
                title=title,
                description=description,
                priority=priority
            )

        # Insert the new task
        query = """
            INSERT INTO tasks (title, description, priority, status)
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (title, description, priority, "Pending")
        )

        connection.commit()

    finally:
        if cursor and connection.is_connected():
            cursor.close()

        if connection.is_connected():
            connection.close()

    return redirect("/")


# Add a task even when its title already exists
@app.route("/add-duplicate", methods=["POST"])
def add_duplicate_task():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "Medium")

    if not title:
        return "Task title cannot be empty.", 400

    if len(title) > 100:
        return "Task title cannot exceed 100 characters.", 400

    if len(description) > 500:
        return "Description cannot exceed 500 characters.", 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        query = """
            INSERT INTO tasks (title, description, priority, status)
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (title, description, priority, "Pending")
        )

        connection.commit()

    finally:
        if cursor and connection.is_connected():
            cursor.close()

        if connection.is_connected():
            connection.close()

    return redirect("/")


# Mark a task as completed
@app.route("/complete/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "UPDATE tasks SET status = %s WHERE id = %s",
            ("Completed", task_id)
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()

    return redirect("/")


# Delete a task
@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "DELETE FROM tasks WHERE id = %s",
            (task_id,)
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)