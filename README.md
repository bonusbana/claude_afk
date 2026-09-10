# Claude AFK — Research

Investigating what it would take to let Claude Code work unattended on a
substantial coding task for a long period — through context exhaustion,
usage-limit pauses, crashes, and other interruptions — safely and
economically. This is **research only**; no implementation of "Claude AFK"
itself happens here yet.

**Status:** all 6 requested deliverables have a first complete pass —
research on both third-party projects plus native Claude Code capabilities,
the comparison/permission-model/economics/local-vs-remote analyses, and a
draft plan. What remains is depth on two flagged leads (`/goal`, Desktop
scheduled tasks — see `planning/open-questions.md`) that could still shift
the draft plan's recommendation, plus validating that the scheduled
overnight continuation actually worked end to end. See [`STATE.md`](STATE.md)
for the precise breakdown and the next best action.

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
