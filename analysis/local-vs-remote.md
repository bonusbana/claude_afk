# Local vs. Remote Execution

Status: partial — one question already answered empirically tonight, rest
open.

## Machine-state questions

- Computer stays awake: presumably fine for a local/interactive approach;
  no new finding tonight.
- Computer sleeps / WSL stops / Windows reboots: **for a local approach,
  these would all kill an in-progress session** (nothing observed tonight
  contradicts this — `CronCreate` jobs are explicitly session-only, so
  anything tied to keeping a local session alive dies with it).
- Computer fully shut down: same as above for local; **does not affect a
  `RemoteTrigger` cloud routine at all**, since it runs entirely in
  Anthropic's cloud with its own git checkout — this was effectively
  confirmed by design tonight (see `claude-code-capabilities.md`), though we
  haven't yet observed a real overnight fire to fully validate it end to end.
- Can a local process auto-recover from these? Not investigated — would
  require OS-level mechanisms (Windows Task Scheduler, systemd inside WSL,
  etc.) outside Claude Code itself, which starts to look like "inventing a
  scheduler" the user explicitly wants to avoid if a native option covers it.

## Local vs. remote tradeoffs (preliminary)

- Remote (`RemoteTrigger`) advantages: survives any local machine state
  change; no dependency on WSL/Windows being up; genuinely "independent of
  the interactive session" as the user required.
- Remote disadvantages/limits: GitHub-native (see capabilities doc) so other
  hosts need workarounds; no local file/env access, so all needed state must
  live in the git repo; can't be deleted via API (UI only); 1-hour floor on
  recurring schedules (irrelevant for one-shot use); tool access is limited
  to what's declared in `allowed_tools`.
- Local advantages: full access to the user's actual environment (WSL,
  Windows paths, locally-installed tools like AutoHotkey/Rainmeter contexts
  the user cares about for *other* projects); no GitHub-only constraint.
- Local disadvantages: fragile to sleep/reboot/shutdown/WSL restart; ties
  continuation to keeping a specific interactive session or machine state
  alive, which is exactly the failure mode Claude AFK is meant to survive.

## Update: there's a third option — Desktop scheduled tasks

Official docs (`/docs/en/scheduled-tasks`, see
`research/claude-code-capabilities.md`) reveal a middle ground we didn't
use tonight: **Desktop scheduled tasks** run locally (so they keep local
file access, unlike a cloud Routine's fresh clone) but — unlike `/loop` —
don't require an open session and *are* persistent across restarts. Not
yet investigated in depth. This directly matters for a future AFK task
that needs this user's actual WSL/Windows environment (AutoHotkey,
Rainmeter files outside any repo) rather than a fresh cloud checkout —
worth comparing against a cloud Routine before deciding which to use for
such a task.

## Desktop scheduled tasks — resolved (official docs, 2026-09-11)

Concrete answers to the questions this project flagged:

- **Mechanism:** requires the **Claude Desktop app itself** (a GUI, not the
  CLI) to be open and the machine awake. "Persistent across restarts" means
  the *task definition* survives (stored as a `SKILL.md` under
  `~/.claude/scheduled-tasks/<task-name>/`), not that it runs while the app
  is closed — Desktop polls the schedule every minute while running and
  starts a fresh session when due. **If the computer sleeps through a
  scheduled time, that run is simply skipped** (not queued).
- **Missed-run recovery:** on app start or wake, Desktop checks the last 7
  days for missed fires and runs **exactly one catch-up** for the most
  recently missed time (older misses discarded) — a real but limited
  safety net, not a guarantee of eventual execution.
- **Local-machine requirements:** "Keep computer awake" (Settings → Desktop
  app → General) prevents idle sleep, but **closing the laptop lid sleeps
  it regardless** — matches `overnight-protocol`'s macOS `caffeinate`
  caveat almost exactly, just Windows-flavored (no lid-override exists).
- **Permissions:** per-task permission mode; global `~/.claude/settings.json`
  allow rules also apply. **Manual mode stalls the run** on an unapproved
  tool, leaving the session open in the sidebar awaiting approval — exactly
  the "one unanswered prompt stalls it" failure mode from
  `analysis/permission-model.md`. Mitigation: run the task once manually via
  "Run now" and click "always allow" on each prompt so future runs don't
  stall; MCP tools marked `requiresUserInteraction` stall on *every* call
  regardless, with no always-allow option.
- **Interaction with CLI sessions:** independent — a fired task is "the
  same as a session you start yourself" (can edit files, run commands,
  commit, open PRs) but doesn't message other open sessions. A `worktree`
  toggle exists to isolate a run's git state from other in-progress work in
  the same folder — directly relevant if a scheduled task and an
  interactive session might touch the same working directory.
- **Windows practicality (untested, flagged not assumed):** this is a
  Windows/WSL2 environment, and Desktop scheduled tasks run through the
  native Desktop app, not inside WSL — a working folder would need to be a
  path the Windows-side app can see (this project's own repo happens to
  work either way, since `/mnt/c/VSCode_workspace/claude_afk` in WSL *is*
  `C:\VSCode_workspace\claude_afk` on the Windows side). Whether the
  Desktop app's Bash tool on Windows actually shells into WSL bash or uses
  native Windows/PowerShell semantics was **not verified** — a real
  practical unknown for anything relying on WSL-specific tooling (this
  project's own `rtk` wrapper, for instance).

**Assessment:** Desktop scheduled tasks are the right tool only when local
file/tool access is required and the machine-awake constraint is
acceptable — for anything that must survive the machine being off, a cloud
Routine remains the only real option of the three.

## Open

- Managed Agents (`/docs/en/managed-agents/overview`) — a separate hosted
  product for "long-running or asynchronous agents without managing your
  own sandbox," mentioned by the Agent SDK docs but not compared against
  Routines for this use case.
- For a "substantial coding task" (as opposed to this research task), does
  the cloud sandbox have what's needed (build tools, language runtimes) or
  does that depend entirely on the chosen `environment_id`?
- Whether Desktop's Bash tool on Windows runs through WSL or native
  Windows shell semantics — untested, matters for any task depending on
  this user's WSL-specific tools (`rtk`, etc.).
