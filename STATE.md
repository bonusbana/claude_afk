# Session State (read this first on resume)

**Objective:** research existing "run Claude unattended for a long time"
projects and Claude Code's own native capabilities, compare them, and draft
a plan for a possible future "Claude AFK" project. Do NOT implement AFK
itself yet.

## Setup (completed 2026-09-11 ~00:40-01:10 CEST)

- SSH key generated (`~/.ssh/id_ed25519`), added to GitHub, verified
  read+write on `bonusbana/windows-automation` and this repo.
- Repo pivoted from **GitLab to GitHub** mid-setup, on the user's explicit
  instruction, once we discovered `RemoteTrigger` (Claude's cloud routine
  scheduler — see `research/claude-code-capabilities.md`) is GitHub-native
  (Claude GitHub App) with no GitLab equivalent found anywhere in the
  tooling. This removed the need for a GitLab access token entirely.
  Repo: **https://github.com/bonusbana/claude_afk** (user created it
  manually as `claude_afk`, not `claude-tools` as originally sketched — the
  planned nested `claude-afk-research/` subfolder was flattened to repo
  root accordingly; all paths below are repo-root-relative).
- Claude GitHub App authorized on this repo (user did this manually,
  claude.ai side — cannot be verified from inside a local session; the
  scheduled continuation's own run log is the real test).
- Local `.claude/settings.json` given narrow allow-rules for git subcommands,
  `python3`, `mkdir -p`, `ssh -T` checks — approved by user after the
  auto-mode classifier blocked Claude from self-editing its own permissions
  (a real finding, logged in capabilities doc).
- One-shot `RemoteTrigger` routine scheduled for the post-reset continuation
  (see "Scheduled continuation" below). This IS the documented
  session-independent mechanism — `CronCreate` was investigated and rejected
  for this purpose (session-only, in-memory, dies when this session ends).

## Scheduled continuation

- Routine name/id: **[fill in after creation]**
- Fires: ~shortly after next usage reset (reset expected ~05:38 CEST /
  03:38 UTC on 2026-09-11; routine set for **03:50 UTC 2026-09-11**).
- Hard cutoff: must stop and leave clean state by **13:00 UTC 2026-09-11**
  (1 hour of margin before the user's 14:00 UTC / 16:00 CEST deadline).
- No further continuation is scheduled after that — by design (user is
  reclaiming afternoon usage).
- The routine's prompt embeds this file's location and instructs it to read
  this STATE.md first, verify actual repo/git state, then continue.

## Completed

- Environment/permission/scheduling investigation (this setup phase).
- Repo scaffold created and pushed.

## In progress / not yet started

- `research/autonomous-loop.md` — investigate `asiridalugoda/autonomous-loop`
- `research/overnight-protocol.md` — investigate `robogears/overnight-protocol`,
  esp. its permission/deny-rule model in depth
- `research/claude-code-capabilities.md` — started (see file), needs the
  official-docs pass (sessions/resume, headless mode, hooks, Agent SDK,
  compaction, usage-limit behaviour)
- `analysis/comparison.md`, `analysis/permission-model.md`,
  `analysis/economics.md`, `analysis/local-vs-remote.md` — not started,
  depend on the research files above
- `planning/draft-claude-afk-plan.md`, `planning/open-questions.md` — not
  started, depend on everything above

## Best next action if you're a fresh session reading this

1. `git log --oneline -10` and `git status` in this repo to confirm what's
   actually landed vs. this file's claims.
2. Check current UTC time against the cutoff above before doing anything else.
3. Pick up the next unchecked item in "In progress / not yet started", in
   order — they're roughly dependency-ordered.
4. Commit and push after every meaningfully-complete file, not just at the end.
