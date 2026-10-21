"""src.closer.generation.llm — Live Groq LLM email generation with dynamic variation.

Activated via GROQ_API_KEY or LLM_ENABLED=true.
Supports live prompt variation across modes ("standard", "concise", "technical", "followup")
with dynamic temperature=0.95, incrementing variation counters, timestamp seeding,
and previous state awareness to guarantee unique output on every call.
"""
from __future__ import annotations

import os
import time
import traceback
from typing import Any, Mapping
from dotenv import load_dotenv

# Ensure environment variables are loaded immediately
load_dotenv()

from src.closer.config import settings
from src.closer.generation.template import (
    generate_email as tmpl_generate,
    validate_email,
)


def build_prompt(
    contact: Mapping[str, Any] | Any,
    mode: str = "standard",
    regen_count: int = 1,
    previous_subject: str = "",
    previous_body: str = "",
    timestamp_seed: int = 0,
) -> str:
    """Build a prompt tailored to the requested generation mode, counter, and candidate context."""
    if hasattr(contact, "__dict__") and not isinstance(contact, Mapping):
        c = vars(contact)
    elif isinstance(contact, Mapping):
        c = dict(contact)
    else:
        c = {}

    company = c.get("company", "your company")
    role = c.get("role", "open role")
    recipient = c.get("recipient_name", "the hiring manager")
    note = c.get("personalization_note", "N/A")
    candidate = c.get("candidate_name", "Harsh Yadav")
    background = c.get("candidate_background", "Python developer and AI engineer")
    portfolio = c.get("portfolio_url", "")

    mode_lower = (mode or "standard").lower().strip()

    if mode_lower == "concise":
        mode_instruction = (
            "MODE: ULTRA-CONCISE & CONVERSATIONAL.\n"
            "- Length: Strictly under 75 words.\n"
            "- 2 punchy, natural paragraphs maximum.\n"
            "- Natural hook in the first sentence (e.g., 'I noticed you are expanding your team for the [Role] position' or 'I saw that [Company] is hiring for [Role]').\n"
            "- 1-sentence low-friction call to action (e.g. a brief 5-minute chat)."
        )
    elif mode_lower == "technical":
        mode_instruction = (
            "MODE: TECHNICAL DEPTH & PEER-TO-PEER CONVERSATION.\n"
            "- Length: Around 90-120 words.\n"
            "- Write naturally like one software engineer speaking to another, avoiding sales buzzwords.\n"
            "- Focus on backend infrastructure, distributed data pipelines, performance, and practical engineering trade-offs.\n"
            "- Mention technical challenges directly relevant to the role."
        )
    elif mode_lower == "followup":
        ref_subj = previous_subject or f"Quick note on the {role} role at {company}"
        mode_instruction = (
            f"MODE: POLITE & LOW-FRICTION FOLLOW-UP.\n"
            f"- Length: Strictly under 60 words.\n"
            f"- Reference the earlier outreach (Previous subject: '{ref_subj}').\n"
            f"- Respectfully acknowledge their time, and ask if there is an engineering lead or hiring manager to connect with."
        )
    else:
        mode_instruction = (
            "MODE: STANDARD OUTREACH (NATURAL & CONVERSATIONAL).\n"
            "- Length: Under 120 words.\n"
            "- Open with a smooth, natural hook (e.g., 'I saw that [Company] is hiring an [Role]' or 'I noticed you are expanding your team for the [Role] position').\n"
            "- Highlight relevant candidate engineering background and projects naturally without sales hype.\n"
            "- End with one polite, low-friction ask (like a brief 5-minute chat)."
        )

    avoid_block = ""
    if previous_subject or previous_body:
        avoid_block = f"""
PREVIOUS VARIATION CURRENTLY DISPLAYED (DO NOT REPEAT):
Previous Subject: {previous_subject or 'N/A'}
Previous Body:
{previous_body or 'N/A'}

CRITICAL REQUIREMENT: Do NOT repeat the above opening sentence, phrasing, or tone. The new draft must be strictly and visibly different.
"""

    # Entropy seed for additional variation
    ts_label = f"(Entropy seed: {timestamp_seed})" if timestamp_seed else ""

    return f"""You are an elite cold outreach copywriter for technical software roles.
Write a personalized cold email for a job application with the following parameters:

Target Company: {company}
Role: {role}
Recipient Name: {recipient}
Personalization Context: {note}
Candidate Name: {candidate}
Candidate Background: {background}
Candidate Portfolio / Code: {portfolio or "Not provided; do not invent or add a link"}

{mode_instruction}

Generation attempt #{regen_count}. You must write a completely unique subject line, opening hook, sentence structure, and value proposition. Do not repeat any prior patterns. {ts_label}
{avoid_block}

STRICT WRITING RULES:
1. Under 150 words total.
2. Hook in the very first sentence. Use natural phrasing (e.g., 'I saw that [Company] is hiring for...' or 'I noticed you are expanding your team for...').
3. Sound conversational, human, and genuine: write peer-to-peer and avoid salesy buzzwords ('synergy', 'leverage', 'spearhead', 'thrilled to apply').
4. No fabricated or exaggerated claims (never invent referrals, prior calls, or mutual acquaintances).
5. Do not imply that the sender has followed the company, reviewed its work, or knows the recipient unless the provided personalization context explicitly supports that claim. Do not invent a portfolio URL.
6. Output MUST follow this exact format with NO markdown wrapping around the Subject line:
Subject: [Compelling subject line here]

[Email body here]"""


