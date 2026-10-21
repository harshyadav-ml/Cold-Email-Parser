"""Unit tests for Phase 5: LLM Rewriting, Gmail API, and Stretch Features."""
import csv
import base64
import io
import os
import shutil
import tempfile
import unittest
from email import policy
from email.parser import BytesParser
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.closer.config import settings
from src.closer.delivery import create_draft, create_gmail_draft, send_email, send_gmail_message
from src.closer.delivery.gmail import _build_raw_message, get_gmail_service
from src.closer.delivery.smtp import _build_message as build_smtp_message
from src.closer.generation import (
    check_spam_risk,
    generate_email,
    generate_followup,
    score_email,
    validate_email,
)
from src.closer.generation.llm import build_prompt, generate_with_llm
from src.closer.input.loader import load_contacts, load_optout_list


class TestPhase5LLM(unittest.TestCase):
    """Tests for LLM Email Generation and its edge cases (Criteria 5L.1 - 5L.6)."""

    def setUp(self) -> None:
        self.sample_contact = {
            "recipient_name": "Priya Sharma",
            "recipient_email": "priya@acmeai.com",
            "company": "Acme AI",
            "role": "Backend Engineer",
            "personalization_note": "Acme AI launched an AI workflow tool",
            "candidate_name": "Alex Chen",
            "candidate_background": "Python development and agentic workflows",
            "portfolio_url": "https://github.com/alexchen",
        }
        # Reset runtime state
        settings.LLM_SESSION_DISABLED = False

    def test_build_prompt_structure(self) -> None:
        """Prompt includes company, role, background, rules, and output format."""
        prompt = build_prompt(self.sample_contact)
        self.assertIn("Acme AI", prompt)
        self.assertIn("Backend Engineer", prompt)
        self.assertIn("Under 150 words", prompt)
        self.assertIn("Subject: [Compelling subject line here]", prompt)

    @patch("src.closer.generation.llm.os.getenv", return_value="")
    @patch("src.closer.generation.llm.settings")
    def test_missing_api_key_falls_back_to_template(self, mock_settings, mock_getenv) -> None:
        """Missing API key triggers fallback with warning (EC-0.5, Criterion 5L.2)."""
        mock_settings.GROQ_API_KEY = ""
        mock_settings.ANTHROPIC_API_KEY = ""
        mock_settings.OPENAI_API_KEY = ""
        mock_settings.LLM_SESSION_DISABLED = False

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            subj, body = generate_with_llm(self.sample_contact)
            output = fake_out.getvalue()

        self.assertIn("[WARNING] GROQ_API_KEY missing", output)
        self.assertIn("Acme AI", subj)
        self.assertIn("Alex Chen", body)

    @patch("src.closer.generation.settings")
    @patch("src.closer.generation.llm.settings")
    @patch("groq.Groq")
    def test_llm_enabled_triggers_api_call(self, mock_groq_cls, mock_llm_settings, mock_gen_settings) -> None:
        """LLM_ENABLED=true triggers API call in generate_email() (Criterion 5L.1)."""
        mock_gen_settings.LLM_ENABLED = True
        mock_gen_settings.LLM_SESSION_DISABLED = False
        mock_llm_settings.LLM_ENABLED = True
        mock_llm_settings.LLM_SESSION_DISABLED = False
        mock_llm_settings.GROQ_API_KEY = "gsk_test_key"
        mock_llm_settings.ANTHROPIC_API_KEY = ""
        mock_llm_settings.OPENAI_API_KEY = ""
        mock_llm_settings.LLM_MODEL = "llama-3.3-70b-versatile"
        mock_llm_settings.LLM_TIMEOUT = 30.0


        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client
        mock_choice = MagicMock()
        mock_choice.message.content = "Subject: Cold Email Note\n\nHi Priya,\nLoved your workflow launch. Best,\nAlex"
        mock_client.chat.completions.create.return_value.choices = [mock_choice]

        subj, body = generate_email(self.sample_contact)
        mock_client.chat.completions.create.assert_called_once()
        self.assertEqual(subj, "Cold Email Note")
        self.assertIn("Loved your workflow launch", body)

    @patch("src.closer.generation.llm.os.getenv", return_value="gsk_test_key")
    @patch("src.closer.generation.llm.settings")
    @patch("groq.Groq")
    def test_llm_empty_response_fallback(self, mock_groq_cls, mock_settings, mock_getenv) -> None:
        """Empty or whitespace response falls back to template (EC-2.4, Criterion 5L.3)."""
        mock_settings.GROQ_API_KEY = "gsk_test_key"
        mock_settings.ANTHROPIC_API_KEY = ""
        mock_settings.OPENAI_API_KEY = ""
        mock_settings.LLM_SESSION_DISABLED = False
        mock_settings.LLM_MODEL = "llama-3.3-70b-versatile"
        mock_settings.LLM_TIMEOUT = 30.0

        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client
        mock_choice = MagicMock()
        mock_choice.message.content = "   \n\n  "
        mock_client.chat.completions.create.return_value.choices = [mock_choice]

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            subj, body = generate_with_llm(self.sample_contact)
            output = fake_out.getvalue()

        self.assertIn("empty", output.lower())
        self.assertIn("Acme AI", subj)
        self.assertIn("Alex Chen", body)

    @patch("src.closer.generation.llm.settings")
    @patch("groq.Groq")
    def test_llm_rate_limit_disables_session(self, mock_groq_cls, mock_settings) -> None:
        """RateLimitError disables LLM for session remainder (EC-2.6, Criterion 5L.4)."""
        import groq

        mock_settings.GROQ_API_KEY = "gsk_test_key"
        mock_settings.ANTHROPIC_API_KEY = ""
        mock_settings.OPENAI_API_KEY = ""
        mock_settings.LLM_SESSION_DISABLED = False
        mock_settings.LLM_MODEL = "llama-3.3-70b-versatile"
        mock_settings.LLM_TIMEOUT = 30.0

        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client

        # Simulate RateLimitError
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_client.chat.completions.create.side_effect = groq.RateLimitError(
            message="Rate limit hit", response=mock_resp, body=None
        )

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            subj, body = generate_with_llm(self.sample_contact)
            output = fake_out.getvalue()

        self.assertIn("RateLimitError", output)
        self.assertTrue(mock_settings.LLM_SESSION_DISABLED)
        # Returned template fallback
        self.assertIn("Acme AI", subj)

    @patch("src.closer.generation.llm.os.getenv", return_value="gsk_test_key")
    @patch("src.closer.generation.llm.settings")
    @patch("groq.Groq")
    def test_llm_timeout_falls_back_to_template(self, mock_groq_cls, mock_settings, mock_getenv) -> None:
        """API timeout (>30s) falls back to template (EC-2.7, Criterion 5L.5)."""
        mock_settings.GROQ_API_KEY = "gsk_test_key"
        mock_settings.ANTHROPIC_API_KEY = ""
        mock_settings.OPENAI_API_KEY = ""
        mock_settings.LLM_SESSION_DISABLED = False
        mock_settings.LLM_MODEL = "llama-3.3-70b-versatile"
        mock_settings.LLM_TIMEOUT = 30.0

        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = TimeoutError("Request timed out after 30s")

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            subj, body = generate_with_llm(self.sample_contact)
            output = fake_out.getvalue()     

        self.assertIn("timed out", output.lower())
        self.assertIn("Acme AI", subj)

    def test_validate_email_detects_fabricated_claims(self) -> None:
        """validate_email rejects hallucinated referrals (EC-2.5, Criterion 5L.6)."""
        hallucinated_body = "Hi Priya, John Smith referred me to your team. Would love to chat. Best, Alex"
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            valid = validate_email(hallucinated_body)
            output = fake_out.getvalue()

        self.assertFalse(valid)
        self.assertIn("Fabricated claim trigger phrase detected: 'referred me'", output)

        clean_body = "Hi Priya, I saw Acme AI's open role and wanted to share my background. Best, Alex"
        self.assertTrue(validate_email(clean_body))


