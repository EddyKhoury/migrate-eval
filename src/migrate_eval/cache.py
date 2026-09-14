"""Disk-backed cache for model completions."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from migrate_eval.models.base import ModelAdapter


def completion_cache_key(
    model_name: str,
    prompt: str,
) -> str:
    """Return a stable key for one model/prompt combination."""

    payload = (
        model_name
        + "\0"
        + prompt
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


class CachedModelAdapter:
    """Wrap a ModelAdapter with persistent completion caching."""

    def __init__(
        self,
        model: ModelAdapter,
        *,
        cache_dir: str | Path,
    ) -> None:
        self._model = model
        self.name = model.name
        self.cache_dir = Path(cache_dir)

        self.last_input_tokens: int | None = None
        self.last_output_tokens: int | None = None
        self.last_model_duration: float | None = None
        self.last_cache_hit = False

    def __getattr__(self, name: str):
        """Forward provider-specific configuration to the wrapped model."""

        return getattr(
            self._model,
            name,
        )

    def complete(self, prompt: str) -> str:
        """Return a cached completion or call the wrapped model."""

        key = completion_cache_key(
            self.name,
            prompt,
        )

        path = (
            self.cache_dir
            / self.name.replace(":", "__").replace("/", "__")
            / f"{key}.json"
        )

        self.last_cache_hit = False
        self.last_input_tokens = None
        self.last_output_tokens = None
        self.last_model_duration = None

        if path.exists():
            data = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

            self.last_input_tokens = data.get(
                "input_tokens"
            )
            self.last_output_tokens = data.get(
                "output_tokens"
            )
            self.last_model_duration = data.get(
                "model_duration"
            )
            self.last_cache_hit = True

            return data["response"]

        start = time.perf_counter()

        response = self._model.complete(
            prompt
        )

        duration = (
            time.perf_counter()
            - start
        )

        self.last_input_tokens = getattr(
            self._model,
            "last_input_tokens",
            None,
        )

        self.last_output_tokens = getattr(
            self._model,
            "last_output_tokens",
            None,
        )

        self.last_model_duration = duration

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        record = {
            "model": self.name,
            "response": response,
            "input_tokens": self.last_input_tokens,
            "output_tokens": self.last_output_tokens,
            "model_duration": duration,
        }

        path.write_text(
            json.dumps(
                record,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        return response
