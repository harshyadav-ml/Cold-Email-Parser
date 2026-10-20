"""src.closer.delivery.gmail — Gmail API delivery and draft creation (Phase 5).

Handles Gmail API OAuth 2.0, draft creation, and message transmission.
Enforces validation guards (EC-4.7), handles token refresh and RefreshError (EC-4.6),
and catches HttpError 429 quota exhaustion with fallback to SMTP (Criterion 5G.4).
"""
from __future__ import annotations

import base64
import json
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Optional

from src.closer.config import settings

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOKEN_FILE = _PROJECT_ROOT / "token.json"
CREDENTIALS_FILE = _PROJECT_ROOT / "credentials.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


def _build_raw_message(to: str, subject: str, body: str) -> str:
    """Build URL-safe base64-encoded MIME string for Gmail API."""
    msg = MIMEMultipart()
    sender_name = settings.SENDER_NAME
    sender_email = settings.SMTP_USER
    if sender_name and sender_email:
        msg["From"] = f"{sender_name} <{sender_email}>"
    elif sender_email:
        msg["From"] = sender_email

    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")


def get_gmail_service(token_path: Optional[Path | str] = None) -> Any:
    """Load or refresh credentials and return authenticated Gmail service.

    Handles token refresh automatically, checks cloud/env tokens, and catches RefreshError (EC-4.6).
    """
    try:
        from google.auth.exceptions import RefreshError
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        print("  [WARNING] google-api-python-client not installed.")
        return None

    creds: Optional[Any] = None
    save_path: Path = TOKEN_FILE

    if token_path:
        path = Path(token_path)
        if path.exists():
            save_path = path
            try:
                creds = Credentials.from_authorized_user_file(str(path), SCOPES)
            except Exception as exc:
                print(f"  [WARNING] Error reading {path.name}: {exc}")
                return None
        else:
            return None
    else:
        # Priority 1: GMAIL_TOKEN_JSON env var
        token_env = os.getenv("GMAIL_TOKEN_JSON", "").strip()
        if token_env:
            try:
                token_data = json.loads(token_env)
                creds = Credentials.from_authorized_user_info(token_data, SCOPES)
                save_path = Path("/tmp/token.json")
            except Exception as exc:
                print(f"  [WARNING] Error parsing GMAIL_TOKEN_JSON env var: {exc}")
                creds = None

        # Priority 2: Render Secret File
        if not creds:
            render_secret = Path("/etc/secrets/token.json")
            if render_secret.exists():
                try:
                    creds = Credentials.from_authorized_user_file(str(render_secret), SCOPES)
                    save_path = Path("/tmp/token.json")
                except Exception as exc:
                    print(f"  [WARNING] Error reading {render_secret}: {exc}")
                    creds = None

        # Priority 3: /tmp/token.json
        if not creds:
            tmp_token = Path("/tmp/token.json")
            if tmp_token.exists():
                try:
                    creds = Credentials.from_authorized_user_file(str(tmp_token), SCOPES)
                    save_path = tmp_token
                except Exception as exc:
                    print(f"  [WARNING] Error reading {tmp_token}: {exc}")
                    creds = None

        # Priority 4: Default local file (TOKEN_FILE or cwd token.json)
        if not creds:
            default_path = TOKEN_FILE if TOKEN_FILE.exists() else Path("token.json")
            if default_path.exists():
                save_path = default_path
                try:
                    creds = Credentials.from_authorized_user_file(str(default_path), SCOPES)
                except Exception as exc:
                    print(f"  [WARNING] Error reading {default_path.name}: {exc}")
                    creds = None
            else:
                save_path = TOKEN_FILE

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                try:
                    with open(save_path, "w", encoding="utf-8") as token_fh:
                        token_fh.write(creds.to_json())
                except OSError:
                    with open(Path("/tmp/token.json"), "w", encoding="utf-8") as token_fh:
                        token_fh.write(creds.to_json())
            except RefreshError as exc:
                # EC-4.6: Token expired and refresh failed
                print(
                    f"  [WARNING] Gmail OAuth token expired and refresh failed: {exc} (EC-4.6). "
                    f"Please re-run OAuth authentication flow to generate a fresh token.json."
                )
                if os.getenv("RENDER") or os.getenv("VERCEL") or os.getenv("CI"):
                    raise EnvironmentError(
                        "Gmail OAuth token missing or invalid in cloud environment. "
                        "Set GMAIL_TOKEN_JSON in Render Environment Variables or mount /etc/secrets/token.json."
                    )
                return None
            except Exception as exc:
                print(f"  [WARNING] Could not refresh Gmail OAuth token: {exc}")
                if os.getenv("RENDER") or os.getenv("VERCEL") or os.getenv("CI"):
                    raise EnvironmentError(
                        "Gmail OAuth token missing or invalid in cloud environment. "
                        "Set GMAIL_TOKEN_JSON in Render Environment Variables or mount /etc/secrets/token.json."
                    )
                return None
        else:
            # Guard interactive browser OAuth flow in headless cloud environment
            if os.getenv("RENDER") or os.getenv("VERCEL") or os.getenv("CI"):
                raise EnvironmentError(
                    "Gmail OAuth token missing or invalid in cloud environment. "
                    "Set GMAIL_TOKEN_JSON in Render Environment Variables or mount /etc/secrets/token.json."
                )

            # Local fallback: try interactive OAuth if client secrets exist
            cred_file = CREDENTIALS_FILE if CREDENTIALS_FILE.exists() else Path("credentials.json")
            if cred_file.exists():
                try:
                    from google_auth_oauthlib.flow import InstalledAppFlow
                    flow = InstalledAppFlow.from_client_secrets_file(str(cred_file), SCOPES)
                    creds = flow.run_local_server(port=0)
                    try:
                        with open(save_path, "w", encoding="utf-8") as token_fh:
                            token_fh.write(creds.to_json())
                    except OSError:
                        with open(Path("/tmp/token.json"), "w", encoding="utf-8") as token_fh:
                            token_fh.write(creds.to_json())
                except Exception as exc:
                    print(f"  [WARNING] Interactive OAuth flow failed: {exc}")
                    return None
            else:
                print("  [WARNING] Invalid credentials in token.json. Please re-authenticate.")
                return None

    try:
        return build("gmail", "v1", credentials=creds, cache_discovery=False)
    except Exception as exc:
        print(f"  [WARNING] Failed to initialize Gmail API client: {exc}")
        return None


