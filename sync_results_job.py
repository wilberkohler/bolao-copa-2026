"""Cron entrypoint for automatic result synchronization."""

import os
import sys

from app import create_app, db, run_result_sync_job


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    app = create_app()
    knockout_only = _env_flag("RESULT_SYNC_KNOCKOUT_ONLY", False)

    try:
        with app.app_context():
            result = run_result_sync_job(
                launched_by="sync-cron-job",
                knockout_only=knockout_only,
                send_reports=True,
            )
    except Exception as exc:
        with app.app_context():
            db.session.rollback()
        print(f"[sync-results-job] failed: {exc}", file=sys.stderr)
        return 1

    stats = result["stats"]
    emails = result["email_reports"]
    print(
        "[sync-results-job] "
        f"knockout_only={stats.get('knockout_only')} "
        f"finished={stats.get('finished', False)} "
        f"window={stats.get('date_from')}..{stats.get('date_to')} "
        f"fetched={stats.get('fetched')} "
        f"created={stats.get('created')} "
        f"updated={stats.get('updated')} "
        f"unchanged={stats.get('unchanged')} "
        f"recalculated={stats.get('recalculated')} "
        f"unmatched={len(stats.get('unmatched') or [])} "
        f"reports_sent={emails.get('sent')} "
        f"reports_skipped={emails.get('skipped')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
