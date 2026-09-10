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

## Open

- Desktop scheduled tasks: read `/docs/en/desktop-scheduled-tasks` in
  detail — how "persistent across restarts" is actually achieved (a
  background service? re-launched on login?), and what happens if the
  machine is fully shut down vs. merely restarted.
- Managed Agents (`/docs/en/managed-agents/overview`) — a separate hosted
  product for "long-running or asynchronous agents without managing your
  own sandbox," mentioned by the Agent SDK docs but not compared against
  Routines for this use case.
- For a "substantial coding task" (as opposed to this research task), does
  the cloud sandbox have what's needed (build tools, language runtimes) or
  does that depend entirely on the chosen `environment_id`?
