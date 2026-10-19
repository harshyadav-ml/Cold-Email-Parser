# Evaluation Rubric — "The Closer" Cold Email Writer + Send Bot

> Sprint 3 · Phase-by-Phase AI Build Evaluation  
> Sources: [architecture.md](file:///Users/harsh/Desktop/Project/Cold%20Email%20Parser/docs/architecture.md) · [implementation_plan.md](file:///Users/harsh/Desktop/Project/Cold%20Email%20Parser/docs/implementation_plan.md) · [edge-cases.md](file:///Users/harsh/Desktop/Project/Cold%20Email%20Parser/docs/edge-cases.md)

---

## How to Use This Document

Each section maps to one build phase. For every phase:

- **Checklist** — binary pass/fail items the AI must satisfy
- **Scoring** — points awarded; 100 pts total per phase
- **Edge-Case Coverage** — which EC-IDs from `edge-cases.md` should be resolved by this phase
- **Red Flags** — outputs from the AI that immediately fail the phase
- **Evaluator Notes** — what to look for when reviewing AI-generated code live in Cursor

Use the **Overall Score Card** at the bottom to tally cross-phase results.

---

## Phase 0 — Project Scaffold & Configuration

> **Goal:** Empty repo → runnable skeleton with safe credential handling

### Checklist

| # | Criterion | Points | Pass / Fail |
|---|-----------|--------|-------------|
| 0.1 | All required files exist (`main.py`, `email_generator.py`, `email_sender.py`, `logger.py`, `contacts.json`, `.env.example`, `.gitignore`, `requirements.txt`, `README.md`) | 20 | |
| 0.2 | `.gitignore` correctly excludes `.env`, `__pycache__/`, `*.pyc`, `outreach_log.csv` | 15 | |
| 0.3 | `.env.example` contains all required keys (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SENDER_NAME`, `DRY_RUN`, `SEND_METHOD`, `LLM_ENABLED`) | 15 | |
| 0.4 | `.env` is NOT committed (confirmed absent from tracked files) | 20 | |
| 0.5 | `requirements.txt` is present and contains at minimum `python-dotenv` | 10 | |
| 0.6 | `main.py` validates required env vars at startup and exits with a helpful message if any are missing (EC-0.1) | 15 | |
| 0.7 | `DRY_RUN` is parsed with truthy-string support, not strict `== "true"` comparison (EC-0.2) | 5 | |

**Phase 0 Total: /100**

### Edge Cases Resolved by Phase 0

| EC-ID | Description |
|-------|-------------|
| EC-0.1 | Missing `.env` file → graceful startup error |
| EC-0.2 | Invalid boolean for `DRY_RUN` / `LLM_ENABLED` |
| EC-6.1 | Python version guard added to `main.py` |
| EC-6.2 | Friendly error if `python-dotenv` not installed |

### Red Flags

- `.env` with real credentials present in scaffold
- `DRY_RUN` defaulting to `False` with no guard
- No `.gitignore` or an empty `.gitignore`
- Module stubs missing entirely (AI skipped scaffold step)

### Evaluator Notes

> The scaffold phase is about safety and structure, not logic. The most common AI failure here is omitting the `.env` validation guard, meaning students would hit confusing `NoneType` errors the moment they forget to create `.env`. Check that the AI warns clearly, not just silently returns `None`.

---

## Phase 1 — Data Layer + Email Generator

> **Goal:** Load contacts and generate a personalized `(subject, body)` tuple for each

### Checklist

| # | Criterion | Points | Pass / Fail |
|---|-----------|--------|-------------|
| 1.1 | `contacts.json` contains at least 3 valid sample records with all required fields | 10 | |
| 1.2 | `load_contacts()` in `main.py` reads `contacts.json` with explicit `encoding="utf-8"` (EC-6.4) | 5 | |
| 1.3 | `json.JSONDecodeError` is caught with a human-readable error (EC-1.2) | 10 | |
| 1.4 | Each contact is validated for required fields before generation; missing fields → `continue` with log (EC-1.3) | 15 | |
| 1.5 | Fields are `.strip()`-ed; whitespace-only values treated as missing (EC-1.7) | 5 | |
| 1.6 | `generate_email(contact)` returns a `(subject, body)` tuple | 10 | |
| 1.7 | Subject uses `role` and `company`; body includes all 6 structural sections (hook, intro, value, CTA, sign-off) | 15 | |
| 1.8 | `recipient_name` missing → fallback salutation, NOT `"Hi None,"` (EC-2.2) | 10 | |
| 1.9 | `portfolio_url` missing → sign-off line omitted, NOT `"None"` printed (EC-2.3) | 5 | |
| 1.10 | `validate_email(body)` checks word count <= 150 and returns `bool` (EC-2.1) | 10 | |
| 1.11 | Empty array `[]` in `contacts.json` → informative exit, not silent success (EC-1.1) | 5 | |

**Phase 1 Total: /100**

### Edge Cases Resolved by Phase 1

| EC-ID | Description |
|-------|-------------|
| EC-1.1 | Empty contacts array |
| EC-1.2 | Malformed JSON |
| EC-1.3 | Missing required fields |
| EC-1.7 | Whitespace-only fields |
| EC-1.8 | Very long field values |
| EC-1.9 | Special/Unicode characters in fields |
| EC-2.1 | Word limit exceeded |
| EC-2.2 | Missing `recipient_name` |
| EC-2.3 | Missing `portfolio_url` |
| EC-2.8 | Empty subject line fallback |
| EC-6.4 | Non-UTF-8 file encoding |

### Red Flags

- `contact["recipient_email"]` without `.get()` — will raise `KeyError`
- `f"Hi {contact['recipient_name']},"` without a default — prints `"Hi None,"`
- No word count validation in `validate_email()`
- `contacts.json` opened without explicit UTF-8 encoding
- `generate_email()` returns a plain string instead of `(subject, body)` tuple

### Evaluator Notes

> The most common AI mistake in Phase 1 is generating the template correctly but forgetting defensive handling for optional fields (`recipient_name`, `portfolio_url`). Run a test contact with those two fields removed and inspect the output literally. Also check that the AI uses `contact.get("field", default)` rather than `contact["field"]` everywhere.

---

## Phase 2 — Preview & Human Review Loop

> **Goal:** Terminal display of generated email + user confirmation before any action

### Checklist

| # | Criterion | Points | Pass / Fail |
|---|-----------|--------|-------------|
| 2.1 | Preview clearly shows: recipient email, company, role, subject, and full body | 15 | |
| 2.2 | Prompt accepts `send`, `draft`, `skip` (case-insensitive, leading/trailing whitespace stripped) (EC-3.1) | 15 | |
| 2.3 | Blank input re-prompts with hint text rather than silently defaulting (EC-3.1) | 10 | |
| 2.4 | `KeyboardInterrupt` (Ctrl+C) handled gracefully; session summary printed (EC-3.2) | 15 | |
| 2.5 | `EOFError` (Ctrl+D / piped stdin) handled; treated as skip (EC-3.3) | 10 | |
| 2.6 | If validation fails (word count), a warning is shown in preview before confirmation (EC-2.1) | 10 | |
| 2.7 | Loop continues to next contact after any decision (`send`, `draft`, `skip`) | 15 | |
| 2.8 | Duplicate emails flagged before preview with a `[DUPLICATE]` warning (EC-1.5) | 10 | |

**Phase 2 Total: /100**

### Edge Cases Resolved by Phase 2

| EC-ID | Description |
|-------|-------------|
| EC-1.5 | Duplicate recipient emails caught before preview |
| EC-3.1 | Unexpected input at confirmation prompt |
| EC-3.2 | Ctrl+C during loop |
| EC-3.3 | EOF/Ctrl+D on stdin |
| EC-3.4 | ANSI colour codes stripped in non-TTY environments |

### Red Flags

- `action = input("...").lower()` without `.strip()` — leading space breaks match
- No `try/except KeyboardInterrupt` — Ctrl+C prints ugly traceback
- `if action == "send"` — not case-insensitive; `"Send"` falls through
- No re-prompt for blank input — silently skips the contact
- Preview shows `None` for missing optional fields

### Evaluator Notes

> Test Phase 2 by typing `SEND` (uppercase), then pressing Enter immediately (blank), then Ctrl+C. All three should behave gracefully. The AI commonly forgets the `EOFError` case entirely — this is important for non-interactive/piped usage.

---

## Phase 3 — Email Delivery via SMTP

> **Goal:** `DRY_RUN=true` prints only; `DRY_RUN=false` actually sends via SMTP

### Checklist

| # | Criterion | Points | Pass / Fail |
|---|-----------|--------|-------------|
| 3.1 | `DRY_RUN=true` prints email details without opening any SMTP connection | 15 | |
| 3.2 | `DRY_RUN=false` connects to `smtp.gmail.com:587` with `STARTTLS` and App Password auth | 15 | |
| 3.3 | `SMTPAuthenticationError` caught with a message pointing to App Passwords (EC-0.4) | 10 | |
| 3.4 | `ConnectionRefusedError` / `OSError` caught; log as `failed`, continue loop (EC-4.1, EC-4.5) | 10 | |
| 3.5 | `SMTPRecipientsRefused` caught per recipient; loop continues (EC-4.3) | 10 | |
| 3.6 | `recipient_email` is validated before SMTP call; invalid format skipped (EC-1.4) | 10 | |
| 3.7 | Email body encoded as `MIMEText(..., "plain", "utf-8")` (EC-1.9) | 10 | |
| 3.8 | `send_email()` returns a status dict `{"status": "sent"/"failed", "error_message": ...}` | 10 | |
| 3.9 | Session-level send cap enforced (max 5 real sends per run) (EC-4.8) | 10 | |

**Phase 3 Total: /100**

### Edge Cases Resolved by Phase 3

| EC-ID | Description |
|-------|-------------|
| EC-0.3 | Wrong SMTP port detected or documented |
| EC-0.4 | App Password vs. account password auth error |
| EC-1.4 | Invalid `recipient_email` format |
| EC-1.9 | Special/Unicode characters in MIME body |
| EC-4.1 | SMTP connection refused |
| EC-4.2 | SMTP `MAIL FROM` rejected |
| EC-4.3 | Recipient address rejected (`550`) |
| EC-4.4 | Gmail daily send limit error |
| EC-4.5 | Network offline during send |
| EC-4.8 | Session send cap exceeded |

### Red Flags

- SMTP connection opened even when `DRY_RUN=true`
- Bare `except Exception` swallowing all errors silently
- `body.encode("ascii")` — breaks on Unicode
- No send cap; 20-contact list sends 20 emails
- `smtplib.SMTP_SSL` used on port 587 (wrong; should be `SMTP` + `STARTTLS`)
- SMTP connection not closed in `finally` block → connection leak

### Evaluator Notes

> The highest-risk failures in Phase 3 are security and ethics failures: sending real emails to real people without a send cap, or leaking SMTP credentials in logs. Confirm the AI never `print()`s the password, and check that the send count guard fires correctly by inspecting the code path, not just trusting the AI's claim.

---

## Phase 4 — Audit Logging (CSV)

> **Goal:** Every action (generated, sent, drafted, skipped, failed) is recorded in `outreach_log.csv`

### Checklist

| # | Criterion | Points | Pass / Fail |
|---|-----------|--------|-------------|
| 4.1 | `log_entry()` appends one row per contact to `outreach_log.csv` | 15 | |
| 4.2 | CSV opened with `encoding="utf-8-sig"` for Windows Excel compatibility (EC-5.4) | 10 | |
| 4.3 | Header row written only if file does not exist or is empty (EC-5.3) | 10 | |
| 4.4 | `PermissionError` on CSV write is caught with a friendly message (EC-5.1) | 10 | |
| 4.5 | `OSError` (disk full) on CSV write is caught; session continues (EC-5.2) | 10 | |
| 4.6 | All 8 required columns present: `timestamp`, `recipient_email`, `company`, `role`, `subject`, `status`, `error_message`, `word_count` | 15 | |
| 4.7 | `status` values are one of the defined enum: `generated`, `drafted`, `sent`, `skipped`, `failed`, `opted_out`, `skipped_duplicate`, `skipped_limit` (EC-5.5) | 10 | |
| 4.8 | `get_log_summary()` returns counts grouped by status | 10 | |
| 4.9 | Session summary printed at the end of every run (including after Ctrl+C via `finally`) (EC-6.7) | 10 | |

**Phase 4 Total: /100**

### Edge Cases Resolved by Phase 4

| EC-ID | Description |
|-------|-------------|
| EC-5.1 | CSV locked by Excel |
| EC-5.2 | Disk full during CSV write |
| EC-5.3 | Header duplication on concurrent writes |
| EC-5.4 | Unicode characters in log fields |
| EC-5.5 | Unexpected status value |
| EC-6.3 | Concurrent `main.py` invocations writing to same CSV |
| EC-6.7 | Session summary missing after Ctrl+C |

### Red Flags

- CSV opened with default encoding (no `encoding=` arg) — breaks on Windows with non-ASCII
- Header written unconditionally — produces double headers after a restart
- `log_entry()` called before send result is known — logs incorrect status
- `get_log_summary()` not called in `finally` block
- `error_message` column omitted — debugging failures becomes impossible

### Evaluator Notes

> Open `outreach_log.csv` in Excel after a run with Unicode company names and verify it displays correctly. Then restart `main.py` and check that the header is NOT duplicated. Finally, simulate a failed send and confirm the `error_message` column contains a useful string, not just `"None"`.

---

## Phase 5 (Stretch) — LLM Rewriting + Gmail API + Streamlit UI

> **Goal:** Upgrade all three optional layers; each is independently testable

### LLM Rewriting Checklist

| # | Criterion | Points | Pass / Fail |
|---|-----------|--------|-------------|
| 5L.1 | `LLM_ENABLED=true` triggers Claude/OpenAI API call in `generate_email()` | 10 | |
| 5L.2 | `ANTHROPIC_API_KEY` missing → fallback to template with `[WARNING]` (EC-0.5) | 10 | |
| 5L.3 | Empty/whitespace LLM response → fallback to template (EC-2.4) | 10 | |
| 5L.4 | `RateLimitError` caught; LLM disabled for remainder of session (EC-2.6) | 10 | |
| 5L.5 | API timeout (> 30s) caught; fallback to template (EC-2.7) | 10 | |
| 5L.6 | `validate_email()` checks for fabricated-claim trigger phrases (EC-2.5) | 10 | |

**LLM Sub-Total: /60**

### Gmail API Checklist

| # | Criterion | Points | Pass / Fail |
|---|-----------|--------|-------------|
| 5G.1 | `SEND_METHOD=gmail_api` triggers Gmail API draft/send path | 10 | |
| 5G.2 | OAuth token refresh handled automatically; `RefreshError` prompts re-auth (EC-4.6) | 10 | |
| 5G.3 | Empty draft body detected before API call; not submitted (EC-4.7) | 10 | |
| 5G.4 | `HttpError 429` (quota) caught; session pauses or falls back to SMTP | 10 | |

**Gmail API Sub-Total: /40**

### Streamlit UI Checklist (Optional Bonus)

| # | Criterion | Points | Pass / Fail |
|---|-----------|--------|-------------|
| 5S.1 | Streamlit app renders all contacts in a list | 5 | |
| 5S.2 | Each contact shows a generated email preview before confirm | 5 | |
| 5S.3 | Send/Draft/Skip buttons functional | 5 | |
| 5S.4 | Log entries visible in a table below the form | 5 | |

**Streamlit Bonus: /20**

**Phase 5 Total: /100 (+ 20 bonus)**

### Edge Cases Resolved by Phase 5

| EC-ID | Description |
|-------|-------------|
| EC-0.5 | `ANTHROPIC_API_KEY` missing |
| EC-2.4 | LLM empty response |
| EC-2.5 | LLM fabricated claims |
| EC-2.6 | LLM API rate limit |
| EC-2.7 | LLM API timeout |
| EC-4.6 | Gmail OAuth token expired |
| EC-4.7 | Gmail draft body empty |

### Red Flags

- LLM response used without length or content validation
- No fallback path when LLM fails — loop crashes
- OAuth credentials stored in plain text instead of `token.json`
- Streamlit `st.button("Send")` triggers send on every re-render (missing session state guard)

---

## Overall Score Card

| Phase | Max Points | Score | Status |
|-------|-----------|-------|--------|
| Phase 0 — Scaffold & Config | 100 | | |
| Phase 1 — Data Layer + Generator | 100 | | |
| Phase 2 — Preview & Review Loop | 100 | | |
| Phase 3 — Email Delivery (SMTP) | 100 | | |
| Phase 4 — Audit Logging | 100 | | |
| Phase 5 — Stretch Goals | 100 (+20 bonus) | | |
| **TOTAL** | **600 (+20)** | | |

### Grading Scale (per phase)

| Score | Grade | Meaning |
|-------|-------|---------|
| 90–100 | A | Production-ready; all edge cases handled |
| 75–89 | B | Solid; minor missing guardrails |
| 60–74 | C | Functional MVP; several edge cases unhandled |
| 40–59 | D | Partially working; critical gaps remain |
| 0–39 | F | Does not meet phase goal |

---

## Cross-Phase Edge Case Coverage Map

This table shows which phase is responsible for first resolving each edge case. Use this to catch regressions — if an EC-ID is marked as Phase 1 but still fails in the Phase 3 demo, that is a regression.

| EC-ID | First Resolved In | Severity |
|-------|------------------|----------|
| EC-0.1 | Phase 0 | Critical |
| EC-0.2 | Phase 0 | Critical |
| EC-0.3 | Phase 3 | High |
| EC-0.4 | Phase 3 | High |
| EC-0.5 | Phase 5 | Medium |
| EC-1.1 | Phase 1 | Medium |
| EC-1.2 | Phase 1 | Critical |
| EC-1.3 | Phase 1 | Critical |
| EC-1.4 | Phase 3 | High |
| EC-1.5 | Phase 2 | High |
| EC-1.6 | Phase 1 | High |
| EC-1.7 | Phase 1 | Medium |
| EC-1.8 | Phase 1 | Medium |
| EC-1.9 | Phase 3 | Medium |
| EC-2.1 | Phase 1 | High |
| EC-2.2 | Phase 1 | Medium |
| EC-2.3 | Phase 1 | Medium |
| EC-2.4 | Phase 5 | Critical |
| EC-2.5 | Phase 5 | Critical |
| EC-2.6 | Phase 5 | High |
| EC-2.7 | Phase 5 | High |
| EC-2.8 | Phase 1 | Medium |
| EC-3.1 | Phase 2 | Medium |
| EC-3.2 | Phase 2 | Medium |
| EC-3.3 | Phase 2 | Medium |
| EC-3.4 | Phase 2 | Low |
| EC-4.1 | Phase 3 | Critical |
| EC-4.2 | Phase 3 | Critical |
| EC-4.3 | Phase 3 | High |
| EC-4.4 | Phase 3 | High |
| EC-4.5 | Phase 3 | High |
| EC-4.6 | Phase 5 | High |
| EC-4.7 | Phase 5 | Medium |
| EC-4.8 | Phase 3 | Critical |
| EC-5.1 | Phase 4 | Medium |
| EC-5.2 | Phase 4 | Medium |
| EC-5.3 | Phase 4 | Medium |
| EC-5.4 | Phase 4 | Medium |
| EC-5.5 | Phase 4 | Low |
| EC-6.1 | Phase 0 | Critical |
| EC-6.2 | Phase 0 | Critical |
| EC-6.3 | Phase 4 | Medium |
| EC-6.4 | Phase 1 | Medium |
| EC-6.5 | Phase 3 | Medium |
| EC-6.6 | Phase 2 | Critical |
| EC-6.7 | Phase 4 | Low |

---

> [!IMPORTANT]
> Before marking any phase as complete, run the checklist manually. Do not accept the AI's self-report that all items pass — test the specific failure inputs listed in each phase's "Red Flags" section.

> [!NOTE]
> This rubric is designed for a live Cursor build session. Each phase should take no longer than 20–30 minutes of coding. If the AI produces a phase in under 5 minutes without any error handling, treat that as a signal to review the Red Flags list carefully.
