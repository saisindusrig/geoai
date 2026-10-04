"""Seed a demo project with boundary, site analysis, and a generated design.

Run from backend/:  python -m scripts.seed_demo
Requires the backend dependencies (and optionally the API server stopped --
it talks to the DB directly).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.demo_seed import DEMO_PROJECT_ID, ensure_demo_project  # noqa: E402
from app.db.init_db import init_db  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        project = ensure_demo_project(db)
        db.commit()
        if project:
            print(f"Demo project ready (id={project.id}, expected={DEMO_PROJECT_ID})")
        else:
            print("Demo project could not be seeded (id conflict)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
