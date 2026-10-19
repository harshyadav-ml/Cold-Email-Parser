"""src.closer.api — FastAPI server connecting Python backend to Next.js frontend.

Exposes REST endpoints for:
- System status & telemetry
- Loading contacts & opt-out verification
- Generating & regenerating personalized emails (Template / Groq LLM)
- Review dispatch actions (Approve & Dispatch, Save Dry Run, Skip Lead)
- Audit log streaming & CSV exports
"""
from __future__ import annotations

import csv
import io
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# Ensure environment variables are loaded immediately
load_dotenv()

import uvicorn
from fastapi import FastAPI, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.closer.config import settings

# If GROQ_API_KEY is present in environment, enable LLM
if os.getenv("GROQ_API_KEY"):
    settings.LLM_ENABLED = True
from src.closer.input.loader import (
    DEFAULT_CONTACTS_PATH,
    SAMPLE_TEMPLATE_RECORDS,
    load_contacts,
    load_optout_list,
    parse_contacts_buffer,
    save_contacts,
    validate_contact_record,
)
from src.closer.generation import (
    check_spam_risk,
    generate_email,
    generate_followup,
    score_email,
    validate_email,
)
from src.closer.generation.llm import generate_with_llm
from src.closer.delivery import create_draft, send_email
from src.closer.audit.logger import (
    FIELDNAMES,
    LOG_FILE,
    get_log_summary,
    log_entry,
)

active_source_file: str = "data/contacts.json"

sender_profile: Dict[str, str] = {
    "candidate_name": "Harsh Yadav",
    "candidate_title": "AI Engineer",
    "candidate_background": "AI Engineer specializing in agentic workflows, FastAPI, Next.js, and production LLM pipelines",
    "portfolio_url": "https://github.com/harshyadav-ml",
}

app = FastAPI(
    title="The Closer API",
    description="Backend API for The Closer — Cold Email Review & Dispatch Engine",
    version="1.0.0",
)


# Enable CORS for Next.js frontend (env-driven with Vercel and localhost support)
_allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
_allowed_origins = [o.strip() for o in _allowed_origins if o.strip()]

if not _allowed_origins:
    _allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

_vercel_url = os.getenv("VERCEL_URL")
_vercel_project_url = os.getenv("VERCEL_PROJECT_PRODUCTION_URL")
if _vercel_url:
    _allowed_origins.append(f"https://{_vercel_url}")
