#!/usr/bin/env python3
"""Promote an existing user to admin by email.

Usage:
  python backend/scripts/create_admin.py user@example.com
"""

from __future__ import annotations

import sys

from app.core.plans import PLAN_ADMIN
from app.core.security import ROLE_ADMIN
from app.db.models import User
from app.db.session import SessionLocal


def promote_admin(email: str) -> int:
    normalized = email.strip().lower()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == normalized).first()
        if user is None:
            print(f"No user found for {normalized}")
            return 1
        user.role = ROLE_ADMIN
        user.plan = PLAN_ADMIN
        db.commit()
        print(f"Promoted {normalized} to admin (id={user.id})")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python backend/scripts/create_admin.py user@example.com")
        sys.exit(2)
    sys.exit(promote_admin(sys.argv[1]))
