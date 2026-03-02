from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_ai_prompt_calls_openrouter() -> None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    client = TestClient(app)

    response = client.post("/api/ai/prompt", json={"prompt": "Say hello in one word."})

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "openai/gpt-oss-120b:free"
    assert isinstance(data["content"], str)
    assert data["content"].strip()
