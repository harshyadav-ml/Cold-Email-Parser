"""src.closer.input.loader — contact record I/O (JSON and CSV).

Reads outreach targets from contacts.json (Phase 1) or a CSV file (Phase 5 stretch).
Also manages the opt-out list (optout_list.txt) to prevent unwanted outreach.
"""
from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path
from typing import Any, Optional

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTACTS_PATH = _PROJECT_ROOT / "data" / "contacts.json"
DEFAULT_OPTOUT_PATH = _PROJECT_ROOT / "optout_list.txt"

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

COLUMN_ALIASES: dict[str, list[str]] = {
    "recipient_email": ["recipient_email", "email", "recipient_mail", "contact_email", "mail", "e-mail"],
    "recipient_name": ["recipient_name", "name", "contact_name", "hiring_manager", "lead_name", "full_name"],
    "company": ["company", "company_name", "organization", "org", "firm", "team"],
    "role": ["role", "job_title", "title", "position"],
    "job_url": ["job_url", "url", "job_link", "link", "posting_url", "job_posting"],
    "personalization_note": ["personalization_note", "note", "notes", "personalization", "hook", "icebreaker"],
    "candidate_name": ["candidate_name", "applicant_name", "sender_name", "my_name"],
    "candidate_background": ["candidate_background", "background", "bio", "experience", "candidate_bio"],
    "portfolio_url": ["portfolio_url", "portfolio", "github", "github_url", "website", "links"],
}

SAMPLE_TEMPLATE_RECORDS: list[dict[str, str]] = [
    {
        "recipient_name": "Priya Sharma",
        "recipient_email": "priya@acmeai.com",
        "company": "Acme AI",
        "role": "Backend Engineering Intern",
        "job_url": "https://acmeai.com/jobs/backend-intern",
        "personalization_note": "Acme AI recently launched an AI workflow automation product",
        "candidate_name": "Harsh Yadav",
        "candidate_background": "Python developer with experience in automation and AI agents",
        "portfolio_url": "https://github.com/alexchen",
    },
    {
        "recipient_name": "Rahul Verma",
        "recipient_email": "rahul@startupxyz.io",
        "company": "StartupXYZ",
        "role": "ML Engineer",
        "job_url": "https://startupxyz.io/careers",
        "personalization_note": "StartupXYZ is building LLM-powered search tools",
        "candidate_name": "Harsh Yadav",
        "candidate_background": "machine learning projects and open-source LLM tooling",
        "portfolio_url": "https://github.com/alexchen",
    },
]


def validate_contact_record(rec: dict) -> dict | None:
    """Validate and normalize a single contact dictionary.

    Checks required fields ('recipient_email', 'company', 'role').
    Enforces valid email address formatting.
    Populates reasonable defaults for candidate info and hiring manager.
    Preserves any additional custom metadata.

    Returns:
        Cleaned contact dict, or None if malformed/invalid.
    """
    if not isinstance(rec, dict):
        return None

    normalized_incoming: dict[str, Any] = {}
    for k, v in rec.items():
        if k is not None:
            normalized_incoming[str(k).strip().lower()] = v

    canonical: dict[str, str] = {}
    for key, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized_incoming and normalized_incoming[alias] is not None:
                val = str(normalized_incoming[alias]).strip()
                if val:
                    canonical[key] = val
                    break

    email = canonical.get("recipient_email", "").strip().lower()
    company = canonical.get("company", "").strip()
    role = canonical.get("role", "").strip()

    # Required fields check (EC-1.3, EC-1.4, EC-1.7)
    if not email or not company or not role:
        return None
    if not EMAIL_REGEX.match(email):
        return None

    cleaned: dict[str, Any] = {
        "recipient_name": canonical.get("recipient_name") or "Hiring Manager",
        "recipient_email": email,
        "company": company,
        "role": role,
        "job_url": canonical.get("job_url") or None,
        "personalization_note": canonical.get("personalization_note") or None,
        "candidate_name": canonical.get("candidate_name") or "Harsh Yadav",
        "candidate_background": canonical.get("candidate_background") or "AI Engineer with experience in agentic workflows",
        "portfolio_url": canonical.get("portfolio_url") or "https://github.com/alexchen",
    }

    # Retain any extra unmapped keys
    known_aliases = {a for aliases in COLUMN_ALIASES.values() for a in aliases}
    for k, v in normalized_incoming.items():
        if k not in known_aliases and k not in cleaned and v is not None:
            cleaned[k] = v

    return cleaned


