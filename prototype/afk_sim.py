#!/usr/bin/env python3
"""
AFK mechanics simulator — one invocation models one "fresh Claude session"
working on a mock objective. No network calls, no real Claude usage; the
"work" is a scripted fixture sequence of outcomes. See prototype/README.md.
"""
import json
import os
import sys
import time
import argparse
from pathlib import Path

TERMINAL = {"COMPLETED", "BLOCKED", "STOPPED"}


def load_state(state_path, objective, target):
    if state_path.exists():
        return json.loads(state_path.read_text())
    return {
        "objective": objective,
        "target_progress": target,
        "progress": 0,
        "status": "RUNNING",
        "pause_reason": None,
        "blocked_action": None,
        "fixture_index": 0,
        "attempts_this_step": 0,
        "total_attempts": 0,
        "cost_spent": 0.0,
        "sessions_run": 0,
        "history": [],
    }


def save_state(state_path, state):
    tmp = state_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    os.replace(tmp, state_path)


def log(log_path, msg):
    with open(log_path, "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}] {msg}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state-dir", required=True)
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--objective", default="mock objective")
    ap.add_argument("--target", type=int, default=3)
    ap.add_argument("--max-retries", type=int, default=3,
                     help="max consecutive transient failures on one step before a safety stop")
    ap.add_argument("--max-total-attempts", type=int, default=50,
                     help="hard cap across all sessions; safety stop if exceeded")
    ap.add_argument("--steps-per-session", type=int, default=5,
                     help="bounded unit of work per invocation, models a session's finite turn budget")
    ap.add_argument("--cost-per-step", type=float, default=1.0)
    ap.add_argument("--cost-budget", type=float, default=1e9)
    ap.add_argument("--simulate-crash-after", type=int, default=None,
                     help="os._exit ungracefully after this many successful steps THIS session, no stop-and-save")
    args = ap.parse_args()

    state_dir = Path(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "state.json"
    log_path = state_dir / "run.log"
    fixture = json.loads(Path(args.fixture).read_text())

    state = load_state(state_path, args.objective, args.target)
    session_no = state["sessions_run"] + 1

    if state["status"] in TERMINAL:
        log(log_path, f"session {session_no}: no-op, status already terminal ({state['status']})")
        print(f"NOOP status={state['status']}")
        return

    # crash recovery detection: RUNNING with no pause_reason on load, but with
    # evidence of prior work, means the prior session died mid-step without a
    # clean stop-and-save (a clean exit always sets status to something else).
    if state["status"] == "RUNNING" and state["pause_reason"] is None and state["total_attempts"] > 0:
        log(log_path, f"session {session_no}: recovered from unclean interruption "
                       f"(prior session ended without stop-and-save) — resuming, not retrying "
                       f"already-durable progress={state['progress']}")

    state["status"] = "RUNNING"
    state["pause_reason"] = None
    # persist the session-start marker immediately, so a crash later in this
    # very session still leaves the correct session count for the next one
    state["sessions_run"] = session_no
    save_state(state_path, state)
    crashed = 0
    steps_taken = 0

    while steps_taken < args.steps_per_session:
        if state["progress"] >= state["target_progress"]:
            state["status"] = "COMPLETED"
            log(log_path, f"session {session_no}: completion condition met "
                           f"({state['progress']}/{state['target_progress']})")
            break
        if state["total_attempts"] >= args.max_total_attempts:
            state["status"] = "STOPPED"
            state["pause_reason"] = "max_total_attempts_exceeded"
            log(log_path, f"session {session_no}: SAFETY STOP — max_total_attempts exceeded")
            break
        if state["cost_spent"] >= args.cost_budget:
            state["status"] = "STOPPED"
            state["pause_reason"] = "cost_budget_exceeded"
            log(log_path, f"session {session_no}: SAFETY STOP — cost budget exceeded "
                           f"({state['cost_spent']}/{args.cost_budget})")
            break
        if state["fixture_index"] >= len(fixture):
            state["status"] = "STOPPED"
            state["pause_reason"] = "fixture_exhausted"
            log(log_path, f"session {session_no}: fixture exhausted with objective unmet — stopping")
            break

        outcome = fixture[state["fixture_index"]]
        state["total_attempts"] += 1
        state["cost_spent"] = round(state["cost_spent"] + args.cost_per_step, 4)

        if outcome == "success":
            state["fixture_index"] += 1
            state["progress"] += 1
            state["attempts_this_step"] = 0
            state["history"].append({"session": session_no, "outcome": "success",
                                      "progress": state["progress"]})
            save_state(state_path, state)  # durable checkpoint after every success
            log(log_path, f"session {session_no}: step ok, progress={state['progress']}"
                           f"/{state['target_progress']}, cost={state['cost_spent']}")
            steps_taken += 1

            if args.simulate_crash_after is not None:
                crashed += 1
                if crashed >= args.simulate_crash_after:
                    log(log_path, f"session {session_no}: SIMULATING CRASH after "
                                   f"{crashed} successful step(s) — no stop-and-save, hard exit")
                    os._exit(1)

        elif outcome == "transient_fail":
            state["attempts_this_step"] += 1
            state["history"].append({"session": session_no, "outcome": "transient_fail",
                                      "attempt": state["attempts_this_step"]})
            log(log_path, f"session {session_no}: transient failure, retry "
                           f"{state['attempts_this_step']}/{args.max_retries}")
            if state["attempts_this_step"] >= args.max_retries:
                state["status"] = "STOPPED"
                state["pause_reason"] = "repeated_failure"
                save_state(state_path, state)
                log(log_path, f"session {session_no}: SAFETY STOP — repeated_failure "
                               f"({state['attempts_this_step']} consecutive transient failures)")
                break
            state["fixture_index"] += 1  # advance past this scripted attempt

        elif outcome in ("usage_limit", "context_overflow"):
            state["status"] = "PAUSED"
            state["pause_reason"] = outcome
            state["fixture_index"] += 1
            save_state(state_path, state)
            log(log_path, f"session {session_no}: interruption '{outcome}' — stop-and-save, "
                           f"clean exit; a real scheduler (RemoteTrigger/Desktop task) resumes this")
            break

        elif outcome.startswith("permission_denied"):
            denied = outcome.split(":", 1)[1] if ":" in outcome else "unspecified action"
            state["status"] = "BLOCKED"
            state["pause_reason"] = "permission_denied"
            state["blocked_action"] = denied
            state["fixture_index"] += 1
            save_state(state_path, state)
            log(log_path, f"session {session_no}: BLOCKED — permission denied for '{denied}', "
                           f"requires human unblock, no auto-resume")
            break

        else:
            raise ValueError(f"unknown fixture outcome: {outcome!r}")

    else:
        # step budget exhausted without a terminal outcome: session-boundary pause
        state["pause_reason"] = state["pause_reason"] or "session_step_budget_exhausted"
        if state["status"] == "RUNNING":
            log(log_path, f"session {session_no}: step budget exhausted, "
                           f"session boundary — clean exit, resumable")

    state["sessions_run"] = session_no
    save_state(state_path, state)
    print(f"status={state['status']} progress={state['progress']}/{state['target_progress']} "
          f"pause_reason={state['pause_reason']} sessions={session_no} "
          f"cost={state['cost_spent']}")


if __name__ == "__main__":
    main()
