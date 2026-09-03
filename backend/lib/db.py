"""Shared Mongo handle — import `client`/`db` from here (server.py, routers, seed.py)."""

import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

try:
    import certifi
    ca_file = certifi.where()
except ImportError:
    ca_file = None

# Load .env if present
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
db_name = os.environ.get("DB_NAME", "ameya_consultancy")

kwargs = {}
if ca_file and "mongodb+srv" in mongo_url:
    kwargs["tlsCAFile"] = ca_file

client = AsyncIOMotorClient(mongo_url, **kwargs)
db = client[db_name]
