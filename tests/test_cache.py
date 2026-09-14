from migrate_eval.cache import (
    CachedModelAdapter,
    completion_cache_key,
)


class FakeModel:
    name = "openai:test-model"
    temperature = None

    def __init__(self) -> None:
        self.calls = 0
        self.last_input_tokens = None
        self.last_output_tokens = None

    def complete(self, prompt: str) -> str:
        self.calls += 1
        self.last_input_tokens = 100
        self.last_output_tokens = 25

        return f"response for {prompt}"


def test_completion_cache_key_is_stable():
    first = completion_cache_key(
        "model",
        "prompt",
    )

    second = completion_cache_key(
        "model",
        "prompt",
    )

    assert first == second
    assert len(first) == 64


def test_cached_adapter_calls_model_on_cache_miss(
    tmp_path,
):
    model = FakeModel()

    adapter = CachedModelAdapter(
        model,
        cache_dir=tmp_path,
    )

    result = adapter.complete(
        "hello"
    )

    assert result == "response for hello"
    assert model.calls == 1
    assert adapter.last_cache_hit is False
    assert adapter.last_input_tokens == 100
    assert adapter.last_output_tokens == 25
    assert adapter.last_model_duration is not None


def test_cached_adapter_reuses_completion_without_model_call(
    tmp_path,
):
    model = FakeModel()

    adapter = CachedModelAdapter(
        model,
        cache_dir=tmp_path,
    )

    first = adapter.complete(
        "hello"
    )

    original_duration = (
        adapter.last_model_duration
    )

    second = adapter.complete(
        "hello"
    )

    assert first == second
    assert model.calls == 1
    assert adapter.last_cache_hit is True
    assert adapter.last_input_tokens == 100
    assert adapter.last_output_tokens == 25
    assert (
        adapter.last_model_duration
        == original_duration
    )


def test_different_prompt_uses_different_cache_entry(
    tmp_path,
):
    model = FakeModel()

    adapter = CachedModelAdapter(
        model,
        cache_dir=tmp_path,
    )

    adapter.complete("first")
    adapter.complete("second")

    assert model.calls == 2
