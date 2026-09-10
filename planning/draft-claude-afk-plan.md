# Draft Claude AFK Plan (DRAFT — not a commitment to build anything)

Grounded in `research/autonomous-loop.md`, `research/overnight-protocol.md`,
`research/claude-code-capabilities.md`, and `analysis/*.md`. This is a
starting point for a conversation, not a spec.

## Headline conclusion

**A custom system is probably not needed for a V1 — more strongly than
first thought.** Native Claude Code already provides the two hardest
pieces, both for free: a truly durable, session-independent continuation
mechanism (`RemoteTrigger` cloud routines / Desktop scheduled tasks), and
— discovered after the first pass of this plan — **`/goal`**, a native
condition-driven work loop with independent per-turn evaluation and
explicit, precise error classification (transient failures like rate
limits leave it running; credit exhaustion, context overflow, and a few
other hard cases cleanly clear it for an explicit restart). Composed
together (`claude -p "/goal <condition>"`, fired by a Routine or Desktop
task), this covers most of what a hand-written loop-prompt or
`autonomous-loop`'s bootstrap-and-iterate cycle does by hand, for a single
bounded objective. See `research/claude-code-capabilities.md`'s `/goal`
section for the detail. The one genuinely hard unsolved problem (proactive
usage-limit awareness *mid-session*, before an error forces the issue)
doesn't need solving for the "schedule a fresh session after reset"
strategy this project already used tonight — it only matters for the
alternative "keep one session alive and sleep through the reset" strategy,
which `overnight-protocol` uses and which brings its heaviest machinery
along with it.

## What should potentially be reused as-is

- **`RemoteTrigger` cloud routines** (or Desktop scheduled tasks, if local
  file access is needed — see `analysis/local-vs-remote.md`) for durable,
  session-independent continuation. Confirmed tonight: survives local
  machine sleep/reboot/shutdown/WSL state by construction (never touches
  the local machine), one API call to set up, GitHub-native. This replaces
  the entire daemon/hook/flag-file apparatus `overnight-protocol` builds to
  solve the same "come back later" problem locally.
- **`/goal`** for the actual "keep working without re-prompting" loop
  within a single fired session, in place of hand-written loop
  instructions — `claude -p "/goal <condition, with a turn/time bound>"`.
  Its independent per-turn evaluator and precise transient-vs-hard-failure
  classification (see `research/claude-code-capabilities.md`) are exactly
  the two things a hand-rolled prompt would otherwise have to specify in
  prose and hope is followed.
- **A small git-committed state file** (this project's own `STATE.md`
  tonight, or `autonomous-loop`'s slightly more structured
  `GOALS.md`/`BOARD.md`/`handover.md` split for a larger task) as the
  single source of resumable truth. "The model forgets, the repo doesn't."
- **A minimal standing `permissions.deny`**: `Bash(git push --force:*)`,
  `Bash(git push -f:*)`, `Bash(git clean:*)` (maybe `git reset --hard:*`).
  Cheap, `overnight-protocol`-validated, and per
  `analysis/permission-model.md` worth adopting for this user's ordinary
  Claude Code usage regardless of AFK.
- **State-first, idempotent resume prompts**: check actual repo/git state
  before acting, no-op if already done, resume the remaining steps if
  stalled. Both `autonomous-loop` and tonight's own `RemoteTrigger` prompt
  independently converged on this; it's cheap insurance against duplicated
  work from an overlapping or re-fired trigger.

## What should potentially be adapted (not adopted wholesale)

