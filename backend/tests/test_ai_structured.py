from __future__ import annotations

import pytest

from app import ai, db, repository
from app.ai_ops import apply_ai_operations
from app.schemas import (
    AiCreateCardOperation,
    AiDeleteCardOperation,
    AiMoveCardOperation,
    AiRenameColumnOperation,
    AiUpdateCardOperation,
)


def test_parse_structured_response_accepts_message_only() -> None:
    parsed = ai.parse_structured_response('{"message":"Hello"}')

    assert parsed.message == "Hello"
    assert parsed.operations == []


def test_parse_structured_response_logs_invalid_json(caplog) -> None:
    with caplog.at_level("WARNING"):
        with pytest.raises(ai.OpenRouterResponseError):
            ai.parse_structured_response("not json")

    assert any("invalid JSON" in record.message for record in caplog.records)


def test_apply_ai_operations_updates_board(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()

    operations = [
        AiRenameColumnOperation(
            type="rename_column",
            columnId="col-backlog",
            title="Ideas",
        ),
        AiUpdateCardOperation(
            type="update_card",
            cardId="card-1",
            title="Updated title",
            details=None,
        ),
        AiMoveCardOperation(
            type="move_card",
            cardId="card-1",
            toColumnId="col-discovery",
            position=0,
        ),
        AiDeleteCardOperation(type="delete_card", cardId="card-2"),
        AiCreateCardOperation(
            type="create_card",
            columnId="col-backlog",
            title="New card",
            details="Some details",
        ),
    ]

    apply_ai_operations(operations)
    board = repository.fetch_board()
    columns_by_id = {column.id: column for column in board.columns}

    assert columns_by_id["col-backlog"].title == "Ideas"
    assert "card-1" in columns_by_id["col-discovery"].card_ids
    assert "card-1" not in columns_by_id["col-backlog"].card_ids
    assert "card-2" not in board.cards
    assert board.cards["card-1"].title == "Updated title"
    assert any(card.title == "New card" for card in board.cards.values())


def test_create_card_in_single_card_column(monkeypatch, tmp_path) -> None:
    """Regression: position calculation was wrong when column had exactly one card at position 0."""
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()

    # col-discovery has exactly one seed card (card-3 at position 0)
    card = repository.create_card("col-discovery", "Second card", "Details")

    board = repository.fetch_board()
    discovery = next(c for c in board.columns if c.id == "col-discovery")

    assert card.id in discovery.card_ids
    assert discovery.card_ids[0] == "card-3"
    assert discovery.card_ids[-1] == card.id


def test_move_card_to_empty_column(monkeypatch, tmp_path) -> None:
    """Regression: moving to an empty column caused a UNIQUE constraint violation."""
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()

    # col-review is empty in seed data
    repository.move_card("card-1", "col-review", 0)

    board = repository.fetch_board()
    review = next(c for c in board.columns if c.id == "col-review")
    backlog = next(c for c in board.columns if c.id == "col-backlog")

    assert "card-1" in review.card_ids
    assert review.card_ids.index("card-1") == 0
    assert "card-1" not in backlog.card_ids


def test_move_card_within_column_reorders_correctly(monkeypatch, tmp_path) -> None:
    """Moving a card to a lower position in its own column reindexes correctly."""
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()

    # col-backlog: [card-1 (0), card-2 (1)] — move card-2 to position 0
    repository.move_card("card-2", "col-backlog", 0)

    board = repository.fetch_board()
    backlog = next(c for c in board.columns if c.id == "col-backlog")

    assert backlog.card_ids == ["card-2", "card-1"]
