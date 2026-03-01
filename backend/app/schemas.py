from __future__ import annotations

from typing import Annotated, Literal, Union

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


class AiChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AiChatRequest(BaseModel):
    message: str
    history: list[AiChatMessage] = Field(default_factory=list)


class AiRenameColumnOperation(BaseModel):
    type: Literal["rename_column"]
    columnId: str
    title: str


class AiCreateCardOperation(BaseModel):
    type: Literal["create_card"]
    columnId: str
    title: str
    details: str | None = None


class AiUpdateCardOperation(BaseModel):
    type: Literal["update_card"]
    cardId: str
    title: str | None = None
    details: str | None = None


class AiMoveCardOperation(BaseModel):
    type: Literal["move_card"]
    cardId: str
    toColumnId: str
    position: int = Field(ge=0)


class AiDeleteCardOperation(BaseModel):
    type: Literal["delete_card"]
    cardId: str


AiBoardOperation = Annotated[
    Union[
        AiRenameColumnOperation,
        AiCreateCardOperation,
        AiUpdateCardOperation,
        AiMoveCardOperation,
        AiDeleteCardOperation,
    ],
    Field(discriminator="type"),
]


class AiStructuredOutput(BaseModel):
    message: str
    operations: list[AiBoardOperation] = Field(default_factory=list)


class AiStructuredResponse(BaseModel):
    message: str
    operations: list[AiBoardOperation] = Field(default_factory=list)
    model: str
