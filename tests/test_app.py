import sys
import sqlite3
from pathlib import Path

import pytest
from flask import url_for
from werkzeug.security import generate_password_hash

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "app"))

import app as employee_app  # noqa: E402
import auth as auth_module  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):

    test_database = tmp_path / "test_employees.db"

    def get_test_connection():
        connection = sqlite3.connect(test_database)
        connection.row_factory = sqlite3.Row
        return connection

    # Replace database connections in both modules
    monkeypatch.setattr(
        employee_app,
        "get_db_connection",
        get_test_connection
    )

    monkeypatch.setattr(
        auth_module,
        "get_db_connection",
        get_test_connection
    )

    employee_app.app.config["TESTING"] = True
    employee_app.app.config["SECRET_KEY"] = "test-secret"

    # Create test database tables
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

    connection.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert test user
    connection.execute("""
        INSERT INTO users (name, email, password_hash)
        VALUES (?, ?, ?)
    """, (
        "Test Admin",
        "admin@test.com",
        generate_password_hash("password123")
    ))

    connection.commit()
    connection.close()

    test_client = employee_app.app.test_client()

    # Log in the test client
    with test_client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Test Admin"
        session["user_email"] = "admin@test.com"

    return test_client


def get_route(endpoint, **kwargs):

    with employee_app.app.test_request_context():
        return url_for(endpoint, **kwargs)


# --------------------------------
# APPLICATION TESTS
# --------------------------------

def test_homepage(client):

    response = client.get("/")

    assert response.status_code == 200
    assert b"Dashboard Overview" in response.data


def test_login_page(client):

    response = client.get("/login")

    assert response.status_code == 200


def test_unauthorized_dashboard_access():

    client = employee_app.app.test_client()

    response = client.get("/")

    assert response.status_code == 302
    assert "/login" in response.location


# --------------------------------
# HEALTH CHECK TEST
# --------------------------------

def test_health_endpoint(client):

    response = client.get("/health")

    assert response.status_code == 200
    assert response.is_json
    assert response.json["status"] == "healthy"


# --------------------------------
# EMPLOYEE TESTS
# --------------------------------

def test_add_employee(client):

    response = client.post(
        get_route("add_employee"),
        data={
            "name": "Rahul Sharma",
            "email": "rahul@gmail.com",
            "department": "IT",
            "salary": "35000"
        }
    )

    assert response.status_code == 302

    response = client.get("/")

    assert response.status_code == 200
    assert b"Rahul Sharma" in response.data
    assert b"rahul@gmail.com" in response.data


def test_edit_employee(client):

    client.post(
        get_route("add_employee"),
        data={
            "name": "Priya Reddy",
            "email": "priya@gmail.com",
            "department": "HR",
            "salary": "40000"
        }
    )

    response = client.post(
        get_route("edit_employee", employee_id=1),
        data={
            "name": "Priya Sharma",
            "email": "priya@gmail.com",
            "department": "Finance",
            "salary": "45000"
        }
    )

    assert response.status_code == 302

    response = client.get("/")

    assert b"Priya Sharma" in response.data
    assert b"Finance" in response.data


def test_delete_employee(client):

    client.post(
        get_route("add_employee"),
        data={
            "name": "Kiran Rao",
            "email": "kiran@gmail.com",
            "department": "IT",
            "salary": "30000"
        }
    )

    response = client.post(
        get_route("delete_employee", employee_id=1)
    )

    assert response.status_code == 302

    response = client.get("/")

    assert b"Kiran Rao" not in response.data


# --------------------------------
# DASHBOARD ANALYTICS TESTS
# --------------------------------

def test_total_employees(client):

    client.post(
        get_route("add_employee"),
        data={
            "name": "Employee One",
            "email": "one@gmail.com",
            "department": "IT",
            "salary": "30000"
        }
    )

    response = client.get("/")

    assert b"Employee One" in response.data
    assert b"Total Employees" in response.data


def test_department_analytics(client):

    client.post(
        get_route("add_employee"),
        data={
            "name": "Employee One",
            "email": "one@gmail.com",
            "department": "IT",
            "salary": "30000"
        }
    )

    client.post(
        get_route("add_employee"),
        data={
            "name": "Employee Two",
            "email": "two@gmail.com",
            "department": "HR",
            "salary": "40000"
        }
    )

    response = client.get("/")

    assert response.status_code == 200
    assert b"Department Distribution" in response.data
    assert b"IT" in response.data
    assert b"HR" in response.data


def test_monthly_payroll(client):

    client.post(
        get_route("add_employee"),
        data={
            "name": "Employee One",
            "email": "one@gmail.com",
            "department": "IT",
            "salary": "30000"
        }
    )

    client.post(
        get_route("add_employee"),
        data={
            "name": "Employee Two",
            "email": "two@gmail.com",
            "department": "HR",
            "salary": "40000"
        }
    )

    response = client.get("/")

    assert response.status_code == 200
    assert b"Monthly Payroll" in response.data
    assert b"70000.00" in response.data


# --------------------------------
# AUTHENTICATION TESTS
# --------------------------------

def test_invalid_login(client):

    with client.session_transaction() as session:
        session.clear()

    response = client.post(
        "/login",
        data={
            "email": "wrong@gmail.com",
            "password": "wrongpassword"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_logout(client):

    response = client.get("/logout")

    assert response.status_code == 302

    response = client.get("/")

    assert response.status_code == 302
