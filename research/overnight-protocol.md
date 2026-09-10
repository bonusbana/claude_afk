# `robogears/overnight-protocol`

Status: core investigation done from actual repo content (SKILL.md read in
full; `install.sh` and the permissions section of `references/launch-guide.md`
read in full; `preflight.sh`, `check_usage.sh`, `usage_daemon.sh`,
`overnightloop_stop.sh`/`overnightloop_session_start.sh` inspected via grep
only, not read line-by-line — see Open below). v0.2.2.

## What it actually is

A Claude Code **skill** (SKILL.md) + a handful of installed shell
scripts/hooks (`~/.claude/overnight-loop/`). Unlike `autonomous-loop`, this
is entirely **local, single-machine, single-session-lineage**: it keeps one
Claude Code CLI process alive (or resumed) indefinitely via hooks, a
background usage daemon, and long `sleep` calls — there is no cloud/durable
scheduler involved anywhere in its design.

## Workflow shape

Phase 0 (once): preflight doctor check → a single ~4-minute question
window (front-loaded, then questions are forbidden except one "end-of-rope"
exception) → record start time → branch to `overnight-loop/YYYY-MM-DD` →
snapshot any dirty tree (excluding secret-shaped files) → write
`OVERNIGHT_LOOP_PLAN.md` + `OVERNIGHT_LOOP_REPORT.md` → baseline test run →
**arm a watchdog flag** (`~/.claude/overnight-loop-active`) → start a
background **usage daemon** → show a live status line/heartbeat.

Then an unbounded work loop: pick top open plan item → mark in-progress →
implement in small increments → commit `loop: <item>` + push → check usage
→ next item. When the plan is exhausted it **generates its own work**
forever via a fixed ladder: Rung 1 QA-harden → Rung 2 run `/audit` and fix →
Rung 3 research + build quality-of-life improvements → Rung 4 loop back to
Rung 1. It is explicitly designed to **never stop on its own** — only the
human removing the flag file ends it.

## How work is broken into goals/tasks

A flat plan file with checkboxes (official mission items, then a
self-generated "Ladder backlog"), timeboxed ~45-60 min per item. No
maker/checker role separation (contrast `autonomous-loop`) — the same
session that writes the code also decides it's done, gated only by tests
passing and the acceptance note being met.

## State persistence / how a fresh session knows what happened

Two layers:
1. **In-repo**: `OVERNIGHT_LOOP_PLAN.md` + `OVERNIGHT_LOOP_REPORT.md`,
   committed with the work, plus git log itself (`loop:` commit prefix
   makes all loop work `git log --grep='^loop'`-discoverable).
2. **Outside the repo**: `~/.claude/overnight-loop-active` (a small JSON
   flag: cwd, plan path, mode, optional end_epoch) is the watchdog's
   arm/disarm switch, and a `SessionStart` hook (matcher
   `startup|resume|compact`) automatically re-injects "here's the plan,
   report, and git log, keep going" into any new/resumed/post-compaction
   session in that project, gated on the flag being present. This is what
   makes recovery automatic rather than something the user has to remember
   to re-invoke.

## Context exhaustion/compaction handling

Explicitly relies on the `SessionStart` hook's `compact` matcher for
recovery, because (per the skill's own note) **Claude Code ignores
PreCompact's `additionalContext`** — an older PreCompact-hook design was
retired for that reason. So this is a hard platform constraint discovered
by this project's own maintainers, not a design choice.

## Usage/rate-limit exhaustion detection

The most elaborate mechanism of anything investigated. A background
**usage daemon** (`usage_daemon.sh`, `nohup`'d, single-instance, heartbeats
the watchdog flag) keeps `~/.claude/overnight-usage.json` fresh on a
source ladder, ordered by trust:

1. `real` — the actual server percentage the terminal CLI's own status
   line receives, but only trusted if fresh (<~210s old) and still inside
   the current rate-limit window.
2. `real-api` — the daemon polling Anthropic's usage endpoint directly
   using the terminal CLI's own Keychain-stored OAuth credentials
   (macOS-specific: `security` + one-time "Always Allow"). Reports the 5h
   window *and every weekly window including per-model ones*.
3. `real-app` — scraped from the Desktop app's local cache; called "dead on
   current app versions" (the app stopped writing the file it relied on
   around July 2026) — kept only for legacy installs.
