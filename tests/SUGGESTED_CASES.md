# Suggested test cases

Per the working agreement, the author writes the tests. This file is the input to that: what each fixture contains, the expected numbers worked out by hand, and the cases worth covering.

Two examples are already written in `test_usage.py` to establish the idioms — one plain assertion, one `@pytest.mark.parametrize`.

## Fixture inventory

All fixtures are synthetic. No real session content.

### `simple.jsonl` — three distinct requests

| requestId | input | cache_read | cache_creation | output | `prompt_tokens` | `context_tokens` |
|-----------|-------|-----------|----------------|--------|-----------------|------------------|
| `req_001` | 2 | 1000 | 500 | 100 | 1502 | 1602 |
| `req_002` | 2 | 1600 | 400 | 200 | 2002 | 2202 |
| `req_003` | 2 | 2200 | 3000 | 50 | 5202 | 5252 |

Series length **3**, latest `context_tokens` **5252**, `largest_jump` **3050** (steps: +600, +3050).

Also contains one `type: "user"` entry, which must be ignored.

### `duplicates.jsonl` — two requests, each written three times

Same numbers as `req_001` and `req_002` above, each repeated 3x with different `uuid` and `timestamp` but identical usage. This is the real transcript's behaviour.

Series length **2**, latest `context_tokens` **2202**, `largest_jump` **600**.

Without deduplication you would get length 6 and a jump series of `+0, +0, +600, +0, +0` — the tell-tale of the bug.

### `sidechain.jsonl` — subagent entries interleaved

Two main-thread requests (1602, 2202) with three `isSidechain: true` entries between and after them, carrying deliberately huge numbers (~95,000–100,000 tokens).

Series length **2**, latest `context_tokens` **2202**, `largest_jump` **600**.

The trap: the last line in the file is a sidechain entry. A parser that takes "the last assistant entry" reports ~100,300 instead of 2,202.

### `malformed.jsonl` — everything that can go wrong

In order: a blank line; `{not json at all`; a JSON array rather than an object; an assistant entry whose `message` is a string; one whose `usage` is a string; then four usable entries; then a truncated final line with no newline (simulating a read mid-append).

| uuid | requestId | Raw usage | `prompt_tokens` | `context_tokens` | Why |
|------|-----------|-----------|-----------------|------------------|-----|
| `m3` | `req_010` | `{"input_tokens": 500}` | 500 | 500 | Missing keys default to 0 |
| `m4` | `req_011` | `cache_read` is the **string** `"600"` | 15 | 18 | Strings coerce to 0, not crash |
| `m5` | `req_012` | `cache_read` is **700.9**, `cache_creation` is **null**, `output` is **true** | 701 | 701 | Float truncates; null → 0; **bool → 0** |
| `m6` | *(none)* | 10 / 20 / 30 / 40 | 60 | 100 | No `requestId` at all |

Series length **4**, latest is `m6` with `context_tokens` **100**, `largest_jump` **683** (contexts run 500 → 18 → 701 → 100; only the +683 step counts).

The `output_tokens: true` case is deliberate. In Python `bool` subclasses `int`, so `isinstance(True, int)` is `True` and a naive coercion turns `true` into `1`. In C# that cast would not compile. `_as_int` checks `bool` first for exactly this reason.

### `empty.jsonl` — zero bytes

Series length **0**, `latest_usage` returns `None`, `largest_jump([])` returns `0`.

## Cases to write

Marked with the property each one actually pins down, so a passing test means something.

**Parsing and coercion**

1. `sidechain.jsonl` — `latest_usage` returns the main-thread record (2202), *not* the trailing sidechain entry. Pins the `isSidechain` filter.
2. `malformed.jsonl` — `read_usage_series` returns 4 records and raises nothing. Pins fail-open parsing.
3. Coercion table, as a `parametrize` over `("600", 0)`, `(700.9, 700)`, `(None, 0)`, `(True, 0)`, `(False, 0)`, `(42, 42)`. Pins `_as_int`. Worth testing the function directly despite the leading underscore.
4. A path that does not exist — `latest_usage("nope.jsonl")` returns `None` and raises nothing. Pins the `OSError` guard. **This is the one that protects a live session**: if a hook throws here, the session breaks.

**Deduplication**

5. `duplicates.jsonl` — the surviving record for each `requestId` is the *last* one written (check `timestamp` ends `...02.000Z` and `...12.000Z`), while the *order* follows first appearance. Pins the dict-assignment trick in `read_usage_series`.
6. Two entries with no `requestId` and different usage are kept as two records, not collapsed into one. Pins the orphan-key branch.

**Jump statistic**

7. `largest_jump` on `simple.jsonl` is 3050, on `duplicates.jsonl` is 600.
8. `largest_jump` ignores decreases — build a series by hand with a drop in the middle (the shape a compaction makes) and assert the drop is not returned as a huge negative or an absolute value.
9. `largest_jump([])` and a single-element series both return 0. Pins the `previous is None` guard.

**Deliberately not tested yet**

- Threshold and percentage maths, the 200K vs 1M window, and `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`. Those belong to milestone 2, and the code for them does not exist.
- Anything asserting against a real transcript. Fixtures only — real transcripts are not committed.

## Running

```
python -m pytest -q
```

Note `python`, not `python3`: on this Windows machine `python3` resolves to the Microsoft Store stub and fails.
