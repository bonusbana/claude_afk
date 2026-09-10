# Open Questions

## High priority — check before finalizing the plan

- **Desktop scheduled tasks** (`/docs/en/desktop-scheduled-tasks`) — runs
  locally (keeps file access) but persists across restarts without an open
  session, unlike `/loop`. Relevant for any future AFK task needing this
  user's actual WSL/Windows environment rather than a fresh cloud clone.
  See `analysis/local-vs-remote.md`.

## Resolved tonight (kept for the record)

- ~~What is `/goal`?~~ Read in full: a native condition-driven work loop
  with independent per-turn evaluation and precise error classification
  (transient failures like rate limits leave it active; credit exhaustion/
  context overflow/auth/model-unavailable clear it for an explicit
  restart). Folded into `research/claude-code-capabilities.md` and
  `planning/draft-claude-afk-plan.md`'s V1 recommendation.
- ~~Does `RemoteTrigger` support GitLab?~~ Never conclusively tested against
  a GitLab URL specifically, but resolved as moot — the repo moved to
  GitHub, and the docs confirm Routines are one of three official
  scheduling mechanisms, all seemingly GitHub-oriented for repo sources.
- ~~Is `CronCreate`/`ScheduleWakeup` durable?~~ Confirmed no, both
  empirically and by official docs and by `autonomous-loop`'s own
  independent guidance — session-scoped, restored on `--resume` (with
  exceptions) but lost if the session is killed outright.
- ~~What triggers the auto-mode classifier, and what's the full permission
  model?~~ Fully resolved by reading `/docs/en/permission-modes` in full —
  see `analysis/permission-model.md`. Settings.json block = protected-path
  write routed to the classifier (not a special rule); ssh-keygen block =
  ordinary classifier judgment call. Headless (`-p`) runs cannot stall on
  a permission block at all (no prompt to wait on) — a major finding for
  AFK's execution-mode choice.
- ~~RemoteTrigger empirical validation (fire/clone/access/read/write/
  commit/push)~~ Done, 2026-09-10T23:48 UTC: ran the actual trigger via
  `RemoteTrigger action=run` with a verification-only prompt. Result: 6/6
  PASS in 25s/10 turns, no permission stalls. See
  `validation/remote-trigger-test.md` and commit `9c57b75`.

## Still open

- Whether `PreCompact` hook blocking behavior has actually changed
  recently (a non-official source claimed so; `overnight-protocol`'s own
  finding — that `additionalContext` is ignored — was taken as accurate
  here, but the blocking-vs-not question specifically is unverified
  against an official source). Low priority — doesn't block the V1 spec.
- Managed Agents vs. Routines — not yet compared for this use case beyond
  noting both exist. Low priority unless a future task genuinely needs
  long-running multi-agent coordination.
- `dontAsk` vs `auto` mode for unattended headless runs specifically —
  see `analysis/permission-model.md`'s "Remaining open" — worth a direct
  decision in `planning/v1-spec.md`.
- Whether `claude -p "/goal <condition>"` combined with a `RemoteTrigger`
  one-shot actually works end to end for a *real* (non-research) coding
  task — tonight's empirical test validated the plumbing (clone/read/
  write/commit/push) but not `/goal` itself in a fired routine. Candidate
  for the Priority 3 prototype.
