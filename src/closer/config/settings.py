"""src.closer.config.settings — centralised environment config.

Loads .env on import and exposes all settings as typed module-level constants.
Every other module reads from here — never from os.getenv() directly.
"""
from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# ── SMTP ──────────────────────────────────────────────────────────────
SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
SENDER_NAME: str = os.getenv("SENDER_NAME", "")

# ── Feature flags ─────────────────────────────────────────────────────
DRY_RUN: bool = os.getenv("DRY_RUN", "true").lower() == "true"
SEND_METHOD: str = os.getenv("SEND_METHOD", "smtp").lower()
MAX_SENDS_PER_SESSION: int = int(os.getenv("MAX_SENDS_PER_SESSION", "5"))
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"))
LLM_TIMEOUT: float = float(os.getenv("LLM_TIMEOUT", "30.0"))

# If GROQ_API_KEY is present, default LLM_ENABLED to True
LLM_ENABLED: bool = True if bool(GROQ_API_KEY and GROQ_API_KEY.strip()) else (os.getenv("LLM_ENABLED", "false").lower() == "true")

# ── Runtime State ─────────────────────────────────────────────────────
LLM_SESSION_DISABLED: bool = False

