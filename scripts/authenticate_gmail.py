"""scripts/authenticate_gmail.py — Interactive OAuth 2.0 re-authentication for Gmail API.

Run locally to authenticate a new Google/Gmail account and generate a fresh token.json.
Also outputs the exact single-line JSON needed for GMAIL_TOKEN_JSON on Render.

Usage:
    python3 scripts/authenticate_gmail.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add project root to path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.closer.config import settings
from src.closer.delivery.gmail import (
    CREDENTIALS_FILE,
    SCOPES,
    TOKEN_FILE,
    get_gmail_service,
    verify_sender_alignment,
)


def main():
    print("=" * 65)
    print("  THE CLOSER — GMAIL API OAUTH RE-AUTHENTICATION")
    print("=" * 65)

    if not CREDENTIALS_FILE.exists() and not Path("credentials.json").exists():
        print(f"\n[ERROR] credentials.json not found in {_ROOT}!")
        print("Please place your OAuth 2.0 Client credentials.json file in the project root.")
        sys.exit(1)

    # 1. Check if an old token exists
    target_token = TOKEN_FILE if TOKEN_FILE.exists() else Path("token.json")
    if target_token.exists():
        print(f"\n[INFO] Found existing token at: {target_token}")
        confirm = input("Do you want to delete this token and log in with a new account? (y/n): ").strip().lower()
        if confirm == "y":
            target_token.unlink()
            print("  -> Deleted old token file.")
        else:
            print("  -> Keeping existing token.")

    # 2. Trigger interactive OAuth flow
    print("\n[INFO] Launching local browser for Google OAuth 2.0 authentication...")
    print("Scopes requested:")
    for s in SCOPES:
        print(f"  - {s}")
    print("\nPlease sign in with your NEW Gmail account in the browser window that opens.\n")

    service = get_gmail_service()
    if not service:
        print("\n[ERROR] Authentication failed or was cancelled.")
        sys.exit(1)

    # 3. Retrieve authenticated user profile
    profile = service.users().getProfile(userId="me").execute()
    new_email = profile.get("emailAddress", "").strip().lower()
    print("\n" + "=" * 65)
    print(f"  [SUCCESS] Successfully authenticated as: {new_email}")
    print("=" * 65)

    # 4. Check alignment with .env
    configured_email = (settings.SMTP_USER or "").strip().lower()
    print(f"\nCurrent .env SMTP_USER: '{configured_email}'")
    if configured_email != new_email:
        print(
            f"  [ACTION REQUIRED] Please update your .env file:\n"
            f"    SMTP_USER={new_email}\n"
        )
    else:
        print("  [OK] SMTP_USER in .env matches authenticated account perfectly!")

    # 5. Output token for Render deployment
    token_path = TOKEN_FILE if TOKEN_FILE.exists() else Path("token.json")
    if token_path.exists():
        with open(token_path, "r", encoding="utf-8") as f:
            token_data = json.load(f)
        single_line_json = json.dumps(token_data)
        print("\n" + "-" * 65)
        print("RENDER DEPLOYMENT HELPER:")
        print("For Render cloud deployment, set this Environment Variable:")
        print(f"Key:   GMAIL_TOKEN_JSON")
        print(f"Value: {single_line_json}")
        print("-" * 65)


if __name__ == "__main__":
    main()
