"""Vercel Serverless Function entrypoint for Ameya Consultancy FastAPI API."""

import sys
from pathlib import Path

# Add backend to sys.path so internal imports (lib, models, routers) resolve cleanly
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Import the pre-configured FastAPI app from backend/server.py
from server import app  # noqa: E402
