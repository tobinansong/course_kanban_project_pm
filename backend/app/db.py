from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import os
import sqlite3
from typing import Iterator

DEFAULT_USER_ID = "user-1"
DEFAULT_BOARD_ID = "board-1"

DB_PATH = os.getenv(
    "PM_DB_PATH",
    str(Path(__file__).resolve().parent / "data" / "pm.db"),
)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS boards (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  title TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS columns (
  id TEXT PRIMARY KEY,
  board_id TEXT NOT NULL,
  title TEXT NOT NULL,
  position INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_columns_board_position
  ON columns(board_id, position);

CREATE TABLE IF NOT EXISTS cards (
  id TEXT PRIMARY KEY,
  column_id TEXT NOT NULL,
  title TEXT NOT NULL,
  details TEXT NOT NULL,
  position INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (column_id) REFERENCES columns(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_cards_column_position
  ON cards(column_id, position);
"""


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class SeedColumn:
    id: str
    title: str
    position: int


@dataclass(frozen=True)
class SeedCard:
    id: str
    column_id: str
    title: str
    details: str
    position: int


SEED_COLUMNS = [
    SeedColumn("col-backlog", "Backlog", 0),
    SeedColumn("col-discovery", "Discovery", 1),
    SeedColumn("col-progress", "In Progress", 2),
    SeedColumn("col-review", "Review", 3),
    SeedColumn("col-done", "Done", 4),
]

SEED_CARDS = [
    SeedCard(
        "card-1",
        "col-backlog",
        "Align roadmap themes",
        "Draft quarterly themes with impact statements and metrics.",
        0,
    ),
    SeedCard(
        "card-2",
        "col-backlog",
        "Gather customer signals",
        "Review support tags, sales notes, and churn feedback.",
        1,
    ),
    SeedCard(
        "card-3",
        "col-discovery",
        "Prototype analytics view",
        "Sketch initial dashboard layout and key drill-downs.",
        0,
    ),
    SeedCard(
        "card-4",
        "col-progress",
        "Refine status language",
        "Standardize column labels and tone across the board.",
        0,
    ),
]


def init_db() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.executescript(SCHEMA_SQL)
        cursor = conn.execute("SELECT COUNT(*) AS count FROM users")
        existing = cursor.fetchone()
        if existing and existing["count"] > 0:
            return

        timestamp = now_iso()
        conn.execute(
            "INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (DEFAULT_USER_ID, "user", "demo-only", timestamp),
        )
        conn.execute(
            "INSERT INTO boards (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (DEFAULT_BOARD_ID, DEFAULT_USER_ID, "Kanban Studio", timestamp, timestamp),
        )
        conn.executemany(
            "INSERT INTO columns (id, board_id, title, position, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    column.id,
                    DEFAULT_BOARD_ID,
                    column.title,
                    column.position,
                    timestamp,
                    timestamp,
                )
                for column in SEED_COLUMNS
            ],
        )
        conn.executemany(
            "INSERT INTO cards (id, column_id, title, details, position, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    card.id,
                    card.column_id,
                    card.title,
                    card.details,
                    card.position,
                    timestamp,
                    timestamp,
                )
                for card in SEED_CARDS
            ],
        )
        conn.commit()
