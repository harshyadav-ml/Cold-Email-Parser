"""src.closer.delivery.smtp — SMTP email delivery with DRY_RUN guard.

Sends or simulates email via smtplib. Reads all config from
src.closer.config.settings — never from os.getenv() directly.
"""
from __future__ import annotations

import smtplib
from datetime import datetime, timezone
from email import policy
from email.message import EmailMessage
from email.utils import format_datetime, formataddr, make_msgid

from src.closer.config import settings
from src.closer.generation.cleaner import clean_email_body


# ── Internal helpers ──────────────────────────────────────────────────

def _get_smtp_connection() -> smtplib.SMTP:
    """Establish an authenticated SMTP session with Gmail or custom provider."""
    smtp_user = (settings.SMTP_USER or "").strip()
    smtp_password = (settings.SMTP_PASSWORD or "").strip()
    smtp_host = (settings.SMTP_HOST or "smtp.gmail.com").strip()
    smtp_port = int(settings.SMTP_PORT)

    if not smtp_user or not smtp_password:
        raise EnvironmentError(
            "SMTP_USER and SMTP_PASSWORD must be set in .env"
        )

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
            server.ehlo()
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
        server.login(smtp_user, smtp_password)
        return server
    except OSError as exc:
        if getattr(exc, "errno", None) == 101 or "101" in str(exc) or "Network is unreachable" in str(exc):
            raise OSError(
                101,
                "[Errno 101] Network is unreachable (Render Free Tier blocks SMTP port 587. Switch SEND_METHOD to gmail_api or use SMTP port 2525)",
            ) from exc
        raise


def _build_message(to: str, subject: str, body: str) -> EmailMessage:
    """Construct a MIME message ready for SMTP transmission."""
    cleaned_body = clean_email_body(body)
    msg = EmailMessage(policy=policy.SMTP)
    sender_name = (settings.SENDER_NAME or "").strip()
    smtp_user = (settings.SMTP_USER or "").strip()
    if sender_name:
        msg["From"] = formataddr((sender_name, smtp_user))
    else:
        msg["From"] = smtp_user
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = format_datetime(datetime.now(timezone.utc))
    sender_domain = smtp_user.rpartition("@")[2] or None
    msg["Message-ID"] = make_msgid(domain=sender_domain)
    msg.set_content(cleaned_body, subtype="plain", charset="utf-8")
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
        smtp_user = (settings.SMTP_USER or "").strip()
        with _get_smtp_connection() as server:
            server.sendmail(smtp_user, to, msg.as_string())
        print(f"  Sent to {to}")
        return {
            "status": "sent",
            "message_id": msg["Message-ID"],
            "error_message": "",
        }
    except OSError as exc:
        err_msg = str(exc)
        if getattr(exc, "errno", None) == 101 or "101" in str(exc) or "Network is unreachable" in str(exc):
            err_msg = "[Errno 101] Network is unreachable (Render Free Tier blocks SMTP port 587. Switch SEND_METHOD to gmail_api or use SMTP port 2525)"
        print(f"  Send failed: {err_msg}")
        return {
            "status": "failed",
            "message_id": None,
            "error_message": err_msg,
        }
    except Exception as exc:
        err_msg = str(exc)
        if "101" in err_msg or "Network is unreachable" in err_msg:
            err_msg = "[Errno 101] Network is unreachable (Render Free Tier blocks SMTP port 587. Switch SEND_METHOD to gmail_api or use SMTP port 2525)"
        print(f"  Send failed: {err_msg}")
        return {
            "status": "failed",
            "message_id": None,
            "error_message": err_msg,
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

