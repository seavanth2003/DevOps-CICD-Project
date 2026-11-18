import sys
import sqlite3
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "app"))

import app as employee_app


@pytest.fixture
def client(tmp_path, monkeypatch):

    test_database = tmp_path / "test_employees.db"

    def get_test_connection():
        connection = sqlite3.connect(test_database)
        connection.row_factory = sqlite3.Row
        return connection

    monkeypatch.setattr(
        employee_app,
        "get_db_connection",
        get_test_connection
    )

    employee_app.app.config["TESTING"] = True
    employee_app.app.config["SECRET_KEY"] = "test-secret"

    connection = get_test_connection()

    connection.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            salary REAL NOT NULL
        )
    """)

    connection.commit()
    connection.close()

    return employee_app.app.test_client()


def test_homepage(client):

    response = client.get("/")

    assert response.status_code == 200


def test_health_endpoint(client):

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {"status": "healthy"}


def test_add_employee(client):

    response = client.post("/add", data={
        "name": "Rahul Sharma",
        "email": "rahul@gmail.com",
        "department": "IT",
        "salary": "35000"
    })

    assert response.status_code == 302

    response = client.get("/")

    assert b"Rahul Sharma" in response.data
    assert b"rahul@gmail.com" in response.data


def test_delete_employee(client):

    client.post("/add", data={
        "name": "Priya Reddy",
        "email": "priya@gmail.com",
        "department": "HR",
        "salary": "40000"
    })

    response = client.get("/")

    assert b"Priya Reddy" in response.data

    response = client.get("/delete/1")

    assert response.status_code == 302

    response = client.get("/")

    assert b"Priya Reddy" not in response.data