4. `estimate-ccusage` — a cost-weighted proxy from the `ccusage` tool when
   no real reading exists, self-calibrating once a real reading appears,
   and deliberately pausing 10 points earlier (85% vs the normal 95%
   threshold) than a real reading would, because it's just an estimate.

A neat, if elaborate, self-healing trick: because the loop itself is the
thing generating API traffic, a stale/missing reading is fixed by taking
one more (cheap) turn rather than by any external mechanism — that turn's
response headers refresh the real snapshot.

## Waiting and resumption

On `PAUSE`, the session commits WIP, logs the pause, then runs **one single
long `sleep` Bash call** for the exact seconds until reset (+120s buffer),
requiring an explicit long timeout parameter — enabled by `install.sh`
setting `env.BASH_MAX_TIMEOUT_MS=18300000` (~5h5m) in the *global*
`~/.claude/settings.json` at install time (this cannot be set mid-session;
Claude Code reads `env` only at session startup). **This entire mechanism
requires the terminal/session to literally stay alive and un-killed for
the whole pause** — there is no independent scheduler standing in for a
dead session; the closest thing to one is the `SessionStart` recovery hook,
which only helps if some *new* session gets launched in that project
later (manually, or via the machine waking a terminal some other way).

## Crash/transient failure handling

A **dead-run failsafe**: the usage daemon refreshes the flag's timestamp
every cycle; if it goes untouched 30+ minutes (crash/reboot/force-quit),
the hooks treat the run as dead and stand down automatically, so a leftover
flag can never wedge a normal session the next day. Recovery (via the
`SessionStart` hook) always re-checks the daemon is actually alive
(`ps`, not just `kill -0`, to avoid a false-positive on a recycled PID)
and relaunches it if not.

## Git/checkpointing

Dedicated `overnight-loop/YYYY-MM-DD` branch, never main; every commit
prefixed `loop:`; push after every commit if a remote exists (the pushed
branch *is* the backup — no local-only work). Force-push, history rewrite,
and touching main are explicitly forbidden. A pre-loop dirty-tree snapshot
excludes secret-shaped filenames (`*.pem`, `*.key`, `*.env*`,
`*credential*`, `*token*`, `*secret*`) by pattern, printed as EXCLUDED so
the user can commit them deliberately if it's a false positive.

## Testing/review/verification

Tests/build/typecheck run after every increment and compared against a
recorded baseline; Rung 2 explicitly delegates to a separate `/audit`
skill for a hardening pass. No maker/checker role split, though — same
session grades its own work (contrast `autonomous-loop`'s structural
separation).

## Continue/stop/retry/escalate decisions

- Blocked after 2 genuinely different attempts on one item → mark skipped,
  keep the diagnostic diff as a committed patch file, move on.
- Environment-blocked (needs a display/human eyeball) → flagged with the
  exact morning command, front-loaded early rather than attempted blind.
- "End-of-rope" is the *only* place it's allowed to ask again after Phase
  0: official mission exhausted **and** a full ladder cycle produced
  nothing that clears its own "this helps because X" value bar **and**
  everything left is parked-for-direction.
- Stop = only the human removing the flag file (or a user-set hard
  `end_epoch` ceiling passing) — genuinely never self-terminates otherwise.

## Additional Claude work its orchestration creates

- The self-generated ladder (QA-harden → audit → QoL research/build →
  repeat forever) is the headline feature and also the headline economic
  risk: once the *official* backlog is done, 100% of further usage is
  self-directed. Explicit "anti-churn" guardrails exist specifically to
  stop this degrading into busywork: a mandatory one-line justification
  before any self-directed change, a ban on cosmetic reversals/reformatting
  churn, and "if a whole cycle produced only trivial changes, widen the
  research scope rather than making smaller noise."
