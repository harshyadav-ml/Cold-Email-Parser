"""src.closer.delivery.smtp — SMTP email delivery with DRY_RUN guard.

Sends or simulates email via smtplib. Reads all config from
src.closer.config.settings — never from os.getenv() directly.
"""
from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.closer.config import settings


# ── Internal helpers ──────────────────────────────────────────────────

def _get_smtp_connection() -> smtplib.SMTP:
    """Establish an authenticated SMTP session with Gmail."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        raise EnvironmentError(
            "SMTP_USER and SMTP_PASSWORD must be set in .env"
        )
    server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
    server.ehlo()
    server.starttls()
    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
    return server


def _build_message(to: str, subject: str, body: str) -> MIMEMultipart:
    """Construct a MIME message ready for SMTP transmission."""
    msg = MIMEMultipart()
    if settings.SENDER_NAME:
        msg["From"] = f"{settings.SENDER_NAME} <{settings.SMTP_USER}>"
    else:
        msg["From"] = settings.SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    return msg


# ── Public API ────────────────────────────────────────────────────────

def send_email(to: str, subject: str, body: str) -> dict:
    """Send *body* to *to* via SMTP. Returns a status dict.

    When DRY_RUN=true no network connection is made.
    SMTP errors are caught and returned in the dict — the app never crashes.
    """
    if settings.DRY_RUN:
        print("  DRY_RUN=true — email not sent (simulated)")
        return {"status": "dry_run", "message_id": None, "error_message": ""}

    try:
        msg = _build_message(to, subject, body)
        with _get_smtp_connection() as server:
            server.sendmail(settings.SMTP_USER, to, msg.as_string())
        print(f"  Sent to {to}")
        return {
            "status": "sent",
            "message_id": msg["Message-ID"],
            "error_message": "",
        }
    except Exception as exc:
        print(f"  Send failed: {exc}")
        return {
            "status": "failed",
            "message_id": None,
            "error_message": str(exc),
        }


def create_draft(to: str, subject: str, body: str) -> dict:
    """Create draft via Gmail API if SEND_METHOD=gmail_api, else print local draft notice."""
    if settings.SEND_METHOD == "gmail_api":
        from src.closer.delivery.gmail import create_gmail_draft
        return create_gmail_draft(to, subject, body)

    if settings.DRY_RUN:
        print("  DRY_RUN=true — draft not created (simulated)")
        return {"status": "dry_run", "draft_id": None, "error_message": ""}

    print(f"  Draft mode — would create Gmail draft for {to}")
    return {"status": "drafted_locally", "draft_id": None, "error_message": ""}

