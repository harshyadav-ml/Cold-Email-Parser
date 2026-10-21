"""src.closer.generation.template — Multi-variant f-string template engine.

Implements a pool of 5 radically different template variants for each mode
(standard, concise, technical, followup) cycling sequentially based on regen_count.
Uses regen_count-based word-choice shuffling so even the same variant index
produces slightly different phrasing on repeated hits.
Word-count gate ensures every generated email stays under 150 words.
"""
from __future__ import annotations


# ── Word-choice pools for deterministic shuffling ─────────────────────

_OPENERS = [
    "I saw that",
    "I noticed that",
    "I saw",
    "I noticed",
    "I noticed recently that",
]

_CTA_PHRASES = [
    "Would you be open to a brief 5-minute chat this week?",
    "Would you have a few minutes for a quick introductory call?",
    "Could we set up a short 5-minute chat sometime this week?",
    "Would you be open to a quick call to see if my background might be a fit?",
    "Could I send over a brief project walkthrough or code sample?",
]

_TIME_PHRASES = [
    "this week",
    "sometime this week",
    "early next week",
    "at your convenience",
    "over the next few days",
]


def _pick(pool: list[str], seed: int) -> str:
    """Deterministically select an item from a pool using seed."""
    return pool[seed % len(pool)]


def generate_email(
    contact: dict,
    variant: int = 0,
    mode: str = "standard",
    regen_count: int = 1,
    previous_subject: str = "",
    previous_body: str = "",
) -> tuple[str, str]:
    """Return a validated (subject, body) tuple for *contact*.

    Args:
        contact: Recipient and candidate details dictionary.
        variant: Integer variant index (0-4).
        mode: Outreach style mode ('standard', 'concise', 'technical', 'followup').
        regen_count: Sequential regeneration counter (1-indexed).
        previous_subject: Active subject in editor to strictly differ from.
        previous_body: Active body in editor to strictly differ from.

    Raises:
        ValueError: If the generated body exceeds 150 words.
    """
    # Use regen_count if provided, otherwise variant
    effective_idx = (regen_count - 1) if regen_count > 0 else variant
    subject, body = _build_template_email(contact, mode=mode, cycle_index=effective_idx, seed=regen_count)

    # Strictly avoid repeating active editor text — try up to 5 offsets
    for offset in range(1, 6):
        matches_subj = bool(previous_subject and subject.strip().lower() == previous_subject.strip().lower())
        matches_body = bool(previous_body and body.strip().lower() == previous_body.strip().lower())
        if matches_subj or matches_body:
            subject, body = _build_template_email(contact, mode=mode, cycle_index=effective_idx + offset, seed=regen_count + offset)
        else:
            break

    if not validate_email(body):
        raise ValueError(
            f"Generated email failed word-count validation for "
            f"{contact.get('company', 'unknown')}"
        )
    return subject, body


