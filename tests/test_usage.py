"""Tests for compact_guard.usage.

Two worked examples are here to establish the idioms. The rest of the cases are
listed in tests/SUGGESTED_CASES.md for the author to write.
"""

import pytest

from compact_guard.usage import (
    ContextUsage,
    largest_jump,
    latest_usage,
    read_usage_series,
)


# Example 1: a plain assertion test.
#
# The point of this one is the caching trap. input_tokens is 2; the real prompt
# is 1502. Anything that reads input_tokens alone fails here.
def test_prompt_sums_all_three_input_fields():
    usage = ContextUsage(
        input_tokens=2,
        cache_read_input_tokens=1000,
        cache_creation_input_tokens=500,
        output_tokens=100,
    )

    assert usage.prompt_tokens == 1502
    assert usage.context_tokens == 1602


# Example 2: a parametrized test.
#
# @pytest.mark.parametrize runs the body once per tuple, each as its own
# reported test. It is the rough equivalent of xUnit's [Theory] + [InlineData],
# with the ids= argument naming the cases in the output.
@pytest.mark.parametrize(
    "filename, expected_length, expected_context",
    [
        ("simple.jsonl", 3, 5252),
        ("duplicates.jsonl", 2, 2202),
        ("empty.jsonl", 0, None),
    ],
    ids=["distinct-requests", "collapses-duplicates", "empty-file"],
)
def test_series_length_and_latest(
    fixture_path, filename, expected_length, expected_context
):
    series = read_usage_series(fixture_path(filename))
    assert len(series) == expected_length

    latest = latest_usage(fixture_path(filename))
    if expected_context is None:
        assert latest is None
    else:
        assert latest is not None
        assert latest.context_tokens == expected_context


# --- Cases for the author to write. See tests/SUGGESTED_CASES.md. ---
