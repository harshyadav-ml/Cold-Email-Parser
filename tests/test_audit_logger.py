"""Unit tests for Phase 4: Audit Logging."""
import csv
import io
import os
import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from src.closer.audit.logger import (
    FIELDNAMES,
    VALID_STATUSES,
    _ensure_header,
    get_log_summary,
    log_entry,
)
from src.closer.domain.models import ContactRecord, LogEntry


class TestAuditLogger(unittest.TestCase):
    """Test suite for CSV audit logger functionality and edge cases."""

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.log_file = Path(self.test_dir) / "test_outreach_log.csv"

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_ensure_header_creates_headers(self) -> None:
        """Header row is created when file does not exist (Criterion 4.3)."""
        self.assertFalse(self.log_file.exists())
        _ensure_header(self.log_file)
        self.assertTrue(self.log_file.exists())

        with open(self.log_file, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, FIELDNAMES)

    def test_ensure_header_no_duplicates_on_restart(self) -> None:
        """Calling _ensure_header multiple times must not write duplicate headers (EC-5.3)."""
        _ensure_header(self.log_file)
        _ensure_header(self.log_file)

        with open(self.log_file, "r", encoding="utf-8-sig", newline="") as f:
            lines = [line.strip() for line in f if line.strip()]
        self.assertEqual(len(lines), 1)

    def test_all_8_columns_present(self) -> None:
        """Verify all 8 required columns in FIELDNAMES (Criterion 4.6)."""
        expected_fields = [
            "timestamp",
            "recipient_email",
            "company",
            "role",
            "subject",
            "status",
            "error_message",
            "word_count",
        ]
        self.assertEqual(FIELDNAMES, expected_fields)

    def test_log_entry_appends_row(self) -> None:
        """log_entry appends one row per contact (Criterion 4.1)."""
        contact = {
            "recipient_name": "Priya Sharma",
            "recipient_email": "priya@acmeai.com",
            "company": "Acme AI",
            "role": "Backend Engineer",
        }
        body = "Hi Priya, I noticed Acme AI is hiring. Best, Alex."
        subject = "Quick note on Backend Engineer at Acme AI"

        log_entry(
            contact=contact,
            subject=subject,
            status="sent",
            error="",
            body=body,
            log_file=self.log_file,
        )

        with open(self.log_file, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["recipient_email"], "priya@acmeai.com")
        self.assertEqual(row["company"], "Acme AI")
        self.assertEqual(row["role"], "Backend Engineer")
        self.assertEqual(row["subject"], subject)
        self.assertEqual(row["status"], "sent")
        self.assertEqual(row["error_message"], "")
        self.assertEqual(row["word_count"], str(len(body.split())))

        # Validate timestamp is non-empty (logger uses IST format, not ISO-8601)
        self.assertTrue(row["timestamp"], "Timestamp should not be empty")

    def test_log_entry_with_contact_dataclass(self) -> None:
        """log_entry supports ContactRecord dataclass instances."""
        contact = ContactRecord(
            recipient_email="sara@devtools.co",
            company="DevTools Co",
            role="Developer Advocate",
            candidate_name="Alex Chen",
            candidate_background="Developer tools",
        )
        log_entry(
            contact=contact,
            subject="Hello",
            status="drafted",
            body="Short body with four words",
            log_file=self.log_file,
        )

        with open(self.log_file, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["company"], "DevTools Co")
        self.assertEqual(rows[0]["status"], "drafted")
        self.assertEqual(rows[0]["word_count"], "5")

    def test_log_entry_appends_across_multiple_runs(self) -> None:
        """Multiple log_entry calls append rows without overwriting (Criterion 4.1)."""
        contact1 = {"recipient_email": "c1@test.com", "company": "Co1", "role": "R1"}
        contact2 = {"recipient_email": "c2@test.com", "company": "Co2", "role": "R2"}

        log_entry(contact1, "Sub1", "sent", body="word1 word2", log_file=self.log_file)
        log_entry(contact2, "Sub2", "skipped", body="", log_file=self.log_file)

        with open(self.log_file, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["company"], "Co1")
        self.assertEqual(rows[1]["company"], "Co2")

    def test_unicode_characters_encoding(self) -> None:
        """Unicode characters (e.g. Müller GmbH, Bengaluru) are preserved via utf-8-sig (EC-5.4)."""
        contact = {
            "recipient_email": "hans@müller.de",
            "company": "Müller GmbH & Co. KG",
            "role": "AI/ML Internship — Bengaluru (ಬೆಂಗಳೂರು)",
        }
        body = "Guten Tag! Üben & Grüßen."
        subject = "Bewerbung: Müller GmbH"

        log_entry(
            contact=contact,
            subject=subject,
            status="sent",
            body=body,
            log_file=self.log_file,
        )

        with open(self.log_file, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["company"], "Müller GmbH & Co. KG")
        self.assertEqual(rows[0]["role"], "AI/ML Internship — Bengaluru (ಬೆಂಗಳೂರು)")
        self.assertEqual(rows[0]["recipient_email"], "hans@müller.de")

    def test_permission_error_handled_gracefully(self) -> None:
        """PermissionError (e.g. Excel locking file) does not crash the app (EC-5.1)."""
        contact = {"recipient_email": "test@test.com", "company": "Test", "role": "Dev"}

        with patch("builtins.open", side_effect=PermissionError("File locked by Excel")):
            with patch("sys.stdout", new=io.StringIO()) as fake_out:
                # Should not raise
                log_entry(contact, "Sub", "sent", log_file=self.log_file)
                output = fake_out.getvalue()
                self.assertIn("Permission denied", output)

    def test_os_error_disk_full_handled_gracefully(self) -> None:
        """OSError (disk full) does not crash the app (EC-5.2)."""
        contact = {"recipient_email": "test@test.com", "company": "Test", "role": "Dev"}

        with patch("builtins.open", side_effect=OSError(28, "No space left on device")):
            with patch("sys.stdout", new=io.StringIO()) as fake_out:
                # Should not raise
                log_entry(contact, "Sub", "sent", log_file=self.log_file)
                output = fake_out.getvalue()
                self.assertIn("Disk or I/O error", output)

    def test_unexpected_status_warning_and_logged(self) -> None:
        """Unexpected status prints a warning but still writes and counts (EC-5.5)."""
        contact = {"recipient_email": "test@test.com", "company": "Test", "role": "Dev"}

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            log_entry(contact, "Sub", "draft_failed", log_file=self.log_file)
            output = fake_out.getvalue()
            self.assertIn("Unexpected status 'draft_failed'", output)

        summary = get_log_summary(log_file=self.log_file)
        self.assertEqual(summary.get("draft_failed"), 1)

    def test_get_log_summary_counts(self) -> None:
        """get_log_summary returns counts grouped by status (Criterion 4.8)."""
        contact = {"recipient_email": "a@b.com", "company": "Co", "role": "R"}

        log_entry(contact, "Sub", "sent", log_file=self.log_file)
        log_entry(contact, "Sub", "sent", log_file=self.log_file)
        log_entry(contact, "Sub", "skipped", log_file=self.log_file)
        log_entry(contact, "Sub", "failed", error="SMTP error", log_file=self.log_file)
        log_entry(contact, "Sub", "dry_run", log_file=self.log_file)

        summary = get_log_summary(log_file=self.log_file)
        self.assertEqual(
            summary,
            {
                "sent": 2,
                "skipped": 1,
                "failed": 1,
                "dry_run": 1,
            },
        )

    def test_get_log_summary_nonexistent_file(self) -> None:
        """get_log_summary returns empty dict for nonexistent file."""
        non_existent = Path(self.test_dir) / "does_not_exist.csv"
        summary = get_log_summary(log_file=non_existent)
        self.assertEqual(summary, {})

    def test_error_message_captured(self) -> None:
        """Failed operations capture non-empty error message."""
        contact = {"recipient_email": "err@test.com", "company": "FailCo", "role": "Role"}
        error_text = "550 5.1.1 Recipient unknown"

        log_entry(
            contact=contact,
            subject="Sub",
            status="failed",
            error=error_text,
            log_file=self.log_file,
        )

        with open(self.log_file, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(rows[0]["status"], "failed")
        self.assertEqual(rows[0]["error_message"], error_text)


if __name__ == "__main__":
    unittest.main()
