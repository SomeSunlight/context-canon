from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import contextcanon.entry as entry
from contextcanon.parser import ContextCanonError


class EntryWindowsLockTests(unittest.TestCase):
    def test_raw_windows_permission_error_becomes_actionable_cli_error(self):
        error = PermissionError(13, "Access is denied", r"C:\\project\\.context\\sources\\package")
        error.winerror = 5
        stderr = io.StringIO()

        with patch("contextcanon.entry.run_journaled", side_effect=error), contextlib.redirect_stderr(stderr):
            result = entry.main([])

        text = stderr.getvalue()
        self.assertEqual(result, 2)
        self.assertIn("Windows denied a ContextCanon filesystem operation", text)
        self.assertIn("WinError 5", text)
        self.assertIn("antivirus and other background scanners", text)
        self.assertIn("exclude the project directory from real-time scanning", text)
        self.assertIn("Exclude Folders", text)
        self.assertIn("rerun the same ContextCanon command", text)
        self.assertIn(r"C:\\project\\.context\\sources\\package", text)
        self.assertNotIn("Traceback", text)

    def test_wrapped_windows_lock_error_keeps_original_context_and_adds_guidance(self):
        error = ContextCanonError(
            "Could not publish immutable package Demo 1.0.0 to "
            r"C:\\project\\.context\\sources\\package after retrying a temporary filesystem lock: "
            "[WinError 5] Access is denied"
        )
        stderr = io.StringIO()

        with patch("contextcanon.entry.run_journaled", side_effect=error), contextlib.redirect_stderr(stderr):
            result = entry.main([])

        text = stderr.getvalue()
        self.assertEqual(result, 2)
        self.assertIn("Could not publish immutable package Demo 1.0.0", text)
        self.assertIn(r"C:\\project\\.context\\sources\\package", text)
        self.assertIn("antivirus and other background scanners", text)
        self.assertIn("See docs/windows.md", text)
        self.assertNotIn("Traceback", text)


if __name__ == "__main__":
    unittest.main()
