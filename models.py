"""
CodeDebugger Environment — models.py
Type-safe data contracts for the CodeDebugger RL environment.

An AI agent is shown buggy Python code and must submit a fixed version.
The environment grades the fix by running hidden test cases.
"""

from typing import List, Optional
from openenv.core.env_server import Action, Observation, State


class DebugAction(Action):
    """The agent's fix attempt: a corrected Python code string."""
    fixed_code: str  # The agent's corrected version of the buggy code


class DebugObservation(Observation):
    """
    What the agent sees after each step.
    Inherits: done: bool, reward: Optional[float]
    """
    buggy_code: str            # The broken Python snippet to fix
    error_description: str     # Human-readable description of the bug category
    hint: Optional[str]        # Progressive hint (unlocked after N failed attempts)
    tests_passed: int          # Number of test cases passed so far
    tests_total: int           # Total test cases
    attempts_used: int         # How many fix attempts consumed
    max_attempts: int          # Max allowed
    feedback: str              # Detailed feedback on last submission
    difficulty: str            # "easy" | "medium" | "hard"


class DebugState(State):
    """
    Episode metadata.
    Inherits: episode_id: Optional[str], step_count: int
    """
    puzzle_id: str = ""        # Unique ID of the current puzzle
    difficulty: str = "easy"
    target_function: str = ""  # Name of the function being debugged
    max_attempts: int = 5