def _build_template_email(contact: dict, mode: str = "standard", cycle_index: int = 0, seed: int = 1) -> tuple[str, str]:
    recipient_name = contact.get("recipient_name", "there")
    company = contact.get("company", "your company")
    role = contact.get("role", "the open role")
    note = contact.get("personalization_note", "")
    candidate = contact.get("candidate_name", "Harsh Yadav")
    background = contact.get("candidate_background", "Python developer and AI engineer")
    portfolio = contact.get("portfolio_url", "")

    note_clause = f" {note.rstrip('.')}." if note else ""
    port_line = f"\n{portfolio}" if portfolio else ""
    idx = cycle_index % 5
    mode_lower = (mode or "standard").lower().strip()

    # Use seed for word-choice shuffling
    opener = _pick(_OPENERS, seed)
    cta = _pick(_CTA_PHRASES, seed + idx)
    time_phrase = _pick(_TIME_PHRASES, seed + idx + 1)

    # ── 1. CONCISE MODE (5 distinct variations) ─────────────────────────
    if mode_lower == "concise":
        if idx == 0:
            subj = f"Quick question re: {role} at {company}"
            bdy = f"Hi {recipient_name},\n\nI noticed you are expanding your team for the {role} position.{note_clause}\n\nI work primarily in {background}, building clean tools and reliable backend services. Would you be open to a brief 5-minute chat {time_phrase}?\n\nBest,\n{candidate}{port_line}"
        elif idx == 1:
            subj = f"{role} role at {company} — {candidate}"
            bdy = f"Hi {recipient_name},\n\nI saw that {company} is hiring for the {role} role and wanted to introduce myself.{note_clause}\n\nI'm {candidate}, focused on {background}. I'd love to help tackle immediate engineering priorities on your team. Would it make sense to share a quick project walkthrough or code sample?\n\nBest,\n{candidate}{port_line}"
        elif idx == 2:
            subj = f"Quick intro / {company} {role}"
            bdy = f"Hi {recipient_name},\n\nI'm reaching out regarding the open {role} position at {company}.{note_clause}\n\nWith hands-on experience in {background}, I enjoy building robust, production-ready systems. Would you be open to a quick 5-minute chat {time_phrase} to see if my background aligns with your needs?\n\nBest,\n{candidate}{port_line}"
        elif idx == 3:
            subj = f"{company} {role} — quick inquiry"
            bdy = f"Hi {recipient_name},\n\nI came across the {role} opening at {company} and thought I'd reach out directly.{note_clause}\n\nI'm {candidate}, and I build systems around {background}. Would you have a few minutes for a brief introductory call, or could you point me to whoever is leading this search?\n\nBest,\n{candidate}{port_line}"
        else:
            subj = f"Interested in the {role} role at {company}"
            bdy = f"Hi {recipient_name},\n\nI saw that {company} is looking for a {role} and wanted to put my name forward.{note_clause}\n\nI work extensively with {background}, shipping dependable software and clean APIs. {cta}\n\nBest,\n{candidate}{port_line}"
        return subj, bdy.strip()

    # ── 2. TECHNICAL MODE (5 distinct variations) ────────────────────────
    if mode_lower == "technical":
        if idx == 0:
            subj = f"Engineering inquiry: {role} at {company}"
            bdy = f"Hi {recipient_name},\n\nI saw that {company} is hiring for the {role} position and wanted to get in touch.{note_clause}\n\nMy background is centered on {background}, focusing on clean system architecture, API performance, and automated testing. I'd welcome the opportunity to apply that experience to the {role} position.\n\nWould you be open to a brief 5-minute technical chat {time_phrase}?\n\nBest regards,\n{candidate}{port_line}"
        elif idx == 1:
            subj = f"Inquiry regarding {company}'s {role} opening"
            bdy = f"Hi {recipient_name},\n\nI saw the {role} opening at {company} and wanted to introduce myself.{note_clause}\n\nAs a developer focused on {background}, I've engineered backend services with thorough testing, observability, and modular designs. I'd love to bring that hands-on experience to your team.\n\nWould you be open to a quick 5-minute chat, or taking a look at a recent project repo?\n\nBest regards,\n{candidate}{port_line}"
        elif idx == 2:
            subj = f"Backend engineering for {company}'s {role} team"
            bdy = f"Hi {recipient_name},\n\nI saw the {role} opening at {company} and wanted to reach out.{note_clause}\n\nI specialize in {background}, building resilient pipelines and maintainable microservices. I'd welcome the chance to discuss how that experience could fit the role.\n\nCould we jump on a brief 5-minute call {time_phrase} to discuss?\n\nBest regards,\n{candidate}{port_line}"
        elif idx == 3:
            subj = f"{candidate} — inquiry regarding {company} {role}"
            bdy = f"Hi {recipient_name},\n\nI saw that {company} is hiring for a {role}.{note_clause}\n\nWith a strong focus on {background}, I build fault-tolerant backend services and automated testing workflows. I would love to bring these engineering practices to your team for the {role} position.\n\nAre you available for a brief 5-minute conversation {time_phrase}?\n\nBest regards,\n{candidate}{port_line}"
        else:
            subj = f"Technical inquiry: {role} at {company}"
            bdy = f"Hi {recipient_name},\n\nI saw that {company} is hiring for the {role} role and wanted to reach out directly.{note_clause}\n\nI've worked extensively with {background}, building reliable services and developer tooling. I'd welcome the chance to discuss how I could contribute to what your engineering team is building.\n\n{cta}\n\nBest regards,\n{candidate}{port_line}"
        return subj, bdy.strip()

    # ── 3. FOLLOWUP MODE (5 distinct variations) ─────────────────────────
    if mode_lower == "followup":
        if idx == 0:
            subj = f"Following up: {role} at {company}"
            bdy = f"Hi {recipient_name},\n\nFollowing up briefly on my earlier note regarding the {role} position at {company}.\n\nI know you're busy, so I'll keep this short — just wanted to see if you had a moment to consider my background, or if there is someone else on the team I should connect with?\n\nThank you for your time.\n\nBest,\n{candidate}{port_line}"
        elif idx == 1:
            subj = f"Checking in on {role} @ {company}"
            bdy = f"Hi {recipient_name},\n\nChecking in on my previous email regarding the {role} opening at {company}.\n\nI'm still very interested in contributing my background in {background} to your team. I'd be happy to send over a quick code sample or project walkthrough if helpful.\n\nAppreciate your time.\n\nBest,\n{candidate}{port_line}"
        elif idx == 2:
            subj = f"Quick follow-up regarding {company} {role}"
            bdy = f"Hi {recipient_name},\n\nHope your week is going well. I wanted to circle back briefly on my note regarding the {role} position at {company}.\n\nI'd be happy to share a short overview of my latest work if useful.\n\nThanks,\n{candidate}{port_line}"
        elif idx == 3:
            subj = f"Following up on the {role} opening at {company}"
            bdy = f"Hi {recipient_name},\n\nTouching base one last time regarding the {role} role at {company}.\n\nIf the position is still open, I'd welcome the chance to speak with the hiring manager or engineering lead.\n\nBest regards,\n{candidate}{port_line}"
        else:
            subj = f"Gentle nudge: {role} at {company}"
            bdy = f"Hi {recipient_name},\n\nJust a friendly follow-up on my earlier note about the {role} position at {company}.\n\nI completely understand if the timing isn't right — would it help if I reached out to someone else on the engineering team instead?\n\nThanks for your time.\n\nBest,\n{candidate}{port_line}"
        return subj, bdy.strip()

    # ── 4. STANDARD MODE (5 distinct variations) ─────────────────────────
    if idx == 0:
        subj = f"Quick note on the {role} role at {company}"
        bdy = f"Hi {recipient_name},\n\n{opener} {company} is hiring for the {role} position.{note_clause}\n\nI'm {candidate}, and I've been building projects around {background}. This role stood out to me because the work connects closely with what I've been building recently.\n\n{cta}\n\nBest,\n{candidate}{port_line}"
    elif idx == 1:
        subj = f"{candidate} <> {company}: {role}"
        bdy = f"Hi {recipient_name},\n\nI noticed you are expanding your team for the {role} position.{note_clause}\n\nAs an engineer specializing in {background}, I've focused on shipping reliable software and building clean architectures. I would love to bring that experience to {company}'s engineering efforts.\n\nCould we schedule 5 minutes {time_phrase} for a brief introductory conversation?\n\nBest regards,\n{candidate}{port_line}"
    elif idx == 2:
        subj = f"{role} inquiry — {company}"
        bdy = f"Hi {recipient_name},\n\nI'm reaching out regarding the open {role} position at {company}.{note_clause}\n\nMy work revolves around {background}, building end-to-end solutions that are practical and reliable. I'd love the opportunity to contribute directly to the technical roadmap at {company}.\n\nWould you be open to a brief 5-minute chat or taking a quick look at my code?\n\nBest,\n{candidate}{port_line}"
    elif idx == 3:
        subj = f"Exploring {role} opportunities at {company}"
        bdy = f"Hi {recipient_name},\n\nI saw the {role} opening at {company} and wanted to introduce myself.{note_clause}\n\nI'm {candidate}, an engineer with a background in {background}. The role looks relevant to the work I have been doing.\n\nDo you have a few minutes {time_phrase} for a brief chat or to look over my portfolio?\n\nBest,\n{candidate}{port_line}"
    else:
        subj = f"Introduction re: {role} role at {company}"
        bdy = f"Hi {recipient_name},\n\nI came across the {role} opening at {company} and wanted to introduce myself.{note_clause}\n\nI'm {candidate} — I build production systems around {background}, and this role looks relevant to my experience.\n\n{cta}\n\nBest,\n{candidate}{port_line}"

    return subj, bdy.strip()


