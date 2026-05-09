"""
core/db.py — Centralised SQLite helper.
Fixes:
  - WAL journal mode (concurrent reads + 1 writer, no blocking)
  - Exponential-backoff retry on OperationalError ("database is locked")
  - Schema-version table + incremental migrations (no silent column drift)
  - check_same_thread=False for multi-threaded FastAPI usage
"""
from __future__ import annotations

import sqlite3
import time
import logging
from contextlib import contextmanager
from typing import Generator

from core.config import DB_PATH

log = logging.getLogger("mahoraga.db")

# ── Schema versions ────────────────────────────────────────────────────────────
# Add new entries here; run() will apply them in order on startup.
_MIGRATIONS: list[tuple[int, str]] = [
    (1, """
        CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            timestamp TEXT,
            source TEXT,
            target_node TEXT,
            action TEXT,
            outcome TEXT,
            severity TEXT,
            risk_delta REAL,
            details TEXT
        );
        CREATE TABLE IF NOT EXISTS attack_patterns (
            id TEXT PRIMARY KEY,
            action TEXT,
            target_node TEXT,
            vuln_class TEXT,
            breach_success INTEGER,
            timestamp TEXT,
            attempts INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS patch_records (
            id TEXT PRIMARY KEY,
            vuln_class TEXT,
            patch_action TEXT,
            target_node TEXT,
            applied_at TEXT,
            effectiveness_score REAL DEFAULT 1.0,
            held INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS reward_log (
            episode INTEGER PRIMARY KEY,
            reward REAL,
            ts TEXT
        );
        CREATE TABLE IF NOT EXISTS triggered_keys (
            key TEXT PRIMARY KEY
        );
        CREATE TABLE IF NOT EXISTS node_patch_state (
            node_name TEXT,
            vuln_class TEXT,
            PRIMARY KEY (node_name, vuln_class)
        );
    """),
    # Future migrations: (2, "ALTER TABLE events ADD COLUMN foo TEXT DEFAULT ''"),
]

_CURRENT_VERSION = _MIGRATIONS[-1][0]


@contextmanager
def _connect() -> Generator[sqlite3.Connection, None, None]:
    """Open a connection with WAL mode and thread-safety."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute(sql: str, params: tuple = (), retries: int = 3) -> list:
    """
    Execute a single SQL statement with exponential-backoff retry.
    Returns fetchall() result for SELECT; empty list for write statements.
    """
    delay = 0.05
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            with _connect() as conn:
                cur = conn.execute(sql, params)
                return cur.fetchall()
        except sqlite3.OperationalError as exc:
            last_exc = exc
            if "locked" in str(exc).lower() and attempt < retries - 1:
                log.warning("DB locked (attempt %d/%d) — retrying in %.0fms", attempt + 1, retries, delay * 1000)
                time.sleep(delay)
                delay *= 2
            else:
                raise
    raise last_exc  # type: ignore[misc]


def executemany(sql: str, param_list: list[tuple], retries: int = 3) -> None:
    delay = 0.05
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            with _connect() as conn:
                conn.executemany(sql, param_list)
            return
        except sqlite3.OperationalError as exc:
            last_exc = exc
            if "locked" in str(exc).lower() and attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                raise
    raise last_exc  # type: ignore[misc]


def run_migrations() -> None:
    """Apply all pending schema migrations on startup."""
    import os
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with _connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)")
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        current = row[0] or 0

    for version, sql in _MIGRATIONS:
        if version > current:
            log.info("Applying DB migration v%d", version)
            with _connect() as conn:
                conn.executescript(sql)
                conn.execute("INSERT OR REPLACE INTO schema_version VALUES (?)", (version,))
            log.info("Migration v%d applied", version)
