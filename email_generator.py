"""Root-level email generator proxy for backward compatibility and test runners.

Delegates directly to src.closer.generation.
"""
from src.closer.generation import (
    check_spam_risk,
    clean_email_body,
    generate_email,
    generate_followup,
    generate_template_email,
    score_email,
    validate_email,
)
from src.closer.generation.llm import build_prompt, generate_with_llm

__all__ = [
    "build_prompt",
    "check_spam_risk",
    "clean_email_body",
    "generate_email",
    "generate_followup",
    "generate_template_email",
    "generate_with_llm",
    "score_email",
    "validate_email",
]
