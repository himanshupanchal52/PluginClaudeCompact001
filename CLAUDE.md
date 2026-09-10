# CLAUDE.md: compact-guard (working name)

Project brief for Claude Code. Read this at the start of every session.

## What we're building

A Claude Code plugin that helps the agent keep its working state through context compaction.

Tiered context warnings and save/restore around compaction already exist in several plugins (for example context-sentinel, compact-ops, and GSD's context monitor). Study them, and don't claim those parts as new.

This project's angle is **adaptive**: it tracks whether each warning actually landed before compaction and tunes itself. That covers the tier thresholds, a predictive trigger based on the largest per-step context jump, and escalation to journal mode after repeated compactions in one session. The MVP rebuilds the common base first as a learning exercise; the adaptive layer is the differentiator.

## Working agreement (most important section)

- The author reviews, understands, and owns every line. The project is built with Claude Code, and the README says so.
- Before writing any hook, explain when it fires, its input JSON, and its output JSON. Then wait for a go-ahead.
- Work in small steps and small commits. Never write code the author can't explain back.
- The author writes or co-writes the tests. Suggest test cases instead of silently writing them all.
- The author is an experienced C#/.NET developer who is building up Python. Point out Python idioms that differ from C#.
- Don't rely on memory for Claude Code behavior. Check the current docs:
  - Hooks: https://code.claude.com/docs/en/hooks
  - Plugins: https://code.claude.com/docs/en/plugins
  - Marketplaces: https://code.claude.com/docs/en/plugin-marketplaces

## Workflow and records

This project is about surviving compaction, and its own sessions are long enough to compact. So the repo keeps its own durable record on disk, and we dogfood the pattern we are building.

- **Branch per unit of work.** Never commit directly to `main`. Create `feature/<slug>` (or `fix/<slug>`, `docs/<slug>`), work there, run the tests on that branch, then merge to `main`. No UAT stage.
- **Push every change.** Every commit is pushed to `origin` as it is made, so the remote is the running history even if a session is lost.
- **Small commits with real messages.** One logical change per commit.
- **`docs/session-state.md` is the live working record.** It holds the task queue (done / in progress / next), the author's standing instructions verbatim, and key findings and decisions. Update it as work happens, not only before a compaction. On resuming after a compaction, read it first.
- **`docs/decisions/` holds the decision records**, written by the author in their own words: context, decision, alternatives rejected. Template in `docs/decisions/TEMPLATE.md`.

## Hard constraints

- Use Python 3 with the standard library only. No network calls; nothing leaves the machine.
- Fail open: if a hook errors, the session must continue normally.
- Never block compaction. PreCompact can block it, and an always-blocking hook has left other people's sessions stuck at the context limit.
- Windows is the main dev platform, but the plugin must also work on macOS and Linux. Watch the interpreter name: usually `python`/`py` on Windows, `python3` elsewhere.
- Use exec form (`command` + `args`) with `${CLAUDE_PLUGIN_ROOT}` paths.
- Hook output, including additionalContext, is capped at 10,000 characters.
- Test fixtures must come from personal projects or be synthetic. Never commit transcripts from work sessions.

## MVP architecture

1. **Measure** (PostToolUse or PostToolBatch)
   - Read token usage from the latest assistant entry in `transcript_path`.
   - Measure against the actual auto-compact point, not 100%. That point moves with `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` / `CLAUDE_CODE_AUTO_COMPACT_WINDOW` and with window size (200K vs 1M).
   - The transcript is written asynchronously and can lag. Add a rough estimate for the tool output that just came back, and confirm that input field's name in the docs.

2. **Warn** (same hook)
   - At configurable tiers (default 75% and 90%), return `hookSpecificOutput.additionalContext`.
   - Each tier fires once per compaction cycle.
   - Phrase the warning as facts, not system-style commands, which can trip Claude's prompt-injection defenses. Example:
     > Context is at 78% of the auto-compact point. Project convention: before compaction, record the task queue and the user's instructions in the state file.

3. **Snapshot** (PreCompact, no model involved)
   - Extract the latest todo list, recent user instructions (verbatim), and files touched.
   - Write them to the state file. This covers the cases where a warning tier was skipped.

4. **Restore** (SessionStart, matcher `compact`)
   - Inject the short queue section itself as additionalContext, plus a pointer to the full state file.
   - Don't rely on a bare "go read the file" pointer; Claude follows those unreliably.

5. **Count** (PostCompact)
   - Increment a per-session compaction counter stored under `${CLAUDE_PLUGIN_DATA}`.

## State file (draft)

- **Location:** undecided. Choose between a gitignored `.compact-guard/` folder in the project and the session's `scratchpad_dir` from the hook input.
- **Queue:** done / in progress / next.
- **User instructions and constraints:** verbatim.
- **Key findings:** file paths, decisions, approaches already ruled out.

## v1 (after MVP)

- **Predictive trigger:** fire when remaining headroom drops below about 2x the largest single-step context jump seen this session.
- **Journal mode:** after N compactions in one session (configurable), switch guidance so findings are logged as they happen.
- **Local self-tuning:** record whether each warning landed before compaction, then adjust the tiers per user. All stats stay local.
- **Plugin options** (`user_config`) for the tiers and N.
- **Optional status-line bridge:** the status line receives the native `context_window.used_percentage`. Writing it to a file could give hooks the exact number.

## Testing

- **Unit tests (pytest):** usage parsing, threshold math, tier state, and the predictive trigger. Use `parametrize` for edge cases: missing fields, empty transcript, 1M window, overridden compact point.
- **Contract tests:** run each hook script as a real subprocess, pipe fixture JSON into stdin, and assert on stdout JSON and the exit code. This is the end-to-end test for a hook.
- **Failure tests:** feed malformed input and a missing transcript. The hook must exit cleanly and never break the session.
- **CI:** GitHub Actions running pytest on Windows, macOS, and Linux.
- **Manual end-to-end:** a real session plus `/compact`, following a written checklist in `docs/manual-test.md`.
- No Playwright; there is no browser UI in this project.

## Learning goals

The author must be able to explain the design without notes. For every milestone:

1. Explain the concept and the options first, then ask the author to choose before writing code.
2. After the code, the author writes a short decision record in `docs/decisions/` in their own words: the context, the decision, and the alternatives rejected.
3. End the milestone by quizzing the author with 3-5 "why" questions, and correct any gaps.

Concepts to make sure the author understands, in their words:

- Each hook is a fresh process, so no state survives in memory. State lives on disk, as with serverless functions.
- Parallel hooks can race on the state file. This calls for atomic writes (temp file plus rename), and it's a reason to prefer PostToolBatch over PostToolUse.
- The transcript lags, which means a stale read. Compensate with an estimate plus a safety margin.
- Fail-open here versus fail-closed in a security gate.
- Hysteresis, so a tier doesn't fire over and over around a threshold.
- Layered fallbacks: the model-written checkpoint first, then the deterministic snapshot.
- Defensive parsing, because the hook JSON schema can change between Claude Code versions.
- Least privilege and prompt-injection-aware wording.

## Milestones

1. Inspect a real transcript from a personal project and confirm the usage fields. Write the parser and its unit tests against fixtures.
2. Build measure plus tiered warnings.
3. Build snapshot plus restore. Test instantly with a manual `/compact`.
4. Package as a plugin, with this repo as its own marketplace. The README states exactly what the plugin reads and writes, and where.
5. Add the v1 features, check on a second OS, and record a demo GIF.
