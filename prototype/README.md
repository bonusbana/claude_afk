# AFK Mechanics Prototype (non-production)

A small, deterministic, offline simulator for the mechanics a real Claude
AFK V1 would need — persistent state, stop-and-save, interruption
classification, retry/backoff, fresh-session continuation, safety stop
conditions, and cost-awareness — without spending real Claude usage or
touching anything outside this directory.

**What this is NOT**: not a framework, not a permanent system, not capable
of running real commands or modifying anything outside `prototype/state/`.
`afk_sim.py` never calls the network or the Claude API — "Claude's work" on
a step is just the next entry in a scripted fixture file. This tests the
*orchestration logic* a real AFK harness would need, in isolation from the
LLM itself.

## Run it

```
python3 run_tests.py
```

Runs all 8 scenarios, each as one or more real subprocess invocations of
`afk_sim.py` (one invocation = one simulated fresh session), and asserts
the final state matches what a correct AFK design should produce. Takes
under a second, zero network calls.

## How it maps to the real thing

- **One `afk_sim.py` invocation = one Claude session.** State lives in
  `state/<scenario>/state.json`, read at the top and durably checkpointed
  after every successful step — the same "the model forgets, the repo
  doesn't" principle from `autonomous-loop`, and the same idempotent-resume
  contract this project's actual `RemoteTrigger` prompt already used.
- **The fixture file is the mock "Claude call" outcome** for each step:
  `success`, `transient_fail`, `usage_limit`, `context_overflow`,
  `permission_denied:<action>`. This is the deliberate substitute for
  "simulate a failure mode without repeatedly consuming real Claude usage."
- **`--simulate-crash-after N`** kills the process (`os._exit`) right after
  the Nth successful step, with no graceful stop-and-save — the one failure
  mode that can't be "returned" from a mock outcome, since a real crash by
  definition doesn't get to run its own handling code.

## Scenarios and what each one tests

| Scenario | Tests |
|---|---|
| `successful_completion` | Baseline: completion detection works at all |
| `transient_failure_retry` | Retry/backoff within one session doesn't burn a session boundary |
| `usage_limit_interruption` | Clean stop-and-save + exit; a *different* fresh invocation resumes correctly |
| `context_overflow_interruption` | Same as above, distinct interruption *type* recorded (not lumped with usage_limit) |
| `permission_interruption` | Blocks require a human — a second invocation must **no-op**, never silently retry past a denial |
| `repeated_failure_safety_stop` | Exceeding max retries on one step is a safety stop, not an infinite retry loop |
| `crash_restart` | Durable checkpointing survives an *unclean* death; the next session detects and logs the recovery instead of corrupting or duplicating state |
| `cost_budget_exceeded` | A cost/usage ceiling actually halts further spend before the objective completes |

## Bugs this prototype already caught (before any real implementation)

Both found by the test suite on the first run, not by inspection — exactly
the point of building this before V1:

1. **Session-count bookkeeping must be persisted at session *start*, not
   session *end*.** The first version only wrote `sessions_run` after the
   work loop finished, so a crash mid-session left the counter stale and
   the next invocation mis-numbered itself. Fix: persist the incremented
   session count immediately on load, before doing any work.
2. **Crash-recovery detection must not depend on any counter that a crash
   itself might leave unpersisted.** Originally gated on `sessions_run > 0`
   (broken by bug 1); fixed to key off `status == RUNNING and pause_reason
   is None and total_attempts > 0` — a combination only a genuine unclean
   interruption can produce, independent of session counting.

**Takeaway for `planning/v1-spec.md`:** any persistent state schema needs
*at least two* fields that are updated and durably saved together at the
true start of a unit of work (not just at its end) if a resumed session
needs to distinguish "this crashed mid-step" from "this is a fresh
session" reliably. A single status field with a small, deliberately
inconsistent set of possible combinations (as used here) is enough.
