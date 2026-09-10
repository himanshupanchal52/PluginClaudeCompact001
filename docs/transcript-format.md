# Transcript format: what's actually in the `.jsonl`

Observations from a real transcript, not from memory or documentation. Re-verify these when Claude Code updates — the schema is not a stable public contract.

**Source:** this project's own session transcript, `~/.claude/projects/t--dBackupOne-GithubContributions-CompactGuard-PluginClaudeCompact001/<session-id>.jsonl`
**Claude Code version at time of observation:** see the `version` field on any entry
**Model:** `claude-opus-5`
**Observed:** 2026-09-11

## Shape

One JSON object per line. 154 entries at time of reading, all decodable. Top-level `type` values seen:

| `type` | Count | Note |
|--------|-------|------|
| `assistant` | 48 → 52 | The only carrier of `usage` |
| `attachment` | 37 | |
| `user` | 23 | |
| `bridge-session`, `atis-latch`, `ai-title`, `last-prompt`, `queue-operation`, `file-history-delta`, `file-history-snapshot` | 3–8 each | Housekeeping entry types |

The count rose from 48 to 52 assistant entries between two reads seconds apart — the file is appended live. Any parser must tolerate reading a file that is being written.

Keys on an `assistant` entry: `apiBlockIndex`, `cwd`, `effort`, `entrypoint`, `gitBranch`, `isSidechain`, `message`, `parentUuid`, `perTurnEffort`, `requestId`, `sessionId`, `timestamp`, `type`, `userType`, `uuid`, `version`.

## Where usage lives

`message.usage`, and **only** on `type: "assistant"` entries. Nothing carries a top-level `usage`.

Keys inside `message.usage`:

```
input_tokens, cache_creation_input_tokens, cache_read_input_tokens, output_tokens,
output_tokens_details, server_tool_use, service_tier, cache_creation,
inference_geo, iterations, speed
```

## Finding 1 — `input_tokens` alone is worthless

A real sample from late in the session:

```json
{"input_tokens": 2, "cache_creation_input_tokens": 1645,
 "cache_read_input_tokens": 66877, "output_tokens": 271}
```

`input_tokens` is **2**. The actual prompt is ~68,500 tokens; virtually all of it is served from the prompt cache. A parser that reads `input_tokens` and compares it to a 200K window would report 0.001% full while the session is a third of the way to compaction.

**The prompt size is the sum of the three input fields:**

```
prompt = input_tokens + cache_read_input_tokens + cache_creation_input_tokens
```

`output_tokens` is *not* part of the prompt that was sent, but it does become part of the next request's prompt. Whether to add it to the current estimate is an open decision.

## Finding 2 — `message.context_management` is `null`

Every assistant entry has a `message.context_management` key, and its value is `null` in all 48 samples. It is not a usable source for the context percentage today. Worth re-checking on version bumps, since a populated version of this field would be a far better input than summing usage fields.

## Finding 3 — entries are duplicated per request

52 assistant entries carried only **25 distinct `requestId` values**. Most requests appear two or three times, at different `timestamp`s, with byte-identical `usage`.

Consequences:

- "The latest assistant entry" is ambiguous. Naively diffing consecutive entries produces a stream of `+0` jumps between duplicates, which would corrupt the largest-jump statistic behind the predictive trigger.
- Deduplicate by `requestId` before computing anything sequential.

## Finding 4 — `isSidechain` exists and must be filtered

Assistant entries carry `isSidechain`. It was `False` for all 52 entries here because this session spawned no subagents. A subagent runs in its own context window, so its `usage` says nothing about the main thread's fill level. Reading a sidechain entry as "the latest" would report the wrong number, and probably a much smaller one.

The parser must ignore entries where `isSidechain` is truthy. This is untested against real sidechain data — a fixture with subagent entries is needed before the filter can be claimed as working.

## Finding 5 — `apiBlockIndex`

Values `0`, `1`, `2` were seen, partitioning the session's requests. Purpose not established. Noted in case it turns out to mark context boundaries.

## Finding 6 — the growth curve

Prompt size over the session, after dedupe, rose monotonically from 40,735 to 73,326 tokens. The largest single-step jump was **3,558 tokens**.

That figure is small because this session did no large file reads. A session that reads a 4,000-line file or receives a large command output will show jumps an order of magnitude bigger. This is exactly the case the predictive trigger exists for: a fixed 90% tier is useless if one tool call can consume the last 10%.

## Interpreter note (not transcript-related, but confirmed here)

On this Windows machine, `python` → 3.10.9 and `py` → 3.10.9, while **`python3` resolves to the Microsoft Store stub and fails**. A hook hardcoding `python3` would break on Windows; one hardcoding `python` would break on distributions where only `python3` exists.

## Reproducing

The exploration scripts used were throwaway, written to the session scratchpad and not committed. They printed structure and numbers only — never message content.