- **`autonomous-loop`'s maker≠checker split** — valuable for a
  "substantial coding task" (the actual eventual AFK use case, vs.
  tonight's research task) where a wrong unverified change is costly. For
  a hobbyist-scale project, a *lightweight* version (one independent review
  pass before marking a goal done) likely captures most of the value
  without the full panel/red-team apparatus, which is itself flagged in
  `analysis/comparison.md` as more infrastructure than a small project
  needs.
- **`overnight-protocol`'s deny-rule recipe** — adapt the specific rules
  (already listed above) without adopting its delivery mechanism (project
  `.claude/settings.local.json`, added/removed at loop arm/wrap-up) unless
  a future design actually has an arm/disarm lifecycle to hook that into.
- **The spine-file *idea*, sized to the task** — a one-page `STATE.md` for
  a small/bounded task (what tonight used), the fuller
  `GOALS`/`BOARD`/`handover` split only once a task is genuinely large and
  multi-goal enough to need dependency ordering and a running narrative.
  Don't default to the heavier version.

## What should probably be left alone

- **`overnight-protocol`'s local daemon/hook/sleep architecture in full** —
  solves a real problem (usage-limit awareness without ending the session)
  but is macOS-native as shipped, meaningfully heavier than this user's
  stated preference for "understandable, maintainable solutions," and per
  `analysis/economics.md` carries a real risk of unverified self-generated
  work at scale. The scheduled-fresh-session strategy this project already
  uses sidesteps the problem it solves.
- **`autonomous-loop`'s Managed Agents coordinator+roster mode** — explicitly
  self-gated by its own authors as "only when the roster earns its
  overhead"; not warranted for a hobbyist-scale project.
- **`autonomous-loop`'s Relay (multi-machine) mode** — solves a problem
  (coordinating across >1 machine) this user hasn't described having.
- **Any unbounded self-generated-work mode** (`overnight-protocol`'s
  ladder) without a structural verifier gate — per `analysis/economics.md`
  this is the single biggest identified economic risk among everything
  investigated, and isn't worth the exposure for a personal project.

## Problems that remain unsolved by everything investigated

- **Proactive usage-limit awareness inside a single long session** — how
  would a session know it's *approaching* a limit before an error forces
  the issue, without `overnight-protocol`'s platform-specific daemon?
  Unresolved; only matters for the "stay alive and sleep" strategy, not
  the "schedule a fresh session" strategy this project used.
- **GitLab (or any non-GitHub host) support for `RemoteTrigger`** —
  apparently unsupported at the structured-source level; would need either
  staying on GitHub (what this project did) or a workaround (embedded
  token + plain `git clone` in Bash instead of the `sources` field —
  untested).
- **Windows/WSL-native equivalents for anything `overnight-protocol`
  solves that isn't replaced by `RemoteTrigger`** — e.g. if a future design
  ever does need the "stay alive and sleep" strategy locally (not
  recommended per above, but possible for a task unsuited to the cloud
  sandbox), the keep-awake/notification/credential-reading mechanisms
  would all need Windows/WSL2 equivalents from scratch.
- **How compaction interacts with a long cloud-routine run** — not yet
  observed; flagged in `planning/open-questions.md`.
- **End-to-end validation that `RemoteTrigger` actually completes a
  multi-step, commit-and-push cycle unattended** — tonight's routine
  creation succeeded (proves repo access), but the first real fire hadn't
  happened as of this writing. First thing to check on resume.

## Smallest sensible V1 (if one is ever warranted)

Given a "substantial coding task" (the real eventual use case):

1. A `STATE.md` (or `GOALS`/`BOARD`/`handover` if the task is large enough
   to need dependency-ordered goals) committed to the repo, read-first by
   every session.
2. A standing `permissions.deny` for the force-push/clean rules.
3. Within a fired session, use **`/goal <verifiable condition>`** rather
   than a hand-written loop-forever prompt — its own evaluator and error
   classification cover most of "keep going without re-prompting" and
   "don't treat a rate limit as a failure" for free.
4. When `/goal` clears for a hard reason (credit exhausted, context
   overflow, etc.) or the fired session otherwise ends, the state file is
   updated and pushed before stopping — same discipline this project used
   tonight, now needed less often since `/goal` absorbs the common
   transient-failure case itself.
5. A `RemoteTrigger` one-shot (or Desktop scheduled task; short recurring
   respecting the 1-hour Routine floor) scheduled to continue, with a
   **state-first, idempotent** prompt: read state + actual repo state,
   verify, re-issue `/goal` with the next condition or no-op if already done.
6. One independent review/verification step before anything is marked
   done — `/goal`'s evaluator gives a lightweight version of this for
   free; add a real independent reviewer subagent only for higher-stakes
   changes, not by default.
7. No daemon, no hooks, no coordinator, no unbounded self-generated-work
   mode — add any of those later, individually, only if a specific,
   observed problem justifies that specific piece of overhead.

This is deliberately close to "native Claude Code + a lightweight
convention," per the headline conclusion above — the honest possible
outcome here is that this smallest V1 *is* Claude AFK, and there's nothing
further to build.
