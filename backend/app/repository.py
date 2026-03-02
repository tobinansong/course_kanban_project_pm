from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import uuid

from .db import DEFAULT_BOARD_ID, get_db, now_iso


@dataclass
class CardRecord:
    id: str
    title: str
    details: str


@dataclass
class ColumnRecord:
    id: str
    title: str
    card_ids: List[str]


@dataclass
class BoardRecord:
    columns: List[ColumnRecord]
    cards: Dict[str, CardRecord]


class BoardNotFoundError(RuntimeError):
    pass


class ColumnNotFoundError(RuntimeError):
    pass


class CardNotFoundError(RuntimeError):
    pass


def fetch_board() -> BoardRecord:
    with get_db() as conn:
        board = conn.execute(
            "SELECT id FROM boards WHERE id = ?",
            (DEFAULT_BOARD_ID,),
        ).fetchone()
        if not board:
            raise BoardNotFoundError("Board not found")

        column_rows = conn.execute(
            "SELECT id, title FROM columns WHERE board_id = ? ORDER BY position",
            (DEFAULT_BOARD_ID,),
        ).fetchall()
        columns = [
            ColumnRecord(id=row["id"], title=row["title"], card_ids=[])
            for row in column_rows
        ]

        cards: Dict[str, CardRecord] = {}
        if not columns:
            return BoardRecord(columns=columns, cards=cards)

        column_ids = [column.id for column in columns]
        placeholders = ",".join("?" for _ in column_ids)
        card_rows = conn.execute(
            f"SELECT id, column_id, title, details FROM cards WHERE column_id IN ({placeholders}) ORDER BY column_id, position",
            column_ids,
        ).fetchall()

        column_map = {column.id: column for column in columns}
        for row in card_rows:
            card_id = row["id"]
            cards[card_id] = CardRecord(
                id=card_id, title=row["title"], details=row["details"]
            )
            column_map[row["column_id"]].card_ids.append(card_id)

        return BoardRecord(columns=columns, cards=cards)


def rename_column(column_id: str, title: str) -> None:
    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE columns SET title = ?, updated_at = ? WHERE id = ?",
            (title, now_iso(), column_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise ColumnNotFoundError("Column not found")


def create_card(column_id: str, title: str, details: str | None) -> CardRecord:
    card_id = f"card-{uuid.uuid4().hex[:8]}"
    now = now_iso()
    details_value = details.strip() if details and details.strip() else "No details yet."
    with get_db() as conn:
        column = conn.execute(
            "SELECT id FROM columns WHERE id = ?",
            (column_id,),
        ).fetchone()
        if not column:
            raise ColumnNotFoundError("Column not found")

        position_row = conn.execute(
            "SELECT MAX(position) AS max_position FROM cards WHERE column_id = ?",
            (column_id,),
        ).fetchone()
        max_pos = position_row["max_position"]
        next_position = (max_pos if max_pos is not None else -1) + 1

        conn.execute(
            "INSERT INTO cards (id, column_id, title, details, position, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (card_id, column_id, title, details_value, next_position, now, now),
        )
        conn.commit()

    return CardRecord(id=card_id, title=title, details=details_value)


def update_card(card_id: str, title: str | None, details: str | None) -> CardRecord:
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id, title, details FROM cards WHERE id = ?",
            (card_id,),
        ).fetchone()
        if not existing:
            raise CardNotFoundError("Card not found")

        next_title = title.strip() if title and title.strip() else existing["title"]
        next_details = (
            details.strip()
            if details and details.strip()
            else existing["details"]
        )
        conn.execute(
            "UPDATE cards SET title = ?, details = ?, updated_at = ? WHERE id = ?",
            (next_title, next_details, now_iso(), card_id),
        )
        conn.commit()

        return CardRecord(id=card_id, title=next_title, details=next_details)


def delete_card(card_id: str) -> None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT column_id FROM cards WHERE id = ?",
            (card_id,),
        ).fetchone()
        if not row:
            raise CardNotFoundError("Card not found")
        column_id = row["column_id"]

        conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        _reindex_column(conn, column_id)
        conn.commit()


def move_card(card_id: str, to_column_id: str, position: int) -> None:
    with get_db() as conn:
        card = conn.execute(
            "SELECT id, column_id FROM cards WHERE id = ?",
            (card_id,),
        ).fetchone()
        if not card:
            raise CardNotFoundError("Card not found")

        target = conn.execute(
            "SELECT id FROM columns WHERE id = ?",
            (to_column_id,),
        ).fetchone()
        if not target:
            raise ColumnNotFoundError("Column not found")

        from_column_id = card["column_id"]
        from_cards = _fetch_column_cards(conn, from_column_id)
        if card_id in from_cards:
            from_cards.remove(card_id)

        if from_column_id == to_column_id:
            next_cards = _insert_at(from_cards, card_id, position)
            _reindex_column(conn, from_column_id, next_cards)
            conn.commit()
            return

        to_cards = _fetch_column_cards(conn, to_column_id)
        next_to_cards = _insert_at(to_cards, card_id, position)
        conn.execute(
            "UPDATE cards SET column_id = ?, position = ?, updated_at = ? WHERE id = ?",
            (to_column_id, len(to_cards), now_iso(), card_id),
        )
        _reindex_column(conn, from_column_id, from_cards)
        _reindex_column(conn, to_column_id, next_to_cards)
        conn.commit()


def _fetch_column_cards(conn, column_id: str) -> List[str]:
    rows = conn.execute(
        "SELECT id FROM cards WHERE column_id = ? ORDER BY position",
        (column_id,),
    ).fetchall()
    return [row["id"] for row in rows]


def _insert_at(card_ids: List[str], card_id: str, position: int) -> List[str]:
    if position < 0:
        position = 0
    if position > len(card_ids):
        position = len(card_ids)
    next_cards = card_ids[:]
    next_cards.insert(position, card_id)
    return next_cards


def _reindex_column(conn, column_id: str, card_ids: List[str] | None = None) -> None:
    if card_ids is None:
        card_ids = _fetch_column_cards(conn, column_id)
    timestamp = now_iso()
    offset = 1_000_000
    for index, card_id in enumerate(card_ids):
        conn.execute(
            "UPDATE cards SET position = ?, updated_at = ? WHERE id = ?",
            (index + offset, timestamp, card_id),
        )
    for index, card_id in enumerate(card_ids):
        conn.execute(
            "UPDATE cards SET position = ?, updated_at = ? WHERE id = ?",
            (index, timestamp, card_id),
        )
