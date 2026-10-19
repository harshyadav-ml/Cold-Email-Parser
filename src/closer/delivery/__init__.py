"""src.closer.delivery — unified email delivery dispatcher (SMTP & Gmail API)."""
from __future__ import annotations

from src.closer.config import settings
from src.closer.delivery.gmail import create_gmail_draft, send_gmail_message
from src.closer.delivery.smtp import (
    create_draft as smtp_create_draft,
    send_email as smtp_send_email,
)


def send_email(to: str, subject: str, body: str) -> dict:
    """Send an email using configured SEND_METHOD (smtp or gmail_api)."""
    if settings.SEND_METHOD == "gmail_api":
        return send_gmail_message(to, subject, body)
    return smtp_send_email(to, subject, body)


def create_draft(to: str, subject: str, body: str) -> dict:
    """Create a draft using configured SEND_METHOD (smtp or gmail_api)."""
    if settings.SEND_METHOD == "gmail_api":
        return create_gmail_draft(to, subject, body)
    return smtp_create_draft(to, subject, body)


__all__ = [
    "create_draft",
    "create_gmail_draft",
    "send_email",
    "send_gmail_message",
    "smtp_create_draft",
    "smtp_send_email",
]
