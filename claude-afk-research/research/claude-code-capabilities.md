# Claude Code Native Capabilities (relevant to unattended operation)

Status: partial — empirical findings from tonight's setup, official-docs
pass still needed for sessions/resume, hooks, Agent SDK, compaction details,
usage-limit behaviour specifics.

## Scheduling mechanisms — two very different things exist

### `CronCreate` / `CronList` / `CronDelete` (in-session cron)

- Fires a prompt on a cron schedule, but **only while this session's REPL is
  idle**, and the job store is **in-memory, session-only** — "gone when
  Claude exits." `durable: true` has **no effect** per the tool's own
  description.
- Recurring jobs auto-expire after 7 days regardless.
- **Verdict: not suitable for overnight independence.** It cannot survive
  this interactive session ending, crashing, or the machine sleeping. It's a
  same-session reminder/retry mechanism, not a continuation mechanism.

### `RemoteTrigger` (cloud "routines") — the actual durable mechanism

- Each routine spawns a **fully isolated cloud session** in Anthropic's
  infrastructure (not on the user's machine), on a cron schedule or a single
  `run_once_at` (RFC3339 UTC) firing.
- Session config (`job_config.ccr`) specifies: model, `sources` (git repos to
  check out), `allowed_tools`, and the initiating prompt.
- **This is genuinely independent of the local machine**: survives PC sleep,
  WSL stopping, reboots, or full shutdown, because it never touches the
  local machine at all.
- **Minimum interval for recurring is 1 hour**; one-shot via `run_once_at`
  has no such floor.
- **Cannot delete routines via API** — only through the web UI
  (claude.ai/code/routines).
- **Key limitation discovered tonight: GitHub-native, not host-agnostic.**
  The `sources: [{git_repository: {url}}]` mechanism, the setup warnings
  ("Couldn't verify GitHub access... install the Claude GitHub App"), and
  every piece of the tooling's own guidance reference GitHub specifically
  (accepting "GitHub URLs in any format"). No GitLab (or other host)
  integration is mentioned anywhere. Repo access for a routine appears to
  depend on the **Claude GitHub App** being authorized for that repo — a
  *separate* auth path from a user's local SSH key or PAT. This is why this
  project's repo was moved from GitLab to GitHub mid-setup: it's not that
  GitLab couldn't work at all (a routine could presumably still `git clone`
  an arbitrary public/token-authenticated URL via Bash rather than the
  structured `sources` field), but the *documented, first-class* path is
  GitHub-only, and improvising around that would have meant embedding a
  long-lived PAT in a routine's cloud-stored prompt instead of using the
  proper App-scoped grant.
- Routines cannot access local files, local services, or local environment
  variables — everything they need must come from the git source(s) and the
  prompt.

**Implication for Claude AFK:** the "wait for a fresh independent session to
pick up work later" building block one might assume needs custom
infrastructure (a daemon, a Windows Task Scheduler entry, a separate VM) is
already provided natively via `RemoteTrigger`, *provided* the work targets
a GitHub repo and the state needed to resume fits in "clone repo + read a
state file + prompt." That covers a lot of the "recover later / continue
from durable state" part of the target workflow for free.

## Permission model layers observed tonight

Two independent layers, not one:

1. **`.claude/settings.json` allow/deny lists** (`permissions.allow`,
   `permissions.defaultMode`). This project's global settings already had
   `defaultMode: "auto"`. Project-level settings can add narrowly-scoped
   `Bash(...)` allow patterns on top.
2. **An auto-mode classifier that sits in front of the allow-list and can
   still block an action even under `defaultMode: auto` and even when the
   action would otherwise match nothing that requires approval.** Observed
   blocking two things tonight, both credential/permission-adjacent:
   - Running `ssh-keygen` to generate a new key (credential generation).
   - Editing `.claude/settings.json` itself to add new allow-rules
     (self-expanding its own permissions).

   Both were resolved by asking the user directly (outside the normal
   allow-list path) — the classifier's denial message explicitly says to
   surface it to the user rather than try to work around it.

**Implication:** a narrowly-scoped allow-list reduces *routine* prompts (git
subcommands, reading/writing project files, running python) but does **not**
give an agent the ability to grant itself more power or mint new credentials
unattended — that boundary held even under `defaultMode: auto`, and appears
to require the user's direct, one-time say-so regardless of any
configuration. This is a meaningful safety property to note when comparing
against `overnight-protocol`'s `--dangerously-skip-permissions` approach:
Claude Code's own classifier layer is *not* the same thing as an
allow/deny list, and isn't simply bypassed by broadening one.

## Still to investigate (official docs pass)

- Session resume (`--resume`/`--continue`) mechanics and what state actually
  carries across.
- Headless/non-interactive mode specifics (`-p`, output formats).
- Hooks (what events exist, what they can block/inject).
- Context compaction behaviour and any user-visible warning before it fires.
- How usage-limit exhaustion actually surfaces to a running session
  (hard stop vs. gracefully-returned error vs. queued retry).
- Agent SDK capabilities beyond what Claude Code CLI exposes directly.
