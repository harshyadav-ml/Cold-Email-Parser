# 🔬 The Closer — Spam Diagnosis Report

> **Deep technical audit of why your Gmail API-sent emails are landing in Spam**

---

## Executive Summary

Your MIME construction in [`gmail.py`](file:///Users/harsh/Desktop/Project/Cold%20Email%20Parser/src/closer/delivery/gmail.py) is actually **well-written** — the header construction itself is not the primary culprit. The spam problem is caused by a **combination of factors across 3 layers**: code-level issues, content/template patterns, and external configuration gaps. Below is the prioritized diagnosis.

---

## PART 1: Code-Level & Header Audit

### ✅ What Your Code Gets Right

| Area | Verdict |
|---|---|
| `EmailMessage(policy=policy.SMTP)` | ✅ Correct — uses standards-compliant SMTP policy |
| `From` with `formataddr()` | ✅ Correct — proper RFC 2822 display name encoding |
| `Date` with `format_datetime(utc)` | ✅ Correct — UTC timestamp, RFC-compliant |
| `Message-ID` with `make_msgid(domain=...)` | ✅ Correct — domain-anchored Message-ID |
| `set_content(body, subtype="plain", charset="utf-8")` | ✅ Correct — clean plain-text MIME |
| `base64.urlsafe_b64encode` on `msg.as_bytes()` | ✅ Correct — exactly what Gmail API expects |

### 🔴 CRITICAL: Missing `Reply-To` Header

**File:** [`gmail.py:32-48`](file:///Users/harsh/Desktop/Project/Cold%20Email%20Parser/src/closer/delivery/gmail.py#L32-L48)

Your message has no `Reply-To` header. When Gmail's spam filter processes an API-sent message, the absence of `Reply-To` combined with an OAuth app sending on behalf of a user can look like a programmatic mailer with no intention of receiving replies — a strong spam signal.

```diff
 msg["Date"] = format_datetime(datetime.now(timezone.utc))
 sender_domain = sender_email.rpartition("@")[2] or None
 msg["Message-ID"] = make_msgid(domain=sender_domain)
+msg["Reply-To"] = sender_email
 msg.set_content(body, subtype="plain", charset="utf-8")
```

### 🔴 CRITICAL: Missing `List-Unsubscribe` Header

Since June 2024, Gmail **requires** bulk senders (and strongly penalizes any sender without it) to include a one-click unsubscribe mechanism. Even for low-volume cold outreach, the absence of this header is a significant negative signal.

```diff
 msg["Reply-To"] = sender_email
+msg["List-Unsubscribe"] = f"<mailto:{sender_email}?subject=unsubscribe>"
+msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
 msg.set_content(body, subtype="plain", charset="utf-8")
```

### 🟡 WARNING: `From` Header / OAuth Token Mismatch Risk

**File:** [`gmail.py:35-40`](file:///Users/harsh/Desktop/Project/Cold%20Email%20Parser/src/closer/delivery/gmail.py#L35-L40)

Your `From` header is set from `settings.SMTP_USER`. But you're authenticating via OAuth with a token in `token.json`. If `SMTP_USER` in `.env` doesn't **exactly match** the Gmail account that authorized the OAuth token, Gmail will either:
1. Silently rewrite the `From` header (causing an SPF/DKIM mismatch downstream), or
2. Treat the mismatch as a spoofing attempt → **instant spam**.

**File:** [`token.json`](file:///Users/harsh/Desktop/Project/Cold%20Email%20Parser/token.json)

Your token has `"account": ""` — the `account` field is empty, which means the token doesn't self-document which Gmail address authorized it. This makes misconfiguration easy to miss.

> [!CAUTION]
> **Verification step:** The email address that completed the OAuth consent screen (the one shown in the browser during `flow.run_local_server()`) **must be identical** to `SMTP_USER` in your `.env`. If it's a `@gmail.com` account, it must match exactly. If it's a Google Workspace account, same rule applies.

### 🟡 WARNING: No `X-Mailer` or User-Agent Header

Legitimate email clients include identification headers. Their absence makes the message look like it was sent by a script (which it is, but you don't want spam filters to think that).

```diff
+msg["X-Mailer"] = "The Closer v1.0"
 msg.set_content(body, subtype="plain", charset="utf-8")
```

### 🟡 WARNING: SMTP Fallback Creates Inconsistent Authentication Path

**File:** [`gmail.py:291-292`](file:///Users/harsh/Desktop/Project/Cold%20Email%20Parser/src/closer/delivery/gmail.py#L291-L292)

When Gmail API is unavailable, you fall back to SMTP (`smtp_send_email`). On Render, SMTP port 587 is blocked, so this fallback silently fails. But the bigger problem: if SMTP ever does work (e.g., locally), it sends with a completely different authentication identity (App Password vs OAuth), producing different DKIM signatures and potentially different `From` alignment. This confuses receiving mail servers that track sender reputation per authentication method.

---

## PART 2: Email Content & Template Analysis

### 🔴 HIGH IMPACT: Repetitive Template Fingerprint

**File:** [`template.py`](file:///Users/harsh/Desktop/Project/Cold%20Email%20Parser/src/closer/generation/template.py)

All 5 variants across all 4 modes share nearly identical structural fingerprints:

```
Hi {name},\n\n{opener} {company} is {verb} for the {role} position.\n\n...
\n\n{cta}\n\nBest,\n{candidate}\n{portfolio_url}
```

Gmail's spam filters use **structural hashing** — if multiple recipients at the same domain (or across domains using Google's spam network) report or ignore emails with identical structural patterns, the template itself gets fingerprinted. Even your word-pool shuffling (`_OPENERS`, `_CTA_PHRASES`) doesn't change the **structure**, only individual phrases.

> [!IMPORTANT]
> **The fix:** Vary paragraph count, sentence order, CTA position, and sign-off style — not just word choice. The LLM path via Groq already does this naturally, which is why LLM-generated emails typically have better deliverability.

### 🔴 HIGH IMPACT: Portfolio URL on Every Email

**File:** [`template.py:96`](file:///Users/harsh/Desktop/Project/Cold%20Email%20Parser/src/closer/generation/template.py#L96)

```python
port_line = f"\n{portfolio}" if portfolio else ""
```

Every single email ends with a bare URL (`https://github.com/harshyadav-ml`). Bare URLs (not hyperlinked, just pasted as text) in cold emails are a **major spam trigger** for several reasons:
1. **Link-to-text ratio** — a short email with a URL has a high link density
2. **GitHub links** from unknown senders often get flagged (phishing vectors)
3. **Every email has the same URL** — pattern detection

**Recommendation:** Remove the portfolio URL from the initial cold email. Offer to share it in the CTA instead:

```
"Would you be open to a brief 5-minute chat? I'd be happy to share my recent project work."
```

### 🟡 WARNING: Subject Line Patterns

Your subject lines follow very predictable patterns:
- `"Quick note on the {role} role at {company}"`
- `"{candidate} <> {company}: {role}"`
- `"{role} inquiry — {company}"`

The word "Quick" in subject lines is a known minor spam signal. More importantly, the formulaic pattern `{role} at {company}` repeated across many outbound emails from the same sender gets fingerprinted.

### 🟡 WARNING: LLM System Prompt Leakage Risk

**File:** [`llm.py:186-190`](file:///Users/harsh/Desktop/Project/Cold%20Email%20Parser/src/closer/generation/llm.py#L186-L190)

Your system prompt says `"You are an elite cold outreach copywriter"`. If the LLM ever leaks prompt artifacts into the email body (rare but possible with some models), this phrase would be catastrophic for deliverability.

---

## PART 3: External Deliverability Factors (Prioritized Checklist)

### Priority 1: DNS Authentication Records (SPF / DKIM / DMARC)

This is the **#1 most likely cause** of your spam problem if you haven't configured these.

#### What's happening under the hood

When you send via the Gmail API using OAuth:
- Gmail signs the message with **Google's DKIM keys** (selector: `20230601` or similar under `._domainkey.gmail.com`)
- The SPF check evaluates against Google's IP ranges
- If you're sending from a `@gmail.com` address, Google handles all of this automatically — **SPF, DKIM, and DMARC should all pass**

**BUT**: If you're sending from a **custom domain** via Google Workspace, you must configure DNS records yourself.

#### Verification Steps

Run these commands in your terminal to check your current DNS setup:

```bash
# Replace yourdomain.com with your actual sending domain

# 1. Check SPF record
dig TXT yourdomain.com +short | grep spf

# Expected output should contain: "v=spf1 include:_spf.google.com ~all"

# 2. Check DKIM record (Google Workspace)
dig TXT google._domainkey.yourdomain.com +short

# Expected: a long DKIM public key string

# 3. Check DMARC record
dig TXT _dmarc.yourdomain.com +short

# Expected: "v=DMARC1; p=none; rua=mailto:dmarc-reports@yourdomain.com"
```

#### If Sending from `@gmail.com`

If `SMTP_USER` is a `@gmail.com` address:
- SPF, DKIM are managed by Google automatically ✅
- DMARC is published by Google at `_dmarc.gmail.com` ✅
- **You cannot modify these records** — they should just work
- **The spam problem is NOT DNS** — focus on content & reputation (Priorities 2-4)

#### If Sending from a Custom Domain (Google Workspace)

You **must** add these DNS records:

| Record Type | Host | Value |
|---|---|---|
| TXT | `@` | `v=spf1 include:_spf.google.com ~all` |
| TXT | `google._domainkey` | *(Get from Google Workspace Admin → Gmail → Authenticate Email)* |
| TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:you@yourdomain.com` |

### Priority 2: OAuth Token ↔ From Header Alignment

**This is the single most likely code-level cause of your spam issue.**

```
token.json authenticated as:  ???  (account field is empty)
.env SMTP_USER:               ???  (whatever you set)
Email From header:            settings.SMTP_USER
```

All three **must** be the same email address. To verify which account your token belongs to:

```bash
# Quick verification script — run locally
python3 -c "
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
creds = Credentials.from_authorized_user_file('token.json')
service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
profile = service.users().getProfile(userId='me').execute()
print(f'Token authenticated as: {profile[\"emailAddress\"]}')
"
```

Compare the output with your `SMTP_USER` in `.env`. **They must match exactly.**

### Priority 3: Sender Reputation & Warm-Up

If this is a **new Gmail account** or a **new custom domain**, you have **zero sending reputation**. Sending cold outreach from a zero-reputation account is the fastest way to get spam-binned.

#### Warm-Up Protocol (2-4 weeks)

| Week | Daily Volume | Target |
|---|---|---|
| Week 1 | 2-3 emails/day | Send to friends/colleagues who will **open and reply** |
| Week 2 | 5-8 emails/day | Continue with known contacts, mix in 1-2 cold leads |
| Week 3 | 10-15 emails/day | 50/50 warm + cold leads |
| Week 4 | 15-25 emails/day | Mostly cold leads, monitor bounce rate |

> [!WARNING]
> **Never exceed 50 emails/day** from a single Gmail/Workspace account for cold outreach. Your `MAX_SENDS_PER_SESSION=50` setting is fine, but that should be the **daily** cap, not per-session.

#### Critical Warm-Up Actions
1. **Get replies** — Ask friends to reply to your emails. Gmail weighs reply rate heavily.
2. **Avoid bounces** — Verify recipient emails before sending. Hard bounces destroy reputation.
3. **Stagger sends** — Don't send 20 emails in 5 seconds. Add delays between sends.

### Priority 4: Google OAuth App "Testing" Status

**File:** [`credentials.json`](file:///Users/harsh/Desktop/Project/Cold%20Email%20Parser/credentials.json)

Your OAuth app (`project_id: "the-close-parser"`) is likely in **"Testing" publishing status** in Google Cloud Console. Apps in testing mode:
- Have token expiry after 7 days (your token shows `"expiry": "2026-10-20T09:54:11Z"` — already expired)
- Are limited to 100 test users
- May have their sent emails flagged with lower trust

**Fix:** Go to [Google Cloud Console → APIs & Services → OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent) and publish the app (or at minimum, verify it).

### Priority 5: Add Send Throttling / Delays

Your code sends emails instantly with no delay between sends. Sending multiple emails in rapid succession from the same account is a classic bot behavior pattern.

---

## PART 4: Exact Code Modifications

### Patch 1: Fix `_build_raw_message()` in `gmail.py`

**File:** [`src/closer/delivery/gmail.py`](file:///Users/harsh/Desktop/Project/Cold%20Email%20Parser/src/closer/delivery/gmail.py#L32-L48)

```diff
 def _build_raw_message(to: str, subject: str, body: str) -> str:
     """Build URL-safe base64-encoded MIME string for Gmail API."""
     msg = EmailMessage(policy=policy.SMTP)
     sender_name = (settings.SENDER_NAME or "").strip()
     sender_email = (settings.SMTP_USER or "").strip()
     if sender_name and sender_email:
         msg["From"] = formataddr((sender_name, sender_email))
     elif sender_email:
         msg["From"] = sender_email
 
     msg["To"] = to
     msg["Subject"] = subject
     msg["Date"] = format_datetime(datetime.now(timezone.utc))
     sender_domain = sender_email.rpartition("@")[2] or None
     msg["Message-ID"] = make_msgid(domain=sender_domain)
+    msg["Reply-To"] = sender_email
+    msg["List-Unsubscribe"] = f"<mailto:{sender_email}?subject=unsubscribe>"
+    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
+    msg["X-Mailer"] = "The Closer v1.0"
     msg.set_content(body, subtype="plain", charset="utf-8")
     return base64.urlsafe_b64encode(msg.as_bytes(policy=policy.SMTP)).decode("ascii")
```

### Patch 2: Fix `_build_message()` in `smtp.py`

**File:** [`src/closer/delivery/smtp.py`](file:///Users/harsh/Desktop/Project/Cold%20Email%20Parser/src/closer/delivery/smtp.py#L51-L66)

Apply the same header additions for consistency:

```diff
 def _build_message(to: str, subject: str, body: str) -> EmailMessage:
     """Construct a MIME message ready for SMTP transmission."""
     msg = EmailMessage(policy=policy.SMTP)
     sender_name = (settings.SENDER_NAME or "").strip()
     smtp_user = (settings.SMTP_USER or "").strip()
     if sender_name:
         msg["From"] = formataddr((sender_name, smtp_user))
     else:
         msg["From"] = smtp_user
     msg["To"] = to
     msg["Subject"] = subject
     msg["Date"] = format_datetime(datetime.now(timezone.utc))
     sender_domain = smtp_user.rpartition("@")[2] or None
     msg["Message-ID"] = make_msgid(domain=sender_domain)
+    msg["Reply-To"] = smtp_user
+    msg["List-Unsubscribe"] = f"<mailto:{smtp_user}?subject=unsubscribe>"
+    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
+    msg["X-Mailer"] = "The Closer v1.0"
     msg.set_content(body, subtype="plain", charset="utf-8")
     return msg
```

### Patch 3: Add Send Throttling in `send_gmail_message()`

**File:** [`src/closer/delivery/gmail.py`](file:///Users/harsh/Desktop/Project/Cold%20Email%20Parser/src/closer/delivery/gmail.py#L263-L308)

```diff
+import time
+import random
+
 def send_gmail_message(
     to: str,
     subject: str,
     body: str,
     service: Optional[Any] = None,
 ) -> dict:
+    # Throttle: random delay between 3-8 seconds to avoid burst detection
+    delay = random.uniform(3.0, 8.0)
+    time.sleep(delay)
+
     if not body or not body.strip():
```

### Patch 4: Add Token-Identity Verification Guard

Add a startup check that verifies the OAuth token matches `SMTP_USER`:

**File:** [`src/closer/delivery/gmail.py`](file:///Users/harsh/Desktop/Project/Cold%20Email%20Parser/src/closer/delivery/gmail.py) — add after `get_gmail_service()`:

```python
def verify_sender_alignment(service=None) -> bool:
    """Verify that the OAuth token's email matches SMTP_USER (From header).
    
    Misalignment causes Gmail to rewrite headers or flag as spoofing.
    """
    srv = service or get_gmail_service()
    if not srv:
        return False
    try:
        profile = srv.users().getProfile(userId="me").execute()
        token_email = profile.get("emailAddress", "").strip().lower()
        configured_email = (settings.SMTP_USER or "").strip().lower()
        if token_email != configured_email:
            print(
                f"  [CRITICAL] Sender mismatch detected!\n"
                f"    OAuth token authenticated as: {token_email}\n"
                f"    SMTP_USER (From header):      {configured_email}\n"
                f"    This WILL cause spam filtering. Update SMTP_USER in .env to match."
            )
            return False
        print(f"  [OK] Sender alignment verified: {token_email}")
        return True
    except Exception as exc:
        print(f"  [WARNING] Could not verify sender alignment: {exc}")
        return False
```

---

## PART 5: Action Priority Matrix

| Priority | Fix | Impact | Effort |
|---|---|---|---|
| 🔴 **P0** | Verify OAuth token email = `SMTP_USER` (Part 3, Priority 2) | **Highest** — misalignment = instant spam | 5 min |
| 🔴 **P0** | Add `Reply-To` + `List-Unsubscribe` headers (Patch 1 & 2) | **High** — Gmail requirement since June 2024 | 5 min |
| 🔴 **P0** | Check DNS records if using custom domain (Part 3, Priority 1) | **Highest** — no SPF/DKIM = spam | 15 min |
| 🟡 **P1** | Remove bare portfolio URL from templates (Part 2) | **High** — link density trigger | 15 min |
| 🟡 **P1** | Warm up sending account (Part 3, Priority 3) | **High** — zero reputation = spam | 2-4 weeks |
| 🟡 **P1** | Add send throttling / delays (Patch 3) | **Medium** — burst detection trigger | 5 min |
| 🟡 **P2** | Publish OAuth app from "Testing" status (Part 3, Priority 4) | **Medium** — lower trust score | 10 min |
| 🟢 **P2** | Vary template structure, not just word choice (Part 2) | **Medium** — template fingerprinting | 1-2 hrs |
| 🟢 **P3** | Add `X-Mailer` header (Patch 1 & 2) | **Low** — minor trust signal | 2 min |
| 🟢 **P3** | Add sender alignment verification guard (Patch 4) | **Low** — defensive, prevents future issues | 10 min |

---

## Quick Diagnostic Commands

Run these right now to diagnose the most likely cause:

```bash
# 1. Verify which Gmail account your OAuth token belongs to
cd "/Users/harsh/Desktop/Project/Cold Email Parser"
python3 -c "
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
creds = Credentials.from_authorized_user_file('token.json')
if creds.expired:
    from google.auth.transport.requests import Request
    creds.refresh(Request())
service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
profile = service.users().getProfile(userId='me').execute()
print(f'OAuth token email: {profile[\"emailAddress\"]}')
"

# 2. Check what SMTP_USER is set to
grep SMTP_USER .env

# 3. If using custom domain, check DNS
# dig TXT yourdomain.com +short
# dig TXT _dmarc.yourdomain.com +short
```

> [!TIP]
> **Start with P0 fixes first.** If the OAuth token email doesn't match `SMTP_USER`, fixing that single issue alone may solve the spam problem entirely.
