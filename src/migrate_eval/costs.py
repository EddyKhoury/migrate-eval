"""Model API cost estimation helpers."""

from __future__ import annotations


# Prices are USD per 1 million tokens.
#
# GPT-5.6 Terra pricing verified from the official OpenAI
# model documentation for the Milestone 4 evaluation.
MODEL_PRICING_USD_PER_MILLION = {
    "openai:gpt-5.6-terra": {
        "input": 2.00,
        "output": 12.00,
    },
}


def has_pricing(model_name: str) -> bool:
    """Return whether cost estimation is configured for a model."""

    return model_name in MODEL_PRICING_USD_PER_MILLION


def estimate_model_cost_usd(
    *,
    model_name: str,
    input_tokens: int | None,
    output_tokens: int | None,
) -> float | None:
    """Estimate one model call's cost in USD.

    Returns None when pricing or token telemetry is unavailable.

    Input tokens are conservatively priced at the normal uncached
    input rate because cached-token telemetry is not currently
    persisted separately by the evaluation harness.
    """

    pricing = MODEL_PRICING_USD_PER_MILLION.get(
        model_name
    )

    if pricing is None:
        return None

    if input_tokens is None or output_tokens is None:
        return None

    if input_tokens < 0 or output_tokens < 0:
        raise ValueError(
            "token counts must be non-negative"
        )

    input_cost = (
        input_tokens
        / 1_000_000
        * pricing["input"]
    )

    output_cost = (
        output_tokens
        / 1_000_000
        * pricing["output"]
    )

    return input_cost + output_cost
