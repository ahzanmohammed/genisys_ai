from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "attendance.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_cursor():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with db_cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfid_uid TEXT UNIQUE NOT NULL,
                roll_no TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS scan_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                device_id TEXT NOT NULL,
                action TEXT CHECK(action IN ('IN', 'OUT')) NOT NULL,
                scanned_at TEXT NOT NULL,
                is_late INTEGER DEFAULT 0,
                FOREIGN KEY(student_id) REFERENCES students(id)
            )
            """
        )


def seed_demo_students() -> None:
    demo = [
        ("A1B2C3D4", "CSE001", "Aarav Menon"),
        ("AA11BB22", "CSE002", "Niharika Das"),
        ("FEED9911", "CSE003", "Rayan Thomas"),
    ]
    with db_cursor() as cur:
        for uid, roll, name in demo:
            cur.execute(
                """
                INSERT INTO students (rfid_uid, roll_no, full_name)
                VALUES (?, ?, ?)
                ON CONFLICT(rfid_uid) DO NOTHING
                """,
                (uid, roll, name),
            )