if _vercel_project_url:
    _allowed_origins.append(f"https://{_vercel_project_url}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)


# ── Pydantic Request / Response Models ────────────────────────────────

class ProfilePayload(BaseModel):
    candidate_name: str = "Harsh Yadav"
    candidate_title: str = "AI Engineer"
    candidate_background: str = "AI Engineer specializing in agentic workflows, FastAPI, Next.js, and production LLM pipelines"
    portfolio_url: str = "https://github.com/harshyadav-ml"


class ContactPayload(BaseModel):
    recipient_name: Optional[str] = "Hiring Manager"
    recipient_email: str
    company: str
    role: str
    job_url: Optional[str] = None
    personalization_note: Optional[str] = None
    candidate_name: Optional[str] = "Harsh Yadav"
    candidate_background: Optional[str] = "AI Engineer with experience in agentic workflows"
    portfolio_url: Optional[str] = None


class DispatchRequest(BaseModel):
    contact: Dict[str, Any]
    subject: str
    body: str
    action: str  # "send" | "draft" | "skip"


class GenerateRequest(BaseModel):
    contact: Dict[str, Any]
    mode: Optional[str] = "standard"  # "standard" | "concise" | "technical" | "followup"
    previous_subject: Optional[str] = ""
    previous_body: Optional[str] = ""
    current_subject: Optional[str] = ""
    current_body: Optional[str] = ""
    regen_count: Optional[int] = None
    timestamp_seed: Optional[int] = None


# Backward-compatible alias for existing callers
RegenerateRequest = GenerateRequest


class ToggleDryRunRequest(BaseModel):
    dry_run: bool


# ── System Status & Telemetry ─────────────────────────────────────────

@app.get("/api/status")
def get_system_status() -> Dict[str, Any]:
    """Return live system telemetry, feature flags, and session summary."""
    summary = get_log_summary()
    total_processed = sum(summary.values())
    sent_count = summary.get("sent", 0)

    return {
        "engine": "THE CLOSER / OUTREACH ENGINE",
        "operator": f"{sender_profile['candidate_name']} • {sender_profile['candidate_title']}",
        "sender_profile": sender_profile,
        "contacts_source": active_source_file,
        "dry_run": settings.DRY_RUN,
        "send_method": settings.SEND_METHOD,
        "send_method_label": "Gmail API / SMTP",
        "llm_enabled": settings.LLM_ENABLED,
        "llm_model": "Groq LLaMA-3.3-70B",
        "session_limit": f"{sent_count} / {settings.MAX_SENDS_PER_SESSION} Live Sends",
        "max_sends": settings.MAX_SENDS_PER_SESSION,
        "summary": summary,
        "total_processed": total_processed,
    }


# ── Sender Profile & Resume Context ───────────────────────────────────

@app.get("/api/profile")
def get_sender_profile() -> Dict[str, Any]:
    """Return the active candidate/sender profile used across email generation."""
    return sender_profile


@app.post("/api/profile")
def update_sender_profile(payload: ProfilePayload) -> Dict[str, Any]:
    """Update sender profile and dynamically re-synthesize drafts for all contacts."""
    global sender_profile
    sender_profile["candidate_name"] = payload.candidate_name.strip() or "Harsh Yadav"
    sender_profile["candidate_title"] = payload.candidate_title.strip() or "AI Engineer"
    sender_profile["candidate_background"] = payload.candidate_background.strip() or "AI Engineer specializing in agentic workflows"
    sender_profile["portfolio_url"] = payload.portfolio_url.strip() or "https://github.com/harshyadav-ml"

    # Also update candidate defaults on active contacts in data/contacts.json
    try:
        contacts_list = load_contacts()
    except Exception:
        contacts_list = []

    updated_contacts = []
    for c in contacts_list:
        c["candidate_name"] = sender_profile["candidate_name"]
        c["candidate_background"] = sender_profile["candidate_background"]
        c["portfolio_url"] = sender_profile["portfolio_url"]
        updated_contacts.append(c)

    if updated_contacts:
        save_contacts(updated_contacts)

    # Re-synthesize initial drafts and scores for all contacts
    optouts = load_optout_list()
    enhanced_contacts = []
    for idx, c in enumerate(updated_contacts):
        email = str(c.get("recipient_email", "") or "").strip().lower()
        is_opted_out = email in optouts

        try:
            subj, bdy = generate_email(c)
        except Exception:
            role = c.get("role", "role")
            company = c.get("company", "team")
            subj = f"Quick note on the {role} role at {company}"
            bdy = f"Hi {c.get('recipient_name', 'there')},\n\nInterested in the {role} position at {company}.\n\nBest,\n{sender_profile['candidate_name']}"

        quality = score_email(subj, bdy)
        passes_hallucination = validate_email(bdy)

        enhanced_contacts.append({
            "id": f"contact-{idx + 1}",
            "contact": c,
            "is_opted_out": is_opted_out,
            "generated_subject": subj,
            "generated_body": bdy,
            "quality": {
                "score": quality["score"],
                "word_count": quality["word_count"],
                "spam_risk": quality["spam_risk"],
                "flags": quality.get("reasons", []),
                "hallucination_guard": "Verified" if passes_hallucination else "Flagged",
            },
        })

    return {
        "status": "success",
        "message": f"Sender profile updated for {sender_profile['candidate_name']}",
        "sender_profile": sender_profile,
        "operator": f"{sender_profile['candidate_name']} • {sender_profile['candidate_title']}",
        "total_contacts": len(enhanced_contacts),
        "contacts": enhanced_contacts,
    }



@app.post("/api/settings/dry-run")
def toggle_dry_run(req: ToggleDryRunRequest) -> Dict[str, Any]:
    """Toggle DRY_RUN setting dynamically at runtime."""
    settings.DRY_RUN = req.dry_run
    return {"dry_run": settings.DRY_RUN, "message": f"DRY_RUN set to {settings.DRY_RUN}"}


# ── Contacts Pipeline ─────────────────────────────────────────────────

@app.get("/api/contacts")
def get_contacts(path: Optional[str] = None) -> Dict[str, Any]:
    """Load all contacts and pre-compute generated drafts and quality scores."""
    try:
        contacts_list = load_contacts(path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    optouts = load_optout_list()
    enhanced_contacts = []

    for idx, c in enumerate(contacts_list):
        email = str(c.get("recipient_email", "") or "").strip().lower()
        is_opted_out = email in optouts

        # Generate initial draft
        try:
            subj, bdy = generate_email(c)
        except Exception as exc:
            role = c.get("role", "role")
            company = c.get("company", "team")
            subj = f"Quick note on the {role} role at {company}"
            bdy = f"Hi {c.get('recipient_name', 'there')},\n\nInterested in the {role} position at {company}.\n\nBest,\nHarsh"

        quality = score_email(subj, bdy)
        passes_hallucination = validate_email(bdy)

        enhanced_contacts.append({
            "id": f"contact-{idx + 1}",
            "contact": c,
            "is_opted_out": is_opted_out,
            "generated_subject": subj,
            "generated_body": bdy,
            "quality": {
                "score": quality["score"],
                "word_count": quality["word_count"],
                "spam_risk": quality["spam_risk"],
                "flags": quality.get("reasons", []),
                "hallucination_guard": "Verified" if passes_hallucination else "Flagged",
            },
        })

    return {
        "contacts": enhanced_contacts,
        "total": len(enhanced_contacts),
        "optouts_count": len(optouts),
    }


@app.post("/api/contacts/upload")
async def upload_contacts(
    request: Request,
    mode: str = Query("replace", enum=["replace", "append"]),
    file: Optional[UploadFile] = File(None),
) -> Dict[str, Any]:
    """Upload and ingest contacts from a .json or .csv file.

    Supports:
    - Multipart file upload or raw JSON payload
    - Modes: 'replace' (clears current contacts and overwrites data/contacts.json)
             'append' (merges new contacts, deduplicating by recipient_email)
    - Validates schema, skipping malformed records gracefully
    - Pre-generates draft and quality scores for new contacts
    - Tracks active source filename for system telemetry
    """
    global active_source_file

    filename = "uploaded_contacts.json"
    content_bytes = b""

    content_type = request.headers.get("content-type", "").lower()
    if "multipart/form-data" in content_type:
        form = await request.form()
        upload = form.get("file")
        if upload is not None and hasattr(upload, "read"):
            filename = getattr(upload, "filename", "uploaded_contacts.json") or "uploaded_contacts.json"
            content_bytes = await upload.read()
            form_mode = form.get("mode")
            if form_mode in ("replace", "append"):
                mode = str(form_mode)
        elif file is not None:
            filename = file.filename or "uploaded_contacts.json"
            content_bytes = await file.read()
        else:
            raise HTTPException(status_code=400, detail="No file uploaded in form data.")
    elif "application/json" in content_type:
        body_json = await request.json()
        filename = "uploaded_payload.json"
        content_bytes = json.dumps(body_json).encode("utf-8")
    else:
        body_raw = await request.body()
        if body_raw:
            content_bytes = body_raw
            filename = "uploaded_contacts.csv" if b"," in body_raw[:200] else "uploaded_payload.json"
        else:
            raise HTTPException(status_code=400, detail="Empty request payload.")

    ext = Path(filename).suffix.lower()
    if ext not in (".json", ".csv"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{ext}'. Only .json and .csv files are supported.",
        )

    try:
        new_contacts, skipped_invalid = parse_contacts_buffer(content_bytes, filename=filename)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse contact file: {exc}")

    if not new_contacts and skipped_invalid == 0:
        raise HTTPException(status_code=400, detail="No contact records found in uploaded file.")
    if not new_contacts and skipped_invalid > 0:
        raise HTTPException(
            status_code=400,
            detail=f"All {skipped_invalid} records in the uploaded file were invalid or missing required fields.",
        )

    # In-batch deduplication by email (case-insensitive)
    deduped_new: list[dict] = []
    seen_new_emails: set[str] = set()
    for c in new_contacts:
        em = c["recipient_email"].lower()
        if em not in seen_new_emails:
            seen_new_emails.add(em)
            deduped_new.append(c)

    if mode == "append":
        try:
            existing_contacts = load_contacts()
        except Exception:
            existing_contacts = []

        existing_emails = {
            str(c.get("recipient_email", "")).strip().lower()
            for c in existing_contacts
            if c.get("recipient_email")
        }

        appended_new = [c for c in deduped_new if c["recipient_email"].lower() not in existing_emails]
        combined_contacts = existing_contacts + appended_new
        loaded_count = len(appended_new)
    else:
        # Replace mode: overwrites queue
        combined_contacts = deduped_new
        loaded_count = len(deduped_new)

    # Persist contacts to data/contacts.json
    save_contacts(combined_contacts)
    active_source_file = Path(filename).name

    # Pre-Generation & Scoring
    optouts = load_optout_list()
    enhanced_contacts = []

    for idx, c in enumerate(combined_contacts):
        email = str(c.get("recipient_email", "") or "").strip().lower()
        is_opted_out = email in optouts

        try:
            subj, bdy = generate_email(c)
        except Exception:
            role = c.get("role", "role")
            company = c.get("company", "team")
            subj = f"Quick note on the {role} role at {company}"
            bdy = f"Hi {c.get('recipient_name', 'there')},\n\nInterested in the {role} position at {company}.\n\nBest,\nHarsh"

        quality = score_email(subj, bdy)
        passes_hallucination = validate_email(bdy)

        enhanced_contacts.append({
            "id": f"contact-{idx + 1}",
            "contact": c,
            "is_opted_out": is_opted_out,
            "generated_subject": subj,
            "generated_body": bdy,
            "quality": {
                "score": quality["score"],
                "word_count": quality["word_count"],
                "spam_risk": quality["spam_risk"],
                "flags": quality.get("reasons", []),
                "hallucination_guard": "Verified" if passes_hallucination else "Flagged",
            },
        })

    return {
        "status": "success",
        "source_file": active_source_file,
        "loaded_count": loaded_count,
        "skipped_invalid": skipped_invalid,
        "total_active": len(combined_contacts),
        "contacts": enhanced_contacts,
    }


@app.get("/api/contacts/template")
def download_contacts_template(format: str = Query("json", enum=["json", "csv"])):
    """Stream clean, valid sample contacts template in JSON or CSV format."""
    if format.lower() == "csv":
        csv_buffer = io.StringIO()
        fieldnames = [
            "recipient_name",
            "recipient_email",
            "company",
            "role",
            "job_url",
            "personalization_note",
            "candidate_name",
            "candidate_background",
            "portfolio_url",
        ]
        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(SAMPLE_TEMPLATE_RECORDS)
        return Response(
            content=csv_buffer.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="contacts_template.csv"'
            },
        )
    else:
        return Response(
            content=json.dumps(SAMPLE_TEMPLATE_RECORDS, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": 'attachment; filename="contacts_template.json"'
            },
        )



# ── Generation & Regeneration ─────────────────────────────────────────

_generation_counters: Dict[str, int] = {}

@app.post("/api/generate")
def generate_or_regenerate(req: GenerateRequest) -> Dict[str, Any]:
    """Generate or rewrite an email with mode presets (Groq LLM / Template)."""
    contact = req.contact
    mode = req.mode or "standard"
    prev_subj = req.previous_subject or req.current_subject or ""
    prev_body = req.previous_body or req.current_body or ""
    email_key = str(contact.get("recipient_email", "") or "").strip().lower()

    # Generate timestamp seed for entropy if not provided
    timestamp_seed = req.timestamp_seed or int(time.time() * 1000)

    # Advance sequential generation counter for this contact
    counter = _generation_counters.get(email_key, 0) + 1
    _generation_counters[email_key] = counter
    regen_count = req.regen_count if req.regen_count and req.regen_count > 0 else counter
    _generation_counters[email_key] = max(_generation_counters.get(email_key, 0), regen_count)

    # Call live Groq LLM with requested mode, attempt counter, and dynamic temperature=0.95
    if settings.LLM_ENABLED:
        try:
            subj, bdy = generate_with_llm(
                contact,
                mode=mode,
                temperature=0.95,
                previous_subject=prev_subj,
                previous_body=prev_body,
                regen_count=regen_count,
                timestamp_seed=timestamp_seed,
            )
        except Exception as exc:
            print(f"  [API] Groq generation failed: {exc}. Falling back to template variants.")
            subj, bdy = generate_email(
                contact,
                mode=mode,
                regen_count=regen_count,
                previous_subject=prev_subj,
                previous_body=prev_body,
            )
    else:
        try:
            subj, bdy = generate_email(
                contact,
                mode=mode,
                regen_count=regen_count,
                previous_subject=prev_subj,
                previous_body=prev_body,
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Generation failed: {exc}")

    # Ensure output is strictly different from previous editor state
    for offset in range(1, 6):
        if prev_subj and subj.strip().lower() == prev_subj.strip().lower():
            alt_subj, _ = generate_email(contact, mode=mode, regen_count=regen_count + offset)
            subj = alt_subj
        else:
            break

    for offset in range(1, 6):
        if prev_body and bdy.strip().lower() == prev_body.strip().lower():
            _, alt_bdy = generate_email(contact, mode=mode, regen_count=regen_count + offset)
            bdy = alt_bdy
        else:
            break

    quality = score_email(subj, bdy)
    passes_hallucination = validate_email(bdy)

    return {
        "subject": subj,
        "body": bdy,
        "quality": {
            "score": quality["score"],
            "word_count": quality["word_count"],
            "spam_risk": quality["spam_risk"],
            "flags": quality.get("reasons", []),
            "hallucination_guard": "Verified" if passes_hallucination else "Flagged",
        },
    }


# ── Dispatch Actions ──────────────────────────────────────────────────

@app.post("/api/dispatch")
def dispatch_action(req: DispatchRequest) -> Dict[str, Any]:
    """Execute review loop actions: Approve & Dispatch, Save Dry Run, or Skip Lead."""
    contact = req.contact
    subject = req.subject
    body = req.body
    action = req.action.lower().strip()
    recipient_email = str(contact.get("recipient_email", "")).strip()

    optouts = load_optout_list()
    if recipient_email.lower() in optouts and action == "send":
        log_entry(contact, subject, "opted_out", error="Recipient on optout_list.txt", body=body)
        return {
            "status": "opted_out",
            "action": action,
            "message": f"Skipped: {recipient_email} is on opt-out list.",
            "summary": get_log_summary(),
        }

    if action == "send":
        # Check session limit for live sends
        summary = get_log_summary()
        sent_count = summary.get("sent", 0)
        if sent_count >= settings.MAX_SENDS_PER_SESSION and not settings.DRY_RUN:
            log_entry(
                contact,
                subject,
                "skipped_limit",
                error=f"Exceeded MAX_SENDS_PER_SESSION ({settings.MAX_SENDS_PER_SESSION})",
                body=body,
            )
            return {
                "status": "skipped_limit",
                "action": action,
                "message": f"Limit reached: maximum {settings.MAX_SENDS_PER_SESSION} live sends per session.",
                "summary": get_log_summary(),
            }

        result = send_email(recipient_email, subject, body)
        log_entry(
            contact=contact,
            subject=subject,
            status=result["status"],
            error=result.get("error_message", ""),
            body=body,
        )
        return {
            "status": result["status"],
            "action": action,
            "message_id": result.get("message_id"),
            "error_message": result.get("error_message", ""),
            "summary": get_log_summary(),
        }

    elif action == "draft":
        result = create_draft(recipient_email, subject, body)
        log_entry(
            contact=contact,
            subject=subject,
            status=result["status"],
            error=result.get("error_message", ""),
            body=body,
        )
        return {
            "status": result["status"],
            "action": action,
            "draft_id": result.get("draft_id"),
            "error_message": result.get("error_message", ""),
            "summary": get_log_summary(),
        }

    elif action == "skip":
        log_entry(
            contact=contact,
            subject=subject,
            status="skipped",
            error="",
            body=body,
        )
        return {
            "status": "skipped",
            "action": action,
            "message": f"Skipped outreach for {recipient_email}.",
            "summary": get_log_summary(),
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}. Must be 'send', 'draft', or 'skip'.")


# ── Audit Log Telemetry ───────────────────────────────────────────────

def format_ist_timestamp(raw_ts: str) -> str:
    """Format raw timestamp string to live Indian Standard Time (IST)."""
    if not raw_ts:
        return ""
    if raw_ts.endswith("IST"):
        return raw_ts
    try:
        clean = raw_ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %I:%M:%S %p IST")
    except Exception:
        return raw_ts


@app.get("/api/audit/logs")
def get_audit_logs(limit: int = Query(50, ge=1, le=500)) -> Dict[str, Any]:
    """Return recent rows from logs/outreach_log.csv with IST timestamps."""
    if not LOG_FILE.exists():
        return {"logs": [], "total": 0, "columns": FIELDNAMES}

    rows = []
    try:
        with open(LOG_FILE, "r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                rows.append({
                    "timestamp": format_ist_timestamp(r.get("timestamp", "")),
                    "recipient_email": r.get("recipient_email", ""),
                    "company": r.get("company", ""),
                    "role": r.get("role", ""),
                    "subject": r.get("subject", ""),
                    "status": r.get("status", ""),
                    "error_message": r.get("error_message", "") or "None",
                    "word_count": int(r.get("word_count", 0) or 0),
                })
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read audit log: {exc}")

    # Return newest logs first
    rows.reverse()
    return {
        "logs": rows[:limit],
        "total": len(rows),
        "columns": [
            "TIMESTAMP (IST)",
            "RECIPIENT EMAIL",
            "COMPANY",
            "ROLE",
            "SUBJECT",
            "STATUS",
            "WORDS",
            "ERROR DETAILS",
        ],
    }


@app.get("/api/audit/csv")
def download_audit_csv():
    """Download outreach_log.csv as a downloadable file."""
    if not LOG_FILE.exists():
        raise HTTPException(status_code=404, detail="Audit log file does not exist yet.")
    return FileResponse(
        path=str(LOG_FILE),
        filename="outreach_log.csv",
        media_type="text/csv",
    )


if __name__ == "__main__":
    uvicorn.run("src.closer.api:app", host="0.0.0.0", port=8000, reload=True)
