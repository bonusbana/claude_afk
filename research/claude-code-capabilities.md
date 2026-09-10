# Claude Code Native Capabilities (relevant to unattended operation)

Status: done for this research pass — combines tonight's empirical findings
with an official-docs pass (code.claude.com, current as of 2026-09-11).
Two promising leads flagged as unexplored in Open below (`/goal`, Desktop
scheduled tasks) — worth a look before finalizing any V1 design.

## Scheduling — three official options, not two

Official docs (`/docs/en/scheduled-tasks`) give an explicit comparison
table that matches and sharpens what we found hands-on tonight:

| | Cloud (Routines) | Desktop scheduled tasks | `/loop` (CronCreate/List/Delete) |
|---|---|---|---|
| Runs on | Cloud, Anthropic-managed | Your machine | Your machine |
| Requires machine on | No | Yes | Yes |
| Requires open session | No | No | Yes |
| Persistent across restarts | Yes | Yes | Restored on `--resume`, with exceptions |
| Local file access | No (fresh clone) | Yes | Yes |
| Permission prompts | No (runs autonomously) | Configurable per task | Inherits from session |
| Minimum interval | 1 hour | 1 minute | 1 minute |

Tonight's own experience maps directly onto this table:

- **`CronCreate`/`CronList`/`CronDelete`** = the `/loop` mechanism's
  underlying tools. Confirmed session-only/in-memory tonight; the docs
  make the exact limitation explicit: "Tasks only fire while Claude Code is
  running and idle... Starting a fresh conversation clears all
  session-scoped tasks." They *do* survive `--resume`/`--continue` (tasks
  that haven't expired restore), which is a nuance we hadn't tested tonight
  — but a session that's fully **killed** (not just closed) and never
  resumed loses them, and a self-paced `/loop`'s pending wakeup specifically
  is never restored on resume either way. Recurring tasks auto-expire after
  7 days; up to 50 tasks per session; jitter is applied automatically to
  avoid thundering-herd fire times.
- **`RemoteTrigger`** = the API surface behind **Routines**
  (`/docs/en/routines`, user-facing name; `/schedule` in the CLI). Confirmed
  tonight: independent of the local machine entirely, GitHub-repo sources,
  no local file access, runs autonomously with no permission prompts,
  1-hour floor on recurring (none on one-shot). This is what we used for
  the overnight continuation.
- **Desktop scheduled tasks** — genuinely new information, not used
  tonight: runs locally like `/loop`, but *doesn't* require an open session
  and *is* persistent across restarts, while still keeping local file
  access. This looks like it could be a real alternative to `RemoteTrigger`
  for a future task that specifically needs local file/tool access (this
  user's WSL/AutoHotkey/Rainmeter work, for instance) without needing the
  whole session to stay alive. Not yet investigated in detail — see Open.

**Implication:** the three-way split maps cleanly onto need — `/loop` for
in-session polling, Desktop tasks for durable-but-local, Routines for
durable-and-machine-independent. Tonight's choice of Routines was correct
for a GitHub-backed research task with no local-file dependency, but a
future AFK task that needs the user's actual WSL environment might want
Desktop scheduled tasks instead of (or alongside) a cloud Routine.

## Permission model — now with the official name

Tonight's empirical finding (a classifier layer that blocks certain
actions even under `defaultMode: auto`, distinct from the allow/deny list)
turns out to be exactly the officially documented **`auto` permission
mode**: "a classifier review[s] most actions instead of you." This is a
named, documented mechanism, not an ad hoc guess — `--permission-mode auto`
is the flag, and it's explicitly one of the built-in permission modes
alongside `acceptEdits`, `dontAsk`, `plan`, and `bypassPermissions`
(formerly `--dangerously-skip-permissions`).

For unattended runs specifically, the docs name the exact combination
`overnight-protocol` improvised without naming it: **`--permission-prompts
none`** — "denies anything that would prompt, tells Claude not to retry,
and the run continues," explicitly recommended for "a scheduled job" with
"nobody available to answer permission prompts." Paired with
`--permission-mode auto`, this is the closest official equivalent to what
`overnight-protocol` builds by hand with `--dangerously-skip-permissions` +
a small deny list — worth comparing directly in a future pass (see Open).

This also resolves an open question from tonight: the classifier's exact
boundary isn't fully mapped, but it is now confirmed to be a named,
documented feature (`auto` mode) rather than an undocumented safety net,
which means its behavior should be spec'd in the permission-modes docs
page — not yet read in full (see Open).

## Session resume — what actually carries over (official, precise)

Per `/docs/en/sessions`:

