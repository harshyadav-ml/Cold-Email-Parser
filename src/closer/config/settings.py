"""src.closer.config.settings — centralised environment config.

Loads .env on import and exposes all settings as typed module-level constants.
Every other module reads from here — never from os.getenv() directly.
"""
from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# ── SMTP ──────────────────────────────────────────────────────────────
SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587").strip())
SMTP_USER: str = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "").strip()
SENDER_NAME: str = os.getenv("SENDER_NAME", "").strip()

# ── Feature flags ─────────────────────────────────────────────────────
DRY_RUN: bool = os.getenv("DRY_RUN", "true").strip().lower() == "true"
SEND_METHOD: str = os.getenv("SEND_METHOD", "gmail_api").strip().lower()
MAX_SENDS_PER_SESSION: int = int(os.getenv("MAX_SENDS_PER_SESSION", "50").strip())
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "").strip()
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
LLM_MODEL: str = os.getenv("LLM_MODEL", os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")).strip()
LLM_TIMEOUT: float = float(os.getenv("LLM_TIMEOUT", "30.0").strip())

# If GROQ_API_KEY is present, default LLM_ENABLED to True
LLM_ENABLED: bool = True if bool(GROQ_API_KEY) else (os.getenv("LLM_ENABLED", "false").strip().lower() == "true")

# ── Runtime State ─────────────────────────────────────────────────────
LLM_SESSION_DISABLED: bool = False

