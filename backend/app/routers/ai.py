from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..ai import (
    OpenRouterConfigError,
    OpenRouterRequestError,
    OpenRouterResponseError,
    run_prompt,
    run_structured_prompt,
)
from ..ai_ops import apply_ai_operations
from ..repository import (
    BoardNotFoundError,
    CardNotFoundError,
    ColumnNotFoundError,
    fetch_board,
)
from ..schemas import (
    AiChatRequest,
    AiPromptRequest,
    AiPromptResponse,
    AiStructuredResponse,
)

router = APIRouter(prefix="/api/ai")


@router.post("/prompt", response_model=AiPromptResponse)
def run_ai_prompt(payload: AiPromptRequest) -> AiPromptResponse:
    try:
        content, model = run_prompt(payload.prompt)
    except OpenRouterConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (OpenRouterRequestError, OpenRouterResponseError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return AiPromptResponse(content=content, model=model)


@router.post("/structured", response_model=AiStructuredResponse)
def run_ai_structured(payload: AiChatRequest) -> AiStructuredResponse:
    try:
        board = fetch_board()
    except BoardNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    board_payload = {
        "columns": [
            {"id": col.id, "title": col.title, "cardIds": col.card_ids}
            for col in board.columns
        ],
        "cards": {
            card_id: {"id": card.id, "title": card.title, "details": card.details}
            for card_id, card in board.cards.items()
        },
    }

    try:
        structured, model = run_structured_prompt(
            payload.message,
            payload.history,
            board_payload,
        )
    except OpenRouterConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (OpenRouterRequestError, OpenRouterResponseError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        apply_ai_operations(structured.operations)
    except (ColumnNotFoundError, CardNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return AiStructuredResponse(
        message=structured.message,
        operations=structured.operations,
        model=model,
    )
