# Claude AFK — Research

Investigating what it would take to let Claude Code work unattended on a
substantial coding task for a long period — through context exhaustion,
usage-limit pauses, crashes, and other interruptions — safely and
economically. This is **research, validation, and a small prototype**; no
implementation of "Claude AFK" itself happens here yet.

**Status:** complete through stage 2. Stage 1 (research) and stage 2
(validation + prototype + implementation-ready spec) are both done, with
an evidenced first pass on everything requested:

- All research (`autonomous-loop`, `overnight-protocol`, native Claude Code
  capabilities) and analysis (comparison, permission model, economics,
  local vs. remote) — see `research/` and `analysis/`.
- The scheduled `RemoteTrigger` continuation was **empirically fired and
  validated live** (clone/read/write/commit/push all PASS) rather than
  assumed — see `validation/remote-trigger-test.md`.
- A small deterministic **prototype** (`prototype/`) tests the actual
  mechanics — persistent state, stop-and-save, interruption classification,
  retry/backoff, crash recovery, safety limits, cost-awareness — entirely
  offline, at zero real Claude usage. 8/8 scenarios pass, and it caught two
  real design bugs before any real implementation.
- **`planning/v1-spec.md`** is the implementation-ready spec and the
  primary planning document now (supersedes the earlier
  `planning/draft-claude-afk-plan.md`, kept for history).

**Bottom line recommendation** (full reasoning in `planning/v1-spec.md`):
don't build custom Claude AFK software. Compose `claude -p "/goal
<condition>"` + `RemoteTrigger` Routines + `auto` permission mode + a
single git-committed state file — all native, all validated tonight.

A short list of low-priority remaining items (not blocking, not required)
is in `STATE.md`'s "Remaining" section.

## Structure

- `research/` — what the existing projects and current Claude Code actually do
  - `autonomous-loop.md` — `asiridalugoda/autonomous-loop`
  - `overnight-protocol.md` — `robogears/overnight-protocol` (incl. its
    permission/deny-rule model)
  - `claude-code-capabilities.md` — native Claude Code mechanisms relevant
    to unattended operation, including `/goal` and scheduling options
- `analysis/` — comparisons and cross-cutting analysis
  - `comparison.md`, `permission-model.md`, `economics.md`,
    `local-vs-remote.md`
- `prototype/` — small offline mechanics simulator (not production code —
  see `prototype/README.md`)
- `validation/` — empirical test artifacts (e.g. the live `RemoteTrigger` test)
- `planning/`
  - `v1-spec.md` — **the implementation-ready spec** (start here for "what
    should V1 be")
  - `draft-claude-afk-plan.md` — stage-1 draft, superseded by `v1-spec.md`
  - `open-questions.md` — remaining low-priority uncertainties

## Ideal eventual workflow (the target we're evaluating against)

give Claude a substantial objective → autonomous work → persistent state →
verify progress → temporarily stop when necessary → recover later → continue
from durable state → finish or safely stop when genuinely blocked → leave a
useful report.
