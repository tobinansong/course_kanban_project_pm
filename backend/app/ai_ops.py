from __future__ import annotations

from .repository import create_card, delete_card, move_card, rename_column, update_card
from .schemas import (
    AiBoardOperation,
    AiCreateCardOperation,
    AiDeleteCardOperation,
    AiMoveCardOperation,
    AiRenameColumnOperation,
    AiUpdateCardOperation,
)


def apply_ai_operations(operations: list[AiBoardOperation]) -> None:
    for op in operations:
        if isinstance(op, AiRenameColumnOperation):
            rename_column(op.columnId, op.title)
        elif isinstance(op, AiCreateCardOperation):
            create_card(op.columnId, op.title, op.details)
        elif isinstance(op, AiUpdateCardOperation):
            update_card(op.cardId, op.title, op.details)
        elif isinstance(op, AiMoveCardOperation):
            move_card(op.cardId, op.toColumnId, op.position)
        elif isinstance(op, AiDeleteCardOperation):
            delete_card(op.cardId)