FABRICATED_CLAIM_TRIGGERS: list[str] = [
    "referred me",
    "recommended that i reach out",
    "suggested that i reach out",
    "suggested that i contact",
    "suggested i contact",
    "suggested i reach out",
    "we spoke earlier",
    "as we discussed",
    "per our conversation",
    "our mutual friend",
    "we met at",
    "you mentioned that",
]


def validate_email(body: str) -> bool:
    """Return True if *body* passes all quality gates (≤150 words, no hallucinated claims)."""
    if not body or not body.strip():
        print("  [validation] Empty email body")
        return False

    word_count = len(body.split())
    if word_count > 150:
        print(f"  [validation] Too long: {word_count} words (max 150)")
        return False

    body_lower = body.lower()
    for trigger in FABRICATED_CLAIM_TRIGGERS:
        if trigger in body_lower:
            print(f"  [validation] Fabricated claim trigger phrase detected: '{trigger}' (EC-2.5)")
            return False

    return True


def generate_followup(contact: dict, previous_subject: str = "") -> tuple[str, str]:
    """Generate a polite follow-up email.

    If previous_subject is provided, the subject becomes 'Re: <previous_subject>'.
    Otherwise falls back to the standard followup template subject.
    """
    _, body = _build_template_email(contact, mode="followup", cycle_index=0)
    if previous_subject and previous_subject.strip():
        subject = f"Re: {previous_subject.strip()}"
    else:
        subject = _build_template_email(contact, mode="followup", cycle_index=0)[0]
    return subject, body