def create_gmail_draft(
    to: str,
    subject: str,
    body: str,
    service: Optional[Any] = None,
) -> dict:
    """Create a draft in Gmail via the Gmail API (Criterion 5G.1).

    Checks:
    - Empty draft body detected before API call (EC-4.7, Criterion 5G.3).
    - DRY_RUN safety check.
    - HttpError 429 (quota) fallback to SMTP (Criterion 5G.4).
    """
    # 1. Guard against empty body (EC-4.7, Criterion 5G.3)
    if not body or not body.strip():
        print("  [ERROR] Draft body is empty. Draft not submitted to Gmail API (EC-4.7).")
        return {
            "status": "failed",
            "draft_id": None,
            "error_message": "Draft body cannot be empty",
        }

    # 2. DRY_RUN check
    if settings.DRY_RUN:
        print("  DRY_RUN=true — draft not created (simulated Gmail API draft)")
        return {"status": "dry_run", "draft_id": None, "error_message": ""}

    # 3. Obtain service
    srv = service or get_gmail_service()
    if not srv:
        print("  [WARNING] Gmail API service unavailable. Falling back to local draft notice.")
        return {
            "status": "drafted_locally",
            "draft_id": None,
            "error_message": "Gmail API token not available; drafted locally",
        }

    # 4. Create draft via API
    try:
        from googleapiclient.errors import HttpError
    except ImportError:
        HttpError = Exception  # type: ignore

    try:
        raw_msg = _build_raw_message(to, subject, body)
        draft = srv.users().drafts().create(
            userId="me",
            body={"message": {"raw": raw_msg}},
        ).execute()

        draft_id = draft.get("id")
        print(f"  Created Gmail draft for {to} (draft_id={draft_id})")
        return {"status": "drafted", "draft_id": draft_id, "error_message": ""}
    except HttpError as exc:
        status_code = getattr(getattr(exc, "resp", None), "status", None)
        if status_code == 429:
            # 5G.4: Quota exceeded, fallback to SMTP
            print("  [WARNING] Gmail API quota exceeded (HTTP 429). Falling back to SMTP (Criterion 5G.4).")
            from src.closer.delivery.smtp import create_draft as smtp_create_draft
            return smtp_create_draft(to, subject, body)
        print(f"  [ERROR] Gmail API draft failed: {exc}")
        return {"status": "failed", "draft_id": None, "error_message": str(exc)}
    except Exception as exc:
        err_str = str(exc)
        if "429" in err_str:
            print("  [WARNING] Gmail API rate limit hit (429). Falling back to SMTP.")
            from src.closer.delivery.smtp import create_draft as smtp_create_draft
            return smtp_create_draft(to, subject, body)
        print(f"  [ERROR] Gmail API draft exception: {exc}")
        return {"status": "failed", "draft_id": None, "error_message": err_str}


