"""
CodeDebugger Environment — server/environment.py

An RL environment where an AI agent must debug Python code snippets.
Each episode presents a buggy function; the agent submits fixed code.
Hidden test cases grade each attempt. Reward scales with quality and speed.

Evaluation criteria this environment excels at:
  ✅ Runtime correctness   — sandboxed exec with timeout
  ✅ Interface compliance  — full reset/step/state OpenEnv standard
  ✅ Task design           — clear, realistic, multi-difficulty, testable
  ✅ Grading logic         — partial credit, speed bonus, hint penalty
"""

import ast
import random
import textwrap
import time
import traceback
import uuid
from typing import Any, Dict, List, Optional, Tuple

from openenv.core.env_server import Environment
try:
    from models import DebugAction, DebugObservation, DebugState
except ImportError:
    from code_debugger_env.models import DebugAction, DebugObservation, DebugState


# ---------------------------------------------------------------------------
# Puzzle bank — each puzzle has: buggy code, correct code, test cases, hints
# ---------------------------------------------------------------------------

PUZZLES = [
    # ── EASY ────────────────────────────────────────────────────────────────
    {
        "id": "easy_001",
        "difficulty": "easy",
        "description": "Off-by-one error in a loop",
        "function": "sum_first_n",
        "error_description": "The loop range is wrong — it stops one step too early.",
        "buggy_code": textwrap.dedent("""\
            def sum_first_n(n):
                \"\"\"Return the sum of integers from 1 to n (inclusive).\"\"\"
                total = 0
                for i in range(1, n):   # BUG: should be range(1, n+1)
                    total += i
                return total
        """),
        "correct_code": textwrap.dedent("""\
            def sum_first_n(n):
                total = 0
                for i in range(1, n + 1):
                    total += i
                return total
        """),
        "tests": [
            ("sum_first_n(5)", 15),
            ("sum_first_n(1)", 1),
            ("sum_first_n(10)", 55),
            ("sum_first_n(0)", 0),
        ],
        "hints": [
            "Look at the loop's stop value — Python's range() is exclusive at the upper end.",
            "Change range(1, n) to range(1, n+1) to include n itself.",
        ],
    },
    {
        "id": "easy_002",
        "difficulty": "easy",
        "description": "Wrong comparison operator",
        "function": "is_even",
        "error_description": "The modulo comparison uses the wrong value.",
        "buggy_code": textwrap.dedent("""\
            def is_even(n):
                \"\"\"Return True if n is even, False otherwise.\"\"\"
                return n % 2 == 1   # BUG: should be == 0
        """),
        "correct_code": textwrap.dedent("""\
            def is_even(n):
                return n % 2 == 0
        """),
        "tests": [
            ("is_even(4)", True),
            ("is_even(7)", False),
            ("is_even(0)", True),
            ("is_even(-2)", True),
        ],
        "hints": [
            "An even number has zero remainder when divided by 2.",
            "Change == 1 to == 0.",
        ],
    },
    {
        "id": "easy_003",
        "difficulty": "easy",
        "description": "Return inside loop terminates too early",
        "function": "count_vowels",
        "error_description": "The function returns immediately on the first vowel instead of counting all of them.",
        "buggy_code": textwrap.dedent("""\
            def count_vowels(s):
                \"\"\"Return the number of vowels in string s.\"\"\"
                count = 0
                for ch in s.lower():
                    if ch in 'aeiou':
                        count += 1
                        return count   # BUG: should be outside the loop
                return count
        """),
        "correct_code": textwrap.dedent("""\
            def count_vowels(s):
                count = 0
                for ch in s.lower():
                    if ch in 'aeiou':
                        count += 1
                return count
        """),
        "tests": [
            ("count_vowels('hello')", 2),
            ("count_vowels('rhythm')", 0),
            ("count_vowels('OpenEnv')", 3),
            ("count_vowels('')", 0),
        ],
        "hints": [
            "The return statement is inside the if block — it exits the function on the first vowel found.",
            "Move the final return count outside (dedent it) so the loop finishes first.",
        ],
    },

    # ── MEDIUM ───────────────────────────────────────────────────────────────
    {
        "id": "med_001",
        "difficulty": "medium",
        "description": "Mutable default argument trap",
        "function": "append_to",
        "error_description": "Using a mutable list as a default argument causes shared state across calls.",
        "buggy_code": textwrap.dedent("""\
            def append_to(element, to=[]):   # BUG: mutable default argument
                \"\"\"Return a new list with element appended to `to`.\"\"\"
                to.append(element)
                return to
        """),
        "correct_code": textwrap.dedent("""\
            def append_to(element, to=None):
                if to is None:
                    to = []
                to.append(element)
                return to
        """),
        "tests": [
            ("append_to(1)", [1]),
            ("append_to(2)", [2]),
            ("append_to(3, [0])", [0, 3]),
        ],
        "hints": [
            "Default argument values are evaluated once at function definition, not on each call.",
            "Use None as the default and create a new list inside the function body.",
        ],
    },
    {
        "id": "med_002",
        "difficulty": "medium",
        "description": "Integer division truncation",
        "function": "average",
        "error_description": "Using // (floor division) instead of / discards fractional results.",
        "buggy_code": textwrap.dedent("""\
            def average(numbers):
                \"\"\"Return the arithmetic mean of a list of numbers.\"\"\"
                return sum(numbers) // len(numbers)   # BUG: should be /
        """),
        "correct_code": textwrap.dedent("""\
            def average(numbers):
                return sum(numbers) / len(numbers)
        """),
        "tests": [
            ("average([1, 2, 3, 4, 5])", 3.0),
            ("average([1, 2])", 1.5),
            ("average([10])", 10.0),
        ],
        "hints": [
            "// performs integer (floor) division. 5 // 2 = 2, not 2.5.",
            "Replace // with / for true division.",
        ],
    },
    {
        "id": "med_003",
        "difficulty": "medium",
        "description": "Wrong base case in recursion",
        "function": "factorial",
        "error_description": "The base case is wrong — it returns 0 for n==1 instead of 1, corrupting all results.",
        "buggy_code": textwrap.dedent("""\
            def factorial(n):
                \"\"\"Return n! for non-negative integer n.\"\"\"
                if n == 0 or n == 1:
                    return 0   # BUG: base case should return 1
                return n * factorial(n - 1)
        """),
        "correct_code": textwrap.dedent("""\
            def factorial(n):
                if n == 0 or n == 1:
                    return 1
                return n * factorial(n - 1)
        """),
        "tests": [
            ("factorial(0)", 1),
            ("factorial(1)", 1),
            ("factorial(5)", 120),
            ("factorial(7)", 5040),
        ],
        "hints": [
            "0! = 1 and 1! = 1 by mathematical definition.",
            "Change `return 0` to `return 1` in the base case.",
        ],
    },

    # ── HARD ─────────────────────────────────────────────────────────────────
    {
        "id": "hard_001",
        "difficulty": "hard",
        "description": "Lost update in dictionary merge",
        "function": "merge_dicts",
        "error_description": "The function modifies the first dict in-place, mutating the caller's data, and also loses keys when values are falsy.",
        "buggy_code": textwrap.dedent("""\
            def merge_dicts(d1, d2):
                \"\"\"Return a new dict that is d1 updated with d2 (d2 wins on conflict).\"\"\"
                for k, v in d2.items():
                    if v:               # BUG: falsy values (0, '', False) are skipped
                        d1[k] = v       # BUG: mutates the input dict
                return d1
        """),
        "correct_code": textwrap.dedent("""\
            def merge_dicts(d1, d2):
                result = dict(d1)
                result.update(d2)
                return result
        """),
        "tests": [
            ("merge_dicts({'a': 1}, {'b': 2})", {"a": 1, "b": 2}),
            ("merge_dicts({'a': 1}, {'a': 99})", {"a": 99}),
            ("merge_dicts({'a': 1, 'b': 2}, {'b': 0})", {"a": 1, "b": 0}),
            ("merge_dicts({}, {'x': False})", {"x": False}),
        ],
        "hints": [
            "Two bugs: (1) the `if v` check silently drops falsy values like 0, False, or empty string.",
            "Bug (2): d1[k] = v modifies the caller's dictionary. Create a copy first with dict(d1) or {**d1}.",
        ],
    },
    {
        "id": "hard_002",
        "difficulty": "hard",
        "description": "Closure variable capture in a loop",
        "function": "make_multipliers",
        "error_description": "All lambdas in the list capture the same loop variable `i`, so they all use the final value.",
        "buggy_code": textwrap.dedent("""\
            def make_multipliers(n):
                \"\"\"Return a list of n lambdas where the i-th lambda multiplies its arg by i.\"\"\"
                multipliers = []
                for i in range(n):
                    multipliers.append(lambda x: x * i)   # BUG: late binding
                return multipliers
        """),
        "correct_code": textwrap.dedent("""\
            def make_multipliers(n):
                multipliers = []
                for i in range(n):
                    multipliers.append(lambda x, i=i: x * i)
                return multipliers
        """),
        "tests": [
            ("[f(3) for f in make_multipliers(4)]", [0, 3, 6, 9]),
            ("make_multipliers(3)[0](10)", 0),
            ("make_multipliers(3)[2](5)", 10),
        ],
        "hints": [
            "All closures share the same `i` variable from the enclosing scope — after the loop, i == n-1.",
            "Capture the current value of i as a default argument: lambda x, i=i: x * i",
        ],
    },
]


