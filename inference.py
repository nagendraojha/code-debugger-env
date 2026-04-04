"""
inference.py — CodeDebugger OpenEnv Environment
Demonstrates how an AI agent interacts with the CodeDebugger environment.
Required by the OpenEnv hackathon automated checks.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openenv.core.env_client import EnvClient
from models import DebugAction, DebugObservation, DebugState
from client import CodeDebuggerEnv

BASE_URL = os.environ.get("SPACE_URL", "https://nagendraojha-code-debugger-env.hf.space")

def run_inference(base_url: str = BASE_URL):
    """Run one full episode: reset, submit a fix, get result."""
    with CodeDebuggerEnv(base_url=base_url).sync() as env:
        # Step 1: Reset — get a buggy puzzle
        obs = env.reset()
        print("=" * 60)
        print(f"Difficulty: {obs.difficulty}")
        print(f"Bug description: {obs.error_description}")
        print(f"Buggy code:\n{obs.buggy_code}")
        print(f"Tests total: {obs.tests_total}")

        # Step 2: Submit a simple fix attempt
        # A real agent would use an LLM to generate the fix.
        # Here we demonstrate the interface with a placeholder.
        fixed_code = obs.buggy_code  # placeholder: submit as-is
        result = env.step(DebugAction(fixed_code=fixed_code))

        print("=" * 60)
        print(f"Tests passed: {result.observation.tests_passed}/{result.observation.tests_total}")
        print(f"Reward: {result.reward}")
        print(f"Done: {result.done}")
        print(f"Feedback:\n{result.observation.feedback}")
        return result

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else BASE_URL
    run_inference(url)