- The heartbeat/status-line/cockpit presence machinery (every ~20 turns, a
  compact status card) is cheap narration overhead, not real work — small
  but nonzero cost paid purely for observability while AFK.
- The usage daemon polling every ~60-180s is background cost paid
  continuously for the run's duration, independent of whether it's
  actually near a limit — the tradeoff for never needing external
  ground-truth.

## Where extra work looks justified vs. wasteful (assessment)

- **Justified:** the source-ladder usage detection (turns a genuinely hard
  problem — "how do I know my real quota without asking" — into a
  self-healing local mechanism); the dead-run failsafe; the anti-churn
  value-bar gate on self-generated work.
- **Genuinely risky/wasteful without the guardrails:** an unbounded
  self-generated ladder with no maker/checker separation could, in
  principle, spend a large amount of usage confidently "improving" a
  project with no independent check that the improvements are real — the
  anti-churn rules are a mitigation, not a structural guarantee the way
  `autonomous-loop`'s separate verifier is.
- **Platform-specific overhead**: several mechanisms (Keychain-authenticated
  `real-api`, `caffeinate`, `osascript` notifications, Full Disk Access)
  are macOS-only conveniences bundled into what is otherwise a portable
  idea — see the permission/platform section below.

## Permission model — deep dive (the user's specific ask)

**Launch mode:** `claude --dangerously-skip-permissions` is the documented,
recommended way to run this unattended ("the most unattended mode").

**What `--dangerously-skip-permissions` changes:** it removes the normal
interactive approve/deny prompt for actions that would otherwise ask.
**It does NOT remove explicit `ask` rules** — the launch guide explicitly
warns to run `/permissions` once beforehand and clear any leftover `ask`
rules, because "explicit ask rules force a prompt even under
`--dangerously-skip-permissions`" (a direct quote from `preflight.sh`'s
own warning text) — i.e. an ask rule left in place would still stall an
unattended run exactly the way a normal prompt would.

**What is automatically permitted:** effectively everything not covered by
a deny or ask rule, once the flag is set — this is the whole point of using
it (no per-action confirmation).

**What is explicitly denied:** a deliberately small, narrowly-scoped set,
written into the **project's** `.claude/settings.local.json` (never the
global `~/.claude/settings.json`, and never hand-edited mid-run — always
via a read-validate-replace Python one-liner, matching the same safe-write
pattern `install.sh` uses for the global file):
```
Bash(git push --force:*)
Bash(git push -f:*)
Bash(git clean:*)
```
using the "colon prefix" glob syntax the skill notes is required (a
space-star pattern does not match). These rules are added at loop-arm time
and **removed again at wrap-up** — so they're scoped to the loop's active
lifetime, not a permanent project setting.

**What can still cause an interruption despite the deny rules:** anything
not covered by them — the deny list covers exactly three destructive git
operations and nothing else. It is not a general lockdown; broader safety
comes from the skill's *instructions* (see next point), not from
Claude-Code-enforced rules. An expired/misconfigured Keychain token for
`real-api`, a dead usage daemon, or a stalled `sleep` timeout misconfiguration
could all still stall or degrade a run — those aren't permission-system
concerns but are practically-equivalent failure modes for an unattended run.

**Enforced by Claude Code itself vs. merely instructions to Claude:**
- **Enforced by Claude Code (a real boundary):** `permissions.deny` rules —
  the launch guide states this outright: "Deny is enforced by Claude Code,
  not the model." An explicit `ask` rule is the same category — it forces
  a prompt regardless of the skip-permissions flag, which is exactly what
  we independently observed tonight when the local auto-mode classifier
  blocked `ssh-keygen` and a settings.json self-edit even under
  `defaultMode: auto` (see `claude-code-capabilities.md`) — different
  mechanism, same category of "the harness itself intervenes, not just the
  model's judgment."
