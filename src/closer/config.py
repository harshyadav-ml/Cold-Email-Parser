"""src.closer.config — re-export settings for top-level access."""
from src.closer.config.settings import *
import src.closer.config.settings as settings

__all__ = [
    "settings",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "SENDER_NAME",
    "DRY_RUN",
    "SEND_METHOD",
    "LLM_ENABLED",
    "MAX_SENDS_PER_SESSION",
    "GROQ_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "LLM_MODEL",
    "LLM_TIMEOUT",
    "LLM_SESSION_DISABLED",
]
