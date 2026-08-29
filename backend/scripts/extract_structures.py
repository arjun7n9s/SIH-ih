"""Extract fee/refund tables into data/index/tables.json"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
load_dotenv(BACKEND.parent / ".env")

from app.services.extract import build_tables  # noqa: E402
from app.services import store  # noqa: E402


def main() -> int:
    cards = build_tables()
    store.clear_cache()
    print(f"{len(cards)} tables -> {store.TABLES_PATH}")
    return 0 if cards else 1


if __name__ == "__main__":
    raise SystemExit(main())
