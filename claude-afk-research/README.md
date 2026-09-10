# Claude AFK — Research

Investigating what it would take to let Claude Code work unattended on a
substantial coding task for a long period — through context exhaustion,
usage-limit pauses, crashes, and other interruptions — safely and
economically. This is **research only**; no implementation of "Claude AFK"
itself happens here yet.

**Status:** in progress, overnight run started 2026-09-11. See
[`STATE.md`](STATE.md) for exactly what's done vs. outstanding, and the
current scheduled-continuation plan.

## Structure

- `research/` — what the existing projects and current Claude Code actually do
  - `autonomous-loop.md` — `asiridalugoda/autonomous-loop`
  - `overnight-protocol.md` — `robogears/overnight-protocol` (incl. its
    permission/deny-rule model)
  - `claude-code-capabilities.md` — native Claude Code mechanisms relevant
    to unattended operation
- `analysis/` — comparisons and cross-cutting analysis
  - `comparison.md`, `permission-model.md`, `economics.md`,
    `local-vs-remote.md`
- `planning/` — where this might go
  - `draft-claude-afk-plan.md`, `open-questions.md`

## Ideal eventual workflow (the target we're evaluating against)

give Claude a substantial objective → autonomous work → persistent state →
verify progress → temporarily stop when necessary → recover later → continue
from durable state → finish or safely stop when genuinely blocked → leave a
useful report.
