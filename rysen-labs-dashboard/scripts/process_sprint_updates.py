from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import Settings, get_settings  # noqa: E402
from app.services.sprint_service import SprintService  # noqa: E402
from app.services.sprint_sync_service import SprintUpdateInboxService  # noqa: E402


def _progress(settings: Settings) -> str:
    sprint = SprintService(settings).load_sprint()
    return f"{sprint.progress.completed_points}/{sprint.progress.total_points} points ({sprint.progress.progress_percentage}%)"


def main() -> int:
    parser = argparse.ArgumentParser(description="Process pending Rysen Labs sprint_update files.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Validate and report without mutating sprint state or moving files.")
    mode.add_argument("--apply", action="store_true", help="Apply authorized update status changes and archive update files.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="Process one pending update file.")
    source.add_argument("--all", action="store_true", help="Process all pending update files.")
    args = parser.parse_args()

    settings = get_settings()
    inbox = SprintUpdateInboxService(settings)
    before = _progress(settings)
    records = (
        inbox.process_all(apply=args.apply)
        if args.all
        else [inbox.process_file(Path(args.file), apply=args.apply)]
    )
    after = _progress(settings)

    print(f"Sprint progress before: {before}")
    for record in records:
        print("---")
        print(f"update_id: {record.update_id}")
        print(f"project: {record.project}")
        print(f"task: {record.task}")
        print(f"checkpoint: {record.checkpoint or ''}")
        print(f"recommended_status: {record.recommended_status or ''}")
        print(f"applied: {record.applied}")
        print(f"already_processed: {record.already_processed}")
        if record.validation_error:
            print(f"validation_error: {record.validation_error}")
        if record.archived_file:
            print(f"archived_file: {record.archived_file}")
    print(f"Sprint progress after: {after}")

    return 1 if any(record.validation_error for record in records) else 0


if __name__ == "__main__":
    raise SystemExit(main())
