# Economics

Where each approach spends, saves, or risks wasting Claude usage — the
distinction the user specifically asked to track: usage that buys
**reliability/quality** vs. usage spent on **orchestration that doesn't
materially improve the result**.

## Native Claude Code

- **Saves usage:** `RemoteTrigger` cloud routines cost nothing while idle —
  no standing daemon, no polling, no background cost between fires. A
  one-shot routine spends exactly what its prompt asks for.
- **Consumes:** whatever the actual work costs — no overhead layer of its
  own to account for separately.
- **Risk:** none observed that's specific to the mechanism itself; the risk
  is entirely in *what you tell it to do* (a badly-scoped prompt wastes the
  whole run, same as any session).

## `autonomous-loop`

- **Spends more, for real reliability:** the goal-scaled checker panel and
  the independent verifier are direct token cost for direct error-
  correction — this is usage buying quality, the "good" side of the
  distinction, and it's explicitly risk-scaled (light review for low-risk
  CRUD, full panel only for security-critical work) rather than a flat tax.
- **Saves usage:** the `EXPERIMENTS.md` anti-repeat rule (never re-run a
  discarded idea) and rewind-before-escalate (abandon a doomed path after
  2 failed passes rather than compounding fixes on top of fixes) both
  directly prevent wasted spend that a less disciplined loop would incur.
- **Risk of waste:** the Managed Agents coordinator+roster mode and Relay
  (multi-machine, dual-scheduler, GitHub-issue protocol) are both
  meaningfully heavier mechanisms that the skill itself gates behind "only
  when it earns its overhead" — i.e. the project's own authors flag these
  as the parts most likely to be orchestration cost without payoff at
  small scale.

## `overnight-protocol`

- **Spends more, for real reliability:** none observed structurally (no
  maker/checker split) — its extra spend is concentrated in monitoring and
  self-generated work, not in verification quality.
- **Consumes continuously:** the usage daemon polls on a fixed cadence
  (~60-180s) for the entire duration the loop is armed, independent of
  whether a check is actually needed soon — background cost paid whether
  or not it turns out to matter that run.
- **Real risk of waste:** the unbounded self-generated ladder (QA → audit →
  QoL → repeat forever) has no independent verifier checking that what it
  builds is actually valuable — only prose anti-churn rules (a
  self-reported "this helps because X" justification, a ban on cosmetic
  churn). This is the single biggest economic risk of the three approaches:
  usage spent confidently generating "improvements" with no structural
  check that they're worth building, bounded only by the model's own
  self-honesty about clearing its stated value bar.
- **Trades tokens for reliability in one place, well:** the source-ranked
  usage-detection ladder is real complexity that buys something concrete —
  it prevents both false-pause (wasting the remaining allowance by
  stopping early on a bad estimate) and false-continue (blowing through
  the cap on a stale reading) — a legitimate token-for-reliability trade,
  not orchestration for its own sake.

## Cross-cutting observations

- **The riskiest kind of spend, across all three, is unbounded
  self-generated work without independent verification** — `overnight-
  protocol` has this by design (its whole point); `autonomous-loop`
  structurally avoids it (maker ≠ checker on every goal, including
  self-generated ones — nothing in its design exempts ladder-style
  self-generated work from the same verifier gate); native Claude Code has
  no opinion either way, so the risk is entirely a function of what gets
  built on top of it.
- **The cheapest kind of spend, across all three, is anything that
  prevents redundant work**: `autonomous-loop`'s experiment anti-repeat
  ledger and rewind-before-escalate, `overnight-protocol`'s self-healing
  usage reading (avoids external polling infrastructure entirely by piggy-
  backing on turns already being taken), and — from tonight's own
  experience — a `RemoteTrigger` prompt that checks actual state before
  acting (idempotent, no-op if nothing to do) rather than assuming and
  redoing work.
- **Reasonable default for a hobbyist-scale V1** (see
  `planning/draft-claude-afk-plan.md`): spend on independent verification
  (cheap relative to the error it catches) and state-first idempotent
  resume prompts (near-zero cost, prevents duplicated work); be skeptical
  of any unbounded self-generated-work mode until/unless a verifier gate is
  also in place; avoid standing background daemons/polling unless something
  concrete (like real usage-limit detection) actually requires it.
