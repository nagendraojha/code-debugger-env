"""
CodeDebugger Environment — server/app.py
Creates the FastAPI app with all OpenEnv standard endpoints.
"""

import sys
import os

# Add both the server dir and the project root to path
_server_dir = os.path.dirname(os.path.abspath(__file__))
_project_dir = os.path.dirname(_server_dir)
sys.path.insert(0, _server_dir)
sys.path.insert(0, _project_dir)

from openenv.core.env_server import create_fastapi_app
from environment import CodeDebuggerEnvironment
from models import DebugAction, DebugObservation

# create_fastapi_app wires up: /ws /reset /step /state /health /web /docs
app = create_fastapi_app(CodeDebuggerEnvironment, DebugAction, DebugObservation)
