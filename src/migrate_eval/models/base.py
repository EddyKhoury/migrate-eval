from typing import Protocol, runtime_checkable


@runtime_checkable
class ModelAdapter(Protocol):
    """Common interface implemented by every LLM backend."""

    name: str

    def complete(self, prompt: str) -> str:
        """Return the model's raw text response for a prompt."""
        ...