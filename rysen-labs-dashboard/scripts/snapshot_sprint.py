from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.services.sprint_snapshot_service import SprintSnapshotService  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a daily Rysen Labs sprint progress snapshot.")
    parser.add_argument("--date", help="Optional snapshot date in YYYY-MM-DD format. Defaults to today.")
    args = parser.parse_args()

    snapshot_date = date.fromisoformat(args.date) if args.date else None
    path = SprintSnapshotService(get_settings()).write_snapshot(snapshot_date)
    print(f"Wrote sprint snapshot: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
