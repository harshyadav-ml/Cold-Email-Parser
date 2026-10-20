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
    "I noticed",
    "I came across",
    "I saw",
    "I've been following",
    "I spotted",
]

_CTA_PHRASES = [
    "Would you be open to a quick look at my profile?",
    "Could we schedule a brief 5-minute chat this week?",
    "Would you have a moment to review my portfolio?",
    "Do you have 7 minutes for a quick introductory call?",
    "Can I send over a short code walkthrough?",
]

_TIME_PHRASES = [
    "this week",
    "this Thursday",
    "sometime soon",
    "early next week",
    "at your convenience",
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

    note_clause = f" {note}." if note else ""
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
            bdy = f"Hi {recipient_name},\n\n{opener} {company} is expanding the {role} team.{note_clause}\n\nI specialize in {background} and build high-throughput tools with clean APIs. Open to a brief 5-minute technical chat?\n\nBest,\n{candidate}{port_line}"
        elif idx == 1:
            subj = f"{candidate} for {company} {role}"
            bdy = f"Hi {recipient_name},\n\nSaw {company}'s recent work in this space.{note_clause}\n\nI'm {candidate}, an engineer focused on {background}. I'd love to help tackle immediate engineering goals for your team. Can I share a quick code sample?\n\nBest,\n{candidate}{port_line}"
        elif idx == 2:
            subj = f"{company} {role} — quick intro"
            bdy = f"Hi {recipient_name},\n\nReaching out regarding the {role} position at {company}.{note_clause}\n\nWith extensive experience in {background}, I ship robust, production-ready systems. Would you be open to a 7-minute call {time_phrase}?\n\nBest,\n{candidate}{port_line}"
        elif idx == 3:
            subj = f"Brief inquiry: {role} @ {company}"
            bdy = f"Hi {recipient_name},\n\nLoved your recent team updates at {company}.{note_clause}\n\nI'm {candidate}, building reliable systems around {background}. Would you have 3 minutes to review my repository or point me to the hiring lead?\n\nBest,\n{candidate}{port_line}"
        else:
            subj = f"Interested in {role} — {company}"
            bdy = f"Hi {recipient_name},\n\n{opener} {company}'s open {role} position.{note_clause}\n\nI'm an engineer shipping production tools around {background}. {cta}\n\nBest,\n{candidate}{port_line}"
        return subj, bdy.strip()

    # ── 2. TECHNICAL MODE (5 distinct variations) ────────────────────────
    if mode_lower == "technical":
        if idx == 0:
            subj = f"Scaling backend systems for {company}'s {role}"
            bdy = f"Hi {recipient_name},\n\nSaw {company}'s engineering progress on {role} challenges.{note_clause}\n\nMy background is centered on {background}, emphasizing distributed architecture, low latency, and modular API design. Given {company}'s architecture demands, I'd love to help your team eliminate bottlenecks.\n\nDo you have 5 minutes {time_phrase} for a technical chat or code review?\n\nBest regards,\n{candidate}{port_line}"
        elif idx == 1:
            subj = f"Architecture & telemetry discussion for {company} {role}"
            bdy = f"Hi {recipient_name},\n\nFollowing {company}'s technical footprint.{note_clause}\n\nAs a developer focused on {background}, I've engineered high-throughput services with rigorous telemetry and automated pipelines. I'd love to contribute to your core stack as a {role}.\n\nWould you be open to reviewing my technical repository and benchmarks?\n\nBest regards,\n{candidate}{port_line}"
        elif idx == 2:
            subj = f"Low-latency pipelines <> {company} {role}"
            bdy = f"Hi {recipient_name},\n\nInspecting {company}'s stack and your open {role} requirements.{note_clause}\n\nI specialize in {background}, optimizing pipeline throughput and building resilient microservices. I'm excited about the scale challenges your team is solving.\n\nCould we jump on a brief 10-minute technical debrief {time_phrase}?\n\nBest regards,\n{candidate}{port_line}"
        elif idx == 3:
            subj = f"{candidate} <> {company}: Systems infrastructure inquiry"
            bdy = f"Hi {recipient_name},\n\nNoticed {company}'s recent technical milestones in production.{note_clause}\n\nWith a deep focus on {background}, I build fault-tolerant backend services and automated testing harnesses. I would love to bring these architectural practices to the {role} position.\n\nAre you available for a brief engineering discussion {time_phrase}?\n\nBest regards,\n{candidate}{port_line}"
        else:
            subj = f"Engineering deep-dive: {role} at {company}"
            bdy = f"Hi {recipient_name},\n\n{opener} {company}'s infrastructure challenges around {role}.{note_clause}\n\nI've built event-driven systems and observability tooling around {background}. I'd welcome the chance to discuss how I could contribute to your architecture roadmap.\n\n{cta}\n\nBest regards,\n{candidate}{port_line}"
        return subj, bdy.strip()

    # ── 3. FOLLOWUP MODE (5 distinct variations) ─────────────────────────
    if mode_lower == "followup":
        if idx == 0:
            subj = f"Following up: {role} at {company}"
            bdy = f"Hi {recipient_name},\n\nFollowing up briefly on my earlier note regarding the {role} opportunity at {company}.\n\nI understand you're busy — just wanted to check if you had a moment to consider my background, or if there's someone else on the team I should connect with?\n\nThank you for your time.\n\nBest,\n{candidate}{port_line}"
        elif idx == 1:
            subj = f"Checking in on {role} @ {company}"
            bdy = f"Hi {recipient_name},\n\nChecking in on my previous email regarding the {role} opening at {company}.\n\nI'm still very interested in contributing my background in {background} to your team. Would love to send over a few relevant project write-ups if helpful.\n\nAppreciate your time.\n\nBest,\n{candidate}{port_line}"
        elif idx == 2:
            subj = f"Quick follow-up regarding {company} {role}"
            bdy = f"Hi {recipient_name},\n\nHope your week is going well. Wanted to circle back on my note regarding the {role} position at {company}.\n\nGiven your team's current focus, I'd love to share a 2-minute walkthrough of my latest work if you have a moment.\n\nThanks,\n{candidate}{port_line}"
        elif idx == 3:
            subj = f"Re: {role} opening at {company}"
            bdy = f"Hi {recipient_name},\n\nTouching base one last time regarding the {role} role at {company}.\n\nIf the position is still open, I'd welcome the chance to speak with the hiring manager or engineering lead.\n\nBest regards,\n{candidate}{port_line}"
        else:
            subj = f"Gentle nudge: {role} at {company}"
            bdy = f"Hi {recipient_name},\n\nJust a friendly bump on my earlier note about the {role} position at {company}.\n\nI completely understand if the timing isn't right — would it help if I reached out to someone else on the engineering team instead?\n\nThanks for your time.\n\nBest,\n{candidate}{port_line}"
        return subj, bdy.strip()

    # ── 4. STANDARD MODE (5 distinct variations) ─────────────────────────
    if idx == 0:
        subj = f"Quick note on the {role} role at {company}"
        bdy = f"Hi {recipient_name},\n\n{opener} {company} is hiring for {role}.{note_clause}\n\nI'm {candidate}, and I've been building projects around {background}. This role stood out because it connects closely with what I've been working on.\n\n{cta}\n\nBest,\n{candidate}{port_line}"
    elif idx == 1:
        subj = f"{candidate} <> {company}: {role}"
        bdy = f"Hi {recipient_name},\n\nSaw {company}'s recent progress and the open {role} position.{note_clause}\n\nAs an engineer specializing in {background}, I've focused on delivering reliable software and shipping fast. I would love to bring this momentum to {company}'s engineering initiatives.\n\nCould we schedule 5 minutes {time_phrase} for a brief introductory conversation?\n\nBest regards,\n{candidate}{port_line}"
    elif idx == 2:
        subj = f"{role} inquiry — {company}"
        bdy = f"Hi {recipient_name},\n\nReaching out regarding the {role} opening on your team.{note_clause}\n\nMy work revolves around {background}, building end-to-end solutions that scale. I'm eager to contribute directly to the technical roadmap at {company}.\n\nWould you be open to a 7-minute introductory call or reviewing my portfolio?\n\nBest,\n{candidate}{port_line}"
    elif idx == 3:
        subj = f"Exploring {role} opportunities at {company}"
        bdy = f"Hi {recipient_name},\n\nFollowing {company}'s exciting momentum around {role}.{note_clause}\n\nI'm {candidate}, an engineer with a track record in {background}. Your team's engineering velocity aligns closely with the tools and systems I love building.\n\nDo you have a moment {time_phrase} for a brief chat or to look over my code?\n\nBest,\n{candidate}{port_line}"
    else:
        subj = f"A quick {role} pitch for {company}"
        bdy = f"Hi {recipient_name},\n\n{opener} {company}'s engineering team and the {role} opening.{note_clause}\n\nI'm {candidate} — I build production systems around {background} and I'm drawn to the kind of problems {company} is solving.\n\n{cta}\n\nBest,\n{candidate}{port_line}"

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
