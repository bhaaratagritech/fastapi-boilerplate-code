#!/usr/bin/env python3
"""
Utility script to generate JWTs for local testing.

Usage:
    python scripts/generate_jwt.py --sub user@example.com --role admin

Defaults pull from environment variables (`JWT_SECRET`, `JWT_ALGORITHM`, etc.)
so tokens match your FastAPI configuration.
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from jose import jwt


# Load .env from the project root so JWT_* values are available automatically.
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a JWT for calling protected API endpoints."
    )
    parser.add_argument("--sub", default="user@example.com", help="Subject / user identifier.")
    parser.add_argument("--role", default="admin", help="Role claim to embed in the token.")
    parser.add_argument("--hours", type=int, default=1, help="Validity period in hours.")
    parser.add_argument("--secret", default=os.getenv("JWT_SECRET", "changeme"), help="JWT secret key.")
    parser.add_argument("--algorithm", default=os.getenv("JWT_ALGORITHM", "HS256"), help="JWT algorithm.")
    parser.add_argument("--aud", default=os.getenv("JWT_AUDIENCE"), help="Audience claim (optional).")
    parser.add_argument("--iss", default=os.getenv("JWT_ISSUER"), help="Issuer claim (optional).")
    parser.add_argument("--debug", action="store_true", help="Print resolved configuration before generating token.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.debug:
        print("Resolved configuration:")
        print(f"  JWT_SECRET     : {args.secret}")
        print(f"  JWT_ALGORITHM  : {args.algorithm}")
        print(f"  JWT_AUDIENCE   : {args.aud or '(not set)'}")
        print(f"  JWT_ISSUER     : {args.iss or '(not set)'}")
        print(f"  Subject (sub)  : {args.sub}")
        print(f"  Role           : {args.role}")
        print(f"  Lifetime (hrs) : {args.hours}")

    now = datetime.now(timezone.utc)
    claims = {
        "sub": args.sub,
        "role": args.role,
        "exp": now + timedelta(hours=args.hours),
        "iat": now,
    }
    if args.aud:
        claims["aud"] = args.aud
    if args.iss:
        claims["iss"] = args.iss

    token = jwt.encode(claims, args.secret, algorithm=args.algorithm)
    print(token)


if __name__ == "__main__":
    main()

