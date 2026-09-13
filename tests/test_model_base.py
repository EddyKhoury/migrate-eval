from migrate_eval.models.base import ModelAdapter


class FakeModel:
    name = "fake-model"

    def complete(self, prompt: str) -> str:
        return f"response:{prompt}"


class IncompleteModel:
    name = "incomplete-model"


def test_model_adapter_accepts_structural_implementation():
    model = FakeModel()

    assert isinstance(model, ModelAdapter)
    assert model.name == "fake-model"
    assert model.complete("hello") == "response:hello"


def test_model_adapter_rejects_missing_complete_method():
    model = IncompleteModel()

    assert not isinstance(model, ModelAdapter)
    