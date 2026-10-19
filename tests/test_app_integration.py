"""Integration tests for orchestrator with Phase 4 audit logging."""
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.closer.app import main
from src.closer.audit.logger import get_log_summary


class TestAppIntegration(unittest.TestCase):
    """Test CLI orchestrator integration with audit logging."""

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.log_file = Path(self.test_dir) / "outreach_log.csv"
        # Patch LOG_FILE in logger module to point to temporary test file
        self.patcher = patch("src.closer.audit.logger.LOG_FILE", self.log_file)
        self.patcher.start()

    def tearDown(self) -> None:
        self.patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("src.closer.app.get_user_decision", side_effect=["send", "draft", "skip"])
    @patch("src.closer.app.load_contacts")
    def test_main_runs_and_logs_all_decisions(
        self, mock_load, mock_decision
    ) -> None:
        """Full run logs each action and outputs session summary in finally block."""
        mock_load.return_value = [
            {
                "recipient_name": "Alice",
                "recipient_email": "alice@alpha.com",
                "company": "Alpha Corp",
                "role": "SWE",
                "candidate_name": "Alex",
                "candidate_background": "Python",
            },
            {
                "recipient_name": "Bob",
                "recipient_email": "bob@beta.io",
                "company": "Beta IO",
                "role": "DevOps",
                "candidate_name": "Alex",
                "candidate_background": "Cloud",
            },
            {
                "recipient_name": "Charlie",
                "recipient_email": "charlie@gamma.ai",
                "company": "Gamma AI",
                "role": "Researcher",
                "candidate_name": "Alex",
                "candidate_background": "ML",
            },
        ]

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            main()
            output = fake_out.getvalue()

        # Session summary was printed
        self.assertIn("Session Summary:", output)
        self.assertTrue(self.log_file.exists())

        summary = get_log_summary(self.log_file)
        # By default DRY_RUN=true, send -> dry_run, draft -> dry_run, skip -> skipped
        self.assertEqual(summary.get("skipped"), 1)
        self.assertEqual(summary.get("dry_run"), 2)

    @patch("src.closer.app.load_contacts")
    @patch("src.closer.app.generate_email", side_effect=ValueError("Email exceeded 150 words"))
    def test_generation_failure_logged_and_continues(
        self, mock_gen, mock_load
    ) -> None:
        """If generation fails, it logs 'failed' with error and prints session summary."""
        mock_load.return_value = [
            {
                "recipient_name": "Dave",
                "recipient_email": "dave@delta.com",
                "company": "Delta Co",
                "role": "Architect",
            }
        ]

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            main()
            output = fake_out.getvalue()

        self.assertIn("Generation failed", output)
        self.assertIn("Session Summary:", output)

        summary = get_log_summary(self.log_file)
        self.assertEqual(summary.get("failed"), 1)

    @patch("src.closer.app.load_contacts")
    @patch("src.closer.app.generate_email", side_effect=KeyboardInterrupt)
    def test_keyboard_interrupt_prints_session_summary(
        self, mock_gen, mock_load
    ) -> None:
        """KeyboardInterrupt still executes finally block to print session summary (EC-6.7)."""
        mock_load.return_value = [
            {
                "recipient_name": "Eve",
                "recipient_email": "eve@echo.com",
                "company": "Echo Inc",
                "role": "Engineer",
            }
        ]

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            main()
            output = fake_out.getvalue()

        self.assertIn("Interrupted by user. Exiting cleanly.", output)
        self.assertIn("Session Summary:", output)


if __name__ == "__main__":
    unittest.main()
