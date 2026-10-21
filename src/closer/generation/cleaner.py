"""src.closer.generation.cleaner — Email body formatting and whitespace normalizer."""
from __future__ import annotations

import re


def clean_email_body(text: str) -> str:
    """Normalize and clean email body text for cross-client and mobile readability.

    Converts hard mid-sentence single line breaks (single \\n) into single spaces
    to allow email clients (especially mobile devices) to wrap text naturally.
    Strictly preserves double line breaks (\\n\\n) so paragraph spacing remains intact.

    Args:
        text: Raw email body text (from LLM output, templates, or editor).

    Returns:
        Cleaned email body string with single line breaks replaced by spaces
        and paragraphs separated by double newlines.
    """
    if not text:
        return ""

    # 1. Normalize CRLF / CR to standard LF
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Treat lines containing only whitespace between newlines as paragraph breaks
    normalized = re.sub(r"\n[ \t]+\n", "\n\n", normalized)

    # 3. Split by two or more newlines to preserve distinct paragraphs
    paragraphs = re.split(r"\n{2,}", normalized)

    cleaned_paragraphs = []
    for para in paragraphs:
        # In each paragraph, replace single line breaks and surrounding whitespace with a single space
        cleaned_para = re.sub(r"[ \t]*\n[ \t]*", " ", para).strip()
        if cleaned_para:
            cleaned_paragraphs.append(cleaned_para)

    return "\n\n".join(cleaned_paragraphs)


# Backward-compatible alias
unwrap_email_body = clean_email_body
