# upload_to_hf.py — Run this to upload your project to HuggingFace Spaces
# Usage: python upload_to_hf.py YOUR_HF_TOKEN

import sys
import os
from huggingface_hub import HfApi, create_repo

TOKEN = sys.argv[1] if len(sys.argv) > 1 else input("Paste your HF token: ").strip()
REPO_ID = "nagendraojha/code-debugger-env"
REPO_TYPE = "space"

api = HfApi(token=TOKEN)

print(f"\n🚀 Creating Space: {REPO_ID}...")
try:
    create_repo(
        repo_id=REPO_ID,
        repo_type=REPO_TYPE,
        space_sdk="docker",
        token=TOKEN,
        exist_ok=True,
        private=False,
    )
    print("✅ Space created (or already exists)")
except Exception as e:
    print(f"Space creation note: {e}")

# Files to upload: (local_path, path_in_repo)
BASE = os.path.dirname(os.path.abspath(__file__))
FILES = [
    ("models.py",               "models.py"),
    ("client.py",               "client.py"),
    ("__init__.py",             "__init__.py"),
    ("openenv.yaml",            "openenv.yaml"),
    ("pyproject.toml",          "pyproject.toml"),
    ("README.md",               "README.md"),
    ("server/app.py",           "server/app.py"),
    ("server/environment.py",   "server/environment.py"),
    ("server/requirements.txt", "server/requirements.txt"),
    ("server/Dockerfile",       "Dockerfile"),
    ("server/__init__.py",      "server/__init__.py"),
]

print(f"\n📤 Uploading {len(FILES)} files...")
for local, remote in FILES:
    local_path = os.path.join(BASE, local)
    if not os.path.exists(local_path):
        print(f"  ⚠️  Skipping (not found): {local}")
        continue
    try:
        api.upload_file(
            path_or_fileobj=local_path,
            path_in_repo=remote,
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            token=TOKEN,
        )
        print(f"  ✅ {remote}")
    except Exception as e:
        print(f"  ❌ {remote}: {e}")

print(f"""
🎉 DONE! Your Space is live at:
   https://huggingface.co/spaces/{REPO_ID}

Wait 3-5 mins for Docker to build, then check:
   https://nagendraojha-code-debugger-env.hf.space/health

Then submit that URL on the hackathon dashboard!
""")
