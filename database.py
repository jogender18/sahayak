import sqlite3
import os
from datetime import datetime
import uuid

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sahayak.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agreements (
            id TEXT PRIMARY KEY,
            owner_name TEXT NOT NULL,
            owner_phone TEXT NOT NULL,
            worker_name TEXT NOT NULL,
            worker_phone TEXT NOT NULL,
            work_description TEXT NOT NULL,
            wage_amount REAL NOT NULL,
            wage_unit TEXT NOT NULL,
            payment_schedule TEXT NOT NULL,
            late_penalty TEXT,
            start_date TEXT NOT NULL,
            duration TEXT NOT NULL,
            work_location TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'VERIFIED'
        )
    """)
    conn.commit()
    conn.close()

def create_agreement(data: dict) -> str:
    agreement_id = str(uuid.uuid4())
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO agreements (
            id, owner_name, owner_phone, worker_name, worker_phone,
            work_description, wage_amount, wage_unit, payment_schedule,
            late_penalty, start_date, duration, work_location, created_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        agreement_id,
        data.get("owner_name", "").strip(),
        data.get("owner_phone", "").strip(),
        data.get("worker_name", "").strip(),
        data.get("worker_phone", "").strip(),
        data.get("work_description", "").strip(),
        float(data.get("wage_amount", 0)),
        data.get("wage_unit", "per day").strip(),
        data.get("payment_schedule", "weekly").strip(),
        data.get("late_penalty", "").strip() or "Standard mutual dispute resolution / No additional penalty specified",
        data.get("start_date", "").strip(),
        data.get("duration", "").strip(),
        data.get("work_location", "").strip(),
        created_at,
        "VERIFIED"
    ))
    conn.commit()
    conn.close()
    return agreement_id

def get_agreement(agreement_id: str) -> dict | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agreements WHERE id = ?", (agreement_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def list_recent_agreements(limit: int = 10) -> list[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agreements ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
