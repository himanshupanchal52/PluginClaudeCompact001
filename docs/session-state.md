# Session state

The live working record for compact-guard. This file is the thing that survives a compaction — if you are Claude and you have just been compacted or restarted, read this file before doing anything else.

Update it as work happens, not only when the context is about to fill.

**Last updated:** 2026-09-11

---

## Standing instructions from the author

Verbatim or near-verbatim, so nothing is lost to paraphrase in a summary.

- "The author reviews, understands, and owns every line."
- "Before writing any hook, explain when it fires, its input JSON, and its output JSON. Then wait for a go-ahead."
- "Work in small steps and small commits. Never write code the author can't explain back."
- "The author writes or co-writes the tests. Suggest test cases instead of silently writing them all."
- "The author is an experienced C#/.NET developer who is building up Python. Point out Python idioms that differ from C#."
- "Don't rely on memory for Claude Code behavior. Check the current docs."
- "keep records etc in md file or something. We are making something about compaction, and this chat will go long and will need compaction so be prepared."
- "I would suggest keep pushing on every change, so that we keep record of everything."
- "We will create copy branches, and then run tests on them, then merge to main. No UAT for this."

Hard constraints live in [CLAUDE.md](../CLAUDE.md#hard-constraints) and are not repeated here.

---

## Task queue

### Done

- Repo recon: remote is `himanshupanchal52/PluginClaudeCompact001`, single `Initial commit`, working tree was clean.
- Created branch `feature/project-scaffold`.
- Wrote `CLAUDE.md` (the brief, plus a new "Workflow and records" section covering branching, pushing, and this file).
- Rewrote `README.md`: what the plugin is, base layer vs. adaptive layer, constraints, milestone table, "built with Claude Code" statement.
- Created this file and `docs/decisions/TEMPLATE.md`.

- Merged `feature/project-scaffold` to `main` and pushed.
- **Milestone 1, part 1: transcript inspected.** Used this project's own session transcript (personal, safe). Findings written up in [transcript-format.md](transcript-format.md).

- **Author's three design decisions taken** (all as recommended): context = prompt + `output_tokens`; dedupe by `requestId`; model the result as a frozen dataclass.
- **Parser written**: `compact_guard/usage.py` with `ContextUsage`, `iter_entries`, `usage_from_entry`, `read_usage_series`, `latest_usage`, `largest_jump`.
- **Five fixtures built** (all synthetic): `simple`, `duplicates`, `sidechain`, `malformed`, `empty`. Expected values worked out and verified in [../tests/SUGGESTED_CASES.md](../tests/SUGGESTED_CASES.md).
- **Behaviour verified** by a throwaway stdlib script — every published expected value confirmed, including coercion, missing-file, dedupe ordering, and drop-handling in `largest_jump`.
- **Verified against the real transcript**: 45 deduped requests, latest context 104,796 tokens (52.4% of a 200K window), largest jump 5,203.

### In progress

- **Milestone 1, part 3: the tests.** Two worked examples exist in `tests/test_usage.py`; the remaining 9 cases are specified in `tests/SUGGESTED_CASES.md` for the author to write.
- **Blocked:** `pytest` is not installed on this machine (`python -m pytest` → no module). Needs the author's call on install method (venv vs. global).

### Next
- Decide the state file location: gitignored `.compact-guard/` in the project vs. the session `scratchpad_dir` from hook input.
- Confirm from the live hooks doc whether to use `PostToolUse` or `PostToolBatch`, and the exact name of the tool-output field on that input. (Milestone 2.)

---

## Key findings

Facts established, so they are not re-derived after a compaction.

- **Repo:** `T:\dBackupOne\GithubContributions\CompactGuard\PluginClaudeCompact001`, remote `origin` → `https://github.com/himanshupanchal52/PluginClaudeCompact001.git`, default branch `main`.
- **The Bash tool here mangles quoted heredocs** on multi-line content — the shell wrapper breaks on apostrophes inside them. Use the Write tool for anything longer than a couple of lines.
- No Python code exists yet. `.gitignore` is the standard GitHub Python template.
- **Transcript format confirmed against a real file** — see [transcript-format.md](transcript-format.md). The headlines: usage lives at `message.usage` on `type: "assistant"` only; `input_tokens` alone reads as **2** because of prompt caching, so the three input fields must be summed; entries are duplicated 2–3x per `requestId`; `message.context_management` is `null` and unusable; `isSidechain` must be filtered.
- **Interpreter on this machine:** `python` and `py` both give 3.10.9; `python3` hits the Microsoft Store stub and fails.

---

## Open questions

Decisions not yet made. Each needs the author's call, not mine.

1. **State file location** — project-local `.compact-guard/` (visible, greppable, survives across sessions, needs a gitignore entry) vs. `scratchpad_dir` (isolated, no repo pollution, but per-session and easy to lose).
2. **`PostToolUse` vs. `PostToolBatch`** — the batch variant fires once per batch rather than once per tool, which reduces state-file write races. Needs confirming against the current hooks doc.
3. **Plugin name.** "compact-guard" is a working name; not checked for collisions in the plugin ecosystem.

---

## Decision records

Written by the author, in their own words. Index them here as they land.

- _(none yet)_
