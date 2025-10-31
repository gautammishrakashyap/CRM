#!/usr/bin/env python3
"""Generate a JWT using SECRET_KEY and ALGORITHM from .env (or constants here).

Usage:
  python scripts/generate_token.py --sub admin --minutes 30
"""
import argparse
import datetime
import os
from pathlib import Path

try:
    import jwt
except ImportError:
    raise SystemExit("Please install PyJWT in the venv: pip install pyjwt")

try:
    from dotenv import load_dotenv
except Exception:
    # dotenv is optional; only used when .env exists
    load_dotenv = None

# Try to load .env from project root when present
project_root = Path(__file__).resolve().parents[1]
env_path = project_root / '.env'
if load_dotenv and env_path.exists():
    load_dotenv(env_path)

# Defaults - prefer environment variables (.env or OS)
SECRET_KEY = os.environ.get("SECRET_KEY", "testestet12345678909876543210")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")

parser = argparse.ArgumentParser()
parser.add_argument("--sub", default="admin", help="sub (subject) claim")
parser.add_argument("--minutes", type=int, default=30, help="expiry in minutes")
args = parser.parse_args()

payload = {
    "sub": args.sub,
    # keep naive UTC for simplicity; server must interpret similarly
    "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=args.minutes)
}

token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
print(token)
