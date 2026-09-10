# Claude AFK — V1 Spec (implementation-ready)

Grounded in `research/*.md`, `analysis/*.md`, tonight's empirical
`RemoteTrigger` validation (`validation/remote-trigger-test.md`), and the
`prototype/` mechanics simulator (8/8 scenarios passing). This is a spec
for what to build, not a plan to research further — where something is
still genuinely uncertain, that's stated explicitly rather than guessed.

## Re-evaluating `autonomous-loop` and `overnight-protocol` (refined, not repeated)

No change to the core verdicts in `analysis/comparison.md`; two refinements
from tonight's deeper validation work:

- **`autonomous-loop`'s maker≠checker verification is worth less custom
  work than it first appeared**, now that `/goal`'s built-in independent
  evaluator is known (`research/claude-code-capabilities.md`). For a
  hobbyist-scale project, `/goal`'s lightweight per-turn evaluation
  (no tool use, judges the transcript) plausibly covers enough of the
  "don't let the same model grade its own work" benefit that
  `autonomous-loop`'s full checker-panel/red-team apparatus is *not*
  worth adopting even for the single-project case it was originally
  being considered for — it remains valuable only at real multi-goal,
  higher-stakes scale (the "many independent goals" case the skill itself
  gates it behind). **Verdict unchanged from comparison.md, now with
  stronger evidence.**
- **`overnight-protocol`'s permission model is narrower and cleaner than
  first credited, but its core value — a small deny-rule set — is now
  redundant with auto mode's own built-in blocks.** `analysis/permission-model.md`'s
  full docs pass shows `auto` mode already blocks force-push and
  work-discarding git commands by default, without any project-specific
  configuration. `overnight-protocol`'s 3-rule deny list is still worth
  keeping as defense-in-depth (a `deny` rule is unconditional; the
  classifier is a judgment call), but it is not filling a gap auto mode
  leaves open the way it appeared to before this validation pass.

Neither project should be adopted wholesale, modified, or combined — this
matches `analysis/comparison.md`'s original position and nothing found
tonight changes it. `overnight-protocol` remains a poor fit (macOS-only,
heavy local daemon architecture) and `autonomous-loop`'s spine-file idea
remains the more portable, adoptable-as-a-pattern piece.

## Recommended architecture

**Fresh-session-per-continuation, not stay-alive-and-sleep.** Confirmed
twice now: once by design (this project's own `RemoteTrigger` routine) and
once by tonight's official-docs permission pass (headless `-p` runs cannot
stall on a permission block the way an interactive session can — see
`analysis/permission-model.md`). A V1 should never keep one session alive
across a usage-limit wait; it should exit cleanly and let a scheduler start
a new one.

Composition, in order of what does the work:

1. **`claude -p "/goal <verifiable condition, with a turn/time bound>"`**
   for the actual "keep working without re-prompting" loop within one
   fired session — replacing a hand-written loop-forever prompt. Run in
   `auto` permission mode.
2. **A single git-committed state file** (this project's own `STATE.md`
   style — or, only once a task is genuinely large enough to need
   dependency-ordered multi-goal tracking, `autonomous-loop`'s
   `GOALS`/`BOARD`/`handover.md` split) as the sole source of resumable
   truth, read first by every fired session.
3. **`RemoteTrigger` (Routines)** as the default scheduler for durable,
   machine-independent continuation — empirically validated tonight
   end-to-end (clone, read, write, commit, push, all PASS, no permission
   stalls, 25s/10 turns). **Desktop scheduled tasks** as the alternative
   only when a task genuinely needs this user's local WSL/Windows
   environment (see Local vs. remote below) — not the default, because it
   requires the machine to stay awake and the Desktop app to stay open.
4. **A narrow `permissions.deny`** (`git push --force:*`, `git push -f:*`,
   `git clean:*`, `git reset --hard:*`) as defense-in-depth alongside
   `auto` mode's own built-in blocks — cheap, unconditional, not reliant on
   the classifier's judgment.

## Persistent state model

One file (`STATE.md` or equivalent), git-committed, containing at minimum:
objective, current status, completed work, remaining work, the single best
next action, and important discoveries/decisions/failures — this project's
own `STATE.md` from tonight's stage 1 is a working example of the format,
already validated as readable by a fresh `RemoteTrigger`-fired session.

**Concrete schema lesson from the prototype** (`prototype/README.md`,
"Bugs this prototype already caught"): whatever tracks *session count or
attempt count* must be persisted at the **start** of a unit of work, not
only at its end, or a crash mid-session corrupts the count for the next
session. A status field should have a small, deliberately restrictive set
of valid combinations, so that "`RUNNING` with no pause reason, but
evidence of prior work" is unambiguously recognizable as an unclean
interruption on load — this one invariant is what let the prototype's
crash-recovery scenario detect and log a crash automatically instead of
silently continuing or corrupting state.

## Stop-and-save protocol

