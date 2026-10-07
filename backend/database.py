"""
database.py
-----------
Lightweight SQLite persistence layer (SRS Section 7.2 Data Requirements).
No ORM dependency required -> keeps the project easy to run for grading.
"""

import sqlite3
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "ifrdss.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            annotated_filename TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            person_count INTEGER NOT NULL,
            flood_ratio REAL NOT NULL,
            damage_score REAL NOT NULL,
            damage_flag INTEGER NOT NULL,
            rescue_priority REAL NOT NULL,
            risk_level TEXT NOT NULL,
            suggested_response TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def insert_submission(data: dict) -> int:
    conn = get_connection()
    cur = conn.execute(
        """
        INSERT INTO submissions
            (filename, annotated_filename, timestamp, person_count, flood_ratio,
             damage_score, damage_flag, rescue_priority, risk_level, suggested_response)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["filename"],
            data["annotated_filename"],
            datetime.datetime.utcnow().isoformat(),
            data["person_count"],
            data["flood_ratio"],
            data["damage_score"],
            int(data["damage_flag"]),
            data["rescue_priority"],
            data["risk_level"],
            data["suggested_response"],
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def get_all_submissions(sort_by="timestamp", order="desc"):
    allowed_sort = {"timestamp", "rescue_priority", "risk_level", "person_count"}
    if sort_by not in allowed_sort:
        sort_by = "timestamp"
    order = "DESC" if order.lower() == "desc" else "ASC"

    conn = get_connection()
    rows = conn.execute(
        f"SELECT * FROM submissions ORDER BY {sort_by} {order}"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_submission(submission_id: int):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM submissions WHERE id = ?", (submission_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None
