from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
import os

app = FastAPI()

# Define MySQL database configuration
db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "Aman@14Mishra"),
    "database": os.getenv("DB_NAME", "procore_db")
}

def connect_db():
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail="Database connection error")

@app.on_event("startup")
def init_db():
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL
        )
    """)
    db.commit()
    cursor.close()
    db.close()

class Project(BaseModel):
    id: int
    name: str
    status: str

@app.post("/import_project")
def import_project(project: Project):
    db = connect_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            INSERT INTO projects (id, name, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE name = %s, status = %s
        """, (project.id, project.name, project.status, project.name, project.status))
        db.commit()
    except mysql.connector.Error:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to import project")
    finally:
        cursor.close()
        db.close()

    return {"message": "Project imported successfully", "project": project}

@app.get("/get_project/{project_id}")
def get_project(project_id: int):
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
    project = cursor.fetchone()
    cursor.close()
    db.close()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.get("/")
def health_check():
    return {"message": "API is running!"}
