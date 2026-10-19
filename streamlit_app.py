"""Streamlit web interface for The Closer (Phase 5).

Run with:
    streamlit run streamlit_app.py
    or:
    streamlit run app.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import streamlit as st

from src.closer.config import settings
from src.closer.audit.logger import LOG_FILE, get_log_summary, log_entry
from src.closer.delivery import create_draft, send_email
from src.closer.generation import generate_email, score_email
from src.closer.input.loader import DEFAULT_CONTACTS_PATH, load_contacts, load_optout_list

# Page config
st.set_page_config(
    page_title="The Closer — Cold Email Agent",
    page_icon="✉️",
    layout="wide",
)

st.title("✉️ The Closer — Cold Email Writer + Send Bot")
st.caption("Sprint 3 · Agent Meets Gmail · Phase 5 Post-MVP UI")

# Sidebar config & status
with st.sidebar:
    st.header("⚙️ Configuration")
    st.markdown(f"**DRY_RUN:** `{'Enabled (Safe)' if settings.DRY_RUN else 'Disabled (Live Sends)'}`")
    st.markdown(f"**Delivery Method:** `{settings.SEND_METHOD.upper()}`")
    st.markdown(f"**LLM Generation:** `{'Enabled' if settings.LLM_ENABLED else 'Disabled (Template)'}`")
    if settings.LLM_ENABLED:
        st.markdown(f"**Model:** `{settings.LLM_MODEL}`")

    st.divider()
    st.header("📊 Audit Summary")
    summary = get_log_summary()
    if summary:
        for status, count in summary.items():
            st.metric(label=status.capitalize(), value=count)
    else:
        st.info("No audit log entries recorded yet.")

# Main area: File loader
st.subheader("1. Load Outreach Targets")
col_upload, col_default = st.columns([2, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "Upload custom contacts (.json or .csv)",
        type=["json", "csv"],
        help="Upload contacts.json or jobs.csv",
    )

with col_default:
    use_default = st.button("Load default data/contacts.json", use_container_width=True)

# Session state initialization
if "contacts_data" not in st.session_state:
    st.session_state.contacts_data = None
if "processed_actions" not in st.session_state:
    st.session_state.processed_actions = {}
if "generated_emails" not in st.session_state:
    st.session_state.generated_emails = {}

# Handle file loading
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            import io
            content = uploaded_file.getvalue().decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(content))
            st.session_state.contacts_data = [dict(r) for r in reader]
        else:
            st.session_state.contacts_data = json.load(uploaded_file)
        st.success(f"Loaded {len(st.session_state.contacts_data)} contacts from {uploaded_file.name}")
    except Exception as exc:
        st.error(f"Error reading file: {exc}")
elif use_default or st.session_state.contacts_data is None:
    try:
        st.session_state.contacts_data = load_contacts(DEFAULT_CONTACTS_PATH)
    except Exception as exc:
        st.warning(f"Could not load default contacts: {exc}")

contacts = st.session_state.contacts_data or []
optouts = load_optout_list()

if not contacts:
    st.info("Please upload a contacts file or click 'Load default contacts.json' to begin.")
else:
    st.subheader(f"2. Contact Review & Dispatch ({len(contacts)} records)")

    for idx, contact in enumerate(contacts):
        email = str(contact.get("recipient_email", "") or "").strip().lower()
        company = contact.get("company", "Unknown Company")
        role = contact.get("role", "Open Role")
        recipient_name = contact.get("recipient_name", "Hiring Manager")

        action_key = f"action_{email}_{idx}"
        status_info = st.session_state.processed_actions.get(action_key)

        with st.expander(
            f"[{idx+1}/{len(contacts)}] {company} — {role} ({email}) "
            + (f"· Status: {status_info['status'].upper()}" if status_info else ""),
            expanded=(status_info is None),
        ):
            c_info, c_email = st.columns([1, 2])

            with c_info:
                st.markdown(f"**Recipient:** {recipient_name}")
                st.markdown(f"**Email:** `{email}`")
                st.markdown(f"**Company:** {company}")
                st.markdown(f"**Role:** {role}")
                if contact.get("personalization_note"):
                    st.markdown(f"**Note:** *{contact['personalization_note']}*")
                if contact.get("portfolio_url"):
                    st.markdown(f"**Portfolio:** {contact['portfolio_url']}")

                if email in optouts:
                    st.warning("⚠️ This email is on the opt-out list (optout_list.txt).")

            with c_email:
                # Generate email if not cached
                if email not in st.session_state.generated_emails:
                    try:
                        subj, bdy = generate_email(contact)
                    except Exception as e:
                        subj, bdy = f"Application for {role}", f"Error generating email: {e}"
                    st.session_state.generated_emails[email] = (subj, bdy)
                else:
                    subj, bdy = st.session_state.generated_emails[email]

                subject_input = st.text_input("Subject", subj, key=f"subj_{email}_{idx}")
                body_input = st.text_area("Body", bdy, height=200, key=f"body_{email}_{idx}")

                # Quality metrics
                quality = score_email(subject_input, body_input)
                m1, m2, m3 = st.columns(3)
                m1.metric("Quality Score", f"{quality['score']}/10")
                m2.metric("Word Count", f"{quality['word_count']} words")
                m3.metric("Spam Risk", quality["spam_risk"].capitalize())

                if status_info:
                    st.success(f"Action completed: **{status_info['status'].upper()}**")
                else:
                    btn_send, btn_draft, btn_skip = st.columns(3)

                    if btn_send.button("🚀 Send Email", key=f"btn_send_{email}_{idx}", use_container_width=True):
                        if email in optouts:
                            log_entry(contact, subject_input, "opted_out", body=body_input)
                            res = {"status": "opted_out"}
                        else:
                            res = send_email(email, subject_input, body_input)
                            log_entry(contact, subject_input, res["status"], error=res.get("error_message", ""), body=body_input)
                        st.session_state.processed_actions[action_key] = res
                        st.rerun()

                    if btn_draft.button("📝 Create Draft", key=f"btn_draft_{email}_{idx}", use_container_width=True):
                        res = create_draft(email, subject_input, body_input)
                        log_entry(contact, subject_input, res["status"], error=res.get("error_message", ""), body=body_input)
                        st.session_state.processed_actions[action_key] = res
                        st.rerun()

                    if btn_skip.button("⏭️ Skip", key=f"btn_skip_{email}_{idx}", use_container_width=True):
                        res = {"status": "skipped", "error_message": ""}
                        log_entry(contact, subject_input, "skipped", body=body_input)
                        st.session_state.processed_actions[action_key] = res
                        st.rerun()

# Audit log viewer
st.divider()
st.subheader("3. Audit Log Entries")
if LOG_FILE.exists():
    try:
        import pandas as pd
        df = pd.read_csv(LOG_FILE, encoding="utf-8-sig")
        st.dataframe(df, use_container_width=True)
    except Exception as exc:
        st.error(f"Error loading log table: {exc}")
else:
    st.info("No audit log file created yet.")