Already specified and twice validated this session (the routine's own
prompt, and the user's own repeated instructions across both stages of
this project): finish the smallest safe atomic step, write objective +
completed + current state + remaining + single best next action +
findings, verify the save against actual repo state, commit, push, stop.
No further design work needed here — it already works; codify it as a
short, literal checklist in whatever prompt or `loop.md`-style file drives
a real fired session, rather than re-deriving it per task.

## Interruption state machine

Directly modeled and tested in `prototype/afk_sim.py`. Five terminal/semi-
terminal states, each with a distinct resume policy — this distinction
(not lumping every interruption together) is the actual design contribution:

| State | Trigger | Resume policy |
|---|---|---|
| `COMPLETED` | Goal condition met | None needed — a later fired session should no-op |
| `PAUSED` (`usage_limit` / `context_overflow`) | Transient, expected, capacity-driven | **Auto-resume** — a scheduled continuation is exactly the right response |
| `BLOCKED` (`permission_denied`) | Classifier/deny-rule refusal | **No auto-resume** — requires a human to unblock; a fresh session should no-op, not retry around it |
| `STOPPED` (`repeated_failure` / `cost_budget_exceeded` / `max_total_attempts`) | A safety limit tripped | **No auto-resume** — same as `BLOCKED`: needs human review, not another scheduled attempt |
| (transient failure, not yet a state) | A single retryable error | Retry with backoff *within* the same session, up to a small cap, before it either succeeds or escalates to `STOPPED` |

`/goal`'s own native error classification (`research/claude-code-capabilities.md`)
already implements roughly this split for real Claude sessions: transient
failures (rate limits) leave a goal active; credit exhaustion/context
overflow/auth/model-unavailable clear it for an explicit restart. A V1
should treat `/goal`'s hard-clear cases as this table's `PAUSED` (for
capacity-driven ones) or as a signal to update the state file and let the
scheduler's next fire re-issue `/goal` — not as `STOPPED`, which should be
reserved for genuine safety-limit trips a human should look at.

## Permission strategy

`auto` mode, headless (`-p`), per `analysis/permission-model.md`'s
strongest finding: this combination structurally cannot deadlock on a
permission prompt, because a non-interactive run with no prompt tool
simply treats a block as "can't do that," not as a stall. Add the narrow
`permissions.deny` set above as unconditional defense-in-depth. Do **not**
use `bypassPermissions`/`--dangerously-skip-permissions` — it buys nothing
over `auto` mode for this use case (both need the same deny-rule
defense-in-depth; `auto` mode additionally blocks a long list of
dangerous-by-default categories that `bypassPermissions` does not) and its
own warning is explicit that it offers no protection against unintended
actions. **Open**: whether `dontAsk` mode (fully deterministic allow-list,
no classifier judgment calls at all) is worth trading `auto` mode's
broader default protections for, in exchange for zero judgment-call
variance — genuinely unresolved, low-cost to decide later by trying both
on a real small task and comparing how often each stalls or misbehaves.

## Scheduler / continuation mechanism

`RemoteTrigger` one-shot per continuation (not recurring — a fresh
one-shot re-armed by the *previous* fired session's own state update, or
by the user, mirrors this project's own two-stage pattern tonight: each
session that stops due to capacity should, as its last action, either
schedule its own one-shot follow-up or leave clear state for a human to
do so). Minimum interval is 1 hour for *recurring* Routines but does not
apply to one-shots. Validated empirically tonight — see
`validation/remote-trigger-test.md`.

**A fired session updating its own schedule** is a real capability gap
worth naming: nothing tested tonight confirms whether a `RemoteTrigger`
Routine can safely call `RemoteTrigger`/`/schedule` *on itself* mid-run to
arrange its own next continuation (as opposed to a human or a separate
session doing it, as happened both times tonight). Treat this as **unverified**
until tried — the safer default for V1 is that a human (or the interactive
session that kicks off a work item) creates the *next* one-shot after
reviewing what a fired session left in its state file, not that fired
sessions self-schedule unattended indefinitely. This is a deliberate
scope boundary, not an oversight: full self-rescheduling is the kind of
"loop forever" capability `overnight-protocol` provides and this project's
own economics analysis flags as the highest-risk pattern without a
verification gate.

## Local vs. remote execution

Default: remote (`RemoteTrigger`/cloud Routines) for anything that doesn't
need this user's actual local files/tools. Use **Desktop scheduled tasks**
only when a task specifically needs local WSL/Windows access (this user's
AutoHotkey/Rainmeter files, `rtk`-wrapped tooling) — and even then, note
the unresolved practical question from `analysis/local-vs-remote.md`:
whether Desktop's Bash tool on this Windows/WSL2 machine actually shells
into WSL or native Windows — untested, would need a real (cheap, one-off)
check before relying on it for anything WSL-specific.

## Usage/cost strategy

