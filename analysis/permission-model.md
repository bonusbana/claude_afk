# Permission Model Analysis

Built on `research/overnight-protocol.md`'s deep dive and tonight's own
first-hand experience setting this project up (see
`research/claude-code-capabilities.md`).

## The core distinction: enforced vs. instructed

Every permission mechanism observed falls into exactly one of two buckets,
and conflating them is the main way an unattended-run design goes wrong:

- **Enforced by Claude Code itself** (a real boundary the model cannot
  reason its way past): `permissions.deny` rules, explicit `ask` rules
  (both survive `--dangerously-skip-permissions`), and — a mechanism
  `overnight-protocol` doesn't use but we hit directly tonight — an
  **auto-mode classifier** that sits in front of the allow-list and blocked
  two things even under `defaultMode: auto`: generating a new credential
  (`ssh-keygen`) and self-editing `.claude/settings.json`'s own permission
  rules. Both required an explicit, out-of-band human approval; neither
  was something a broader allow-list or `--dangerously-skip-permissions`-
  equivalent setting could have bypassed.
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

## What we found in Claude Code itself, independent of any skill

The classifier layer discovered tonight is a *different* mechanism from
`permissions.deny`/`ask` — it's not configurable via settings.json at all
(as far as observed), it simply refuses certain action categories
(credential generation, self-permission-editing) and directs the agent to
surface the decision to the user. This is arguably a stronger guarantee
than a hand-written deny list for the specific things it covers, precisely
because it can't be turned off by the agent choosing a more permissive
mode — but it's narrow in scope (we only observed it trigger for two
specific action types) and its exact boundary is not established. See
`planning/open-questions.md`.

## Takeaways for general (non-AFK) Claude Code usage

Independent of whether Claude AFK ever gets built, two things from this
research are worth adopting for this user's ordinary Claude Code usage:

1. **A small standing `permissions.deny` set** —
   `Bash(git push --force:*)`, `Bash(git push -f:*)`, `Bash(git clean:*)`,
   plausibly also `Bash(git reset --hard:*)` — as a normal project default,
   not just during an unattended run. These are rarely legitimate day-to-day
   operations, the downside of getting one wrong is unrecoverable, and
   `overnight-protocol`'s own experience validates this as a
   high-value/low-friction default.
2. **Never assume `defaultMode: auto` or a skip-permissions-equivalent
   flag makes an agent fully unattended for every action category** — the
   classifier boundary we hit tonight is real and un-bypassable from
   inside a session; any future AFK design needs to expect it to fire
   occasionally and have a graceful "surface and pause" path for exactly
   that case (which is what tonight's approach did, by necessity).

## Open

- Full boundary of the auto-mode classifier is unknown — only two trigger
  cases observed (credential generation, settings.json self-edit). Worth
  probing further only if a future session needs to know in advance
  whether some other action category will stall unattended (see
  `planning/open-questions.md`).
- Whether Claude Code's official docs describe this classifier layer
  formally (name, full scope) — not yet checked against
  `research/claude-code-capabilities.md`'s planned docs pass.
