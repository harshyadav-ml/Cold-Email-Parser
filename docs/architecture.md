# Architecture: "The Closer" — Cold Email Writer + Send Bot

> Sprint 3 · Agent Meets Gmail

---

## 1. High-Level System Overview

```mermaid
flowchart TD
    A["📋 Input Layer\ncontacts.json / jobs.csv / hardcoded list"]
    B["🧠 Email Generator\nemail_generator.py"]
    C["👁️ Preview & Review\nTerminal / Streamlit UI"]
    D{User Decision}
    E["📤 Email Sender\nemail_sender.py"]
    F["📝 Logger\nlogger.py"]
    G["📬 Gmail / SMTP\nDraft or Sent Folder"]
    H["🗂️ outreach_log.csv"]

    A --> B
    B --> C
    C --> D
    D -- "send" --> E
    D -- "skip" --> F
    D -- "draft" --> E
    E --> G
    E --> F
    F --> H
```

---

## 2. Layered Architecture

```mermaid
graph TB
    subgraph UI["UI Layer (Optional Stretch)"]
        ST["Streamlit Frontend"]
    end

    subgraph CLI["CLI / Terminal Layer (MVP)"]
        MAIN["main.py\nOrchestrator"]
    end

    subgraph CORE["Core Business Logic Layer"]
        GEN["email_generator.py\nTemplate Engine / LLM Rewriter"]
        PREV["Preview Module\n(inline in main.py)"]
        SEND["email_sender.py\nSMTP / Gmail API / MCP"]
        LOG["logger.py\nCSV Append Writer"]
    end

    subgraph DATA["Data Layer"]
        CONTACTS["contacts.json\njobs.csv\nHardcoded List"]
        ENV[".env\nCredentials & Config"]
        LOGFILE["outreach_log.csv"]
        OPTOUT["optout_list.txt\n(future)"]
    end

    subgraph EXTERNAL["External Services"]
        GMAIL["Gmail / SMTP\n(smtp.gmail.com:587)"]
        LLM["Groq API\n(optional)"]
        SENDGRID["SendGrid / Resend\n(optional)"]
    end

    ST --> MAIN
    MAIN --> GEN
    MAIN --> PREV
    MAIN --> SEND
    MAIN --> LOG

    GEN --> LLM
    SEND --> GMAIL
    SEND --> SENDGRID
    LOG --> LOGFILE
    CONTACTS --> MAIN
    ENV --> MAIN
    ENV --> SEND
```

---

## 3. Component Breakdown

### 3.1 `main.py` — Orchestrator

The central controller that wires all components together.

**Responsibilities:**
- Load outreach targets from the configured input source
- Iterate over each contact record
- Call `email_generator.generate_email(contact)` for each record
- Display email preview in terminal
- Prompt user for: `send / draft / skip`
- Dispatch to `email_sender.send()` or `email_sender.draft()`
- Pass result to `logger.log_entry()`

**State machine per contact:**

```mermaid
stateDiagram-v2
    [*] --> Load
    Load --> Generate
    Generate --> Preview
    Preview --> AwaitDecision
    AwaitDecision --> Send : user types "send"
    AwaitDecision --> Draft : user types "draft"
    AwaitDecision --> Skip : user types "skip"
    Send --> LogSent
    Draft --> LogDrafted
    Skip --> LogSkipped
    LogSent --> [*]
    LogDrafted --> [*]
    LogSkipped --> [*]
```

---

### 3.2 `email_generator.py` — Email Generation Engine

Accepts a single contact record dict and returns a `(subject, body)` tuple.

**Two-tier generation strategy:**

```mermaid
flowchart LR
    A["Contact Record Dict"] --> B{LLM_ENABLED?}
    B -- "No (MVP)" --> C["Python f-string Template"]
    B -- "Yes (Advanced)" --> D["LLM Prompt Builder"]
    D --> E["Groq API"]
    E --> F["Parse & Validate Response"]
    C --> G["(subject, body) Tuple"]
    F --> G
```

**Email structure enforced (≤150 words):**

| # | Section | Source Field |
|---|---------|-------------|
| 1 | Subject Line | `role`, `company` |
| 2 | Personalization Hook | `personalization_note` |
| 3 | Intro | `candidate_name`, `candidate_background` |
| 4 | Value/Fit Statement | `role`, `candidate_background` |
| 5 | Clear Ask | hardcoded CTA |
| 6 | Sign-off | `candidate_name`, `portfolio_url` |

**Key functions:**
```python
def generate_email(contact: dict) -> tuple[str, str]:
    """Returns (subject, body)"""

def build_prompt(contact: dict) -> str:
    """Builds LLM prompt with personalization constraints"""

def validate_email(body: str) -> bool:
    """Checks word count, presence of CTA, no fake claims"""
```

---

### 3.3 `email_sender.py` — Delivery Engine

Abstracts the actual sending mechanism behind a unified interface.

**Sending modes:**

