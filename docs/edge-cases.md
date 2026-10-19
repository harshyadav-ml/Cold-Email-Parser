# Edge Cases — "The Closer" Cold Email Writer + Send Bot

> Sprint 3 · Comprehensive Edge-Case Reference  
> Sources: [architecture.md](file:///Users/harsh/Desktop/Project/Cold%20Email%20Parser/docs/architecture.md) · [problemStatement.md](file:///Users/harsh/Desktop/Project/Cold%20Email%20Parser/docs/problemStatement.md)

---

## Overview

This document catalogues every known and anticipated edge case across all modules of "The Closer". Each case includes the **trigger condition**, **expected behaviour**, **failure mode** if unhandled, and a **recommended mitigation**. Cases are grouped by the module they originate in, mirroring the layered architecture.

---

## EC-0 · Configuration & Environment Layer

### EC-0.1 — Missing `.env` file

| Attribute | Detail |
|-----------|--------|
| **Trigger** | User runs `main.py` without creating a `.env` file |
| **Expected** | Graceful error with a pointer to `.env.example` |
| **Failure mode** | `KeyError` / `None` propagated into SMTP or LLM call |
| **Mitigation** | Validate all required env vars at startup; print actionable message and exit |

```python
# Recommended guard in main.py
required_vars = ["SMTP_USER", "SMTP_PASSWORD", "SENDER_NAME"]
missing = [v for v in required_vars if not os.getenv(v)]
if missing:
    print(f"Missing env vars: {missing}. Copy .env.example to .env")
    sys.exit(1)
```

---

### EC-0.2 — Invalid boolean for `DRY_RUN` / `LLM_ENABLED`

| Attribute | Detail |
|-----------|--------|
| **Trigger** | `.env` contains `DRY_RUN=yes` or `DRY_RUN=1` instead of `true` |
| **Expected** | Correctly parsed as `True` |
| **Failure mode** | `"yes" == True` evaluates to `False`; real emails sent unintentionally |
| **Mitigation** | Use `os.getenv("DRY_RUN","true").lower() in ("true","1","yes")` |

---

### EC-0.3 — Wrong `SMTP_PORT`

| Attribute | Detail |
|-----------|--------|
| **Trigger** | User sets `SMTP_PORT=465` (SSL) but code uses `STARTTLS` flow |
| **Expected** | Clear error or automatic port-mode detection |
| **Failure mode** | `SMTPNotSupportedError` or silent connection hang |
| **Mitigation** | Document supported ports; validate port is `587` or `465` and branch accordingly |

---

### EC-0.4 — `SMTP_PASSWORD` is account password, not App Password

| Attribute | Detail |
|-----------|--------|
| **Trigger** | User pastes their Gmail login password |
| **Expected** | Authentication fails with a clear error explaining App Passwords |
| **Failure mode** | `SMTPAuthenticationError` with no helpful message |
| **Mitigation** | Catch `SMTPAuthenticationError`; print link to Google App Password setup |

---

### EC-0.5 — `ANTHROPIC_API_KEY` missing when `LLM_ENABLED=true`

| Attribute | Detail |
|-----------|--------|
| **Trigger** | User enables LLM but forgets API key |
| **Expected** | Fallback to template mode with a warning |
| **Failure mode** | `anthropic.AuthenticationError` crashes the loop |
| **Mitigation** | Check key at startup; fall back to template with `[WARNING]` log |

---

## EC-1 · Input / Data Layer

### EC-1.1 — `contacts.json` is empty array

| Attribute | Detail |
|-----------|--------|
| **Trigger** | `contacts.json` contains `[]` |
| **Expected** | Inform user no contacts found, exit cleanly |
| **Failure mode** | Silent success; session summary shows 0 emails |
| **Mitigation** | `if not contacts: print("No contacts found."); sys.exit(0)` |

---

### EC-1.2 — `contacts.json` is malformed JSON

| Attribute | Detail |
|-----------|--------|
| **Trigger** | File has a trailing comma, missing bracket, or is empty |
| **Expected** | `json.JSONDecodeError` caught with a clear error message and line hint |
| **Failure mode** | Raw Python traceback printed; confusing for students |
| **Mitigation** | Wrap `json.load()` in try/except; print filename and error position |

---

### EC-1.3 — Required field missing from a contact record

| Attribute | Detail |
|-----------|--------|
| **Trigger** | A record lacks `recipient_email`, `company`, `role`, `candidate_name`, or `candidate_background` |
| **Expected** | Skip that contact, log it as `failed`, continue with next |
| **Failure mode** | `KeyError` crashes the entire loop |
| **Mitigation** | Validate each record before the generation step; collect missing fields in error message |

```python
REQUIRED = ["recipient_email", "company", "role", "candidate_name", "candidate_background"]
missing = [f for f in REQUIRED if not contact.get(f)]
if missing:
    logger.log_entry(contact, subject="", status="failed",
                     error=f"Missing fields: {missing}")
    continue
```

---

### EC-1.4 — `recipient_email` is not a valid email address

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Field contains `"priya@"` or `"notanemail"` |
| **Expected** | Validation error before attempting send; log as `failed` |
| **Failure mode** | SMTP server returns `550 Bad address` mid-session |
| **Mitigation** | Regex or `email.utils.parseaddr` check during input validation |

---

### EC-1.5 — Duplicate recipient emails

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Same email appears twice in `contacts.json` |
| **Expected** | Warn user; skip the duplicate or ask for confirmation |
| **Failure mode** | Same person receives two emails; looks like spam |
| **Mitigation** | Deduplicate on load; log `"skipped_duplicate"` for the second entry |

---

### EC-1.6 — CSV (`jobs.csv`) has wrong column headers

| Attribute | Detail |
|-----------|--------|
| **Trigger** | CSV uses `Email` instead of `recipient_email` |
| **Expected** | Clear schema mismatch error listing expected columns |
| **Failure mode** | `KeyError` on first row |
| **Mitigation** | Validate CSV headers against expected schema on load; provide a column-mapping hint |

---

### EC-1.7 — Contact record fields contain only whitespace

| Attribute | Detail |
|-----------|--------|
| **Trigger** | `"company": "   "` or `"role": "\t"` |
| **Expected** | Treated as missing; same handling as EC-1.3 |
| **Failure mode** | Email generated with blank company/role placeholders |
| **Mitigation** | `.strip()` all string fields; treat empty-after-strip as missing |

---

### EC-1.8 — Very long field values

| Attribute | Detail |
|-----------|--------|
| **Trigger** | `personalization_note` is 2,000 characters |
| **Expected** | Truncated to a sensible limit (e.g. 300 chars) before template injection |
| **Failure mode** | Generated email massively exceeds 150-word limit; validation fails every time |
| **Mitigation** | Truncate optional fields with a `...` suffix; warn user |

---

### EC-1.9 — Special characters in contact fields

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Name contains `"O'Brien"`, company `"AT&T"`, or Unicode `"Müller"` |
| **Expected** | Email body renders correctly in UTF-8 |
| **Failure mode** | SMTP `UnicodeEncodeError`; email body corrupted |
| **Mitigation** | Use `email.mime.text.MIMEText(body, "plain", "utf-8")`; test with non-ASCII names |

---

## EC-2 · Email Generator (`email_generator.py`)

### EC-2.1 — Generated email exceeds 150-word limit

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Template expands with a very long `candidate_background` or `personalization_note` |
| **Expected** | `validate_email()` returns `False`; email is flagged for review |
| **Failure mode** | Oversized email sent unreviewed |
| **Mitigation** | Hard-truncate fields before generation; re-validate after; warn in preview |

---

### EC-2.2 — `recipient_name` is missing (optional field)

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Contact has no `recipient_name` |
| **Expected** | Salutation falls back to `"Hi there,"` or `"Hello,"` |
| **Failure mode** | Email opens with `"Hi None,"` or `"Hi ,"` |
| **Mitigation** | `salutation = f"Hi {contact.get('recipient_name', 'there')},"` |

---

### EC-2.3 — `portfolio_url` is missing (optional field)

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Contact has no `portfolio_url` |
| **Expected** | Sign-off omits the URL line gracefully |
| **Failure mode** | Email contains `"None"` or an empty line where the URL should appear |
| **Mitigation** | Conditional inclusion: `if contact.get("portfolio_url"): sign_off += url_line` |

---

### EC-2.4 — LLM returns an empty response

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Claude/OpenAI API returns `""` or a whitespace-only string |
| **Expected** | Fallback to Python template; log warning |
| **Failure mode** | Empty email body sent or previewed |
| **Mitigation** | Check `len(response.strip()) == 0`; fall back to template |

---

### EC-2.5 — LLM response contains fabricated claims

| Attribute | Detail |
|-----------|--------|
| **Trigger** | LLM invents a referral (`"John Smith referred me"`) not present in contact data |
| **Expected** | `validate_email()` detects flagged phrases and rejects |
| **Failure mode** | False claim sent to recruiter; trust violated |
| **Mitigation** | Maintain blocklist of hallucination triggers; scan body before approve |

---

### EC-2.6 — LLM API rate limit or quota exceeded

| Attribute | Detail |
|-----------|--------|
| **Trigger** | `anthropic.RateLimitError` raised mid-session |
| **Expected** | Fallback to template for remaining contacts; log warning per contact |
| **Failure mode** | Loop crashes; remaining contacts never processed |
| **Mitigation** | Catch `RateLimitError`; set `LLM_ENABLED=False` for session remainder |

---

### EC-2.7 — LLM API timeout

| Attribute | Detail |
|-----------|--------|
| **Trigger** | API call takes > 30 seconds (network issue) |
| **Expected** | Timeout after configurable limit; fallback to template |
| **Failure mode** | Infinite hang; terminal appears frozen |
| **Mitigation** | Set `timeout=30` in API client; catch `TimeoutError` |

---

### EC-2.8 — Subject line is empty after generation

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Template or LLM produces a blank subject |
| **Expected** | Fallback subject: `"Quick note from {candidate_name}"` |
| **Failure mode** | Email sent with no subject; looks unprofessional |
| **Mitigation** | Validate `subject.strip()` is non-empty post-generation |

---

## EC-3 · Preview & Human Review Loop (`main.py`)

### EC-3.1 — User enters unexpected input at confirmation prompt

| Attribute | Detail |
|-----------|--------|
| **Trigger** | User types `"y"`, `"YES"`, `"Send"`, or hits Enter without input |
| **Expected** | Case-insensitive match; blank input loops back with help text |
| **Failure mode** | Action not recognised; email skipped silently |
| **Mitigation** | Normalise with `.strip().lower()`; accept `"s"`/`"send"`, `"d"`/`"draft"`, `"sk"`/`"skip"` |

---

### EC-3.2 — User hits `Ctrl+C` during the loop

| Attribute | Detail |
|-----------|--------|
| **Trigger** | `KeyboardInterrupt` mid-session |
| **Expected** | Print session summary for contacts already processed; exit cleanly |
| **Failure mode** | Partial log with no summary; traceback printed |
| **Mitigation** | Wrap main loop in `try/except KeyboardInterrupt`; call `get_log_summary()` on exit |

---

### EC-3.3 — `Ctrl+D` / EOF on stdin

| Attribute | Detail |
|-----------|--------|
| **Trigger** | User pipes a script and stdin closes unexpectedly |
| **Expected** | Treat as "skip" for remaining contacts |
| **Failure mode** | `EOFError` crashes the loop |
| **Mitigation** | `except EOFError: action = "skip"` |

---

### EC-3.4 — Terminal does not support ANSI colours

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Running inside a pipe, CI, or non-ANSI terminal |
| **Expected** | Plain-text output with no escape sequences |
| **Failure mode** | Garbled escape characters pollute the preview |
| **Mitigation** | Check `sys.stdout.isatty()` before applying colour codes |

---

## EC-4 · Email Sender (`email_sender.py`)

### EC-4.1 — SMTP connection refused

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Firewall blocks port 587 or SMTP host is incorrect |
| **Expected** | `ConnectionRefusedError` caught; log as `failed`; continue with next contact |
| **Failure mode** | Unhandled exception; loop crashes |
| **Mitigation** | Wrap SMTP calls in try/except; include host/port in error log for easy debugging |

---

### EC-4.2 — SMTP connection succeeds but `MAIL FROM` rejected

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Gmail rejects sender address (e.g. alias mismatch) |
| **Expected** | `SMTPSenderRefused` caught; log `failed` with reason |
| **Failure mode** | Exception propagates; next contacts not reached |
| **Mitigation** | Specific `except smtplib.SMTPSenderRefused` handler |

---

### EC-4.3 — Recipient address permanently rejected (`550`)

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Email address does not exist on recipient server |
| **Expected** | `SMTPRecipientsRefused` caught; log `failed` with `recipient_email` |
| **Failure mode** | Loop crashes |
| **Mitigation** | Handle `SMTPRecipientsRefused`; skip and continue |

---

### EC-4.4 — Gmail daily SMTP send limit exceeded

| Attribute | Detail |
|-----------|--------|
| **Trigger** | User has sent 500+ emails from personal Gmail that day |
| **Expected** | SMTP `421` or `550` error caught; inform user of daily limit |
| **Failure mode** | All subsequent sends silently fail or crash |
| **Mitigation** | Catch `SMTPDataError`; check error code; print rate-limit guidance |

---

### EC-4.5 — `DRY_RUN=false` but network is offline

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Machine has no internet when attempting a real send |
| **Expected** | `socket.gaierror` or `OSError` caught; log as `failed` |
| **Failure mode** | Traceback on first send; remaining contacts not processed |
| **Mitigation** | Catch broad `OSError`; recommend `DRY_RUN=true` for offline testing |

---

### EC-4.6 — Gmail API OAuth token expired

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Stored OAuth token is stale when using `gmail_api` send method |
| **Expected** | `google.auth.exceptions.RefreshError` caught; prompt re-auth |
| **Failure mode** | `HttpError 401` crashes the send loop |
| **Mitigation** | Check token validity before loop; refresh automatically or prompt user |

---

### EC-4.7 — Gmail draft creation succeeds but draft is empty

| Attribute | Detail |
|-----------|--------|
| **Trigger** | MIME encoding error produces an empty message body |
| **Expected** | Validate draft payload before API call |
| **Failure mode** | Empty draft saved; user does not notice until manually checking Gmail |
| **Mitigation** | Assert `len(body.strip()) > 0` before encoding; check API response `snippet` |

---

### EC-4.8 — Session sends more than 5 emails

| Attribute | Detail |
|-----------|--------|
| **Trigger** | `contacts.json` has 20 records and `DRY_RUN=false` |
| **Expected** | Hard cap at 5 sends per session; remaining marked `skipped_limit` |
| **Failure mode** | Mass sending; potential spam flag from Gmail |
| **Mitigation** | Track `send_count`; break when `send_count >= MAX_SENDS_PER_SESSION` (default 5) |

---

## EC-5 · Logger (`logger.py`)

### EC-5.1 — `outreach_log.csv` is open in Excel during a write

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Windows user has the CSV open in Excel, which locks the file |
| **Expected** | `PermissionError` caught; warn user to close Excel; skip log entry |
| **Failure mode** | `PermissionError` crashes the loop |
| **Mitigation** | `except PermissionError: print("Close outreach_log.csv and retry")` |

---

### EC-5.2 — Disk is full when writing log

| Attribute | Detail |
|-----------|--------|
| **Trigger** | `OSError: [Errno 28] No space left on device` |
| **Expected** | Catch error; warn user; continue session (emails may still send) |
| **Failure mode** | Loop crash; no audit trail for successful sends |
| **Mitigation** | Wrap CSV write in try/except `OSError`; degrade gracefully |

---

### EC-5.3 — CSV headers missing on first write

| Attribute | Detail |
|-----------|--------|
| **Trigger** | `outreach_log.csv` does not exist yet and multiple processes try to create it simultaneously |
| **Expected** | Only one process writes the header; rows from others append correctly |
| **Failure mode** | Double header row; `get_log_summary()` miscounts |
| **Mitigation** | Check `os.path.exists()` before writing header; use file locking if concurrent use is expected |

---

### EC-5.4 — Unicode characters in log fields

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Company name is `"Müller GmbH"` or role is `"AI/ML Internship - Bengaluru"` |
| **Expected** | Written and read back correctly |
| **Failure mode** | `UnicodeEncodeError` on Windows (default `cp1252` encoding) |
| **Mitigation** | Open CSV with `encoding="utf-8-sig"` for cross-platform compatibility |

---

### EC-5.5 — `status` field contains an unexpected value

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Code passes `status="draft_failed"` instead of `"failed"` |
| **Expected** | `get_log_summary()` still counts and reports it |
| **Failure mode** | Unknown status silently dropped from summary counts |
| **Mitigation** | Use an enum/constant for all status values; reject unknown values with a warning |

---

## EC-6 · Cross-Cutting / System-Level

### EC-6.1 — Running in Python 2 or Python < 3.9

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Student runs `python main.py` where `python` is Python 2 |
| **Expected** | Immediate version check failure with a clear message |
| **Failure mode** | Cryptic `SyntaxError` on f-string or type hints |
| **Mitigation** | Add at the top of `main.py`: `assert sys.version_info >= (3, 9), "Python 3.9+ required"` |

---

### EC-6.2 — `python-dotenv` not installed

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Student skips `pip install -r requirements.txt` |
| **Expected** | `ImportError` caught; message says `pip install python-dotenv` |
| **Failure mode** | `ModuleNotFoundError: No module named 'dotenv'` with full traceback |
| **Mitigation** | Wrap import in try/except at top of `main.py` |

---

### EC-6.3 — Concurrent invocations of `main.py`

| Attribute | Detail |
|-----------|--------|
| **Trigger** | Student runs two terminal windows with `main.py` simultaneously |
| **Expected** | Both processes write to the log; no corruption |
| **Failure mode** | Race condition on CSV write; rows interleaved or header duplicated |
| **Mitigation** | Use `fcntl.flock` (Unix) or a simple lock file for the CSV write; document single-process expectation |

---

### EC-6.4 — `contacts.json` encoding is not UTF-8

| Attribute | Detail |
|-----------|--------|
| **Trigger** | File saved with Latin-1 encoding (common on Windows) |
| **Expected** | Decode error caught; prompt user to resave as UTF-8 |
| **Failure mode** | `UnicodeDecodeError` on load |
| **Mitigation** | `open("contacts.json", encoding="utf-8")` explicitly; catch `UnicodeDecodeError` |

---

### EC-6.5 — `.env` file has Windows line endings (`\r\n`)

| Attribute | Detail |
|-----------|--------|
| **Trigger** | `.env` created with Notepad on Windows |
| **Expected** | Values parsed correctly regardless of line endings |
| **Failure mode** | `SMTP_PASSWORD` contains a trailing `\r`; auth fails |
| **Mitigation** | Document that `.env` must use LF endings; or strip values: `os.getenv("X","").strip()` |

---

### EC-6.6 — Opt-out contact re-appears in contacts list

| Attribute | Detail |
|-----------|--------|
| **Trigger** | `optout_list.txt` contains an email that also appears in `contacts.json` |
| **Expected** | Contact is skipped before generation; logged as `opted_out` |
| **Failure mode** | Email generated and potentially sent to someone who asked to stop |
| **Mitigation** | Load opt-out list first; filter contacts before entering the main loop |

---

### EC-6.7 — Session summary is not printed after Ctrl+C

| Attribute | Detail |
|-----------|--------|
| **Trigger** | User interrupts mid-session; summary never appears |
| **Expected** | `finally` block always prints summary |
| **Failure mode** | No feedback on how many emails were processed |
| **Mitigation** | Use `try/finally` around the main loop: `finally: print(get_log_summary())` |

---

## Summary Table

| ID | Module | Severity | Category |
|----|--------|----------|----------|
| EC-0.1 | Config | Critical | Missing file |
| EC-0.2 | Config | Critical | Silent wrong value |
| EC-0.3 | Config | High | Connectivity |
| EC-0.4 | Config | High | Auth failure |
| EC-0.5 | Config | Medium | Degraded mode |
| EC-1.1 | Input | Medium | Empty data |
| EC-1.2 | Input | Critical | Parse error |
| EC-1.3 | Input | Critical | Missing required field |
| EC-1.4 | Input | High | Invalid email |
| EC-1.5 | Input | High | Duplicate recipient |
| EC-1.6 | Input | High | Schema mismatch |
| EC-1.7 | Input | Medium | Whitespace-only field |
| EC-1.8 | Input | Medium | Field too long |
| EC-1.9 | Input | Medium | Special characters |
| EC-2.1 | Generator | High | Word limit exceeded |
| EC-2.2 | Generator | Medium | Optional field missing |
| EC-2.3 | Generator | Medium | Optional field missing |
| EC-2.4 | Generator | Critical | LLM empty response |
| EC-2.5 | Generator | Critical | Fabricated claim |
| EC-2.6 | Generator | High | API rate limit |
| EC-2.7 | Generator | High | API timeout |
| EC-2.8 | Generator | Medium | Empty subject |
| EC-3.1 | Preview | Medium | Unexpected input |
| EC-3.2 | Preview | Medium | Interrupt handling |
| EC-3.3 | Preview | Medium | EOF on stdin |
| EC-3.4 | Preview | Low | Terminal compatibility |
| EC-4.1 | Sender | Critical | Connection refused |
| EC-4.2 | Sender | Critical | SMTP rejection |
| EC-4.3 | Sender | High | Bad recipient |
| EC-4.4 | Sender | High | Daily limit |
| EC-4.5 | Sender | High | Offline |
| EC-4.6 | Sender | High | OAuth expiry |
| EC-4.7 | Sender | Medium | Empty draft |
| EC-4.8 | Sender | Critical | Send cap exceeded |
| EC-5.1 | Logger | Medium | File locked |
| EC-5.2 | Logger | Medium | Disk full |
| EC-5.3 | Logger | Medium | Header duplication |
| EC-5.4 | Logger | Medium | Unicode encoding |
| EC-5.5 | Logger | Low | Unknown status |
| EC-6.1 | System | Critical | Python version |
| EC-6.2 | System | Critical | Missing dependency |
| EC-6.3 | System | Medium | Concurrency |
| EC-6.4 | System | Medium | File encoding |
| EC-6.5 | System | Medium | Line endings |
| EC-6.6 | System | Critical | Ethics / opt-out |
| EC-6.7 | System | Low | UX / summary |

---

> [!IMPORTANT]
> All Critical edge cases must be handled before enabling `DRY_RUN=false`. They represent paths that can cause data loss, real emails to the wrong recipients, or total loop crashes.

> [!TIP]
> Use this document alongside `eval.md` — each phase evaluation maps directly to the edge-case IDs that should be resolved by the end of that phase.