- **Restored:** full conversation history (a tool still running at crash
  time doesn't finish or rerun — Claude continues without its output);
  model; agent (with its tool restrictions); permission mode (via a
  detailed table of exceptions depending on how you resume); an **active
  goal** if one was running (turn count/timer/token-spend baseline reset —
  see the `/goal` flag below); scheduled tasks that haven't expired.
- **Not restored:** background Bash and monitor tasks; a self-paced
  `/loop`'s pending wakeup; several launch flags (`--mcp-config`,
  `--settings`, `--plugin-dir`, `--fallback-model`, `--add-dir`) — must be
  passed again on resume, though `settings.json`/`settings.local.json`
  themselves are re-read at launch so config living there doesn't need
  repeating.
- **"Resume from a summary" dialog:** on Pro/Max, resuming a session
  inactive >~1hr and over 100k tokens offers 3 choices — resume from an
  immediate `/compact` summary (cheaper per later request, loses whatever
  the summary drops), resume as-is (keeps everything, costs more per
  request), or "don't ask again." This is a concrete, user-controllable
  cost/completeness tradeoff directly relevant to
  `analysis/economics.md` for any design that pauses and resumes a local
  session repeatedly.
- Cross-project session lookup by ID has worked since v2.1.223 (used to
  require resuming from the original directory).

## Context compaction

`/compact` replaces history with a summary plus the most recent exchanges
and up to 5 recently-read files — this is also exactly what "resume from
summary" runs automatically. No user-visible pre-compaction warning
mechanism was found in what was read; `overnight-protocol`'s own finding
that `PreCompact`'s `additionalContext` is ignored appears to still be
accurate as a hook-input limitation (separate from `/compact` itself,
which is a normal user/session-triggered action, not a hook). One
third-party (non-official) source claims `PreCompact` hook *blocking*
behavior changed recently — flagged as unverified in Open, needs an
official hooks-reference check, not taken as fact here.

## Headless (`claude -p`) mode — official mechanics

- `-p`/`--print` runs non-interactively; `--bare` skips
  hooks/skills/commands/plugins/MCP/auto-memory/CLAUDE.md discovery for
  faster, more deterministic CI-style runs (recommended for scripted
  calls, becoming the `-p` default in future).
- `--output-format json`/`stream-json` gives structured output including
  `total_cost_usd` per invocation (client-side estimate) — directly useful
  for tracking spend per scheduled run without a separate usage daemon.
- Retryable API failures emit a `system/api_retry` event with an explicit
  error-category field (`rate_limit`, `overloaded`, `server_error`, etc.) —
  this is the closest thing found to an official, structured usage/rate-
  limit signal surfaced to a running session, though it's a retry-in-
  progress signal, not a proactive "you're approaching your cap" one.
- SIGTERM leaves the in-progress turn unfinished and resumable; SIGINT (or
  the SDK's `interrupt()`) ends the turn cleanly first. Background Bash
  tasks are killed ~5s after a `-p` run's final result; background
  subagents/workflows keep the process alive until done (capped at 10 min
  idle by default).

## Still open / not yet investigated

- **`/goal`** (`/docs/en/goal`) — mentioned in passing by the sessions doc
  ("keep the session working turn after turn toward a condition") and
  confirmed to survive resume (turn count/timer/token-baseline reset on
  resume). This could be a **directly relevant native feature for Claude
  AFK** — a built-in bounded, condition-driven work loop — and hasn't been
  read at all yet. **High priority for the next research pass** before
  finalizing `planning/draft-claude-afk-plan.md`; it may change the "smallest
  sensible V1" recommendation.
- **Desktop scheduled tasks** (`/docs/en/desktop-scheduled-tasks`) — the
  local-persistent-with-file-access option flagged above; not read in
  detail. Relevant specifically for any future AFK task needing this
  user's actual WSL/Windows environment rather than a fresh cloud clone.
- **`/docs/en/permission-modes`** in full — to map the `auto`-mode
  classifier's exact boundary (only two trigger cases observed empirically:
  credential generation, settings.json self-edit) against the documented
  behavior, and to properly compare `--permission-mode auto` +
  `--permission-prompts none` against `overnight-protocol`'s
  `--dangerously-skip-permissions` + deny-list approach.
- **`/docs/en/hooks`** in full — to verify or refute the third-party claim
  that `PreCompact` blocking behavior recently changed (currently
  unverified, see Compaction section).
- **`/docs/en/goal`, `/docs/en/channels`, `/docs/en/checkpointing`,
  `/docs/en/worktrees`** — mentioned by the docs read so far as related
  mechanisms, not yet explored for AFK relevance.
- Agent SDK vs. Managed Agents vs. Claude Code CLI: a comparison table was
  found (`/docs/en/agent-sdk/overview`) — Managed Agents is described as
  "long-running or asynchronous agents without managing your own sandbox,"
  a **separate hosted product** from both the Agent SDK and `RemoteTrigger`
  Routines, not yet compared against Routines for this use case.