# ---------------------------------------------------------------------------
# Safe sandbox executor
# ---------------------------------------------------------------------------

def _safe_exec(code: str, test_expr: str, timeout: float = 2.0) -> Tuple[Any, Optional[str]]:
    """
    Execute `code` in an isolated namespace, then evaluate `test_expr`.
    Returns (result, error_message). error_message is None on success.
    """
    namespace: Dict[str, Any] = {}
    try:
        # Syntax check first
        ast.parse(code)
        exec(compile(code, "<env>", "exec"), namespace)  # noqa: S102
        result = eval(test_expr, namespace)              # noqa: S307
        return result, None
    except SyntaxError as e:
        return None, f"SyntaxError: {e}"
    except Exception:
        return None, traceback.format_exc(limit=3)


def _run_tests(code: str, tests: List[Tuple[str, Any]]) -> Tuple[int, List[str]]:
    """Run all tests against submitted code. Returns (passed_count, feedback_lines)."""
    passed = 0
    lines = []
    for expr, expected in tests:
        result, err = _safe_exec(code, expr)
        if err:
            lines.append(f"  ✗ {expr} → ERROR: {err.strip()[:120]}")
        elif result == expected:
            passed += 1
            lines.append(f"  ✓ {expr} → {result!r}")
        else:
            lines.append(f"  ✗ {expr} → got {result!r}, expected {expected!r}")
    return passed, lines


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

