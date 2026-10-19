"""Root-level email sender proxy for backward compatibility and test runners.

Delegates directly to src.closer.delivery.
"""
from src.closer.delivery import (
    create_draft,
    create_gmail_draft,
    send_email,
    send_gmail_message,
    smtp_create_draft,
    smtp_send_email,
)

__all__ = [
    "create_draft",
    "create_gmail_draft",
    "send_email",
    "send_gmail_message",
    "smtp_create_draft",
    "smtp_send_email",
]