```mermaid
flowchart TD
    A["send_or_draft(contact, subject, body, mode)"]
    A --> B{DRY_RUN?}
    B -- "True" --> C["🖨️ Print Only\nNo real email sent"]
    B -- "False" --> D{SEND_METHOD}
    D -- "smtp" --> E["smtplib.SMTP\nGmail App Password"]
    D -- "gmail_api" --> F["Google Gmail API\ngmail.compose / gmail.drafts"]
    D -- "sendgrid" --> G["SendGrid API\nsendgrid-python"]
    D -- "resend" --> H["Resend API\nresend-python"]
    E --> I["Return status: sent/drafted/failed"]
    F --> I
    G --> I
    H --> I
    C --> I
```

**Key functions:**
```python
def send_email(to: str, subject: str, body: str) -> dict:
    """Sends via configured provider. Returns status dict."""

def create_draft(to: str, subject: str, body: str) -> dict:
    """Creates Gmail draft. Returns draft ID."""

def get_smtp_connection() -> smtplib.SMTP:
    """Establishes authenticated SMTP session."""
```

**SMTP auth flow:**
```mermaid
sequenceDiagram
    participant App
    participant Gmail as smtp.gmail.com:587
    App->>Gmail: EHLO
    Gmail-->>App: 250 capabilities
    App->>Gmail: STARTTLS
    Gmail-->>App: 220 Go ahead
    App->>Gmail: AUTH LOGIN (user + app_password)
    Gmail-->>App: 235 Authentication successful
    App->>Gmail: MAIL FROM / RCPT TO / DATA
    Gmail-->>App: 250 OK / 221 Bye
```

---

### 3.4 `logger.py` — Audit Trail

Appends a row to `outreach_log.csv` after every action.

**Log schema:**

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | ISO 8601 | When the action occurred |
| `recipient_email` | string | Target email address |
| `company` | string | Target company |
| `role` | string | Job role title |
| `subject` | string | Generated subject line |
| `status` | enum | `generated` / `drafted` / `sent` / `skipped` / `failed` |
| `error_message` | string | Error detail if failed, else empty |
| `word_count` | int | Word count of generated email body |

**Key functions:**
```python
def log_entry(contact: dict, subject: str, status: str, error: str = "") -> None:
    """Appends one row to outreach_log.csv"""

def get_log_summary() -> dict:
    """Returns counts by status for session summary"""
```

---

## 4. Data Flow — End-to-End

```mermaid
sequenceDiagram
    participant User
    participant Main as main.py
    participant Gen as email_generator.py
    participant LLM as Groq API (optional)
    participant Prev as Preview (terminal)
    participant Send as email_sender.py
    participant Gmail as Gmail/SMTP
    participant Log as logger.py
    participant CSV as outreach_log.csv

    User->>Main: python main.py
    Main->>Main: Load contacts.json
    loop For each contact
        Main->>Gen: generate_email(contact)
        alt LLM enabled
            Gen->>LLM: Prompt with contact fields
            LLM-->>Gen: Raw email text
            Gen->>Gen: Parse & validate
        else Template mode
            Gen->>Gen: f-string render
        end
        Gen-->>Main: (subject, body)
        Main->>Prev: Print preview
        Prev-->>User: Display subject + body
        User->>Main: "send" / "draft" / "skip"
        alt send or draft
            Main->>Send: send_email() or create_draft()
            Send->>Gmail: SMTP DATA or API call
            Gmail-->>Send: 250 OK / Draft ID
            Send-->>Main: {status: "sent"/"drafted"}
        else skip
            Main->>Main: status = "skipped"
        end
        Main->>Log: log_entry(contact, subject, status)
        Log->>CSV: Append row
    end
    Main->>User: Session summary
```

---

## 5. Input Schema

```mermaid
classDiagram
    class ContactRecord {
        +string recipient_email*
        +string company*
        +string role*
        +string candidate_name*
        +string candidate_background*
        +string recipient_name
        +string job_url
        +string portfolio_url
        +string personalization_note
        +string linkedin_url
        +string resume_link
    }
    note for ContactRecord "* = Required field"
```

---

## 6. Output Schema

```mermaid
classDiagram
    class GeneratedEmail {
        +string subject
        +string body
        +int word_count
        +bool passes_validation
    }

    class SendResult {
        +string status
        +string message_id
        +string draft_id
        +string error_message
        +datetime timestamp
    }

    class LogEntry {
        +datetime timestamp
        +string recipient_email
        +string company
        +string role
        +string subject
        +string status
        +string error_message
        +int word_count
    }

    GeneratedEmail --> SendResult : triggers
    SendResult --> LogEntry : recorded as
```

---

## 7. Configuration & Environment Variables

