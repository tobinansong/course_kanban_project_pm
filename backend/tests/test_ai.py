from __future__ import annotations

import os

from fastapi.testclient import TestClient

from app.main import app


def test_ai_chat_calls_openrouter() -> None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise AssertionError("OPENROUTER_API_KEY must be set for live OpenRouter test")

    client = TestClient(app)

    response = client.post("/api/chat")

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "openai/gpt-oss-120b:free"
    assert isinstance(data["content"], str)
    assert data["content"].strip()
