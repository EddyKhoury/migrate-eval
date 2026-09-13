import httpx

from migrate_eval.models.base import ModelAdapter
from migrate_eval.models.ollama_adapter import OllamaAdapter


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        data: dict | None = None,
    ) -> None:
        self.status_code = status_code
        self._data = data or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request(
                "POST",
                "http://localhost:11434/api/generate",
            )

            response = httpx.Response(
                self.status_code,
                request=request,
            )

            raise httpx.HTTPStatusError(
                "request failed",
                request=request,
                response=response,
            )

    def json(self) -> dict:
        return self._data


class FakeClient:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls = []

    def post(self, path: str, *, json: dict):
        self.calls.append(
            {
                "path": path,
                "json": json,
            }
        )

        return self.responses.pop(0)


def successful_response() -> FakeResponse:
    return FakeResponse(
        data={
            "response": "generated Go code",
            "prompt_eval_count": 25,
            "eval_count": 10,
        }
    )


def test_ollama_adapter_satisfies_model_adapter_protocol():
    adapter = OllamaAdapter(
        model="test-model",
        client=FakeClient([successful_response()]),
    )

    assert isinstance(adapter, ModelAdapter)
    assert adapter.name == "ollama:test-model"


def test_ollama_adapter_returns_response_text():
    adapter = OllamaAdapter(
        model="test-model",
        client=FakeClient([successful_response()]),
    )

    result = adapter.complete("migrate this code")

    assert result == "generated Go code"


def test_ollama_adapter_sends_expected_request():
    client = FakeClient([successful_response()])

    adapter = OllamaAdapter(
        model="test-model",
        client=client,
    )

    adapter.complete("migrate this code")

    assert client.calls == [
        {
            "path": "/api/generate",
            "json": {
                "model": "test-model",
                "prompt": "migrate this code",
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "seed": 0,
                },
            },
        }
    ]


def test_ollama_adapter_retries_server_error(monkeypatch):
    client = FakeClient(
        [
            FakeResponse(status_code=500),
            successful_response(),
        ]
    )

    monkeypatch.setattr(
        "migrate_eval.models.ollama_adapter.time.sleep",
        lambda _: None,
    )

    adapter = OllamaAdapter(
        model="test-model",
        client=client,
        max_retries=1,
    )

    result = adapter.complete("migrate this code")

    assert result == "generated Go code"
    assert len(client.calls) == 2