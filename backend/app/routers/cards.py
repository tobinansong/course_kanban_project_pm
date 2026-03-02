from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..repository import (
    CardNotFoundError,
    ColumnNotFoundError,
    create_card,
    delete_card,
    move_card,
    update_card,
)
from ..schemas import CreateCardRequest, MoveCardRequest, UpdateCardRequest

router = APIRouter(prefix="/api/cards")


@router.post("")
def create_board_card(payload: CreateCardRequest) -> dict[str, str]:
    try:
        card = create_card(payload.columnId, payload.title, payload.details)
    except ColumnNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": card.id, "title": card.title, "details": card.details}


@router.patch("/{card_id}")
def update_board_card(card_id: str, payload: UpdateCardRequest) -> dict[str, str]:
    try:
        card = update_card(card_id, payload.title, payload.details)
    except CardNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": card.id, "title": card.title, "details": card.details}


@router.delete("/{card_id}")
def delete_board_card(card_id: str) -> dict[str, str]:
    try:
        delete_card(card_id)
    except CardNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "ok"}


@router.post("/{card_id}/move")
def move_board_card(card_id: str, payload: MoveCardRequest) -> dict[str, str]:
    try:
        move_card(card_id, payload.toColumnId, payload.position)
    except (CardNotFoundError, ColumnNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "ok"}