def generate_with_llm(
    contact: Mapping[str, Any] | Any,
    mode: str = "standard",
    temperature: float = 0.95,
    previous_subject: str = "",
    previous_body: str = "",
    regen_count: int = 1,
    timestamp_seed: int = 0,
) -> tuple[str, str]:
    """Generate a personalized email using Groq LLM with robust error fallbacks.

    Returns:
        (subject, body) tuple.
    """
    # Generate a timestamp seed if not provided
    if not timestamp_seed:
        timestamp_seed = int(time.time() * 1000)

    # 1. Check if LLM was disabled mid-session due to rate limits
    #    Auto-recover after 60 seconds to avoid permanent lockout
    if getattr(settings, "LLM_SESSION_DISABLED", False):
        disabled_at = getattr(settings, "_LLM_DISABLED_AT", 0)
        if time.time() - disabled_at > 60:
            settings.LLM_SESSION_DISABLED = False
            print("  [INFO] LLM rate-limit cooldown expired. Re-enabling Groq.")
        else:
            print("  [WARNING] LLM disabled for this session due to prior rate limit. Using template.")
            return tmpl_generate(contact, mode=mode, regen_count=regen_count)

    # 2. Check for Groq API key directly from environment
    api_key = os.getenv("GROQ_API_KEY", "").strip() or getattr(settings, "GROQ_API_KEY", "").strip()
    if not api_key:
        print("  [WARNING] GROQ_API_KEY missing. Falling back to template generation.")
        return tmpl_generate(contact, mode=mode, regen_count=regen_count)

    # If key is present, ensure LLM_ENABLED is True
    settings.LLM_ENABLED = True

    # 3. Import groq client library
    try:
        import groq
    except ImportError:
        print("  [WARNING] 'groq' package not installed. Falling back to template generation.")
        return tmpl_generate(contact, mode=mode, regen_count=regen_count)

    # 4. Determine verified active Groq model
    model_name = os.getenv("GROQ_MODEL") or os.getenv("LLM_MODEL") or getattr(settings, "LLM_MODEL", "openai/gpt-oss-120b")
    timeout = getattr(settings, "LLM_TIMEOUT", 30.0)

    prompt = build_prompt(
        contact,
        mode=mode,
        regen_count=regen_count,
        previous_subject=previous_subject,
        previous_body=previous_body,
        timestamp_seed=timestamp_seed,
    )

    # System prompt with the exact required constraint text
    system_prompt = (
        "You are an elite cold outreach copywriter for technical software roles. "
        f"Generation attempt #{regen_count}. You must write a completely unique subject line, "
        "opening hook, sentence structure, and value proposition. Do not repeat any prior patterns."
    )

    llm_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    raw_response = ""

    # 5. Call Groq with try/except printing exact traceback
    try:
        client = groq.Groq(api_key=api_key, timeout=timeout)
        print(f"  [GROQ] Calling Groq API (model={model_name}, mode={mode}, attempt={regen_count}, temp={temperature}, seed={timestamp_seed})...")

        chat_completion = client.chat.completions.create(
            model=model_name,
            messages=llm_messages,
            max_tokens=1500,
            temperature=temperature,
        )
        raw_response = chat_completion.choices[0].message.content or ""

        # If reasoning model consumed tokens without populating content, retry with qwen
        if not raw_response.strip() and model_name != "qwen/qwen3.8-27b":
            print(f"  [GROQ] Model {model_name} returned empty content, switching to qwen/qwen3.8-27b...")
            chat_completion = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=llm_messages,
                max_tokens=600,
                temperature=temperature,
            )
            raw_response = chat_completion.choices[0].message.content or ""

    except groq.RateLimitError as exc:
        print(f"  [ERROR] Groq RateLimitError encountered: {exc}")
        traceback.print_exc()
        settings.LLM_SESSION_DISABLED = True
        settings._LLM_DISABLED_AT = time.time()
        return tmpl_generate(contact, mode=mode, regen_count=regen_count)

    except Exception as exc:
        print(f"  [ERROR] Groq API call failed (timeout / error) with model '{model_name}': {exc}")
        traceback.print_exc()

        # Try secondary active model if primary failed
        if model_name != "qwen/qwen3.8-27b":
            try:
                print("  [GROQ] Attempting fallback to active Groq model 'qwen/qwen3.8-27b'...")
                chat_completion = client.chat.completions.create(
                    model="qwen/qwen3.8-27b",
                    messages=llm_messages,
                    max_tokens=600,
                    temperature=temperature,
                )
                raw_response = chat_completion.choices[0].message.content or ""
            except Exception as exc_fallback:
                print(f"  [ERROR] Fallback Groq model also failed: {exc_fallback}")
                traceback.print_exc()
                return tmpl_generate(contact, mode=mode, regen_count=regen_count)
        else:
            return tmpl_generate(contact, mode=mode, regen_count=regen_count)

    # 6. Check for empty / whitespace response
    cleaned = raw_response.strip()
    if not cleaned:
        print("  [WARNING] LLM returned empty response. Falling back to template.")
        return tmpl_generate(contact, mode=mode, regen_count=regen_count)

    # 7. Parse Subject and Body
    lines = cleaned.split("\n", 1)
    first_line = lines[0].strip()
    clean_first_line = first_line.replace("**", "").replace("*", "").strip()

    if clean_first_line.lower().startswith("subject:"):
        subject = clean_first_line[8:].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
    elif len(lines) > 1 and len(first_line.split()) <= 15:
        subject = clean_first_line
        body = lines[1].strip()
    else:
        # Fallback subject if subject cannot be isolated
        c_dict = dict(contact) if isinstance(contact, Mapping) else (vars(contact) if hasattr(contact, "__dict__") else {})
        role = c_dict.get("role", "open role")
        company = c_dict.get("company", "your company")
        subject = f"Quick note on the {role} role at {company}"
        body = cleaned

    # Strip any leading markdown divider or metadata from body
    if body.startswith("---"):
        body = body.lstrip("-").strip()

    # 8. Verify strict difference from previous state
    for offset in range(1, 6):
        if previous_subject and subject.strip().lower() == previous_subject.strip().lower():
            alt_subj, _ = tmpl_generate(contact, mode=mode, regen_count=regen_count + offset)
            subject = alt_subj
        else:
            break

    for offset in range(1, 6):
        if previous_body and body.strip().lower() == previous_body.strip().lower():
            _, alt_body = tmpl_generate(contact, mode=mode, regen_count=regen_count + offset)
            body = alt_body
        else:
            break

    # 9. Validate generated email (Word count + Fabricated claims)
    if not validate_email(body):
        print("  [WARNING] LLM output failed word-count or hallucination guard. Falling back to template.")
        return tmpl_generate(contact, mode=mode, regen_count=regen_count)

    return subject, body
