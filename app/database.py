import sqlite3
import os
from pathlib import Path

DATABASE = Path(
    os.environ.get(
        "DATABASE_PATH",
        str(Path(__file__).resolve().parent / "employees.db")
    )
)


def get_db_connection():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    return connection


def init_db():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            salary REAL NOT NULL
        )
    """)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")