"""Read token usage out of a Claude Code transcript.

The transcript is JSON Lines: one object per line, appended while the session
runs. Only ``type: "assistant"`` entries carry usage, at ``message.usage``.

Everything here parses defensively and never raises on bad input. The schema is
not a public contract and changes between Claude Code versions, and a hook that
throws is a hook that breaks someone's session. Unreadable input yields an empty
result, not an exception.

Observed details that shape this module are written up in docs/transcript-format.md.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterator, List, Optional, Sequence


@dataclass(frozen=True)
class ContextUsage:
    """Token usage for a single assistant response.

    Fields default to 0 so a missing key degrades to an undercount rather than
    a crash.
    """

    input_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    output_tokens: int = 0
    request_id: Optional[str] = None
    timestamp: Optional[str] = None

    @property
    def prompt_tokens(self) -> int:
        """What was actually sent on the wire for this request.

        All three input fields must be summed. Under prompt caching
        ``input_tokens`` alone is routinely single digits while the real prompt
        is tens of thousands of tokens.
        """
        return (
            self.input_tokens
            + self.cache_read_input_tokens
            + self.cache_creation_input_tokens
        )

    @property
    def context_tokens(self) -> int:
        """Best estimate of context occupied once this response landed.

        The response text becomes part of the next request's prompt, so it
        counts. This still excludes any tool result that arrived after the
        response; the measuring hook adds that estimate itself.
        """
        return self.prompt_tokens + self.output_tokens


def _as_int(value: object) -> int:
    """Coerce a JSON value to int, defaulting to 0.

    ``bool`` is checked first because in Python ``bool`` subclasses ``int``,
    so ``isinstance(True, int)`` is True and ``True`` would arrive as 1.
    """
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0


def iter_entries(path: str) -> Iterator[dict]:
    """Yield each decodable JSON object from the transcript.

    Blank lines and undecodable lines are skipped. A truncated final line is
    normal: the file is appended to while it is being read.
    """
    try:
        handle = open(path, "r", encoding="utf-8", errors="replace")
    except OSError:
        return

    with handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except (ValueError, TypeError):
                continue
            if isinstance(entry, dict):
                yield entry


def _is_main_thread_assistant(entry: dict) -> bool:
    """True for assistant entries on the main conversation thread.

    Sidechain entries come from subagents, which run in their own context
    window. Their usage says nothing about how full the main thread is.
    """
    if entry.get("type") != "assistant":
        return False
    if entry.get("isSidechain"):
        return False
    return isinstance(entry.get("message"), dict)


def usage_from_entry(entry: dict) -> Optional[ContextUsage]:
    """Extract usage from one entry, or None if it carries none."""
    if not _is_main_thread_assistant(entry):
        return None

    raw = entry["message"].get("usage")
    if not isinstance(raw, dict):
        return None

    request_id = entry.get("requestId")
    timestamp = entry.get("timestamp")
    return ContextUsage(
        input_tokens=_as_int(raw.get("input_tokens")),
        cache_read_input_tokens=_as_int(raw.get("cache_read_input_tokens")),
        cache_creation_input_tokens=_as_int(raw.get("cache_creation_input_tokens")),
        output_tokens=_as_int(raw.get("output_tokens")),
        request_id=request_id if isinstance(request_id, str) else None,
        timestamp=timestamp if isinstance(timestamp, str) else None,
    )


def read_usage_series(path: str) -> List[ContextUsage]:
    """All main-thread usage records in order, one per request.

    A single request is written to the transcript two or three times with
    identical usage. Collapsing by ``requestId`` matters for anything that
    looks at differences between consecutive records: without it the series is
    full of +0 steps that would hide the real jumps.

    Entries with no usable ``requestId`` are kept individually rather than
    collapsed together, since they cannot be shown to be the same request.
    """
    by_request: "dict[str, ContextUsage]" = {}
    orphan_count = 0

    for entry in iter_entries(path):
        usage = usage_from_entry(entry)
        if usage is None:
            continue
        if usage.request_id:
            key = usage.request_id
        else:
            key = "\x00orphan-{0}".format(orphan_count)
            orphan_count += 1
        # Assigning an existing key keeps the record's original position while
        # replacing the value, so the series stays chronological and each
        # request resolves to its last-written copy.
        by_request[key] = usage

    return list(by_request.values())


def latest_usage(path: str) -> Optional[ContextUsage]:
    """The most recent main-thread usage record, or None if there is none."""
    series = read_usage_series(path)
    return series[-1] if series else None


def largest_jump(series: Sequence[ContextUsage]) -> int:
    """Largest single-step growth in context across the series.

    Feeds the predictive trigger: one tool call can consume more headroom than
    the gap between two warning tiers, so the trigger sizes itself against the
    worst step seen so far rather than a fixed percentage.

    Decreases are ignored. Context drops when a compaction happens, and that is
    not a step this is trying to measure.
    """
    biggest = 0
    previous: Optional[int] = None

    for usage in series:
        current = usage.context_tokens
        if previous is not None:
            step = current - previous
            if step > biggest:
                biggest = step
        previous = current

    return biggest
