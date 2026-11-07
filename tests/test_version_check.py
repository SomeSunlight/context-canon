from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from contextcanon.cli import main
from contextcanon.version import display_version, installed_git_origin, installed_git_provenance
from contextcanon.version_check import (
    InstallIdentity, VersionCheck, _github_coordinates, check_remote_version,
)


LOCAL_SHA = "a" * 40
REMOTE_SHA = "b" * 40


class InstalledVersionTests(unittest.TestCase):
    def _distribution(self, payload):
        dist = Mock()
        dist.read_text.return_value = payload
        return dist

    def test_git_url_distribution_resolves_immutable_sha(self):
        payload = json.dumps({
            "url": "https://github.com/SomeSunlight/context-canon.git",
            "vcs_info": {
                "vcs": "git", "requested_revision": "main", "commit_id": LOCAL_SHA,
            },
        })
        with patch("contextcanon.version.distribution", return_value=self._distribution(payload)):
            self.assertEqual(installed_git_origin(), (
                "https://github.com/SomeSunlight/context-canon.git", LOCAL_SHA, "main",
            ))
            self.assertEqual(installed_git_provenance(), "main@aaaaaaa")
            with patch("contextcanon.version._project_root", return_value=None):
                self.assertEqual(display_version(), "0.10.0 (main@aaaaaaa)")

    def test_pinned_sha_and_unlabelled_git(self):
        for revision, label in ((LOCAL_SHA, "detached"), (None, "git")):
            with self.subTest(revision=revision):
                info = {"vcs": "git", "commit_id": LOCAL_SHA}
                if revision:
                    info["requested_revision"] = revision
                with patch("contextcanon.version.distribution", return_value=self._distribution(
                    json.dumps({"url": "https://github.com/owner/repo.git", "vcs_info": info})
                )):
                    self.assertEqual(installed_git_provenance(), f"{label}@aaaaaaa")

    def test_invalid_or_non_git_metadata_is_ignored(self):
        cases = [None, "{bad", '{"vcs_info":{}}',
                 '{"url":"https://example.com/file.whl","archive_info":{}}',
                 json.dumps({"url": "https://github.com/owner/repo",
                             "vcs_info": {"vcs": "hg", "commit_id": LOCAL_SHA}}),
                 json.dumps({"url": "https://github.com/owner/repo",
                             "vcs_info": {"vcs": "git", "commit_id": "invalid"}})]
        for metadata in cases:
            with self.subTest(metadata=metadata):
                with patch("contextcanon.version.distribution", return_value=self._distribution(metadata)):
                    self.assertIsNone(installed_git_origin())

    def test_offline_version_does_not_call_network(self):
        with patch("contextcanon.version_check._read_json", side_effect=AssertionError("network")):
            with redirect_stdout(io.StringIO()) as output:
                with self.assertRaises(SystemExit) as ended:
                    main(["--version"])
                self.assertEqual(ended.exception.code, 0)
            self.assertIn("contextcanon 0.10.0", output.getvalue())


class RemoteVersionTests(unittest.TestCase):
    origin = InstallIdentity(
        "https://github.com/SomeSunlight/context-canon.git", LOCAL_SHA, "main"
    )

    def _check(self, remote=REMOTE_SHA, comparison="ahead", branch=None, source=None):
        with patch("contextcanon.version_check._identity", return_value=source or self.origin):
            def respond(url):
                if "/branches/" in url:
                    return {"commit": {"sha": remote}}
                if "/compare/" in url:
                    return {"status": comparison}
                return {"default_branch": "main"}
            with patch("contextcanon.version_check._read_json", side_effect=respond) as request:
                result = check_remote_version(branch=branch)
        return result, [c.args[0] for c in request.call_args_list]

    def test_same_commit_skips_compare(self):
        result, urls = self._check(remote=LOCAL_SHA)
        self.assertEqual(result.status, "up to date")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(len(urls), 1)

    def test_git_comparison_direction(self):
        for github, expected in [
            ("ahead", "behind"), ("behind", "ahead"),
            ("diverged", "diverged"), ("identical", "up to date"),
        ]:
            with self.subTest(github=github):
                result, urls = self._check(comparison=github)
                self.assertEqual(result.status, expected)
                self.assertIn("/compare/" + LOCAL_SHA + "..." + REMOTE_SHA, urls[-1])
                self.assertEqual(result.exit_code, 0 if expected == "up to date" else 1)

    def test_missing_branch_resolves_default(self):
        identity = InstallIdentity(self.origin.url, LOCAL_SHA, None)
        result, urls = self._check(source=identity)
        self.assertEqual(result.status, "behind")
        self.assertTrue(urls[0].endswith("/context-canon"))
        self.assertIn("/branches/main", urls[1])

    def test_explicit_branch_overrides_checkout(self):
        result, urls = self._check(branch="develop/topic")
        self.assertEqual(result.status, "behind")
        self.assertIn("/branches/develop%2Ftopic", urls[0])

    def test_network_failure_cannot_claim_current(self):
        with patch("contextcanon.version_check._identity", return_value=self.origin):
            with patch("contextcanon.version_check._read_json", side_effect=OSError("offline")):
                result = check_remote_version()
        self.assertEqual(result.status, "unknown")
        self.assertEqual(result.exit_code, 2)

    def test_unknown_origin_and_unsupported_hosts_do_not_call_network(self):
        for identity in [None, InstallIdentity("https://evil.example/repo", LOCAL_SHA, "main")]:
            with self.subTest(identity=identity):
                with patch("contextcanon.version_check._identity", return_value=identity):
                    with patch("contextcanon.version_check._read_json", side_effect=AssertionError("network")):
                        self.assertEqual(check_remote_version().status, "unknown")

    def test_remote_url_allowlist(self):
        self.assertEqual(_github_coordinates("git@github.com:owner/repo.git"), ("owner", "repo"))
        self.assertEqual(_github_coordinates("ssh://git@github.com/owner/repo.git"), ("owner", "repo"))
        self.assertIsNone(_github_coordinates("https://github.com.evil.example/owner/repo"))
        self.assertIsNone(_github_coordinates("https://example.com/owner/repo"))

    def test_cli_output_and_exit_code(self):
        result = VersionCheck("contextcanon 0.10.0 (main@aaaaaaa)", "main@bbbbbbb", "behind")
        with patch("contextcanon.version_check.check_remote_version", return_value=result):
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["version", "check"]), 1)
        self.assertIn("Installed: contextcanon 0.10.0", output.getvalue())
        self.assertIn("Status:    behind", output.getvalue())
