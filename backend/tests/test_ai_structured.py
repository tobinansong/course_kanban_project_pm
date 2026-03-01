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
