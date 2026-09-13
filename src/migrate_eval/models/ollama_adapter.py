import logging
import time
from typing import Any

import httpx


logger = logging.getLogger(__name__)


class OllamaAdapter:
    """Model adapter for locally hosted Ollama models."""

    def __init__(
        self,
        model: str,
        *,
        client: Any | None = None,
        base_url: str = "http://localhost:11434",
        temperature: float = 0.0,
        seed: int = 0,
        max_retries: int = 2,
        retry_backoff: float = 0.5,
        timeout: float = 120.0,
    ) -> None:
        self.model = model
        self.name = f"ollama:{model}"

        self.temperature = temperature
        self.seed = seed
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

        self._client = client or httpx.Client(
            base_url=base_url,
            timeout=timeout,
        )

    def complete(self, prompt: str) -> str:
        """Generate one completion and return its raw text."""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "seed": self.seed,
            },
        }

        for attempt in range(self.max_retries + 1):
            start = time.perf_counter()

            try:
                response = self._client.post(
                    "/api/generate",
                    json=payload,
                )
                response.raise_for_status()

                data = response.json()
                duration = time.perf_counter() - start

                logger.info(
                    "Ollama completion model=%s latency=%.3fs "
                    "input_tokens=%s output_tokens=%s",
                    self.model,
                    duration,
                    data.get("prompt_eval_count"),
                    data.get("eval_count"),
                )

                return data["response"]

            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code

                retriable = status_code == 429 or status_code >= 500

                if not retriable or attempt == self.max_retries:
                    raise

            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt == self.max_retries:
                    raise

            delay = self.retry_backoff * (2**attempt)

            logger.warning(
                "Ollama request failed; retrying in %.2fs",
                delay,
            )

            time.sleep(delay)

        raise RuntimeError("Ollama completion failed unexpectedly")