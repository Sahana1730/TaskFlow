import mysql.connector
import os

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.environ.get("DB_PASSWORD"),
    database="taskflow"
)

cursor = connection.cursor()

cursor.execute("SELECT * FROM tasks")

tasks = cursor.fetchall()

for task in tasks:
    print(task)

cursor.close()
connection.close()