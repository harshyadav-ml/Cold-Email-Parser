"""src.closer.app — CLI orchestrator (Phases 1-5).

Load → Filter (Opt-out & Deduplicate) → Generate (Template/LLM) → Preview
     → Human Review → Dispatch (SMTP/Gmail API) → Audit Log → Session Summary.
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.closer.config import settings
from src.closer.input.loader import load_contacts, load_optout_list
from src.closer.generation import generate_email, score_email
from src.closer.preview.terminal import preview_email, get_user_decision
from src.closer.delivery import send_email, create_draft
from src.closer.audit.logger import log_entry, get_log_summary


def main(contacts_path: str | Path | None = None) -> None:
    """Entry point for the CLI."""
    if not contacts_path and len(sys.argv) > 1:
        contacts_path = sys.argv[1]

    try:
        contacts = load_contacts(contacts_path)
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return

    if not contacts:
        print("No contacts found to process.")
        return

    print(f"\nThe Closer — {len(contacts)} contacts loaded.")
    print(f"Mode: {'LLM-powered' if settings.LLM_ENABLED else 'Template-based'} | Delivery: {settings.SEND_METHOD.upper()} | DRY_RUN: {settings.DRY_RUN}\n")

    optouts = load_optout_list()
    seen_emails: set[str] = set()
    sent_count = 0

    try:
        for i, contact in enumerate(contacts, 1):
            email = str(contact.get("recipient_email", "") or "").strip().lower()
            company = contact.get("company", "Company")
            role = contact.get("role", "Role")

            print(f"\n[{i}/{len(contacts)}] Processing: {company} — {role}")

            # 1. Opt-out check (Phase 5 stretch, EC-6.4)
            if email in optouts:
                print(f"  [opt-out] {email} is on the opt-out list. Skipping.")
                log_entry(
                    contact=contact,
                    subject="",
                    status="opted_out",
                    error="Recipient in optout_list.txt",
                    body="",
                )
                continue

            # 2. Deduplication check (Phase 5 stretch, EC-1.4 / EC-1.7)
            if email in seen_emails:
                print(f"  [duplicate] {email} already processed in this session. Skipping.")
                log_entry(
                    contact=contact,
                    subject="",
                    status="skipped_duplicate",
                    error="Duplicate contact in same session",
                    body="",
                )
                continue
            if email:
                seen_emails.add(email)

            # 3. Email Generation (Template or LLM with fallback)
            try:
                subject, body = generate_email(contact)
            except ValueError as exc:
                print(f"  Generation failed: {exc}")
                log_entry(
                    contact=contact,
                    subject="",
                    status="failed",
                    error=str(exc),
                    body="",
                )
                continue

            # Quality analysis (Phase 5 stretch)
            quality = score_email(subject, body)
            if quality["spam_risk"] != "low":
                print(f"  [notice] Quality Score: {quality['score']}/10 | Spam Risk: {quality['spam_risk'].upper()}")

            # 4. Human Review & Decision Loop
            preview_email(contact, subject, body)
            decision = get_user_decision()
            print(f"  Decision recorded: {decision}")

            # 5. Delivery Dispatch
            if decision == "send":
                # Session limit check (EC-4.8)
                if sent_count >= settings.MAX_SENDS_PER_SESSION and not settings.DRY_RUN:
                    print(
                        f"  [limit] Session send limit of {settings.MAX_SENDS_PER_SESSION} reached. "
                        f"Skipping send to prevent spam flags (EC-4.8)."
                    )
                    result = {
                        "status": "skipped_limit",
                        "error_message": f"Exceeded MAX_SENDS_PER_SESSION ({settings.MAX_SENDS_PER_SESSION})",
                    }
                else:
                    result = send_email(contact["recipient_email"], subject, body)
                    if result["status"] == "sent":
                        sent_count += 1
            elif decision == "draft":
                result = create_draft(contact["recipient_email"], subject, body)
            else:
                result = {"status": "skipped", "error_message": ""}

            # 6. Audit Logging
            log_entry(
                contact=contact,
                subject=subject,
                status=result["status"],
                error=result.get("error_message", ""),
                body=body,
            )

    except KeyboardInterrupt:
        print("\n\n  Interrupted by user. Exiting cleanly.")
    finally:
        summary = get_log_summary()
        print("\nSession Summary:")
        if summary:
            for status, count in summary.items():
                print(f"  {status}: {count}")
        else:
            print("  No actions recorded.")


if __name__ == "__main__":
    main()
