"""src.closer.domain.models — canonical data contracts.

All modules share these dataclasses. Keeps the domain pure;
no I/O, no external imports.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ContactRecord:
    """A single outreach target parsed from contacts.json."""

    # Required
    recipient_email: str
    company: str
    role: str
    candidate_name: str
    candidate_background: str

    # Optional
    recipient_name: Optional[str] = None
    job_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    personalization_note: Optional[str] = None
    linkedin_url: Optional[str] = None
    resume_link: Optional[str] = None


@dataclass
class GeneratedEmail:
    """Validated output of the generation step."""

    subject: str
    body: str
    word_count: int = 0
    passes_validation: bool = False

    def __post_init__(self) -> None:
        self.word_count = len(self.body.split())
        self.passes_validation = self.word_count <= 150


@dataclass
class SendResult:
    """Outcome of a send / draft / skip action."""

    status: str          # sent | drafted | skipped | failed | dry_run
    message_id: Optional[str] = None
    draft_id: Optional[str] = None
    error_message: str = ""


@dataclass
class LogEntry:
    """Audit log entry recorded in outreach_log.csv."""

    timestamp: str
    recipient_email: str
    company: str
    role: str
    subject: str
    status: str
    error_message: str = ""
    word_count: int = 0

