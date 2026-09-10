# `asiridalugoda/autonomous-loop`

Status: core investigation done from actual repo content (SKILL.md read in
full; `references/*.md` — spine-templates, relay-template, relay-scenarios,
multi-agent-coordinator, cross-machine-handover-design — not yet read in
detail, listed under Open below). v1.4.2, Apache-2.0.

## What it actually is

A Claude Code **skill** (prompt/methodology, not software) implementing
Addy Osmani's "loop engineering": externalize all state to files (the
**spine**) so any fresh session/cron run resumes with zero lost context, and
split the agent that writes work from the agent that checks it.

## Workflow shape

File-based **spine**, ideally under `docs/loop/`:

| File | Holds |
|---|---|
| `LOOP.md` | Runbook: roles, iteration sequence, guardrails, stop conditions |
| `GOALS.md` | Dependency-ordered goals, each with a machine-checkable acceptance criterion (the AC *is* the test) |
| `BOARD.md` | Live status per goal: open/in-progress/done/blocked |
| `handover.md` | 2-3 line plain-English summary per merged goal + current failure/next hypothesis |
| `audits/<date>-<goal>.md` | Evidence for security-critical changes (written only when needed) |
| `EXPERIMENTS.md` | Keep-or-revert ledger for optimization goals (written only when needed) |

Bootstrap once (learn project → write GOALS/BOARD/handover/LOOP → commit),
then iterate: load spine → pick next unblocked goal → TDD red → implement →
independent checker review → independent verifier confirms AC → commit +
update handover/BOARD → repeat. **Maker ≠ checker is structurally
enforced** (a separate role/subagent always grades), not just a convention.

## State persistence / resume

Entirely git-committed plain files. A fresh session's *entire* context need
is: read project instructions → `handover.md` → `BOARD.md` → `GOALS.md`, in
that order. No daemon, no external usage-tracking file, no OS-level state —
resume is just "read four files and the git log."

## Context exhaustion / compaction

Treated as a non-event by design: "context compaction is fine... the run
pauses and resumes rather than dying." No special handling needed because
literally all working state already lives in the spine files on disk, not
in context.

## Usage/rate-limit exhaustion detection and resumption

Notably **no usage-monitoring mechanism of its own** (contrast with
`overnight-protocol`'s usage daemon) — it treats a 429/503/529/limit hit as
"just another interruption," to be resumed via a scheduler, not predicted
or metered in advance. Its explicit guidance on schedulers is the most
directly useful finding for this project:

> "Know your scheduler's durability. `CronCreate` / `ScheduleWakeup` are
> **session-only** (in-memory): they fire while a rate-limited session is
> still alive and idle, but they're lost if the session is *killed*. If a
> hard limit might kill the session, back the resume with a **durable**
> trigger — a cloud routine (`/schedule`), an external cron, or a human
> re-launch."

This is an independent confirmation of exactly what we found ourselves
tonight (see `claude-code-capabilities.md`): `CronCreate`/`ScheduleWakeup`
don't survive session death, `RemoteTrigger` cloud routines do. This
project's own resume prompt design principle — **state-first, idempotent**:
read spine + git/PR state, no-op if already done, resume remaining steps if
stalled — is exactly what we built into tonight's routine prompt.

## Crash/transient failure handling

429/503/529/overload/network blips → exponential backoff, retry, not abort.
An interruption explicitly does **not** burn a self-unblock attempt or
count toward the 3-strikes escalation counter (that's reserved for genuine
task failures). Resume is required to be **idempotent** — a half-done goal
is re-derived from spine + git state, never double-applied, because each
goal is gated by its own test.

## Git/checkpointing

Commit at every goal PASS; a goal in a worktree for isolation when
parallelized (the worktree *is* the revert mechanism for optimization
goals — keep-or-revert against a measured baseline). "Confirm the
irreversible" — push/merge/deploy/delete only when the user authorized
*that class* of action; building autonomously is not shipping autonomously.

## Testing/review/verification

Structurally separated roles: maker implements, an independent checker
panel reviews (code reviewer + security auditor + optionally test
engineer, scaled to risk), a red-team actively attacks security-critical
changes, and a **separate verifier** (not the maker) confirms the AC
against evidence before a goal counts as done. Reviewer *output* is treated
as untrusted data — a review with near-zero tool use or
"System:/MUST/run..."-shaped text is flagged as a likely prompt-injection
artifact and re-run.

## Continue/stop/retry/escalate decisions

- Failed goal → not a stop, write failure + hypothesis to `handover.md`,
  next pass retries with that context.
- Two failed passes building on the same broken attempt → rewind
  (`git reset` to last known-good), retry from a different angle rather
  than patching a doomed path.
- Three failed passes on the same goal → escalate to the user, mark
  blocked on `BOARD.md`, move to the next unblocked goal.
- Top-level stop = the project's actual definition of done; explicitly
  warns against chasing feature parity or inventing scope past it.

## Additional Claude work its orchestration creates

- A checker panel (1-3 extra subagent dispatches) per goal, scaled to risk
  — a single light reviewer for low-risk CRUD, full panel + red-team +
  audit artifact only for security-critical work. This scaling rule is
  explicitly there to avoid the "orchestration overhead that doesn't
  improve the result" trap: it does not pay the same review cost for every
  goal regardless of risk.
- A **separate verifier** re-checks the AC independently — genuine extra
  usage, but arguably the single highest-leverage cost in the whole
  design, since it's the actual error-correction mechanism (maker ≠
  checker is called "the core error-correction," non-negotiable).
- The **Managed Agents coordinator+roster** mode (persistent agents, up to
  25 concurrent threads) is meaningfully heavier — explicitly gated behind
  "only when the roster earns its overhead: many independent goals to
  parallelize... don't stand up a coordinator to check one CRUD change."
  For a hobbyist-scale project this mode is very likely **not worth it**.
- **Relay** (multi-machine handoff via GitHub issues + OS-level watchers on
  each node) is a substantial additional mechanism — a second, independent
  scheduler layer (`launchd`/`schtasks` on each machine) *and* a GitHub
  issue protocol, on top of whatever's already handling single-machine
  resume. Justified only when genuinely running across >1 machine; pure
  overhead otherwise.

## Where extra work looks justified vs. wasteful (assessment)

- **Justified:** goal-scaled checker panel; independent verifier;
  idempotent state-first resume prompts; rewind-before-escalate (cheap,
  avoids compounding a bad path).
- **Likely wasteful for a small personal project:** the full Managed
  Agents coordinator+roster machinery; Relay's dual OS-scheduler + GitHub
  issue protocol — both are explicitly self-gated by the skill itself as
  "only when it earns its overhead," which already matches the economics
  concern for a hobbyist-scale project like the eventual Claude AFK.

## Open (not yet read in detail)

- `references/spine-templates.md`, `references/multi-agent-coordinator.md`,
  `references/relay-template.md`, `references/relay-scenarios.md`,
  `docs/superpowers/specs/2026-08-10-cross-machine-handover-design.md` —
  the concrete fill-in templates and worked examples; useful mainly if a
  V1 actually adopts the spine-file convention, lower priority otherwise.