No custom usage-monitoring daemon (rejecting `overnight-protocol`'s
approach, per `analysis/economics.md`) — the fresh-session-per-continuation
architecture sidesteps the problem a local usage daemon solves. Cost
control instead comes from: (a) `/goal`'s own turn/time bound written into
the condition text, (b) a state-file-tracked attempt/cost counter with an
explicit ceiling (modeled and tested in `prototype/afk_sim.py`'s
`cost_budget_exceeded` scenario) that trips a `STOPPED` state a human must
clear, and (c) headless `--output-format json`'s per-invocation
`total_cost_usd` field (`research/claude-code-capabilities.md`) logged to
the state/report file after every fired session, giving a real (if
client-side-estimated) running total without any extra infrastructure.

## Git/checkpoint strategy

Commit after every meaningful unit of work, not only at session end —
already this project's own practice tonight and validated by the
prototype's finding that per-step durable checkpointing (not just
per-session) is what makes crash recovery actually work. Push after every
commit (a remote with history is the real backup). No dedicated branch
strategy is prescribed here — `overnight-protocol`'s "never touch main,
always a dated branch" convention is reasonable and cheap to adopt if a
real coding task follows, but committing straight to `main` (as tonight's
research work and validation test both did) is acceptable for lower-stakes
work with a human reviewing the repository the next day.

## Logging / reporting

One state file is the primary log (per Persistent state model above); no
separate structured logging system is needed for a hobbyist-scale V1. A
fired session should end by making sure the state file *and* the repo's
top-level `README.md` both say, in plain language: what was done, what's
left, and what the next sensible step is — the same requirement this
project's own instructions have imposed on every session tonight, and
which worked.

## Safety limits

Three independent trip-wires, all modeled in the prototype: a max-retry
cap per step (transient-failure escalation → `STOPPED`), a max-total-attempts
cap across the whole run, and a cost/usage ceiling. All three produce a
`STOPPED` state requiring human review — never an automatic retry past a
safety limit, and never a further self-scheduled continuation once
`STOPPED` (mirrors the `BLOCKED` policy above). This is deliberately
conservative: the goal, per this project's own brief, was never "eliminate
all prompts at any cost."

## Testing strategy

For the orchestration logic itself (state transitions, stop-and-save,
crash recovery, cost ceilings): keep using the `prototype/` pattern —
deterministic, fixture-driven, zero real Claude usage, fast enough to run
on every change. This is the cheap, repeatable layer. For the actual
Claude-driven work (does `/goal` correctly judge a real completion
condition, does a real fired Routine actually do useful coding work end to
end): a small number of **targeted, deliberately real** empirical tests —
the same philosophy as tonight's one live `RemoteTrigger` run — spent only
when a specific decision hinges on the result, never as routine coverage.

## Final recommendation

**If implementing Claude AFK tomorrow: don't build a framework. Compose
four things Claude Code already has.**

- **Foundation**: `claude -p "/goal <condition>"` for the work loop,
  `RemoteTrigger` Routines for durable continuation, `auto` permission
  mode, and a single git-committed state file. All four are native,
  already validated (either empirically tonight or via authoritative
  current docs), and require no new software.
- **Do not build**: a usage-monitoring daemon, a multi-agent
  coordinator/roster, a permission-bypass wrapper, or anything resembling
  `overnight-protocol`'s local hook/daemon architecture. None of these
  problems exist in the fresh-session-per-continuation design.
- **What to build ourselves** (small, and only this): a short, reusable
  state-file template/convention (the `STATE.md` format already in this
  repo is sufficient — copy it, don't reinvent it) and, if a real coding
  task ever needs multi-goal tracking, `autonomous-loop`'s
  `GOALS`/`BOARD`/`handover.md` split adopted as-is rather than redesigned.
- **Smallest useful V1**: take one real, small, bounded coding objective
  with a genuinely verifiable completion condition. Write a `STATE.md`.
  Kick it off interactively with `claude -p "/goal <condition, with a
  turn/time bound>"` in `auto` mode. When it stalls or completes, check the
  state file and the `/goal` status; if it needs to continue later, create
  one `RemoteTrigger` one-shot with a state-first idempotent prompt (the
  same shape this project's own routine used tonight). No prototype
  scaffolding, no custom permission tooling — the `prototype/` in this repo
  existed only to de-risk the *design*, not to become part of the product.
- **Future feature, not V1**: fired sessions self-scheduling their own
  next continuation (currently unverified and deliberately out of scope);
  multi-goal spine files for anything beyond a single bounded objective;
  any form of the audit-and-improve-forever ladder `overnight-protocol`
  uses, which this project's own economics analysis flags as the
  single biggest identified risk of wasted usage without a verification
  gate — worth revisiting only if `/goal`-based verification proves
  insufficient on a real task.

It is an acceptable and, on this evidence, the *correct* conclusion:
**don't build Claude AFK as custom software. Use `/goal` + Routines +
`auto` mode + a state file, and only add machinery later in response to a
specific, observed failure a real task actually hits.**