def send_gmail_message(
    to: str,
    subject: str,
    body: str,
    service: Optional[Any] = None,
) -> dict:
    """Send an email via the Gmail API (Criterion 5G.1).

    Checks:
    - Empty body validation (EC-4.7).
    - DRY_RUN safety check.
    - HttpError 429 fallback to SMTP (Criterion 5G.4).
    """
    if not body or not body.strip():
        print("  [ERROR] Message body is empty. Email not sent (EC-4.7).")
        return {
            "status": "failed",
            "message_id": None,
            "error_message": "Email body cannot be empty",
        }

    if settings.DRY_RUN:
        print("  DRY_RUN=true — email not sent (simulated Gmail API send)")
        return {"status": "dry_run", "message_id": None, "error_message": ""}

    srv = service or get_gmail_service()
    if not srv:
        print("  [WARNING] Gmail API unavailable. Falling back to SMTP.")
        from src.closer.delivery.smtp import send_email as smtp_send
        return smtp_send(to, subject, body)

    try:
        from googleapiclient.errors import HttpError
    except ImportError:
        HttpError = Exception  # type: ignore

    try:
        raw_msg = _build_raw_message(to, subject, body)
        msg = srv.users().messages().send(
            userId="me",
            body={"raw": raw_msg},
        ).execute()

        msg_id = msg.get("id")
        print(f"  Sent via Gmail API to {to} (id={msg_id})")
        return {"status": "sent", "message_id": msg_id, "error_message": ""}
    except HttpError as exc:
        status_code = getattr(getattr(exc, "resp", None), "status", None)
        if status_code == 429:
            print("  [WARNING] Gmail API quota exceeded (HTTP 429). Falling back to SMTP (Criterion 5G.4).")
            from src.closer.delivery.smtp import send_email as smtp_send
            return smtp_send(to, subject, body)
        print(f"  [ERROR] Gmail API send failed: {exc}")
        return {"status": "failed", "message_id": None, "error_message": str(exc)}
    except Exception as exc:
        err_str = str(exc)
        if "429" in err_str:
            print("  [WARNING] Gmail API rate limit hit (429). Falling back to SMTP.")
            from src.closer.delivery.smtp import send_email as smtp_send
            return smtp_send(to, subject, body)
        print(f"  [ERROR] Gmail API send exception: {exc}")
        return {"status": "failed", "message_id": None, "error_message": err_str}
