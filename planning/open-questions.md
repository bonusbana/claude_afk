# Open Questions

## High priority — check before finalizing the plan

- **`/goal`** (`/docs/en/goal`) — an official Claude Code feature,
  described only in passing so far as keeping "the session working turn
  after turn toward a condition," and confirmed to survive session resume
  (turn count/timer/token-spend baseline reset). This has not been read at
  all yet and could be a **directly relevant native building block for
  Claude AFK** — possibly reducing the "smallest sensible V1" in
  `planning/draft-claude-afk-plan.md` even further. Read it next.
- **Desktop scheduled tasks** (`/docs/en/desktop-scheduled-tasks`) — runs
  locally (keeps file access) but persists across restarts without an open
  session, unlike `/loop`. Relevant for any future AFK task needing this
  user's actual WSL/Windows environment rather than a fresh cloud clone.
  See `analysis/local-vs-remote.md`.

## Resolved tonight (kept for the record)

- ~~Does `RemoteTrigger` support GitLab?~~ Never conclusively tested against
  a GitLab URL specifically, but resolved as moot — the repo moved to
  GitHub, and the docs confirm Routines are one of three official
  scheduling mechanisms, all seemingly GitHub-oriented for repo sources.
- ~~Is `CronCreate`/`ScheduleWakeup` durable?~~ Confirmed no, both
  empirically and by official docs and by `autonomous-loop`'s own
  independent guidance — session-scoped, restored on `--resume` (with
  exceptions) but lost if the session is killed outright.
- ~~What triggers the auto-mode classifier?~~ Named: this is the
  documented `auto` permission mode. Exact boundary still only
  empirically known for 2 cases (credential generation, settings.json
  self-edit) — full mapping would require reading `/docs/en/permission-modes`
  in full (not yet done).

## Still open

- Full boundary of the `auto`-mode classifier beyond the two observed
  trigger cases — worth reading `/docs/en/permission-modes` in full if a
  future session needs to know in advance whether some other action
  category will stall an unattended run.
- Whether `PreCompact` hook blocking behavior has actually changed
  recently (a non-official source claimed so; `overnight-protocol`'s own
  finding — that `additionalContext` is ignored — was taken as accurate
  here, but the blocking-vs-not question specifically is unverified
  against an official source).
- Real end-to-end validation of tonight's scheduled continuation is still
  pending — routine creation succeeded (proves repo access at
  creation-time preflight) but the first real fire (2026-09-11T03:50:00Z)
  hadn't happened as of this writing. First thing to check on resume via
  `RemoteTrigger get_run_log` on trigger id `trig_01WDqrGYk4JgLwkNL86HR72u`.
- Managed Agents vs. Routines — not yet compared for this use case beyond
  noting both exist.
- Whether an adapted, official `--permission-mode auto` +
  `--permission-prompts none` combination could replace
  `overnight-protocol`'s hand-rolled `--dangerously-skip-permissions` +
  deny-list approach entirely, if a future design ever needs the
  "stay-alive-and-sleep" local strategy rather than the
  "schedule-a-fresh-session" strategy this project used.
