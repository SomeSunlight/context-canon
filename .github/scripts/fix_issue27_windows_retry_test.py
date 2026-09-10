from pathlib import Path
import re

path = Path('tests/test_source_acceptance.py')
text = path.read_text(encoding='utf-8')
pattern = r'''    def test_package_publish_retries_transient_permission_error\(self\):\n.*?\n\n    def test_failed_atomic_pin_replace_preserves_old_source_and_old_build'''
replacement = '''    def test_package_publish_retries_transient_permission_error(self):
        _, v1, _ = self.make_provider("1.0.0", "Prefer explicit Python v1.")
        _, v2, candidate = self.make_provider("2.0.0", "Prefer explicit Python v2.")
        consumer = self.make_consumer(v1)

        package_destination = consumer / ".context" / "sources" / v2.package_digest
        real_replace = sources_module.os.replace
        attempts = {"package": 0}

        def flaky_replace(src, dst):
            if attempts["package"] == 0:
                attempts["package"] += 1
                raise PermissionError(13, "simulated transient Windows access denied")
            return real_replace(src, dst)

        with patch("contextcanon.sources.os.replace", side_effect=flaky_replace), patch(
            "contextcanon.sources.time.sleep", return_value=None
        ):
            package = sources_module.load_package(candidate)
            sources_module._install_package(consumer, candidate, package)

        self.assertEqual(attempts["package"], 1)
        self.assertTrue((package_destination / ".context/package.json").is_file())
        installed = sources_module.load_package(package_destination)
        self.assertEqual(installed.package_digest, v2.package_digest)

    def test_failed_atomic_pin_replace_preserves_old_source_and_old_build'''
updated, count = re.subn(pattern, lambda _match: replacement, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit(f'expected one Windows retry regression method, found {count}')
path.write_text(updated, encoding='utf-8')