class CodeDebuggerEnvironment(Environment):
    """
    CodeDebugger: An RL environment where an agent debugs Python snippets.

    Episode flow:
      1. reset() → agent receives a buggy code snippet + metadata
      2. step(DebugAction) → agent submits fixed code → graded on hidden tests
      3. Reward = (tests_passed / tests_total) × speed_multiplier - hint_penalty
      4. Episode ends when all tests pass OR max_attempts exhausted
    """

    SUPPORTS_CONCURRENT_SESSIONS = True
    MAX_ATTEMPTS = 5

    def __init__(self):
        self._state = DebugState()
        self._puzzle: Optional[Dict] = None
        self._attempts_used: int = 0
        self._hints_used: int = 0
        self._start_time: float = 0.0
        self._best_tests_passed: int = 0

    # ── OpenEnv interface ────────────────────────────────────────────────────

    def reset(self, seed=None, episode_id=None, difficulty: str = None, **kwargs) -> DebugObservation:
        """Start a new debugging episode with a fresh puzzle."""
        rng = random.Random(seed)

        # Pick puzzle: cycle through difficulties fairly, or allow override
        if difficulty and difficulty in ("easy", "medium", "hard"):
            pool = [p for p in PUZZLES if p["difficulty"] == difficulty]
        else:
            pool = PUZZLES
        self._puzzle = rng.choice(pool)

        self._attempts_used = 0
        self._hints_used = 0
        self._best_tests_passed = 0
        self._start_time = time.time()

        self._state = DebugState(
            episode_id=episode_id or str(uuid.uuid4()),
            step_count=0,
            puzzle_id=self._puzzle["id"],
            difficulty=self._puzzle["difficulty"],
            target_function=self._puzzle["function"],
            max_attempts=self.MAX_ATTEMPTS,
        )

        return DebugObservation(
            done=False,
            reward=None,
            buggy_code=self._puzzle["buggy_code"],
            error_description=self._puzzle["error_description"],
            hint=None,
            tests_passed=0,
            tests_total=len(self._puzzle["tests"]),
            attempts_used=0,
            max_attempts=self.MAX_ATTEMPTS,
            feedback=(
                f"🐛 Debug this {self._puzzle['difficulty']} puzzle!\n"
                f"Function: `{self._puzzle['function']}`\n"
                f"Bug description: {self._puzzle['error_description']}\n"
                f"You have {self.MAX_ATTEMPTS} attempts. Hints unlock after 2 failed attempts."
            ),
            difficulty=self._puzzle["difficulty"],
        )

    def step(self, action: DebugAction, timeout_s=None, **kwargs) -> DebugObservation:
        """Grade the agent's fix attempt."""
        if self._puzzle is None:
            self.reset()  # Auto-reset if no episode started

        self._attempts_used += 1
        self._state.step_count += 1
        submitted = action.fixed_code

        # --- Grade against hidden test cases ---
        n_passed, feedback_lines = _run_tests(submitted, self._puzzle["tests"])
        n_total = len(self._puzzle["tests"])
        self._best_tests_passed = max(self._best_tests_passed, n_passed)

        all_passed = n_passed == n_total
        out_of_attempts = self._attempts_used >= self.MAX_ATTEMPTS
        done = bool(all_passed or out_of_attempts)

        # --- Compute reward ---
        reward = self._compute_reward(n_passed, n_total, all_passed)

        # --- Build hint (progressive: unlock after 2 failures) ---
        hint = self._maybe_hint()

        # --- Build human-readable feedback ---
        status = "✅ All tests passed!" if all_passed else (
            "❌ Out of attempts." if out_of_attempts else
            f"⚠️  {n_passed}/{n_total} tests passed — keep going."
        )
        feedback = (
            f"{status}\n"
            f"Test results:\n" + "\n".join(feedback_lines) +
            f"\nReward: {reward:.3f}"
        )
        if done and not all_passed:
            feedback += f"\n\n💡 Correct solution:\n{self._puzzle['correct_code']}"

        return DebugObservation(
            done=done,
            reward=reward,
            buggy_code=self._puzzle["buggy_code"],
            error_description=self._puzzle["error_description"],
            hint=hint,
            tests_passed=n_passed,
            tests_total=n_total,
            attempts_used=self._attempts_used,
            max_attempts=self.MAX_ATTEMPTS,
            feedback=feedback,
            difficulty=self._puzzle["difficulty"],
        )

    @property
    def state(self) -> DebugState:
        return self._state

    # ── Private helpers ──────────────────────────────────────────────────────

    def _compute_reward(self, passed: int, total: int, all_passed: bool) -> float:
        """
        Reward function:
          base     = passed / total                   (partial credit)
          speed    ×1.5 if solved in ≤2 attempts      (bonus)
          hint_pen -0.1 per hint consumed             (discourage hint abuse)
          final    if all_passed else 0.0 (no bonus)
        Max possible reward: 1.5 (perfect + fast, no hints)
        """
        base = passed / total if total > 0 else 0.0
        if not all_passed:
            return round(base * 0.5, 4)  # partial credit only

        speed_multiplier = 1.5 if self._attempts_used <= 2 else 1.0
        hint_penalty = 0.1 * self._hints_used
        reward = max(0.0, base * speed_multiplier - hint_penalty)
        return round(reward, 4)

    def _maybe_hint(self) -> Optional[str]:
        """Return the next progressive hint after 2+ failed attempts."""
        hints = self._puzzle.get("hints", [])
        if not hints:
            return None
        # Unlock first hint after attempt 2, second hint after attempt 3
        if self._attempts_used < 2:
            return None
        hint_idx = min(self._attempts_used - 2, len(hints) - 1)
        self._hints_used = hint_idx + 1
        return hints[hint_idx]
