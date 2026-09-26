from __future__ import annotations

import unittest

from contextcanon.entry import _windows_permission_error


class WindowsPermissionErrorTests(unittest.TestCase):
    def test_generic_errno13_does_not_claim_winerror5_or_scanner_lock(self) -> None:
        exc = PermissionError(13, "Permission denied", r"C:\project\P1\F1")

        message = _windows_permission_error(exc)

        self.assertIn("errno 13", message)
        self.assertIn(r"C:\project\P1\F1", message)
        self.assertIn("not being classified as the known transient WinError 5", message)
        self.assertNotIn("exclude the project directory from real-time scanning", message)

    def test_real_winerror5_keeps_scanner_guidance(self) -> None:
        exc = PermissionError(13, "Access is denied", r"C:\project\file.md")
        exc.winerror = 5

        message = _windows_permission_error(exc)

        self.assertIn("WinError 5 / access denied", message)
        self.assertIn("exclude the project directory from real-time scanning", message)


if __name__ == "__main__":
    unittest.main()
