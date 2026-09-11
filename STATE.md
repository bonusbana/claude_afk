# Session State (read this first on resume)

**Objective (stage 2, current):** turn stage-1 research into validated
conclusions, a small tested prototype, and an implementation-ready V1 spec
for a possible future "Claude AFK" project. Do NOT implement AFK itself.

**Stage 1 objective (completed 2026-09-11, see git history before commit
`9c57b75`):** research existing "run Claude unattended" projects and
Claude Code's native capabilities, compare them, draft a plan. Done — see
`research/`, `analysis/`, and the (now superseded by `planning/v1-spec.md`)
`planning/draft-claude-afk-plan.md`.

## Stage 2: completed (2026-09-10 ~23:48 UTC – 2026-09-11 ~00:05 UTC)

- **Priority 1 (continuation/scheduling):** the existing `RemoteTrigger`
  routine (`trig_01WDqrGYk4JgLwkNL86HR72u`) was inspected, then **fired
  live** with a scoped verification-only prompt via `RemoteTrigger
  action=run` — see "Scheduled continuation" below for the full empirical
  result. Its stored prompt has now been repurposed for stage 2's own
  fallback continuation (see below); same hard cutoff retained; no
  recurring/orphaned schedule left behind (still a single one-shot).
- **Priority 2 (highest-value open questions), all closed:**
  - Desktop scheduled tasks: read `/docs/en/desktop-scheduled-tasks` in
    full — see `analysis/local-vs-remote.md`. Answered: persistence,
    machine/awake requirements, catch-up behavior, permission behavior, and
    the (still-open, low-priority) Windows/WSL Bash-shell-semantics
    question.
  - `RemoteTrigger` empirical validation: **PASS 6/6** (clone, repo-access,
    state-read, file-write, commit, push) — real live test, not assumed.
    See `validation/remote-trigger-test.md`, commit `9c57b75`.
  - Permission/auto-mode edge cases: `/docs/en/permission-modes` read in
    full — see `analysis/permission-model.md`. Corrected an earlier
    stage-1 mischaracterization (the settings.json block was a
    protected-path classifier judgment, not a special
    self-permission-editing rule) and established the single most
    important finding for AFK: **headless (`-p`) runs cannot stall on a
    permission block at all** (no prompt to wait on) — decisive for the
    architecture recommendation.
- **Priority 3 (small POC), done:** `prototype/` — a deterministic,
  offline, zero-Claude-usage simulator of AFK mechanics (persistent state,
  stop-and-save, interruption classification, retry/backoff, fresh-session
  continuation, safety limits, cost-awareness). **8/8 scenarios pass.**
  Caught and fixed two real design bugs before any real implementation
  (session-count bookkeeping timing; crash-detection logic) — see
  `prototype/README.md`'s "Bugs this prototype already caught" section,
  and the corresponding lesson folded into `planning/v1-spec.md`'s
  Persistent state model.
- **Implementation-ready spec:** `planning/v1-spec.md` — supersedes
  `planning/draft-claude-afk-plan.md` as the primary planning document
  (that file is kept for history/context, not deleted). Final
  recommendation: **don't build custom AFK software** — compose
  `claude -p "/goal <condition>"` + `RemoteTrigger` Routines + `auto`
  permission mode + a single state file. Full reuse/adapt/leave-alone
  breakdown and smallest-useful-V1 description are in that file.

## Scheduled continuation

- Routine: `claude-afk-research-continuation`, id `trig_01WDqrGYk4JgLwkNL86HR72u`.
  View/manage at https://claude.ai/code/routines (routines can't be
  deleted via API, UI only — still just one routine, no orphans).
- **Empirically validated tonight** (2026-09-10T23:48–23:49 UTC): fired
  on-demand via `RemoteTrigger action=run` with a scoped verification
  prompt. Result: clone OK, repo-access OK, STATE.md read OK, file write
  OK, commit OK, push OK — 25s, 10 turns, zero permission stalls. Full
  transcript summary in `validation/remote-trigger-test.md` (commit
  `9c57b75`) and this file's git history (see `RemoteTrigger get_run_log`
  on session `cse_01WDLmBQ4EUeuCpG8cSs58oe` for the raw log if needed).
- **Stored prompt has been repurposed for stage 2 fallback continuation**
  (see below) — it now targets whatever remains in this file's "Remaining"
  section, not the original stage-1 research task.
- Still fires once at **2026-09-11T03:50:00Z** (`run_once_at`, not
  recurring) if this session stops before the user returns.
- Hard cutoff unchanged and still baked into the stored prompt: stop and
  leave clean state by **2026-09-11T13:00:00Z** (1 hour margin before the
  user's real 14:00 UTC / 15:00 Stockholm return). No further continuation
  scheduled after that, and none should be — this is intentional, not an
  oversight.

## Remaining (small, low priority — everything requested has a first complete pass)

1. Desktop scheduled tasks: whether its Bash tool on this Windows/WSL2
   machine shells into WSL or native Windows — untested, flagged in
   `analysis/local-vs-remote.md`. Only matters if a future task actually
   uses Desktop scheduled tasks.
2. Whether a fired `RemoteTrigger` session can safely self-reschedule its
   own next continuation — deliberately left unverified and out of V1
   scope per `planning/v1-spec.md`'s Scheduler section; not a gap, a
   stated boundary.
3. `dontAsk` vs `auto` mode for unattended runs — open question in
   `analysis/permission-model.md`, low priority, decidable later by trying
   both on a real task.
4. General proofreading — only if genuinely idle with time before the
   cutoff; do not manufacture busywork here (see this project's own
   economics analysis on the risk of unverified self-generated work).

## Best next action if you're a fresh session reading this

1. `git log --oneline -20` and `git status` to confirm what's actually
   landed vs. this file's claims.
2. Check current UTC time against `2026-09-11T13:00:00Z` before doing
   anything else. If past it, do not start new work — verify the repo is
   clean, confirm `README.md` is accurate, stop.
3. If genuinely idle with time remaining, work the short "Remaining" list
   above, in order. This is optional depth, not required scope — everything
   the user asked for already has a complete, evidenced first pass.
4. Commit and push after every meaningfully-complete change, not just at
   the end.

## Fallback fire log

- **2026-09-11T03:50 UTC:** the scheduled fallback continuation fired as a
  safety net. Verified repo state against this file's claims (all matched)
  and re-ran the prototype's 8/8 test suite (still all passing). Found one
  real issue unrelated to task content: the prior session's stage-2 commits
  had been made on a **detached HEAD**, never merged onto `main` or pushed
  — `main`/`origin/main` were still sitting at the pre-stage-2 commit
  (`11c0b1a`). Fast-forwarded `main` to the detached tip (`11e5c0c`,
  confirmed a strict ancestor relationship first) and pushed; `origin/main`
  now correctly carries all stage-2 work. Confirmed the "Remaining" section
  above only lists low-priority optional items and all deliverables
  (`research/`, `analysis/`, `prototype/`, `validation/`,
  `planning/v1-spec.md`) have real, substantial content. Per this file's
  own instructions, did not invent further work. Repo left clean and
  pushed.
