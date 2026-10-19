"""src.closer.generation — public generation API.

Dispatcher: routes to template engine (MVP) or LLM (Phase 5)
based on the LLM_ENABLED setting.
"""
from __future__ import annotations

from src.closer.config import settings
from src.closer.generation.quality import check_spam_risk, score_email
from src.closer.generation.template import (
    generate_email as generate_template_email,
    generate_followup,
    validate_email,
)


def generate_email(
    contact: dict,
    variant: int = 0,
    mode: str = "standard",
    regen_count: int = 1,
    temperature: float = 0.9,
    previous_subject: str = "",
    previous_body: str = "",
) -> tuple[str, str]:
    """Route to the correct generation backend and return (subject, body)."""
    if settings.LLM_ENABLED and not getattr(settings, "LLM_SESSION_DISABLED", False):
        from src.closer.generation.llm import generate_with_llm
        return generate_with_llm(
            contact,
            mode=mode,
            temperature=temperature,
            previous_subject=previous_subject,
            previous_body=previous_body,
            regen_count=regen_count,
        )

    return generate_template_email(
        contact,
        variant=variant,
        mode=mode,
        regen_count=regen_count,
        previous_subject=previous_subject,
        previous_body=previous_body,
    )


__all__ = [
    "check_spam_risk",
    "generate_email",
    "generate_followup",
    "generate_template_email",
    "score_email",
    "validate_email",
]
