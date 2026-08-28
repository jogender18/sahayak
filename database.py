import os
import uuid
from datetime import datetime

# ── Backend selection ─────────────────────────────────────────────────────────
# On Render: DATABASE_URL is set automatically by the linked PostgreSQL service.
# Locally:   DATABASE_URL is unset → falls back to SQLite (sahayak.db).
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Render's PostgreSQL connection strings start with "postgres://"; psycopg2
# requires "postgresql://" — normalise it here.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

USE_POSTGRES = bool(DATABASE_URL)

# ── SQLite path (local dev only) ──────────────────────────────────────────────
_data_dir = os.path.dirname(os.path.abspath(__file__))
SQLITE_PATH = os.path.join(_data_dir, "sahayak.db")

# ── Schema (same for both backends) ──────────────────────────────────────────
_CREATE_TABLE = """
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
"""

# ── Connection helpers ────────────────────────────────────────────────────────

def _get_pg_conn():
    import psycopg2
    import psycopg2.extras
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def _get_sqlite_conn():
    import sqlite3
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _get_conn():
    if USE_POSTGRES:
        return _get_pg_conn()
    return _get_sqlite_conn()

def _row_to_dict(row, cursor=None):
    """Convert a DB row to a plain dict regardless of backend."""
    if USE_POSTGRES:
        cols = [d[0] for d in cursor.description]
        return dict(zip(cols, row))
    return dict(row)

# ── Public API ────────────────────────────────────────────────────────────────

def init_db():
    """Create the agreements table if it doesn't exist."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(_CREATE_TABLE)
    conn.commit()
    cur.close()
    conn.close()


def create_agreement(data: dict) -> str:
    """Insert a new agreement and return its UUID."""
    agreement_id = str(uuid.uuid4())
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    late_penalty = (
        data.get("late_penalty", "").strip()
        or "Standard mutual dispute resolution / No additional penalty specified"
    )

    values = (
        agreement_id,
        data.get("owner_name", "").strip(),
        data.get("owner_phone", "").strip(),
        data.get("worker_name", "").strip(),
        data.get("worker_phone", "").strip(),
        data.get("work_description", "").strip(),
        float(data.get("wage_amount", 0)),
        data.get("wage_unit", "per day").strip(),
        data.get("payment_schedule", "weekly").strip(),
        late_penalty,
        data.get("start_date", "").strip(),
        data.get("duration", "").strip(),
        data.get("work_location", "").strip(),
        created_at,
        "VERIFIED",
    )

    if USE_POSTGRES:
        sql = """
            INSERT INTO agreements (
                id, owner_name, owner_phone, worker_name, worker_phone,
                work_description, wage_amount, wage_unit, payment_schedule,
                late_penalty, start_date, duration, work_location, created_at, status
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
    else:
        sql = """
            INSERT INTO agreements (
                id, owner_name, owner_phone, worker_name, worker_phone,
                work_description, wage_amount, wage_unit, payment_schedule,
                late_penalty, start_date, duration, work_location, created_at, status
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(sql, values)
    conn.commit()
    cur.close()
    conn.close()
    return agreement_id


def get_agreement(agreement_id: str) -> dict | None:
    """Fetch a single agreement by its UUID."""
    if USE_POSTGRES:
        sql = "SELECT * FROM agreements WHERE id = %s"
    else:
        sql = "SELECT * FROM agreements WHERE id = ?"

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(sql, (agreement_id,))
    row = cur.fetchone()
    result = _row_to_dict(row, cur) if row else None
    cur.close()
    conn.close()
    return result


def list_recent_agreements(limit: int = 10) -> list[dict]:
    """Return the most recent agreements, newest first."""
    if USE_POSTGRES:
        sql = "SELECT * FROM agreements ORDER BY created_at DESC LIMIT %s"
    else:
        sql = "SELECT * FROM agreements ORDER BY created_at DESC LIMIT ?"

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(sql, (limit,))
    rows = cur.fetchall()
    result = [_row_to_dict(r, cur) for r in rows]
    cur.close()
    conn.close()
    return result
