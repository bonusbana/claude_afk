#!/usr/bin/env python3
"""
Drives afk_sim.py through 8 scripted scenarios, each as one or more real
subprocess invocations (one invocation = one simulated "fresh session"),
and asserts the final persisted state matches what the AFK design expects.
No network access, no real Claude usage. Run: python3 run_tests.py
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
PY = sys.executable


def run_session(scenario, extra_args=()):
    state_dir = HERE / "state" / scenario
    fixture = HERE / "fixtures" / f"{scenario}.json"
    cmd = [PY, str(HERE / "afk_sim.py"), "--state-dir", str(state_dir),
           "--fixture", str(fixture), *extra_args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip(), state_dir


def read_state(state_dir):
    return json.loads((state_dir / "state.json").read_text())


def read_log(state_dir):
    p = state_dir / "run.log"
    return p.read_text() if p.exists() else ""


SCENARIOS = [
    dict(name="successful_completion",
         sessions=[["--target", "3"]],
         expect=lambda s, log: s["status"] == "COMPLETED" and s["progress"] == 3),
    dict(name="transient_failure_retry",
         sessions=[["--target", "1", "--max-retries", "3"]],
         expect=lambda s, log: s["status"] == "COMPLETED" and s["total_attempts"] == 3),
    dict(name="usage_limit_interruption",
         sessions=[["--target", "3"], ["--target", "3"]],
         expect=lambda s, log: s["status"] == "COMPLETED" and s["sessions_run"] == 2
         and "usage_limit" in log),
    dict(name="context_overflow_interruption",
         sessions=[["--target", "2"], ["--target", "2"]],
         expect=lambda s, log: s["status"] == "COMPLETED" and s["sessions_run"] == 2
         and "context_overflow" in log),
    dict(name="permission_interruption",
         sessions=[["--target", "2"], ["--target", "2"]],  # 2nd call must NOOP, not retry past a block
         expect=lambda s, log: s["status"] == "BLOCKED"
         and s["blocked_action"] == "rm -rf /" and "no-op" in log),
    dict(name="repeated_failure_safety_stop",
         sessions=[["--target", "1", "--max-retries", "3"]],
         expect=lambda s, log: s["status"] == "STOPPED" and s["pause_reason"] == "repeated_failure"),
    dict(name="crash_restart",
         sessions=[["--target", "2", "--simulate-crash-after", "1"], ["--target", "2"]],
         expect=lambda s, log: s["status"] == "COMPLETED" and s["sessions_run"] == 2
         and "recovered from unclean interruption" in log),
    dict(name="cost_budget_exceeded",
         sessions=[["--target", "10", "--steps-per-session", "10",
                    "--cost-per-step", "1.0", "--cost-budget", "3.0"]],
         expect=lambda s, log: s["status"] == "STOPPED" and s["pause_reason"] == "cost_budget_exceeded"
         and s["progress"] == 3),
]


def main():
    results = []
    for sc in SCENARIOS:
        state_dir = HERE / "state" / sc["name"]
        shutil.rmtree(state_dir, ignore_errors=True)
        outputs = []
        for session_args in sc["sessions"]:
            out, state_dir = run_session(sc["name"], session_args)
            outputs.append(out)
        state = read_state(state_dir)
        log = read_log(state_dir)
        ok = sc["expect"](state, log)
        results.append((sc["name"], ok, state["status"], state.get("pause_reason"), outputs[-1]))

    width = max(len(r[0]) for r in results)
    all_pass = True
    for name, ok, status, reason, last_out in results:
        mark = "PASS" if ok else "FAIL"
        all_pass &= ok
        print(f"{mark:4} {name:<{width}}  final={status:<10} reason={reason}")
        if not ok:
            print(f"       last session output: {last_out}")
    print()
    print("ALL SCENARIOS PASSED" if all_pass else "SOME SCENARIOS FAILED")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
