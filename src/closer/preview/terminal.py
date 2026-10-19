"""src.closer.preview.terminal — terminal-based email preview (Phase 2).

Prints a formatted preview block and prompts for a send/draft/skip decision.
"""
from __future__ import annotations


def preview_email(contact: dict, subject: str, body: str) -> None:
    """Print a formatted email preview to stdout."""
    print("\n" + "=" * 60)
    print("  EMAIL PREVIEW")
    print("=" * 60)
    print(f"  To      : {contact.get('recipient_email')}")
    print(f"  Company : {contact.get('company')} — {contact.get('role')}")
    print(f"  Subject : {subject}")
    print("-" * 60)
    print(body)
    print("=" * 60)


def get_user_decision() -> str:
    """Prompt the user and return one of 'send' | 'draft' | 'skip'.

    Re-prompts on invalid input; never raises on bad input.
    """
    while True:
        try:
            decision = input("\nAction? [send / draft / skip]: ").strip().lower()
        except EOFError:
            print("\n  EOF received. Defaulting to 'skip'.")
            return "skip"
        if decision in ("send", "draft", "skip"):
            return decision
        print("  Invalid choice. Type 'send', 'draft', or 'skip'.")

