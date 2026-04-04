"""
CodeDebugger Environment — server/app.py
Uses singleton environment instance so /reset and /step share state.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openenv.core.env_server import create_fastapi_app
from environment import CodeDebuggerEnvironment
from models import DebugAction, DebugObservation

# Singleton: one shared instance so /reset and /step share the same state
_env_instance = CodeDebuggerEnvironment()

def env_factory():
    """Return the singleton environment instance."""
    return _env_instance

# Wire up FastAPI with our singleton factory
app = create_fastapi_app(env_factory, DebugAction, DebugObservation)

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
