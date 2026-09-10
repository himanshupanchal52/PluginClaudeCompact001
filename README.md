# compact-guard

A Claude Code plugin that helps the agent keep its working state through context compaction.

> **Status: pre-MVP.** Nothing is implemented yet. This repo currently holds the project brief, the working record, and the decision log. See [Milestones](#milestones) for where the work is.

## The problem

When a Claude Code session fills its context window, the conversation is compacted into a summary. Useful things get lost in that summary: the task queue, the constraints you stated three hours ago, the approaches already tried and ruled out. You then spend the next few turns re-explaining yourself.

## What this plugin does

Two layers.

**The base layer** — warn as the context fills, snapshot the working state deterministically just before compaction, and re-inject the queue on the other side. This part is not new. Several plugins already do it (context-sentinel, compact-ops, GSD's context monitor), and this project rebuilds it deliberately, as a learning exercise.

**The adaptive layer** — this is the actual contribution. compact-guard tracks whether each warning actually landed before compaction happened, and tunes itself from that:

- **Self-tuning tiers.** If the 75% warning keeps arriving too late to be acted on, the tier moves down. All stats stay on your machine.
- **Predictive trigger.** A single tool call can add a large chunk of context at once. Rather than waiting for a fixed percentage, fire when the remaining headroom drops below roughly twice the largest single-step jump seen this session.
- **Journal mode.** After repeated compactions in one session, escalate: switch the guidance so findings get logged as they happen rather than only at the threshold.

## Design constraints

- **Python 3, standard library only.** No dependencies to install.
- **No network calls. Nothing leaves your machine.** All state and all tuning statistics are local files.
- **Fails open.** If a hook errors, the session continues normally.
- **Never blocks compaction.** A `PreCompact` hook is technically able to block compaction; an always-blocking hook can strand a session at the context limit. This one does not block, ever.
- **Cross-platform.** Windows is the main development platform; macOS and Linux are supported and covered in CI.

## What it reads and what it writes

To be documented precisely before the plugin is packaged (milestone 4), and kept accurate after that. In outline: it reads the session transcript that Claude Code already passes to hooks, and writes a state file plus local tuning statistics. Exact paths land here once they are decided.

## Milestones

| # | Milestone | State |
|---|-----------|-------|
| 1 | Confirm the transcript usage fields; write the parser and its unit tests | Not started |
| 2 | Measure plus tiered warnings | Not started |
| 3 | Snapshot plus restore | Not started |
| 4 | Package as a plugin, with this repo as its own marketplace | Not started |
| 5 | The adaptive v1 features, second-OS check, demo | Not started |

## Repository layout

| Path | What it is |
|------|------------|
| [CLAUDE.md](CLAUDE.md) | The project brief and working agreement, read by Claude Code at the start of every session |
| [docs/session-state.md](docs/session-state.md) | The live working record: task queue, standing instructions, key findings |
| [docs/decisions/](docs/decisions/) | Decision records — the context, the decision, the alternatives rejected |

## How this project is built

This project is built with [Claude Code](https://claude.com/claude-code), and the author reviews, understands, and owns every line of it. Claude explains a design and its alternatives first; the author chooses, writes the decision record in their own words, and co-writes the tests. That constraint is the point of the project as much as the plugin is.

## Development workflow

Work happens on a branch — `feature/<slug>`, `fix/<slug>`, or `docs/<slug>` — never directly on `main`. Tests run on the branch, then it merges to `main`. Every commit is pushed as it is made, so the remote is the running record.

## License

MIT. See [LICENSE](LICENSE).
