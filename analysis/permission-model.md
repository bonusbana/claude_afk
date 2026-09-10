# Permission Model Analysis

Built on `research/overnight-protocol.md`'s deep dive and tonight's own
first-hand experience setting this project up (see
`research/claude-code-capabilities.md`).

## The core distinction: enforced vs. instructed

Every permission mechanism observed falls into exactly one of two buckets,
and conflating them is the main way an unattended-run design goes wrong:

- **Enforced by Claude Code itself** (a real boundary the model cannot
  reason its way past): `permissions.deny` rules, explicit `ask` rules
  (both survive `--dangerously-skip-permissions`), the always-on
  critical-path deletion circuit breaker, **protected paths** (`.claude/`,
  `.git`, and others — never pre-approved by an allow rule in any mode),
  and — a mechanism `overnight-protocol` doesn't use but we hit directly
  tonight — the **auto-mode classifier**, which blocked two things under
  `defaultMode: auto`: a protected-path write (editing
  `.claude/settings.json`) and an ordinary command it judged risky
  (`ssh-keygen`, generating a new credential). Both required an explicit,
  out-of-band human approval; see "What we found in Claude Code itself"
  below for the full, docs-confirmed mechanics of why.
- **Merely instructions to Claude** (convention the model is trusted to
  follow, nothing stops it mechanically): everything in a skill's prose —
  "never touch main," "no secrets," "no deploys," anti-churn rules,
  timeboxes. A model that ignores these faces no tool-level block.

This means a design's *real* safety envelope is exactly its enforced set,
never its prose — the prose is real risk-reduction (a well-behaved model
mostly follows it) but it is not a guarantee, and shouldn't be counted as
one when reasoning about worst-case blast radius for an unattended run.

## What overnight-protocol enforces, concretely

Three rules, in the *project's* `.claude/settings.local.json`, scoped to
the loop's active lifetime (added at arm-time, removed at wrap-up):
```
Bash(git push --force:*)
Bash(git push -f:*)
Bash(git clean:*)
```
That's the entire enforced safety net once `--dangerously-skip-permissions`
is set. Deliberately minimal — it targets exactly the operations where an
autonomous mistake becomes unrecoverable (rewritten history, wiped
untracked work), not a general lockdown.

## What we found in Claude Code itself — now fully explained by official docs

**Correction to the account above**, now that `/docs/en/permission-modes`
has been read in full: the settings.json block tonight was not a special
"self-permission-editing" rule. It's the general **protected-paths**
mechanism — `.claude/` (along with `.git`, `.vscode`, `.husky`, and others)
is a protected directory; writes to it are never pre-approved by an
allow rule in any mode (the safety check runs *before* allow rules are
even evaluated), and in `auto` mode specifically such writes are routed to
the classifier for a judgment call rather than flatly blocked or allowed.
Tonight the classifier judged the edit unsafe and its own refusal message
instructed escalating to the user — exactly what happened, by design, not
a gap. The `ssh-keygen` block was different: not a protected-path write,
just an ordinary command that fell through to "everything else goes to the
classifier" and got judged risky — general judgment on credential-shaped
actions, not a named enumerated rule.

**The decision order for every action** (first match wins): (1) explicit
allow/ask/deny rules resolve immediately, *except* protected-path writes
and `rm`/`rmdir` on a critical path, which route to the classifier even if
an allow rule matches; (2) read-only actions and working-directory file
edits auto-approve; (3) everything else goes to the classifier; (4) a
classifier block returns Claude a reason and it tries an alternative.

**Full mode lineup:** `default`/Manual (asks before most things),
`acceptEdits` (auto-approves file edits + common filesystem commands),
`plan` (analyze without editing), `auto` (classifier reviews instead of a
human — the Pro/Max/Team built-in default, and what this project used),
`dontAsk` (auto-denies anything that would otherwise prompt, running only
allow-rule/read-only/hook-approved actions — built for CI/deterministic
environments), `bypassPermissions` (`--dangerously-skip-permissions`).