def parse_contacts_buffer(content: str | bytes, filename: str = "contacts.json") -> tuple[list[dict], int]:
    """Parse JSON or CSV content buffer, validate contacts, and skip malformed records.

    Returns:
        tuple of (valid_contacts_list, skipped_invalid_count)
    """
    if isinstance(content, bytes):
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("latin-1", errors="replace")
    else:
        text = str(content)

    ext = Path(filename).suffix.lower() if filename else ".json"

    raw_records: list[Any] = []
    if ext == ".csv":
        fh = io.StringIO(text)
        reader = csv.DictReader(fh)
        raw_records = [dict(row) for row in reader]
    else:
        try:
            data = json.loads(text)
        except Exception as exc:
            raise ValueError(f"Malformed JSON content: {exc}")

        if isinstance(data, list):
            raw_records = data
        elif isinstance(data, dict):
            if "contacts" in data and isinstance(data["contacts"], list):
                raw_records = data["contacts"]
            elif "data" in data and isinstance(data["data"], list):
                raw_records = data["data"]
            else:
                raw_records = [data]
        else:
            raise ValueError("JSON must be a list of records or an object containing a 'contacts' list.")

    valid_contacts: list[dict] = []
    skipped_count = 0
    for item in raw_records:
        cleaned = validate_contact_record(item)
        if cleaned:
            valid_contacts.append(cleaned)
        else:
            skipped_count += 1

    return valid_contacts, skipped_count


def save_contacts(contacts: list[dict], path: str | Path | None = None) -> Path:
    """Persist contacts list to disk as formatted JSON.

    Args:
        contacts: List of contact record dicts.
        path: Destination file path. Defaults to ``DEFAULT_CONTACTS_PATH``.

    Returns:
        The resolved Path where contacts were written.
    """
    target = Path(path) if path else DEFAULT_CONTACTS_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as fh:
        json.dump(contacts, fh, indent=2)
    return target


def load_contacts(path: str | Path | None = None) -> list[dict]:
    """Load contact records from a JSON or CSV file.

    Args:
        path: Path to a JSON or CSV contacts file.
              Defaults to ``<project_root>/data/contacts.json``.

    Returns:
        List of contact record dicts, one per outreach target.

    Raises:
        FileNotFoundError: If the resolved path does not exist.
        ValueError: If file extension is unsupported or content is malformed.
    """
    file_path = Path(path) if path else DEFAULT_CONTACTS_PATH

    if not file_path.exists():
        # Fallback to root contacts.json or jobs.csv if default data path missing
        root_json = _PROJECT_ROOT / "contacts.json"
        root_csv = _PROJECT_ROOT / "jobs.csv"
        data_csv = _PROJECT_ROOT / "data" / "jobs.csv"
        if not path and root_json.exists():
            file_path = root_json
        elif not path and data_csv.exists():
            file_path = data_csv
        elif not path and root_csv.exists():
            file_path = root_csv
        else:
            raise FileNotFoundError(f"Contacts file not found: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        with open(file_path, "r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            return [dict(row) for row in reader]

    with open(file_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_optout_list(path: str | Path | None = None) -> set[str]:
    """Load opted-out email addresses from optout_list.txt.

    Returns:
        A set of lowercase email strings that should never be contacted.
    """
    target = Path(path) if path else DEFAULT_OPTOUT_PATH
    if not target.exists():
        alt = _PROJECT_ROOT / "data" / "optout_list.txt"
        if alt.exists():
            target = alt
        else:
            cwd_alt = Path("optout_list.txt")
            if cwd_alt.exists():
                target = cwd_alt
            else:
                return set()

    optouts = set()
    try:
        with open(target, "r", encoding="utf-8") as fh:
            for line in fh:
                cleaned = line.strip().lower()
                # Ignore comments and blank lines
                if cleaned and not cleaned.startswith("#"):
                    optouts.add(cleaned)
    except OSError:
        pass
    return optouts

