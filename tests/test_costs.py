import pytest

from migrate_eval.costs import (
    estimate_model_cost_usd,
    has_pricing,
)


def test_gpt_56_terra_has_configured_pricing():
    assert has_pricing(
        "openai:gpt-5.6-terra"
    )


def test_estimate_terra_cost():
    cost = estimate_model_cost_usd(
        model_name="openai:gpt-5.6-terra",
        input_tokens=1_000,
        output_tokens=500,
    )

    assert cost == pytest.approx(
        0.008
    )


def test_unknown_model_cost_is_unavailable():
    cost = estimate_model_cost_usd(
        model_name="openai:unknown",
        input_tokens=1_000,
        output_tokens=500,
    )

    assert cost is None


def test_missing_token_telemetry_has_no_cost_estimate():
    cost = estimate_model_cost_usd(
        model_name="openai:gpt-5.6-terra",
        input_tokens=None,
        output_tokens=500,
    )

    assert cost is None