class TestPhase5GmailAPI(unittest.TestCase):
    """Tests for Gmail API delivery and draft creation (Criteria 5G.1 - 5G.4)."""

    @patch("src.closer.delivery.gmail.settings")
    def test_raw_message_serializes_utf8_headers_and_plain_text(self, mock_settings) -> None:
        """The Gmail raw payload contains parseable UTF-8 MIME."""
        mock_settings.SENDER_NAME = "Alex Résumé"
        mock_settings.SMTP_USER = "erharshyadavjpr@gmail.com"
        raw = _build_raw_message(
            "priya@example.net",
            "Résumé for the ingénieur role",
            "Bonjour, Priya.\n\nJe vous écris au sujet du rôle d'ingénieur.",
        )

        message = BytesParser(policy=policy.default).parsebytes(base64.urlsafe_b64decode(raw))

        self.assertEqual(message["From"].addresses[0].display_name, "Alex Résumé")
        self.assertEqual(message["From"].addresses[0].addr_spec, "erharshyadavjpr@gmail.com")
        self.assertEqual(message["To"].addresses[0].addr_spec, "priya@example.net")
        self.assertEqual(str(message["Subject"]), "Résumé for the ingénieur role")
        self.assertEqual(message.get_content_type(), "text/plain")
        self.assertEqual(message.get_content_charset(), "utf-8")
        self.assertIn("rôle d'ingénieur", message.get_content())
        self.assertIsNotNone(message["Date"])
        self.assertIsNotNone(message["Message-ID"])

    @patch("src.closer.delivery.smtp.settings")
    def test_smtp_fallback_message_uses_utf8_and_rfc_headers(self, mock_settings) -> None:
        mock_settings.SENDER_NAME = "Alex Résumé"
        mock_settings.SMTP_USER = "erharshyadavjpr@gmail.com"
        message = build_smtp_message(
            "priya@example.net",
            "Résumé for the ingénieur role",
            "Bonjour, Priya.\n\nJe vous écris au sujet du rôle d'ingénieur.",
        )
        parsed = BytesParser(policy=policy.default).parsebytes(message.as_bytes())

        self.assertEqual(parsed.get_content_charset(), "utf-8")
        self.assertIn("rôle d'ingénieur", parsed.get_content())
        self.assertIsNotNone(parsed["Date"])
        self.assertIsNotNone(parsed["Message-ID"])

    def test_empty_draft_body_detected_before_api(self) -> None:
        """Empty draft body is rejected before API call (EC-4.7, Criterion 5G.3)."""
        with patch("sys.stdout", new=io.StringIO()):
            res = create_gmail_draft("test@example.com", "Subject", "   ")
        self.assertEqual(res["status"], "failed")
        self.assertIn("Draft body cannot be empty", res["error_message"])

    def test_empty_message_body_detected_before_send(self) -> None:
        """Empty message body is rejected before API call (EC-4.7)."""
        with patch("sys.stdout", new=io.StringIO()):
            res = send_gmail_message("test@example.com", "Subject", "")
        self.assertEqual(res["status"], "failed")
        self.assertIn("Email body cannot be empty", res["error_message"])

    @patch("src.closer.delivery.gmail.settings")
    def test_dry_run_simulates_draft_and_send(self, mock_settings) -> None:
        """DRY_RUN=true returns simulated results without network calls."""
        mock_settings.DRY_RUN = True
        with patch("sys.stdout", new=io.StringIO()):
            draft_res = create_gmail_draft("test@example.com", "Subj", "Body text")
            send_res = send_gmail_message("test@example.com", "Subj", "Body text")

        self.assertEqual(draft_res["status"], "dry_run")
        self.assertEqual(send_res["status"], "dry_run")

    @patch("src.closer.delivery.gmail.settings")
    def test_gmail_api_draft_creation_success(self, mock_settings) -> None:
        """Successful draft creation returns drafted status and draft_id (Criterion 5G.1)."""
        mock_settings.DRY_RUN = False
        mock_settings.SENDER_NAME = "Alex"
        mock_settings.SMTP_USER = "erharshyadavjpr@gmail.com"
        mock_service = MagicMock()
        mock_draft = {"id": "draft_xyz123"}
        mock_service.users().drafts().create().execute.return_value = mock_draft

        with patch("sys.stdout", new=io.StringIO()):
            res = create_gmail_draft(
                "priya@acmeai.com",
                "Quick note",
                "Hello Priya",
                service=mock_service,
            )

        self.assertEqual(res["status"], "drafted")
        self.assertEqual(res["draft_id"], "draft_xyz123")

    @patch("src.closer.delivery.gmail.settings")
    def test_gmail_api_429_quota_falls_back_to_smtp(self, mock_settings) -> None:
        """HttpError 429 quota exhaustion falls back to SMTP (Criterion 5G.4)."""
        from googleapiclient.errors import HttpError
        import httplib2

        mock_settings.DRY_RUN = False
        mock_settings.SENDER_NAME = "Alex"
        mock_settings.SMTP_USER = "erharshyadavjpr@gmail.com"
        mock_service = MagicMock()
        resp = httplib2.Response({"status": "429"})
        mock_service.users().drafts().create().execute.side_effect = HttpError(resp, b"Rate Limit Exceeded")

        with patch("sys.closer.delivery.smtp.create_draft" if False else "src.closer.delivery.smtp.create_draft") as mock_smtp:
            mock_smtp.return_value = {"status": "drafted_locally", "draft_id": None, "error_message": ""}
            with patch("sys.stdout", new=io.StringIO()) as fake_out:
                res = create_gmail_draft("test@co.com", "Sub", "Body", service=mock_service)
                out = fake_out.getvalue()

        self.assertIn("quota exceeded", out.lower())
        mock_smtp.assert_called_once()


