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

### In progress

- Nothing. Awaiting go-ahead on milestone 1.

### Next

- **Milestone 1.** Find a transcript from a personal project (never a work session), inspect it, and confirm the real usage field names. Then write the parser plus unit tests against fixtures.
  - Blocked on: locating a suitable transcript. Claude Code stores them under `~/.claude/projects/<slugged-path>/*.jsonl`.
- Decide the state file location: gitignored `.compact-guard/` in the project vs. the session `scratchpad_dir` from hook input.
- Confirm from the live hooks doc whether to use `PostToolUse` or `PostToolBatch`, and the exact name of the tool-output field on that input.

---

## Key findings

Facts established, so they are not re-derived after a compaction.

- **Repo:** `T:\dBackupOne\GithubContributions\CompactGuard\PluginClaudeCompact001`, remote `origin` → `https://github.com/himanshupanchal52/PluginClaudeCompact001.git`, default branch `main`.
- **The Bash tool here mangles quoted heredocs** on multi-line content — the shell wrapper breaks on apostrophes inside them. Use the Write tool for anything longer than a couple of lines.
- No Python code exists yet. `.gitignore` is the standard GitHub Python template.

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