**What survives even `bypassPermissions`** — the strongest mode: explicit
`ask` rules still prompt; `rm`/`rmdir` targeting a **critical path**
(filesystem root, top-level dirs, home directory, working directory and
parents, Windows drive roots) still asks for approval — a hard circuit
breaker no allow rule or mode can lift; a one-time interactive acceptance
dialog is required before first use, and it's refused outright under
root/sudo on Linux/macOS and in any session (including a background one)
that hasn't had that dialog accepted interactively first.
`overnight-protocol`'s launch guide understated this slightly — critical-path
deletion protection is separate from and additional to its documented
`ask`-rules-still-fire caveat.

**The single most important finding for Claude AFK — headless mode cannot
stall on permissions at all.** Per the docs' "sessions that can't prompt"
case: a non-interactive `-p` run with no `--permission-prompt-tool` has
nothing to fall back to when the classifier blocks something, including
hitting the repeated-block threshold (3 in a row / 20 total) that would
otherwise pause auto mode and start prompting in an *interactive* session
— **the blocked action just doesn't run, and Claude keeps working.** This
means the exact failure mode this project hit twice tonight (`ssh-keygen`,
the settings.json edit) happened only because tonight's session was
*interactive*; the same blocks in an unattended headless AFK run would not
stall it — Claude would simply be unable to do that one thing and would
have to route around it. **This is the strongest evidence yet that a
future AFK design should run unattended work via `claude -p` (headless) in
`auto` mode, not an interactive session left open unattended** — it
structurally cannot deadlock on a permission prompt the way an interactive
session can.

**Auto mode's blocked-by-default list** (illustrative, not exhaustive —
full list via `claude auto-mode defaults`): `curl | bash`, force push,
work-discarding git commands (`reset --hard`, `clean -fd`, etc.),
production deploys/migrations/IaC destroy, printing a live credential to
the transcript, pushing secrets out of the repo, and — a detail directly
relevant if a future design ever has Claude launch Claude — **launching
another autonomous agent loop with `--dangerously-skip-permissions` is
itself blocked by default**. **Allowed by default**: local file ops in the
working directory, installing lockfile-declared dependencies, reading
`.env` and sending credentials to their *matching* API, read-only HTTP,
and pushing to **any** branch of the repo being worked in, including the
default branch (as of v2.1.211 — not just a branch Claude created).

## Takeaways for general (non-AFK) Claude Code usage

Independent of whether Claude AFK ever gets built, worth adopting for this
user's ordinary Claude Code usage:

1. **A small standing `permissions.deny` set** —
   `Bash(git push --force:*)`, `Bash(git push -f:*)`, `Bash(git clean:*)`,
   plausibly also `Bash(git reset --hard:*)` — as a normal project default,
   not just during an unattended run. These are rarely legitimate day-to-day
   operations, the downside of getting one wrong is unrecoverable, and
   `overnight-protocol`'s own experience validates this as a
   high-value/low-friction default. (Redundant with auto mode's own
   built-in blocks for force-push and work-discarding commands, but a
   `deny` rule is unconditional — worth keeping as defense-in-depth for
   non-`auto` modes too.)
2. **Auto mode's classifier boundary is a real, un-bypassable-from-inside
   safety layer** — now fully documented (see above), not a mystery. Any
   future AFK design should expect protected-path writes and
   judgment-call-risky commands to occasionally get blocked, and should run
   headless specifically so that a block degrades to "can't do that one
   thing" rather than "stalled waiting for a prompt that will never come."

## Remaining open

- Whether `dontAsk` mode (fully deterministic allow-list, no classifier
  judgment calls, no repeated-block ambiguity) might be a *better* fit than
  `auto` mode for a fully unattended AFK run specifically, trading the
  classifier's flexibility for predictability — worth weighing directly in
  `planning/v1-spec.md` against `auto` mode's "never stalls headless"
  property above.
