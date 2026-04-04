---
title: Code Debugger Env
emoji: 🐛
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
---

# 🐛 CodeDebugger — OpenEnv RL Environment

> **Hackathon submission** | Meta × PyTorch × Scaler School of Technology  
> **Author:** Nagendra Kumar Ojha  
> **Round 1 Task:** Build a complete, real-world OpenEnv environment

---

## What Is This?

**CodeDebugger** is an RL environment where an AI agent is presented with a **buggy Python function** and must submit a corrected version. The agent is graded on **hidden test cases**, receives **partial credit**, gets **speed bonuses** for fast fixes, and can unlock **progressive hints** after failed attempts.

This maps directly to a real-world, high-value skill: automated program repair — used in developer tools, LLM code assistants, and software QA pipelines.

---

## Quick Start

```python
# Install
pip install git+https://huggingface.co/spaces/nagendraojha/code-debugger-env

# Use (sync)
from code_debugger_env import CodeDebuggerEnv, DebugAction

with CodeDebuggerEnv(base_url="https://nagendraojha-code-debugger-env.hf.space").sync() as env:
    obs = env.reset()
    print(obs.buggy_code)        # See the broken function
    print(obs.error_description) # Understand the bug category

    fixed = obs.buggy_code.replace("range(1, n)", "range(1, n + 1)")  # Fix it!
    result = env.step(DebugAction(fixed_code=fixed))
    print(result.observation.feedback)  # ✅ All tests passed!
    print(result.reward)                # 1.5 (perfect + speed bonus)
```

---

## Environment Interface

Follows the standard OpenEnv 3-method interface: `reset()`, `step()`, `state()`.

### Action
```python
class DebugAction(Action):
    fixed_code: str   # The agent's corrected Python function
```

### Observation
```python
class DebugObservation(Observation):
    buggy_code: str             # The broken snippet
    error_description: str      # Bug category description
    hint: Optional[str]         # Progressive hint (unlocks after 2 failed attempts)
    tests_passed: int           # Tests passed on last submission
    tests_total: int            # Total test cases
    attempts_used: int          # Attempts consumed so far
    max_attempts: int           # Max = 5
    feedback: str               # Detailed test-by-test results
    difficulty: str             # "easy" | "medium" | "hard"
```

### State
```python
class DebugState(State):
    puzzle_id: str
    difficulty: str
    target_function: str
    max_attempts: int
```

---

## Reward Function

| Scenario | Reward |
|---|---|
| All tests pass in ≤ 2 attempts, no hints | **1.5** (max) |
| All tests pass, 3–5 attempts | **1.0** |
| All tests pass + hints used | **1.0 – 0.1×hints** |
| Partial pass (not done) | **0.5 × (passed/total)** |
| 0 tests pass | **0.0** |

---

## Puzzle Difficulties

| Level | Bug Types |
|---|---|
| 🟢 Easy | Off-by-one, wrong operator, misplaced return |
| 🟡 Medium | Mutable defaults, integer division, wrong base case |
| 🔴 Hard | Closure capture bugs, dict mutation, falsy value traps |

---

## File Structure

```
code_debugger_env/
├── models.py               ← Action, Observation, State types
├── client.py               ← CodeDebuggerEnv(EnvClient)
├── server/
│   ├── environment.py      ← Game logic (reset, step, state)
│   ├── app.py              ← FastAPI server
│   ├── Dockerfile          ← Container definition
│   └── requirements.txt
├── openenv.yaml            ← Manifest
├── pyproject.toml
└── README.md
```

---

## Deployment

```bash
# Test locally
uv run server

# Deploy to Hugging Face Spaces
openenv push --repo-id nagendraojha/code-debugger-env
```

Live endpoints (after deploy):
- **API:** `https://nagendraojha-code-debugger-env.hf.space`
- **Web UI:** `https://nagendraojha-code-debugger-env.hf.space/web`
- **Docs:** `https://nagendraojha-code-debugger-env.hf.space/docs`

---

## Design Highlights

1. **Real-world task** — Automated program repair is used in GitHub Copilot, SWE-bench, and code review tools
2. **Sandboxed execution** — Submissions run in an isolated `exec()` namespace with AST pre-validation
3. **Partial credit** — Agents are rewarded proportionally for passing some tests, not just all-or-none
4. **Progressive hints** — Encourages the agent to try independently before consuming hints (hint penalty)
5. **Speed bonus** — Rewards agents that solve efficiently in ≤2 attempts (×1.5 multiplier)
6. **Multi-difficulty** — 3 difficulty levels with 8 puzzles covering classic Python bug patterns
7. **Concurrent sessions** — `SUPPORTS_CONCURRENT_SESSIONS = True` for scalable RL training
