import logging
import time
from typing import Any

from openai import OpenAI


logger = logging.getLogger(__name__)


class OpenAIAdapter:
    """Model adapter for OpenAI models using the Responses API."""

    def __init__(
        self,
        model: str,
        *,
        client: Any | None = None,
        temperature: float = 0.0,
        max_retries: int = 2,
        timeout: float = 60.0,
    ) -> None:
        self.model = model
        self.name = f"openai:{model}"
        self.temperature = temperature

        self._client = client
        self._max_retries = max_retries
        self._timeout = timeout

    def _get_client(self) -> Any:
        """Create the OpenAI client lazily when first needed."""

        if self._client is None:
            self._client = OpenAI(
                max_retries=self._max_retries,
                timeout=self._timeout,
            )

        return self._client

    def complete(self, prompt: str) -> str:
        """Generate one completion and return its raw text."""

        client = self._get_client()

        start = time.perf_counter()

        response = client.responses.create(
            model=self.model,
            input=prompt,
            temperature=self.temperature,
        )

        duration = time.perf_counter() - start

        usage = getattr(response, "usage", None)
        input_tokens = getattr(
            usage,
            "input_tokens",
            None,
        )
        output_tokens = getattr(
            usage,
            "output_tokens",
            None,
        )

        logger.info(
            "OpenAI completion model=%s latency=%.3fs "
            "input_tokens=%s output_tokens=%s",
            self.model,
            duration,
            input_tokens,
            output_tokens,
        )

        return response.output_text