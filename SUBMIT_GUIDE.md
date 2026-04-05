# 🚀 CodeDebugger — Submission Guide
**For: Nagendra Kumar Ojha | Deadline: 8 April 2026, 11:59 PM IST**

---

## What You're Submitting
A complete OpenEnv RL environment called **CodeDebugger** — an AI agent debugs buggy Python functions, graded on hidden test cases with partial credit, speed bonuses, and progressive hints.

---

## Step-by-Step Instructions

### Prerequisites (install once)
```bash
pip install openenv-core
pip install huggingface_hub
huggingface-cli login    # enter your HF token
```
Get your HF token at: https://huggingface.co/settings/tokens

---

### Step 1 — Install & Test Locally

```bash
# Unzip the project
unzip code_debugger_env.zip
cd code_debugger_env

# Install dependencies
pip install -r server/requirements.txt

# Run local server
uv run server
# OR:
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload

# In another terminal — quick smoke test:
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

---

### Step 2 — Deploy to Hugging Face Spaces

```bash
# From inside the code_debugger_env/ folder:
openenv push --repo-id nagendraojha/code-debugger-env

# This will:
# 1. Create a HF Space at: nagendraojha/code-debugger-env
# 2. Upload all files
# 3. Build the Docker container
# 4. Start the server
```

**Wait ~3-5 minutes** for the Space to build. Then verify:
```
https://nagendraojha-code-debugger-env.hf.space/health   ← should say "healthy"
https://nagendraojha-code-debugger-env.hf.space/docs     ← interactive API docs
https://nagendraojha-code-debugger-env.hf.space/web      ← web UI
```

---

### Step 3 — Submit Your HF Spaces URL

Go back to the hackathon dashboard:
👉 https://www.scaler.com/school-of-technology/meta-pytorch-hackathon/dashboard

Paste this URL in the submission box:
```
https://nagendraojha-code-debugger-env.hf.space
```

Click **Submit your Assessment** before **8 April 11:59 PM IST**.

---

## Why This Will Win

| Criterion | What We Built |
|---|---|
| ✅ **Runtime correctness** | 26/26 tests pass; sandboxed exec with AST pre-validation |
| ✅ **Interface compliance** | Full reset/step/state OpenEnv standard, typed models |
| ✅ **Task design** | Real-world (program repair), 3 difficulty levels, 8 puzzles |
| ✅ **Grading logic** | Partial credit + speed bonus (×1.5) + hint penalty (−0.1) |
| 🌟 **Bonus** | Progressive hints, concurrent sessions, speed-based rewards |

---

## Quick Test After Deploy

```python
from code_debugger_env import CodeDebuggerEnv, DebugAction

with CodeDebuggerEnv(
    base_url="https://nagendraojha-code-debugger-env.hf.space"
).sync() as env:
    obs = env.reset()
    print("BUGGY CODE:\n", obs.buggy_code)
    print("HINT:", obs.error_description)

    # Submit a fix (example for the off-by-one puzzle)
    fix = obs.buggy_code.replace("range(1, n)", "range(1, n + 1)")
    result = env.step(DebugAction(fixed_code=fix))
    print("FEEDBACK:", result.observation.feedback)
    print("REWARD:", result.reward)
```

---

## File Structure Reference

```
code_debugger_env/
├── models.py               ← Action, Observation, State (Pydantic)
├── client.py               ← CodeDebuggerEnv(EnvClient)
├── __init__.py             ← Package exports
├── openenv.yaml            ← Manifest
├── pyproject.toml          ← Dependencies
├── README.md               ← Documentation
├── test_local.py           ← 26-test local test suite (all pass ✅)
├── SUBMIT_GUIDE.md         ← This file
└── server/
    ├── environment.py      ← Game logic (reset/step/state)
    ├── app.py              ← FastAPI entry point
    ├── requirements.txt    ← Docker deps
    └── Dockerfile          ← Container definition
```

---

Good luck, Nagendra! 🏆