```mermaid
graph LR
    ENV[".env file"] --> A["SMTP_HOST\nsmtp.gmail.com"]
    ENV --> B["SMTP_PORT\n587"]
    ENV --> C["SMTP_USER\nyour@gmail.com"]
    ENV --> D["SMTP_PASSWORD\nApp Password"]
    ENV --> E["SENDER_NAME\nYour Name"]
    ENV --> F["DRY_RUN\ntrue/false"]
    ENV --> G["SEND_METHOD\nsmtp/gmail_api/sendgrid"]
    ENV --> H["LLM_ENABLED\ntrue/false"]
    ENV --> I["GROQ_API_KEY\n(if LLM enabled)"]
```

> [!CAUTION]
> Never commit `.env` to version control. The `.env.example` template (without secrets) should be committed instead. Gmail requires App Passwords (not your account password) when using SMTP with 2FA enabled.

---

## 8. Safety & Ethics Guardrails (Architecture-Level)

```mermaid
flowchart TD
    A["Outreach Target List"] --> B{"Opt-Out Check\n(future)"}
    B -- "On list" --> C["Skip — Log as 'opted_out'"]
    B -- "Not on list" --> D["Generate Email"]
    D --> E{"Validation Gate"}
    E -- "Fails (>150 words\nor fake claims)" --> F["Regenerate or Reject"]
    E -- "Passes" --> G["Human Preview"]
    G --> H{"User Confirms?"}
    H -- "No" --> I["Skip — Log as 'skipped'"]
    H -- "Yes" --> J{"DRY_RUN?"}
    J -- "true" --> K["Print Only — No Send"]
    J -- "false" --> L["Send/Draft\n(max 5 per session)"]
```

---

## 9. Folder Structure (Detailed)

```text
the-closer/
│
├── main.py                  # Orchestrator — load, loop, confirm, dispatch
├── email_generator.py       # Template + LLM email generation
├── email_sender.py          # SMTP / Gmail API / SendGrid abstraction
├── logger.py                # CSV audit log writer
│
├── contacts.json            # Input: list of outreach target records
├── jobs.csv                 # Alt input: CSV format contacts
│
├── outreach_log.csv         # Output: per-attempt audit log (auto-created)
│
├── .env                     # Secret credentials (NOT committed)
├── .env.example             # Template for .env (committed)
├── .gitignore               # Excludes .env, __pycache__, etc.
│
├── requirements.txt         # pip dependencies
└── README.md                # Setup + usage instructions
```

---

## 10. Dependency Map

```mermaid
graph LR
    main --> email_generator
    main --> email_sender
    main --> logger
    email_generator --> groq["groq (optional)"]
    email_sender --> smtplib["smtplib (stdlib)"]
    email_sender --> google["google-auth\ngoogle-api-python-client (optional)"]
    email_sender --> sendgrid["sendgrid (optional)"]
    email_sender --> resend["resend (optional)"]
    logger --> csv["csv (stdlib)"]
    main --> dotenv["python-dotenv"]
    main --> json["json (stdlib)"]
```

**`requirements.txt` (minimal MVP):**
```
python-dotenv
```

**`requirements.txt` (full optional stack):**
```
python-dotenv
groq
google-auth
google-auth-oauthlib
google-api-python-client
sendgrid
resend
streamlit
```

---

## 11. MVP vs. Stretch Goal Feature Matrix

| Feature | MVP | Stretch |
|---------|-----|---------|
| Hardcoded contact list | ✅ | — |
| `contacts.json` input | ✅ | — |
| `jobs.csv` input | — | ✅ |
| Python f-string template | ✅ | — |
| LLM-powered rewriting | — | ✅ |
| Email word count validation | ✅ | — |
| Terminal preview + confirm | ✅ | — |
| Streamlit UI | — | ✅ |
| SMTP sending | ✅ | — |
| Gmail Draft creation | — | ✅ |
| Gmail API sending | — | ✅ |
| SendGrid / Resend | — | ✅ |
| `DRY_RUN` mode | ✅ | — |
| CSV audit logging | ✅ | — |
| Opt-out list | — | ✅ |
| Follow-up generator | — | ✅ |
| Email quality scorer | — | ✅ |
| Spam-risk checker | — | ✅ |
| Deduplication | — | ✅ |

---

## 12. Sprint Build Sequence (Teachable Steps)

```mermaid
gantt
    title Sprint 3 Build Sequence
    dateFormat  X
    axisFormat Step %s

    section Foundation
    Sample contacts data        :done, s1, 0, 1
    email_generator.py template :done, s2, 1, 2

    section Core Loop
    Preview in terminal         :active, s3, 2, 3
    Confirm prompt (yes/no)     :s4, 3, 4

    section Delivery
    SMTP send (DRY_RUN=true)    :s5, 4, 5
    CSV logger                  :s6, 5, 6

    section Validation
    Turn off DRY_RUN, test send :s7, 6, 7
    Show proof in Gmail         :s8, 7, 8
```

---

> [!NOTE]
> This architecture is intentionally layered so that each module can be built, tested, and explained independently in a live Cursor session. The `DRY_RUN` flag makes it safe to demo the full pipeline without sending real emails until the final step.
