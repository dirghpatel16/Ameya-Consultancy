"""Shared Mongo handle — import `client`/`db` from here (server.py, routers, seed.py)."""

import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load .env if present
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
db_name = os.environ.get("DB_NAME", "ameya_consultancy")

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]