class TestPhase5StretchFeatures(unittest.TestCase):
    """Tests for additional stretch features (CSV input, opt-out, deduplication, follow-ups)."""

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_contacts_from_csv(self) -> None:
        """load_contacts parses CSV files via csv.DictReader."""
        csv_file = Path(self.test_dir) / "test_jobs.csv"
        with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["recipient_name", "recipient_email", "company", "role"])
            writer.writeheader()
            writer.writerow({"recipient_name": "Maya", "recipient_email": "maya@cloud.io", "company": "CloudIO", "role": "Dev"})

        contacts = load_contacts(csv_file)
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0]["company"], "CloudIO")

    def test_load_optout_list(self) -> None:
        """load_optout_list parses emails ignoring comments and whitespace."""
        opt_file = Path(self.test_dir) / "optout.txt"
        with open(opt_file, "w", encoding="utf-8") as f:
            f.write("# comment line\nSTOP@company.com\n\nleave-me-alone@corp.io\n")

        optouts = load_optout_list(opt_file)
        self.assertIn("stop@company.com", optouts)
        self.assertIn("leave-me-alone@corp.io", optouts)
        self.assertEqual(len(optouts), 2)

    def test_generate_followup(self) -> None:
        """generate_followup creates a polite follow-up email under 100 words."""
        contact = {
            "recipient_name": "Marcus",
            "company": "NextGen Robotics",
            "role": "Robotics Engineer",
            "candidate_name": "Alex",
        }
        subj, body = generate_followup(contact, previous_subject="Application for Robotics Engineer")
        self.assertEqual(subj, "Re: Application for Robotics Engineer")
        self.assertIn("Following up briefly", body)
        self.assertLessEqual(len(body.split()), 100)

    def test_quality_and_spam_checker(self) -> None:
        """score_email and check_spam_risk identify spam triggers and score quality."""
        spammy_body = "CONGRATULATIONS! ACT NOW and WINNER 100% FREE! Contact me right away!!!!"
        spam_res = check_spam_risk("URGENT OFFER", spammy_body)
        self.assertTrue(spam_res["is_spam_risk"])
        self.assertEqual(spam_res["risk_level"], "high")

        score_res = score_email("URGENT OFFER", spammy_body)
        self.assertLess(score_res["score"], 6)

        clean_subj = "Quick note on Backend Engineer role at Acme AI"
        clean_body = (
            "Hi Priya,\n\n"
            "I noticed Acme AI is hiring for Backend Engineer. "
            "I've been building Python workflow tools that align with your recent launch.\n\n"
            "Would you be open to a quick 10-minute chat?\n\n"
            "Best,\nAlex"
        )
        clean_score = score_email(clean_subj, clean_body)
        self.assertGreaterEqual(clean_score["score"], 8)
        self.assertEqual(clean_score["spam_risk"], "low")

    def test_root_proxies(self) -> None:
        """Root modules email_generator.py and email_sender.py proxy successfully."""
        import email_generator
        import email_sender

        contact = {"recipient_name": "Priya", "company": "Acme", "role": "SWE", "candidate_name": "Alex"}
        subj, body = email_generator.generate_email(contact)
        self.assertIn("Acme", subj)

        with patch("sys.stdout", new=io.StringIO()):
            res = email_sender.send_email("test@acme.com", subj, body)
            self.assertEqual(res["status"], "dry_run")

    @patch("src.closer.app.load_optout_list", return_value={"optout@block.com"})
    @patch("src.closer.app.load_contacts")
    @patch("src.closer.app.get_user_decision", return_value="send")
    def test_app_optout_and_deduplication(self, mock_decision, mock_load, mock_optouts) -> None:
        """app.py skips opted-out contacts and duplicate contacts in same session."""
        from src.closer.app import main
        from src.closer.audit.logger import get_log_summary

        log_file = Path(self.test_dir) / "test_app_log.csv"

        contacts = [
            {"recipient_name": "Opted Out", "recipient_email": "optout@block.com", "company": "BlockCo", "role": "Dev"},
            {"recipient_name": "First Entry", "recipient_email": "repeat@repeat.com", "company": "RepeatCo", "role": "Dev"},
            {"recipient_name": "Second Entry", "recipient_email": "repeat@repeat.com", "company": "RepeatCo", "role": "Dev"},
        ]
        mock_load.return_value = contacts

        with patch("src.closer.audit.logger.LOG_FILE", log_file):
            with patch("sys.stdout", new=io.StringIO()) as fake_out:
                main()
                out = fake_out.getvalue()

        self.assertIn("[opt-out]", out)
        self.assertIn("[duplicate]", out)

        summary = get_log_summary(log_file)
        self.assertEqual(summary.get("opted_out"), 1)
        self.assertEqual(summary.get("skipped_duplicate"), 1)
        self.assertEqual(summary.get("dry_run"), 1)

    @patch("src.closer.app.load_optout_list", return_value=set())
    @patch("src.closer.app.load_contacts")
    @patch("src.closer.app.get_user_decision", return_value="send")
    @patch("src.closer.app.send_email", return_value={"status": "sent", "message_id": "1", "error_message": ""})
    def test_app_max_sends_limit(self, mock_send, mock_decision, mock_load, mock_optouts) -> None:
        """When live sends exceed MAX_SENDS_PER_SESSION, remainder marked skipped_limit (EC-4.8)."""
        from src.closer.app import main
        from src.closer.audit.logger import get_log_summary

        log_file = Path(self.test_dir) / "test_limit_log.csv"

        # 3 contacts, but limit is 2 live sends
        contacts = [
            {"recipient_name": "C1", "recipient_email": "c1@co.com", "company": "Co1", "role": "Dev"},
            {"recipient_name": "C2", "recipient_email": "c2@co.com", "company": "Co2", "role": "Dev"},
            {"recipient_name": "C3", "recipient_email": "c3@co.com", "company": "Co3", "role": "Dev"},
        ]
        mock_load.return_value = contacts

        with patch("src.closer.audit.logger.LOG_FILE", log_file):
            with patch("src.closer.app.settings.MAX_SENDS_PER_SESSION", 2):
                with patch("src.closer.app.settings.DRY_RUN", False):
                    with patch("sys.stdout", new=io.StringIO()) as fake_out:
                        main()
                        out = fake_out.getvalue()

        self.assertIn("[limit]", out)
        summary = get_log_summary(log_file)
        self.assertEqual(summary.get("sent"), 2)
        self.assertEqual(summary.get("skipped_limit"), 1)



if __name__ == "__main__":
    unittest.main()
