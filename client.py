"""
CodeDebugger Environment — client.py
Type-safe client that translates between typed models and the WebSocket wire format.
"""

from openenv.core.env_client import EnvClient
from openenv.core.client_types import StepResult
try:
    from models import DebugAction, DebugObservation, DebugState
except ImportError:
    from code_debugger_env.models import DebugAction, DebugObservation, DebugState


class CodeDebuggerEnv(EnvClient[DebugAction, DebugObservation, DebugState]):
    """
    Client for the CodeDebugger environment.

    Usage (sync):
        with CodeDebuggerEnv(base_url="https://<your-space>.hf.space").sync() as env:
            obs = env.reset()
            print(obs.buggy_code)
            result = env.step(DebugAction(fixed_code="def sum_first_n(n): ..."))
            print(result.observation.feedback)

    Usage (async):
        async with CodeDebuggerEnv(base_url="...") as env:
            obs = await env.reset()
            result = await env.step(DebugAction(fixed_code="..."))
    """

    def _step_payload(self, action: DebugAction) -> dict:
        """Serialize action → wire format dict."""
        return {"fixed_code": action.fixed_code}

    def _parse_result(self, payload: dict) -> StepResult:
        """Deserialize wire format → typed StepResult."""
        obs_data = payload.get("observation", {})
        return StepResult(
            observation=DebugObservation(
                done=payload.get("done", False),
                reward=payload.get("reward"),
                buggy_code=obs_data.get("buggy_code", ""),
                error_description=obs_data.get("error_description", ""),
                hint=obs_data.get("hint"),
                tests_passed=obs_data.get("tests_passed", 0),
                tests_total=obs_data.get("tests_total", 0),
                attempts_used=obs_data.get("attempts_used", 0),
                max_attempts=obs_data.get("max_attempts", 5),
                feedback=obs_data.get("feedback", ""),
                difficulty=obs_data.get("difficulty", "easy"),
            ),
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict) -> DebugState:
        """Deserialize wire format → typed DebugState."""
        return DebugState(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
            puzzle_id=payload.get("puzzle_id", ""),
            difficulty=payload.get("difficulty", "easy"),
            target_function=payload.get("target_function", ""),
            max_attempts=payload.get("max_attempts", 5),
        )
