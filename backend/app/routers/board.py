from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..repository import (
    BoardNotFoundError,
    ColumnNotFoundError,
    fetch_board,
    rename_column,
)
from ..schemas import Board, RenameColumnRequest

router = APIRouter(prefix="/api")


@router.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/board", response_model=Board)
def read_board() -> Board:
    try:
        board = fetch_board()
    except BoardNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return Board(
        columns=[
            {"id": col.id, "title": col.title, "cardIds": col.card_ids}
            for col in board.columns
        ],
        cards={
            card_id: {"id": card.id, "title": card.title, "details": card.details}
            for card_id, card in board.cards.items()
        },
    )


@router.post("/columns/{column_id}/rename")
def rename_board_column(column_id: str, payload: RenameColumnRequest) -> dict[str, str]:
    try:
        rename_column(column_id, payload.title)
    except ColumnNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "ok"}
