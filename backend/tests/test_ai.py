from __future__ import annotations

from typing import Any, Dict

from fastapi.testclient import TestClient

from app import ai
from app.main import app


def test_ai_prompt_uses_configured_model(monkeypatch) -> None:
    client = TestClient(app)
    captured: Dict[str, Any] = {}

    def fake_post(base_url: str, payload: dict[str, Any], headers: dict[str, str]):
        captured["payload"] = payload
        captured["headers"] = headers

        class FakeResponse:
            def raise_for_status(self) -> None:
                return None

            def json(self) -> dict[str, Any]:
                return {"choices": [{"message": {"content": "4"}}]}

        return FakeResponse()

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(ai, "_post_openrouter", fake_post)

    response = client.post("/api/ai/prompt", json={"prompt": "2+2"})

    assert response.status_code == 200
    data = response.json()
    assert data == {"content": "4", "model": "openai/gpt-oss-120b:free"}
    assert captured["payload"]["model"] == "openai/gpt-oss-120b:free"
    assert captured["payload"]["messages"][0]["content"] == "2+2"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
