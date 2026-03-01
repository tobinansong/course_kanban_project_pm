from pathlib import Path

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .ai import (
  OpenRouterConfigError,
  OpenRouterRequestError,
  OpenRouterResponseError,
  run_prompt,
  run_structured_prompt,
)
from .ai_ops import apply_ai_operations
from .db import init_db
from .repository import (
  BoardNotFoundError,
  CardNotFoundError,
  ColumnNotFoundError,
  create_card,
  delete_card,
  fetch_board,
  move_card,
  rename_column,
  update_card,
)
from .schemas import (
  AiChatRequest,
  AiPromptRequest,
  AiPromptResponse,
  AiStructuredResponse,
  Board,
  CreateCardRequest,
  MoveCardRequest,
  RenameColumnRequest,
  UpdateCardRequest,
)

load_dotenv()

app = FastAPI()

STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.on_event("startup")
def startup() -> None:
  init_db()


@app.get("/api/health")
def read_health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/board", response_model=Board)
def read_board() -> Board:
  try:
    board = fetch_board()
  except BoardNotFoundError as exc:
    raise HTTPException(status_code=404, detail=str(exc)) from exc

  return Board(
    columns=[
      {"id": column.id, "title": column.title, "cardIds": column.card_ids}
      for column in board.columns
    ],
    cards={
      card_id: {"id": card.id, "title": card.title, "details": card.details}
      for card_id, card in board.cards.items()
    },
  )


@app.post("/api/columns/{column_id}/rename")
def rename_board_column(column_id: str, payload: RenameColumnRequest) -> dict[str, str]:
  try:
    rename_column(column_id, payload.title)
  except ColumnNotFoundError as exc:
    raise HTTPException(status_code=404, detail=str(exc)) from exc
  return {"status": "ok"}


@app.post("/api/cards")
def create_board_card(payload: CreateCardRequest) -> dict[str, str]:
  try:
    card = create_card(payload.columnId, payload.title, payload.details)
  except ColumnNotFoundError as exc:
    raise HTTPException(status_code=404, detail=str(exc)) from exc
  return {"id": card.id, "title": card.title, "details": card.details}


@app.patch("/api/cards/{card_id}")
def update_board_card(card_id: str, payload: UpdateCardRequest) -> dict[str, str]:
  try:
    card = update_card(card_id, payload.title, payload.details)
  except CardNotFoundError as exc:
    raise HTTPException(status_code=404, detail=str(exc)) from exc
  return {"id": card.id, "title": card.title, "details": card.details}


@app.delete("/api/cards/{card_id}")
def delete_board_card(card_id: str) -> dict[str, str]:
  try:
    delete_card(card_id)
  except CardNotFoundError as exc:
    raise HTTPException(status_code=404, detail=str(exc)) from exc
  return {"status": "ok"}


@app.post("/api/cards/{card_id}/move")
def move_board_card(card_id: str, payload: MoveCardRequest) -> dict[str, str]:
  try:
    move_card(card_id, payload.toColumnId, payload.position)
  except (CardNotFoundError, ColumnNotFoundError) as exc:
    raise HTTPException(status_code=404, detail=str(exc)) from exc
  return {"status": "ok"}


@app.post("/api/ai/prompt", response_model=AiPromptResponse)
def run_ai_prompt(payload: AiPromptRequest) -> AiPromptResponse:
  try:
    content, model = run_prompt(payload.prompt)
  except OpenRouterConfigError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  except (OpenRouterRequestError, OpenRouterResponseError) as exc:
    raise HTTPException(status_code=502, detail=str(exc)) from exc
  return AiPromptResponse(content=content, model=model)


@app.post("/api/ai/structured", response_model=AiStructuredResponse)
def run_ai_structured(payload: AiChatRequest) -> AiStructuredResponse:
  try:
    board = fetch_board()
  except BoardNotFoundError as exc:
    raise HTTPException(status_code=404, detail=str(exc)) from exc

  board_payload = {
    "columns": [
      {"id": column.id, "title": column.title, "cardIds": column.card_ids}
      for column in board.columns
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


@app.post("/api/chat", response_model=AiPromptResponse)
def run_ai_chat() -> AiPromptResponse:
  try:
    content, model = run_prompt("Say hello from OpenRouter in one short sentence.")
  except OpenRouterConfigError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  except (OpenRouterRequestError, OpenRouterResponseError) as exc:
    raise HTTPException(status_code=502, detail=str(exc)) from exc
  return AiPromptResponse(content=content, model=model)


if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
else:
    @app.get("/", response_class=HTMLResponse)
    def read_root() -> HTMLResponse:
        return HTMLResponse(
            """
            <!doctype html>
            <html lang=\"en\">
              <head>
                <meta charset=\"utf-8\" />
                <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
                <title>PM App - Build Required</title>
                <style>
                  :root {
                    color-scheme: light;
                    font-family: "Segoe UI", system-ui, sans-serif;
                    background: #f7f8fb;
                    color: #032147;
                  }
                  body {
                    margin: 0;
                    padding: 40px;
                  }
                  .card {
                    max-width: 640px;
                    background: #ffffff;
                    border-radius: 20px;
                    padding: 24px;
                    box-shadow: 0 18px 40px rgba(3, 33, 71, 0.12);
                  }
                  h1 {
                    margin: 0 0 8px;
                    font-size: 28px;
                  }
                  p {
                    margin: 0 0 12px;
                    color: #888888;
                  }
                  code {
                    display: inline-block;
                    padding: 2px 6px;
                    background: #eef2f7;
                    border-radius: 6px;
                    color: #032147;
                  }
                </style>
              </head>
              <body>
                <div class=\"card\">
                  <h1>Frontend build not found</h1>
                  <p>Build the frontend to generate static assets.</p>
                  <p>Expected folder: <code>backend/app/static</code></p>
                </div>
              </body>
            </html>
            """
        )