- **Merely instructions to Claude (convention, not a hard boundary):**
  everything else in the skill — "branch only, never touch main," "no
  deploys/publishing/paid signups," "no secrets," the anti-churn rules, the
  timebox-per-item guidance, the ladder itself. All of this is prose the
  model is trusted to follow; nothing in Claude Code prevents a model that
  ignores the instructions from, say, editing main directly, since only
  force-push/`git push -f`/`git clean` are denied at the tool level (a
  plain `git push` to main, or a non-force history edit, is not blocked by
  anything in this configuration).

**What `--dangerously-skip-permissions` changes for this specific
skill's threat model, concretely:** without it, the loop would stall on the
very first action that would normally prompt (a file write, a shell
command outside any allowlist) — exactly the "one unanswered prompt stalls
the loop" problem the skill calls out as the reason for using it. The three
deny rules are the *entire* Claude-Code-enforced safety net once that flag
is set; everything else is the prose guardrails above.

**Gaps:** the deny list protects git history/force-push/clean specifically
— it does not deny, for example, `rm -rf` outside git, arbitrary network
calls, package installs, or writing outside the project directory. The
skill's prose ("no destructive filesystem/git operations beyond the
working tree," "no secrets") is the only thing standing between an
unattended, skip-permissions session and those categories — i.e. the same
"instructions, not enforcement" gap noted above, just for a wider set of
actions than git alone.

**Particularly useful rules:** the force-push/git-clean denial is a good,
cheap, high-value default — these are exactly the operations where an
autonomous agent's mistake becomes unrecoverable (rewritten history, wiped
untracked work), and they're rarely legitimately needed mid-loop even when
everything is going right.

**Particularly restrictive/annoying rules:** none observed — the set is
notably minimal (3 rules), which is itself worth calling out: this project
did not try to enumerate a comprehensive deny list, it picked the smallest
set that blocks irreversible git mistakes specifically, leaving everything
else to skip-permissions + prose.

**Could an adapted version improve ordinary (non-AFK) Claude Code usage?**
Yes, plausibly, independent of anything AFK-related: a small
`permissions.deny` set for `git push --force:*` / `git push -f:*` /
`git clean:*` (and maybe `git reset --hard:*`) as a standing project
default — not just during an unattended loop — would guard against the
same class of unrecoverable mistakes during ordinary interactive sessions
too, at effectively zero cost to normal workflow (these are rarely
legitimate day-to-day operations). Worth a line in
`analysis/permission-model.md`.

## Platform assumptions (Windows/WSL relevance)

This project's tooling is **macOS-specific in multiple places**:
`caffeinate` for keep-awake, `osascript` for notifications, Keychain +
`security` for the `real-api` OAuth token, System Settings → Full Disk
Access warnings. None of these exist on Windows/WSL2. The *design* (hooks +
flag file + usage daemon + long sleep) is portable in principle, but the
concrete scripts as shipped are not directly runnable as-is in this user's
environment — every macOS-specific piece would need a WSL2/Windows
equivalent (a different keep-awake mechanism, a different notification
method, and critically a different way to get authoritative real-time
usage percentages, since the Keychain-based `real-api` path has no direct
Windows analog investigated here yet).

## Open (not yet read line-by-line)

- `scripts/preflight.sh`, `scripts/check_usage.sh`, `scripts/usage_daemon.sh`,
  `scripts/feeder.sh`, `scripts/cockpit.sh`, `hooks/overnightloop_stop.sh`,
  `hooks/overnightloop_session_start.sh` — grepped for keywords, not read in
  full. Lower priority: SKILL.md + install.sh + the launch-guide permissions
  section already answered every question in the brief; these would mainly
  add implementation detail, not new architectural findings.
- `tests/test_estimator.sh`, `tests/test_real_api.sh` — not inspected.
