"""src.closer.generation.quality — Email quality scoring and spam risk checker (Phase 5)."""
from __future__ import annotations

import re

SPAM_KEYWORDS = [
    "100% free",
    "act now",
    "apply now",
    "as seen on",
    "bargain",
    "best price",
    "buy direct",
    "call now",
    "cancel at any time",
    "click here",
    "clearance",
    "congratulations",
    "dear friend",
    "direct marketing",
    "discount",
    "do it today",
    "don't delete",
    "double your income",
    "earn extra cash",
    "eliminate debt",
    "exclusive deal",
    "expect to earn",
    "extra income",
    "fast cash",
    "financial freedom",
    "free trial",
    "get out of debt",
    "get paid",
    "giveaway",
    "guaranteed",
    "increase sales",
    "instant",
    "limited time",
    "lowest price",
    "make money",
    "miracle",
    "money back",
    "no catch",
    "no cost",
    "no credit check",
    "no experience",
    "no fees",
    "no gimmick",
    "no hidden",
    "no obligation",
    "no purchase necessary",
    "no risk",
    "no strings attached",
    "not spam",
    "once in a lifetime",
    "one time",
    "open immediately",
    "order now",
    "promise you",
    "pure profit",
    "risk free",
    "save big",
    "special promotion",
    "urgent",
    "winner",
    "winning",
]


def check_spam_risk(subject: str, body: str) -> dict:
    """Analyze subject and body for spam indicators.

    Checks:
    - All-caps words density
    - Exclamation mark count
    - Known spam trigger phrases

    Returns:
        Dict with 'is_spam_risk' (bool), 'risk_level' ('low'|'medium'|'high'),
        and list of 'flags'.
    """
    flags = []
    combined = f"{subject} {body}"
    words = combined.split()

    # 1. Exclamation marks
    exclamation_count = combined.count("!")
    if exclamation_count > 2:
        flags.append(f"Excessive exclamation marks ({exclamation_count})")

    # 2. All-caps words (ignoring short acronyms <= 3 chars like AI, ML, AWS)
    caps_words = [w for w in words if w.isupper() and len(re.sub(r"\W", "", w)) > 3]
    if len(caps_words) >= 2:
        flags.append(f"Excessive ALL-CAPS words: {', '.join(caps_words[:3])}")

    # 3. Spam keywords
    text_lower = combined.lower()
    found_triggers = [kw for kw in SPAM_KEYWORDS if kw in text_lower]
    if found_triggers:
        flags.append(f"Spam trigger phrases: {', '.join(found_triggers)}")

    if len(flags) >= 2 or found_triggers:
        risk_level = "high"
    elif len(flags) == 1:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "is_spam_risk": risk_level in ("medium", "high"),
        "risk_level": risk_level,
        "flags": flags,
    }


def score_email(subject: str, body: str) -> dict:
    """Rate email quality from 1 to 10 and provide diagnostic feedback.

    Criteria:
    - Brevity & word count (sweet spot: 50–120 words)
    - Subject line length and specificity (sweet spot: 4–10 words)
    - Presence of clear CTA / ask
    - Spam risk deduction
    """
    score = 10
    reasons = []

    words = body.split()
    word_count = len(words)
    subj_words = len(subject.split())

    # Subject line checks
    if subj_words == 0:
        score -= 4
        reasons.append("Subject line is missing")
    elif subj_words > 12:
        score -= 1
        reasons.append("Subject line is slightly long (>12 words)")

    # Body length checks
    if word_count < 30:
        score -= 2
        reasons.append("Body may be too brief (<30 words)")
    elif word_count > 150:
        score -= 3
        reasons.append(f"Body exceeds 150-word ceiling ({word_count} words)")
    elif word_count > 120:
        score -= 1
        reasons.append(f"Body is slightly long ({word_count} words)")

    # Check for call to action / question
    if "?" not in body:
        score -= 2
        reasons.append("No clear question / call-to-action detected")

    # Check for personalization greeting
    if not any(body.strip().lower().startswith(g) for g in ["hi ", "hello ", "dear ", "hey "]):
        score -= 1
        reasons.append("Missing standard greeting (Hi / Hello)")

    # Spam risk check
    spam_res = check_spam_risk(subject, body)
    if spam_res["risk_level"] == "high":
        score -= 3
        reasons.extend(spam_res["flags"])
    elif spam_res["risk_level"] == "medium":
        score -= 1
        reasons.extend(spam_res["flags"])

    final_score = max(1, min(10, score))
    return {
        "score": final_score,
        "word_count": word_count,
        "spam_risk": spam_res["risk_level"],
        "reasons": reasons if reasons else ["Clean structure, focused length, and clear CTA"],
    }
