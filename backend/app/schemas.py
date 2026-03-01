from __future__ import annotations

from pydantic import BaseModel, Field


class Card(BaseModel):
    id: str
    title: str
    details: str


class Column(BaseModel):
    id: str
    title: str
    cardIds: list[str] = Field(default_factory=list)


class Board(BaseModel):
    columns: list[Column]
    cards: dict[str, Card]


class RenameColumnRequest(BaseModel):
    title: str


class CreateCardRequest(BaseModel):
    columnId: str
    title: str
    details: str | None = None


class UpdateCardRequest(BaseModel):
    title: str | None = None
    details: str | None = None


class MoveCardRequest(BaseModel):
    toColumnId: str
    position: int = Field(ge=0)


class AiPromptRequest(BaseModel):
    prompt: str


class AiPromptResponse(BaseModel):
    content: str
    model: str
