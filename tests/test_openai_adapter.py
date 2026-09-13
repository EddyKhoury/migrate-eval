from types import SimpleNamespace

from migrate_eval.models.base import ModelAdapter
from migrate_eval.models.openai_adapter import OpenAIAdapter


class FakeResponses:
    def __init__(self) -> None:
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)

        return SimpleNamespace(
            output_text="generated Go code",
            usage=SimpleNamespace(
                input_tokens=25,
                output_tokens=10,
            ),
        )


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


def test_openai_adapter_satisfies_model_adapter_protocol():
    adapter = OpenAIAdapter(
        model="test-model",
        client=FakeOpenAIClient(),
    )

    assert isinstance(adapter, ModelAdapter)
    assert adapter.name == "openai:test-model"


def test_openai_adapter_returns_response_text():
    adapter = OpenAIAdapter(
        model="test-model",
        client=FakeOpenAIClient(),
    )

    result = adapter.complete("migrate this code")

    assert result == "generated Go code"


def test_openai_adapter_sends_expected_request():
    client = FakeOpenAIClient()

    adapter = OpenAIAdapter(
        model="test-model",
        client=client,
    )

    adapter.complete("migrate this code")

    assert client.responses.calls == [
        {
            "model": "test-model",
            "input": "migrate this code",
        }
    ]


def test_openai_adapter_sends_temperature_when_configured():
    client = FakeOpenAIClient()

    adapter = OpenAIAdapter(
        model="test-model",
        client=client,
        temperature=0.0,
    )

    adapter.complete("migrate this code")

    assert client.responses.calls == [
        {
            "model": "test-model",
            "input": "migrate this code",
            "temperature": 0.0,
        }
    ]


def test_openai_adapter_records_token_usage():
    adapter = OpenAIAdapter(
        model="test-model",
        client=FakeOpenAIClient(),
    )

    adapter.complete("migrate this code")

    assert adapter.last_input_tokens == 25
    assert adapter.last_output_tokens == 10
