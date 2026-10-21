"""src.closer.audit.logger — CSV audit trail (Phase 4).

Appends one row to logs/outreach_log.csv per outreach action.
Auto-creates the file with headers on first write.
"""
from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOG_FILE = _PROJECT_ROOT / "logs" / "outreach_log.csv"

FIELDNAMES: list[str] = [
    "timestamp",
    "recipient_email",
    "company",
    "role",
    "subject",
    "status",
    "error_message",
    "word_count",
]

VALID_STATUSES: set[str] = {
    "generated",
    "drafted",
    "sent",
    "skipped",
    "failed",
    "opted_out",
    "skipped_duplicate",
    "skipped_limit",
    "dry_run",
    "drafted_locally",
}


def _sync_root_symlink(log_file: Path) -> None:
    """Ensure root outreach_log.csv points to logs/outreach_log.csv for convenience."""
    try:
        # Only sync if log_file is within this project (not in temporary test directories)
        log_file.resolve().relative_to(_PROJECT_ROOT.resolve())
    except ValueError:
        return

    root_file = _PROJECT_ROOT / "outreach_log.csv"
    try:
        if root_file.is_symlink() or root_file.exists():
            if root_file.resolve() == log_file.resolve():
                return
            root_file.unlink(missing_ok=True)
        rel_path = os.path.relpath(log_file, _PROJECT_ROOT)
        root_file.symlink_to(rel_path)
    except (OSError, NotImplementedError):
        pass


def _ensure_header(target_file: Path) -> None:
    """Create the CSV file with headers if it does not exist or is empty (EC-5.3)."""
    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        if not target_file.exists() or target_file.stat().st_size == 0:
            with open(target_file, "a", encoding="utf-8-sig", newline="") as f:
                if f.tell() == 0:
                    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                    writer.writeheader()
        if target_file == LOG_FILE:
            _sync_root_symlink(target_file)
    except PermissionError:
        print(
            f"  Warning: Permission denied writing header to {target_file.name}. "
            f"Please close the file if open in another program (e.g. Excel) and retry."
        )
    except OSError as exc:
        print(
            f"  Warning: Disk or I/O error writing header to {target_file.name}: {exc}. "
            f"Session continuing."
        )


def log_entry(
    contact: Mapping[str, Any] | Any,
    subject: str,
    status: str,
    error: str = "",
    body: str = "",
    log_file: Path | str | None = None,
) -> None:
    """Append one row to outreach_log.csv.

    Args:
        contact: Contact dictionary or dataclass instance.
        subject: Subject line generated or used.
        status: Action status (e.g. sent, drafted, skipped, failed, dry_run).
        error: Error message string if failed, else empty string.
        body: Body of the email (used to compute word_count).
        log_file: Optional override path for the CSV log file. Defaults to LOG_FILE.
    """
    if status not in VALID_STATUSES:
        print(
            f"  Warning: Unexpected status '{status}'. Expected one of {sorted(VALID_STATUSES)}"
        )

    # Support dict or dataclass/object for contact
    if hasattr(contact, "__dict__") and not isinstance(contact, Mapping):
        contact_dict = vars(contact)
    elif isinstance(contact, Mapping):
        contact_dict = dict(contact)
    else:
        contact_dict = {}

    target_file = Path(log_file) if log_file else LOG_FILE
    _ensure_header(target_file)

    word_count = len(body.split()) if body else 0
    row = {
        "timestamp": datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %I:%M:%S %p IST"),
        "recipient_email": str(contact_dict.get("recipient_email", "") or ""),
        "company": str(contact_dict.get("company", "") or ""),
        "role": str(contact_dict.get("role", "") or ""),
        "subject": str(subject or ""),
        "status": str(status or ""),
        "error_message": str(error or ""),
        "word_count": word_count,
    }

    try:
        with open(target_file, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writerow(row)
        print(f"  Logged: [{status}] -> {target_file}")
    except PermissionError:
        print(
            f"  Warning: Permission denied writing to {target_file.name}. "
            f"Please close the file if open in another program (e.g. Excel) and retry."
        )
    except OSError as exc:
        print(
            f"  Warning: Disk or I/O error writing to {target_file.name}: {exc}. "
            f"Session continuing."
        )


def get_log_summary(log_file: Path | str | None = None) -> dict[str, int]:
    """Return a status -> count dict from the current log file.

    Counts all occurrences grouped by status. Returns an empty dict if the file
    does not exist or cannot be read.
    """
    target_file = Path(log_file) if log_file else LOG_FILE
    if not target_file.exists():
        # Fallback check for root outreach_log.csv
        root_csv = _PROJECT_ROOT / "outreach_log.csv"
        if log_file is None and root_csv.exists():
            target_file = root_csv
        else:
            return {}

    summary: dict[str, int] = {}
    try:
        with open(target_file, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                s = row.get("status")
                if s:
                    summary[s] = summary.get(s, 0) + 1
    except PermissionError:
        print(
            f"  Warning: Permission denied reading log {target_file.name}."
        )
    except OSError as exc:
        print(
            f"  Warning: I/O error reading log {target_file.name}: {exc}."
        )
    return summary
