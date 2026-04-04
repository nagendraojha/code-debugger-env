"""
test_local.py — Verify CodeDebugger environment logic before deploying.
Run this WITHOUT installing openenv-core (tests game logic only).

Usage:
    python test_local.py
"""

import sys
import os
import textwrap

# ── Minimal stubs so we can test environment.py without openenv-core ─────────

import types

# Stub openenv.core.env_server
env_server_mod = types.ModuleType("openenv.core.env_server")

from pydantic import BaseModel
from typing import Optional

class Action(BaseModel):
    pass

class Observation(BaseModel):
    done: bool = False
    reward: Optional[float] = None

class State(BaseModel):
    episode_id: Optional[str] = None
    step_count: int = 0

class Environment:
    pass

env_server_mod.Action = Action
env_server_mod.Observation = Observation
env_server_mod.State = State
env_server_mod.Environment = Environment

core_mod = types.ModuleType("openenv.core")
openenv_mod = types.ModuleType("openenv")
openenv_mod.core = core_mod
core_mod.env_server = env_server_mod

sys.modules["openenv"] = openenv_mod
sys.modules["openenv.core"] = core_mod
sys.modules["openenv.core.env_server"] = env_server_mod

# Now patch path and import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "server"))

from models import DebugAction, DebugObservation, DebugState
from environment import CodeDebuggerEnvironment, _run_tests, _safe_exec

# ── Tests ─────────────────────────────────────────────────────────────────────

PASS = "✅"
FAIL = "❌"
results = []

def check(label, condition):
    icon = PASS if condition else FAIL
    print(f"  {icon}  {label}")
    results.append(condition)

print("\n" + "="*60)
print("  CodeDebugger Environment — Local Test Suite")
print("="*60)

# ── 1. Safe exec sandbox ──────────────────────────────────────────────────────
print("\n[1] Safe exec sandbox")
val, err = _safe_exec("def f(x): return x*2", "f(5)")
check("Correct code returns right value", val == 10 and err is None)

val, err = _safe_exec("def f(x): return x", "f(")
check("Syntax error caught gracefully", err is not None and "SyntaxError" in err)

val, err = _safe_exec("def f(): raise ValueError('oops')", "f()")
check("Runtime error caught gracefully", err is not None)

# ── 2. Test runner ────────────────────────────────────────────────────────────
print("\n[2] Test runner")
good_code = "def sum_first_n(n):\n    return sum(range(1, n+1))"
passed, lines = _run_tests(good_code, [("sum_first_n(5)", 15), ("sum_first_n(10)", 55)])
check(f"Correct code passes all tests ({passed}/2)", passed == 2)

buggy_code = "def sum_first_n(n):\n    return sum(range(1, n))"
passed, lines = _run_tests(buggy_code, [("sum_first_n(5)", 15), ("sum_first_n(10)", 55)])
check(f"Buggy code fails tests ({passed}/2 passed)", passed == 0)

# ── 3. Environment lifecycle ──────────────────────────────────────────────────
print("\n[3] Environment lifecycle")
env = CodeDebuggerEnvironment()
obs = env.reset(seed=42)
check("reset() returns DebugObservation", isinstance(obs, DebugObservation))
check("reset() done=False", obs.done == False)
check("reset() reward=None", obs.reward is None)
check("reset() buggy_code is non-empty", len(obs.buggy_code) > 10)
check("reset() attempts_used=0", obs.attempts_used == 0)
check("reset() difficulty set", obs.difficulty in ("easy", "medium", "hard"))

state = env.state
check("state() returns DebugState", isinstance(state, DebugState))
check("state() puzzle_id set", len(state.puzzle_id) > 0)
check("state() step_count=0", state.step_count == 0)

# ── 4. Step with wrong answer ─────────────────────────────────────────────────
print("\n[4] Step — wrong answer")
obs2 = env.step(DebugAction(fixed_code="def foo(): pass"))
check("step() increments step_count", env.state.step_count == 1)
check("step() wrong answer → done=False (has remaining attempts)", not obs2.done or obs2.attempts_used >= obs2.max_attempts)
check("step() feedback contains test results", "✗" in obs2.feedback or "✓" in obs2.feedback)
check("step() attempts_used=1", obs2.attempts_used == 1)

# ── 5. Hint system ────────────────────────────────────────────────────────────
print("\n[5] Hint system")
env2 = CodeDebuggerEnvironment()
env2.reset(seed=0)
env2.step(DebugAction(fixed_code="def foo(): pass"))  # attempt 1 — no hint
obs_no_hint = env2.step(DebugAction(fixed_code="def bar(): pass"))  # attempt 2 — hint unlocks
check("Hint unlocks after 2 failed attempts", obs_no_hint.hint is not None)

# ── 6. Correct answer — easy puzzle ──────────────────────────────────────────
print("\n[6] Correct answer gives reward")
env3 = CodeDebuggerEnvironment()
obs_start = env3.reset(seed=42)

# Find which puzzle was selected and use the correct code
from environment import PUZZLES
import random
rng = random.Random(42)
puzzle = rng.choice(PUZZLES)
correct = puzzle["correct_code"]

obs_win = env3.step(DebugAction(fixed_code=correct))
check("Correct answer → done=True", obs_win.done == True)
check("Correct answer → reward > 0", obs_win.reward is not None and obs_win.reward > 0)
check("Correct answer in 1 attempt → speed bonus (reward ≥ 1.0)", obs_win.reward >= 1.0)
check("All tests passed", obs_win.tests_passed == obs_win.tests_total)

# ── 7. Difficulty selection ───────────────────────────────────────────────────
print("\n[7] Difficulty selection")
env4 = CodeDebuggerEnvironment()
obs_hard = env4.reset(difficulty="hard")
check("difficulty='hard' resets to hard puzzle", obs_hard.difficulty == "hard")

env5 = CodeDebuggerEnvironment()
obs_easy = env5.reset(difficulty="easy")
check("difficulty='easy' resets to easy puzzle", obs_easy.difficulty == "easy")

# ── 8. Max attempts exhaustion ────────────────────────────────────────────────
print("\n[8] Max attempts exhaust → done")
env6 = CodeDebuggerEnvironment()
env6.reset(seed=1)
done = False
for i in range(6):  # max is 5
    obs_ex = env6.step(DebugAction(fixed_code="def bad(): return None"))
    if obs_ex.done:
        done = True
        break
check("Episode ends after max_attempts exhausted", done == True)
check("Final reward is 0 for all-wrong", obs_ex.reward == 0.0)

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "="*60)
total = len(results)
passed_total = sum(results)
print(f"  Result: {passed_total}/{total} checks passed")
if passed_total == total:
    print(f"  {PASS} ALL TESTS PASSED — ready to deploy!")
else:
    print(f"  {FAIL} {total - passed_total} checks failed — review above")
print("="*60 + "\n")
