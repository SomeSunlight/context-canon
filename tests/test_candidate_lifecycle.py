from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
import warnings
from pathlib import Path, PureWindowsPath
from unittest.mock import patch

from contextcanon.candidate_store import candidate_path, store_candidate
from contextcanon.compiler import Compiler
from contextcanon.git_transport import _clone_location, candidate_provenance_path, fetch_git_candidate
from contextcanon.gitignore import TRANSIENT_STORE_RULES, ensure_candidate_gitignore
from contextcanon.onboarding_workspace import GITIGNORE_START, ensure_onboarding_gitignore
from contextcanon.outputs import check_outputs, write_outputs
from contextcanon.package import artifact_files, compiled_package, load_package
from contextcanon.parser import ContextCanonError
from contextcanon.path_budget import WINDOWS_PATH_BUDGET, WINDOWS_PATH_LIMIT, _length, preflight_paths
from contextcanon.sources import accept_parent_candidate, accept_source_candidate, review_parent_candidate, review_source_candidate
from tests import test_git_transport as git_fixtures
from tests import test_parent_acceptance as parent_fixtures

PARENT_TEMPLATE = parent_fixtures.PARENT_TEMPLATE

DEEP = 'CONTEXT/references/c4c94726-3cc7-4df6-b779-72bbf9c06f40/nodes/library/development-workflow/docs/change-workflow.md'


class CandidateLifecycleTests(unittest.TestCase):
    def temporary(self):
        value = tempfile.TemporaryDirectory()
        self.addCleanup(value.cleanup)
        return Path(value.name)

    def parent_case(self):
        repo, parent, child, old = parent_fixtures.ParentAcceptanceTests().make_case()
        self.addCleanup(shutil.rmtree, repo, True)
        # Exercise canonical imports, not only the compatibility carrier.
        source = child / 'CONTEXT.src.md'
        source.write_text(source.read_text(encoding="utf-8").replace('## Parent', '## Context Imports').replace('ctx:parent', 'ctx:source').replace('— `1.0.0`', '— `1.0.0` — `relationship=parent`'), encoding="utf-8")
        (parent / 'CONTEXT.src.md').write_text(PARENT_TEMPLATE.format(version='2.0.0', statement='Reviewed v2.'), encoding="utf-8")
        _, receipt = review_parent_candidate(child)
        raw = json.loads(receipt.read_text(encoding="utf-8"))
        candidate = child / raw['candidate_path']
        return repo, parent, child, old, receipt, candidate

    def test_parent_accept_cleans_only_matching_scratch_and_builds_offline(self):
        repo, parent, child, old, receipt, candidate = self.parent_case()
        new = load_package(candidate)
        self.assertEqual(len(candidate.name), 16)
        # A second independently frozen candidate and receipt must survive.
        (parent / 'CONTEXT.src.md').write_text(PARENT_TEMPLATE.format(version='3.0.0', statement='Unreviewed v3.'), encoding="utf-8")
        other_compiled = Compiler(repo).compile(parent)
        other = store_candidate(child, 'parent-candidates', compiled_package(other_compiled), artifact_files(other_compiled))
        other_receipt = receipt.with_name('another-parent.json')
        other_receipt.write_text('unrelated receipt', encoding="utf-8")
        shutil.rmtree(parent)
        accepted = accept_parent_candidate(child)
        self.assertEqual(accepted.package_digest, new.package_digest)
        self.assertFalse(candidate.exists())
        self.assertFalse(receipt.exists())
        self.assertTrue(other.is_dir())
        self.assertEqual(other_receipt.read_text(encoding="utf-8"), 'unrelated receipt')
        self.assertTrue((child / '.context/sources' / old.package_digest).is_dir())
        self.assertTrue((child / '.context/sources' / new.package_digest).is_dir())
        shutil.rmtree(child / '.context/parent-candidates')
        shutil.rmtree(child / '.context/parent-reviews')
        compiled = Compiler(repo).compile(child)
        self.assertEqual(compiled.inherited_rules[0].statement, 'Reviewed v2.')
        write_outputs(compiled)
        self.assertEqual(check_outputs(Compiler(repo).compile(child)), [])

    def test_legacy_full_digest_parent_candidate_is_recovered_and_cleaned(self):
        _, _, child, _, receipt, short = self.parent_case()
        digest = load_package(short).package_digest
        legacy = short.with_name(digest)
        short.rename(legacy)
        raw = json.loads(receipt.read_text(encoding="utf-8"))
        raw['candidate_path'] = legacy.relative_to(child).as_posix()
        receipt.write_text(json.dumps(raw), encoding="utf-8")
        self.assertEqual(accept_parent_candidate(child).package_digest, digest)
        self.assertFalse(legacy.exists())
        self.assertFalse(receipt.exists())

    def test_failed_parent_pin_and_stale_review_keep_exact_scratch(self):
        repo, _, child, old, receipt, candidate = self.parent_case()
        before = (child / 'CONTEXT.src.md').read_bytes()
        with patch('contextcanon.sources._write_parent_pin', side_effect=OSError('pin failure')):
            with self.assertRaisesRegex(OSError, 'pin failure'):
                accept_parent_candidate(child)
        self.assertTrue(candidate.is_dir())
        self.assertTrue(receipt.is_file())
        self.assertEqual((child / 'CONTEXT.src.md').read_bytes(), before)
        self.assertEqual(Compiler(repo).compile(child).parent_package.package_digest, old.package_digest)
        (child / 'CONTEXT.src.md').write_bytes(before + b'\n<!-- edited -->\n')
        with self.assertRaisesRegex(ContextCanonError, 'changed after Parent review'):
            accept_parent_candidate(child)
        self.assertTrue(candidate.is_dir())
        self.assertTrue(receipt.is_file())

    def test_windows_acceptance_preflight_preserves_review_and_old_pin(self):
        repo, _, child, old, receipt, candidate = self.parent_case()
        long_child = repo / ('Project Node ' * 12)
        child.rename(long_child)
        receipt = long_child / receipt.relative_to(child)
        candidate = long_child / candidate.relative_to(child)
        before = (long_child / 'CONTEXT.src.md').read_bytes()
        with patch('contextcanon.path_budget._windows', return_value=True), patch.dict('os.environ', {}, clear=True):
            with self.assertRaisesRegex(ContextCanonError, 'accepted immutable package installation'):
                accept_parent_candidate(long_child)
        self.assertEqual((long_child / 'CONTEXT.src.md').read_bytes(), before)
        self.assertTrue(receipt.is_file())
        self.assertTrue(candidate.is_dir())
        self.assertEqual(Compiler(repo).compile(long_child).parent_package.package_digest, old.package_digest)

    def test_reference_success_and_failure_preserve_the_correct_transaction(self):
        helper = git_fixtures.GitTransportTests()
        provider, old, new = helper.make_provider()
        consumer = helper.make_consumer(provider, old)
        self.addCleanup(shutil.rmtree, provider, True)
        self.addCleanup(shutil.rmtree, consumer, True)
        source = consumer / 'CONTEXT.src.md'
        source.write_text(source.read_text(encoding="utf-8").replace('— `1.0.0`', '— `1.0.0` — `relationship=reference`'), encoding="utf-8")
        package, candidate = fetch_git_candidate(consumer, 'node-python')
        _, receipt = review_source_candidate(consumer, 'node-python', candidate)
        sidecar = candidate_provenance_path(consumer, package.package_digest)
        other = candidate.parent / 'unrelated'
        other.mkdir()
        (other / 'keep').write_text('other candidate', encoding="utf-8")
        other_sidecar = candidate.parent / 'unrelated.git.json'
        other_sidecar.write_text('other provenance', encoding="utf-8")
        other_receipt = receipt.with_name('unrelated.json')
        other_receipt.write_text('other receipt', encoding="utf-8")
        before = source.read_bytes()
        with patch('contextcanon.sources._write_source_pin', side_effect=OSError('pin failure')):
            with self.assertRaisesRegex(OSError, 'pin failure'):
                accept_source_candidate(consumer, 'node-python', candidate)
        self.assertEqual(source.read_bytes(), before)
        for path in (candidate, receipt, sidecar):
            self.assertTrue(path.exists(), path)
        shutil.rmtree(provider)
        accepted = accept_source_candidate(consumer, 'node-python', candidate)
        self.assertEqual(accepted.package_digest, new.package_digest)
        for path in (candidate, receipt, sidecar):
            self.assertFalse(path.exists(), path)
        for path in (other, other_receipt, other_sidecar):
            self.assertTrue(path.exists(), path)
        compiled = Compiler(consumer).compile(consumer)
        self.assertEqual(compiled.inherited_rules, [])
        write_outputs(compiled)
        self.assertEqual(check_outputs(Compiler(consumer).compile(consumer)), [])
        self.assertTrue((consumer / '.context/sources' / old.package_digest).exists())
        self.assertTrue((consumer / '.context/sources' / new.package_digest).exists())

    def test_explicit_external_candidate_package_is_never_deleted(self):
        repo, parent, child, _, receipt, scratch = self.parent_case()
        write_outputs(Compiler(repo).compile(parent))
        _, source_receipt = review_source_candidate(child, 'node-parent', parent)
        accept_source_candidate(child, 'node-parent', parent)
        self.assertTrue(parent.is_dir())
        self.assertFalse(source_receipt.exists())
        # That acceptance did not consume the separate Parent-review transaction.
        self.assertTrue(receipt.exists())
        self.assertTrue(scratch.exists())

    def test_legacy_source_candidate_and_provenance_are_cleaned_after_accept(self):
        helper = git_fixtures.GitTransportTests()
        provider, old, _ = helper.make_provider()
        consumer = helper.make_consumer(provider, old)
        self.addCleanup(shutil.rmtree, provider, True)
        self.addCleanup(shutil.rmtree, consumer, True)
        package, short = fetch_git_candidate(consumer, 'node-python')
        legacy = short.with_name(package.package_digest)
        short.rename(legacy)
        _, receipt = review_source_candidate(consumer, 'node-python', legacy)
        accept_source_candidate(consumer, 'node-python', legacy)
        self.assertFalse(legacy.exists())
        self.assertFalse(receipt.exists())
        self.assertFalse(candidate_provenance_path(consumer, package.package_digest).exists())

    def test_cleanup_failure_reports_successful_acceptance_and_keeps_diagnostics(self):
        repo, _, child, _, receipt, candidate = self.parent_case()
        expected = load_package(candidate).package_digest
        with patch('contextcanon.candidate_store.shutil.rmtree', side_effect=PermissionError('scanner lock')):
            with self.assertWarnsRegex(RuntimeWarning, 'Package accepted, but'):
                accepted = accept_parent_candidate(child)
        self.assertEqual(accepted.package_digest, expected)
        self.assertEqual(Compiler(repo).compile(child).parent_package.package_digest, expected)
        self.assertTrue(candidate.is_dir())
        self.assertTrue(receipt.is_file())

    def test_real_prefix_collision_extends_token_and_verifies_full_digest(self):
        repo = self.temporary()
        (repo / '.git').mkdir()
        source = repo / 'CONTEXT.src.md'
        seen = {}
        collision = None
        for index in range(40):
            source.write_text(PARENT_TEMPLATE.format(version=f'1.0.{index}', statement=f'Policy {index}.'), encoding="utf-8")
            compiled = Compiler(repo).compile(repo)
            token = compiled.package_digest[:1]
            if token in seen:
                collision = (seen[token], compiled)
                break
            seen[token] = compiled
        self.assertIsNotNone(collision)
        first, second = collision
        with patch('contextcanon.candidate_store.TOKEN_LENGTHS', (1, 2, 64)):
            a = store_candidate(repo, 'candidates', compiled_package(first), artifact_files(first))
            b = store_candidate(repo, 'candidates', compiled_package(second), artifact_files(second))
            self.assertEqual(len(a.name), 1)
            self.assertEqual(len(b.name), 2)
            self.assertNotEqual(a, b)
            self.assertEqual(load_package(a).package_digest, first.package_digest)
            self.assertEqual(load_package(b).package_digest, second.package_digest)
            self.assertEqual(candidate_path(repo, 'candidates', second.package_digest), b)
            self.assertEqual(store_candidate(repo, 'candidates', compiled_package(second), artifact_files(second)), b)
            (b / 'CONTEXT.md').write_text('tampered', encoding="utf-8")
            with self.assertRaises(ContextCanonError):
                candidate_path(repo, 'candidates', second.package_digest)

    def test_tampered_parent_candidate_cannot_be_accepted_or_cleaned(self):
        _, _, child, _, receipt, candidate = self.parent_case()
        (candidate / 'CONTEXT.md').write_text('tampered', encoding="utf-8")
        with self.assertRaises(ContextCanonError):
            accept_parent_candidate(child)
        self.assertTrue(candidate.is_dir())
        self.assertTrue(receipt.is_file())


class WindowsPathBudgetTests(unittest.TestCase):
    def test_realistic_windows_prefix_and_deep_workflow_diagnostic(self):
        root = PureWindowsPath('C:/Users/Owner/Corporate Projects/Knowledge Platform/Project One')
        store = root / '.context/parent-candidates' / ('a' * 64)
        self.assertLess(_length(root / 'CONTEXT.md'), WINDOWS_PATH_BUDGET)
        self.assertGreaterEqual(_length(store / DEEP), WINDOWS_PATH_LIMIT)
        with patch('contextcanon.path_budget._windows', return_value=True), patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ContextCanonError) as caught:
                preflight_paths(store, ['CONTEXT.md', DEEP], action='Parent review', node_root=root)
        message = str(caught.exception)
        for expected in (str(store / DEEP), str(_length(store / DEEP)), 'Parent review', 'ContextCanon-owned', 'tool-dependent', 'partial success', 'core.longpaths true', 'long-path support'):
            self.assertIn(expected, message)
        self.assertIn('exceeds the Node/project root contribution', message)

    def test_long_user_node_and_unc_names_are_preserved(self):
        for root in (PureWindowsPath('C:/Projects') / ('Long Project Name ' * 8), PureWindowsPath('//company-server/Engineering/Context Library') / ('Node Name ' * 10)):
            with self.subTest(root=root), patch('contextcanon.path_budget._windows', return_value=True), patch.dict('os.environ', {}, clear=True):
                with self.assertRaises(ContextCanonError) as caught:
                    preflight_paths(root, [DEEP], action='Official Context output publication')
                self.assertIn(str(root / DEEP), str(caught.exception))

    def test_unicode_budget_boundary_and_explicit_long_path_opt_in(self):
        root = PureWindowsPath('C:/P')
        def relative(length):
            return 'x' * (length - _length(root) - 1)

        with patch('contextcanon.path_budget._windows', return_value=True), patch.dict('os.environ', {}, clear=True):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                preflight_paths(root, [relative(239)], action='test')
                self.assertEqual(caught, [])
            for length in (240, 251, 259):
                with self.subTest(length=length), self.assertWarnsRegex(RuntimeWarning, f'{length} characters'):
                    preflight_paths(root, [relative(length)], action='test')
            # One non-BMP character occupies two UTF-16 units.
            with self.assertWarnsRegex(RuntimeWarning, '240 characters'):
                preflight_paths(root, [relative(238) + '\U0001f4da'], action='test')
            with self.assertRaises(ContextCanonError):
                preflight_paths(root, [relative(260)], action='test')
            with self.assertRaises(ContextCanonError):
                preflight_paths(root, [relative(258) + '\U0001f4da'], action='test')
            with patch.dict('os.environ', {'CONTEXTCANON_ALLOW_LONG_PATHS': '1'}):
                with self.assertWarnsRegex(RuntimeWarning, 'tool-dependent'):
                    preflight_paths(root, [relative(260)], action='test')
        with patch('contextcanon.path_budget._windows', return_value=False):
            with warnings.catch_warnings(record=True) as caught:
                preflight_paths(root, [DEEP * 5], action='unchanged non-Windows behavior')
                self.assertEqual(caught, [])

    def test_251_unit_parent_acceptance_warns_publishes_and_builds_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            # Match preflight's resolved destination, including Windows temp
            # directory aliases, before sizing the exact 251-unit fixture.
            repo = Path(directory).resolve()
            (repo / '.git').mkdir()
            resource_rel = 'nodes/library/development-workflow/docs/change-workflow.md'
            resource = repo / resource_rel
            resource.parent.mkdir(parents=True)
            resource.write_text('# Workflow\n', encoding='utf-8')
            source = repo / 'CONTEXT.src.md'
            parent_text = PARENT_TEMPLATE.replace('node-parent', 'c4c94726-3cc7-4df6-b779-72bbf9c06f40') + f'''
## Topics

### Workflow
<!-- ctx:topic id="WORKFLOW" -->
When developing:

Required:
- Resource: `{resource_rel}`
'''
            source.write_text(parent_text.format(version='1.0.0', statement='Old policy.'), encoding='utf-8')
            old = Compiler(repo).compile(repo)
            accepted_rel = Path('.context/sources') / old.package_digest / DEEP
            name_length = 251 - _length(repo / accepted_rel) - 1
            self.assertGreater(name_length, 0)
            child = repo / ('P' * name_length)
            for rel, content in artifact_files(old).items():
                path = child / '.context/sources' / old.package_digest / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            (child / 'CONTEXT.src.md').write_text(f'''# Child
<!-- ctx:node id="child" name="Child" version="1.0.0" -->

## Context Imports

- [{old.metadata.name}](..) — `1.0.0` — `relationship=parent`
  <!-- ctx:source id="{old.metadata.id}" version="1.0.0" normalized-digest="{old.normalized_digest}" package-digest="{old.package_digest}" -->
''', encoding='utf-8')
            source.write_text(parent_text.format(version='2.0.0', statement='Reviewed policy.'), encoding='utf-8')
            with patch('contextcanon.path_budget._windows', return_value=True), patch.dict('os.environ', {}, clear=True):
                _, receipt = review_parent_candidate(child)
                raw = json.loads(receipt.read_text(encoding='utf-8'))
                candidate = child / raw['candidate_path']
                with self.assertWarnsRegex(RuntimeWarning, '251 characters') as caught:
                    accepted = accept_parent_candidate(child)
                self.assertIn('C:\\Projektverzeichnis', str(caught.warning))
                self.assertIn('at least 12 characters', str(caught.warning))
                self.assertIn('Continuing with a warning', str(caught.warning))
                destination = child / '.context/sources' / accepted.package_digest / DEEP
                self.assertEqual(_length(destination), 251)
                self.assertEqual(destination.read_bytes(), b'# Workflow\n')
                self.assertFalse(candidate.exists())
                self.assertFalse(receipt.exists())
                self.assertTrue((child / '.context/sources' / old.package_digest).is_dir())
                source.unlink()  # Only the exact accepted package supplies Parent Context.
                compiled = Compiler(repo).compile(child)
                self.assertEqual(compiled.inherited_rules[0].statement, 'Reviewed policy.')
                write_outputs(compiled)
                self.assertEqual(check_outputs(Compiler(repo).compile(child)), [])

    def test_short_candidate_passes_where_old_digest_path_exceeded_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / '.git').mkdir()
            resource = repo / 'nodes/library/development-workflow/docs/change-workflow.md'
            resource.parent.mkdir(parents=True)
            resource.write_text('# Workflow\n', encoding="utf-8")
            (repo / 'CONTEXT.src.md').write_text('''# Workflow
<!-- ctx:node id="c4c94726-3cc7-4df6-b779-72bbf9c06f40" name="Workflow" version="1.0.0" -->

## Topics

### Workflow
<!-- ctx:topic id="WORKFLOW" -->
When developing:

Required:
- Resource: `nodes/library/development-workflow/docs/change-workflow.md`
''', encoding="utf-8")
            compiled = Compiler(repo).compile(repo)
            package = compiled_package(compiled)
            internal_old = Path('.context/parent-candidates') / package.package_digest / DEEP
            name_length = max(1, WINDOWS_PATH_BUDGET - _length(repo / internal_old) + 20)
            consumer = repo / ('P' * name_length)
            self.assertGreaterEqual(_length(consumer / internal_old), WINDOWS_PATH_BUDGET)
            with patch('contextcanon.path_budget._windows', return_value=True), patch.dict('os.environ', {}, clear=True):
                candidate = store_candidate(consumer, 'parent-candidates', package, artifact_files(compiled))
                self.assertEqual(load_package(candidate).package_digest, package.package_digest)
                self.assertLess(_length(candidate / DEEP), WINDOWS_PATH_BUDGET)
                # Durable stores keep full digests; headroom pressure alone must
                # not prevent an existing project from accepting an update.
                from contextcanon.sources import _install_package
                with self.assertWarnsRegex(RuntimeWarning, 'accepted immutable package installation'):
                    _install_package(consumer, candidate, package)
                self.assertEqual(load_package(consumer / '.context/sources' / package.package_digest).package_digest, package.package_digest)
                self.assertTrue(candidate.is_dir())

    def test_failed_output_preflight_does_not_delete_or_write_any_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / '.git').mkdir()
            (repo / 'CONTEXT.src.md').write_text(PARENT_TEMPLATE.format(version='1.0.0', statement='Policy.'), encoding="utf-8")
            compiled = Compiler(repo).compile(repo)
            stale = repo / 'CONTEXT/stale.md'
            stale.parent.mkdir()
            stale.write_text('keep before successful preflight', encoding="utf-8")
            compiled.resources[DEEP + ('x' * 150)] = b'resource'
            with patch('contextcanon.path_budget._windows', return_value=True), patch.dict('os.environ', {}, clear=True):
                with self.assertRaisesRegex(ContextCanonError, 'Official Context output publication'):
                    write_outputs(compiled)
            self.assertEqual(stale.read_text(encoding="utf-8"), 'keep before successful preflight')
            self.assertFalse((repo / 'CONTEXT.md').exists())


class GitCheckoutPreflightTests(unittest.TestCase):
    def test_git_checkout_is_preflighted_before_package_files_are_created(self):
        helper = git_fixtures.GitTransportTests()
        provider, _, _ = helper.make_provider()
        self.addCleanup(shutil.rmtree, provider, True)
        unicode_name = 'Übersicht 📚' + ('x' * 60) + '.md'
        (provider / unicode_name).write_text('Unicode path', encoding='utf-8')
        helper.git(provider, 'add', unicode_name)
        helper.git(provider, 'commit', '-m', 'Publish Unicode path')
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory) / ('Checkout' * 22)
            with patch('contextcanon.path_budget._windows', return_value=True), patch.dict('os.environ', {}, clear=True):
                with self.assertRaisesRegex(ContextCanonError, 'Git Source candidate checkout') as caught:
                    _clone_location(str(provider), checkout, 'main')
            self.assertIn(unicode_name, str(caught.exception))
            self.assertTrue((checkout / '.git').exists())
            self.assertFalse((checkout / 'nodes').exists())
            first = helper.git(provider, 'log', '--reverse', '--format=%H').stdout.splitlines()[0]
            exact_checkout = Path(directory) / 'exact'
            self.assertEqual(_clone_location(str(provider), exact_checkout, first), first)
            self.assertEqual(load_package(exact_checkout / 'nodes/library/python-development').metadata.version, '1.0.0')


class GitIgnoreLifecycleTests(unittest.TestCase):
    def test_recursive_migration_two_nodes_and_ordinary_git_add(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            old = '# >>> ContextCanon onboarding (managed)\n/contextcanon-onboarding/\n/.context/onboarding/*\n!/.context/onboarding/inventory-state.json\n!/.context/onboarding/inventory-acceptance.json\n# <<< ContextCanon onboarding (managed)\n'
            (repo / '.gitignore').write_text('project-temp/\n\n' + old, encoding="utf-8")
            ensure_onboarding_gitignore(repo, repo / 'contextcanon-onboarding')
            before = (repo / '.gitignore').read_bytes()
            ensure_onboarding_gitignore(repo, repo / 'contextcanon-onboarding')
            self.assertEqual((repo / '.gitignore').read_bytes(), before)
            self.assertEqual(before.decode().count(GITIGNORE_START), 1)
            self.assertNotIn('\n/.context/onboarding/', before.decode())
            visible = {'.gitignore'}
            hidden = set()
            for local in (Path('.'), Path('P1'), Path('projects/P2')):
                visible.update(str(local / '.context/onboarding' / name) for name in ('inventory-state.json', 'inventory-acceptance.json'))
                visible.add(str(local / '.context/sources' / ('a' * 64) / 'CONTEXT.md'))
                hidden.update(str(local / '.context' / store / 'candidate' / DEEP) for store in ('candidates', 'parent-candidates', 'source-reviews', 'parent-reviews'))
                hidden.add(str(local / 'contextcanon-onboarding/PLAN.md'))
                hidden.add(str(local / '.context/onboarding/snapshot/evidence/docs/deep.md'))
            for rel in visible | hidden:
                target = repo / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                if rel != '.gitignore':
                    target.write_text('test', encoding="utf-8")
            for rel in hidden:
                result = subprocess.run(['git', '-C', str(repo), 'check-ignore', rel], capture_output=True)
                self.assertEqual(result.returncode, 0, rel)
            for rel in visible:
                result = subprocess.run(['git', '-C', str(repo), 'check-ignore', rel], capture_output=True)
                self.assertEqual(result.returncode, 1, rel)
            subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True)
            staged = subprocess.check_output(['git', '-C', str(repo), 'diff', '--cached', '--name-only'], text=True).splitlines()
            self.assertEqual(set(staged), {Path(rel).as_posix() for rel in visible})

    def test_existing_repository_review_installs_ignore_rules_and_keeps_packages_visible(self):
        repo, _, child, _, receipt, candidate = CandidateLifecycleTests().parent_case()
        self.addCleanup(shutil.rmtree, repo, True)
        # make_case uses only a repository marker; turn it into a real Git repo.
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        before = (repo / '.gitignore').read_bytes()
        ensure_candidate_gitignore(child)
        self.assertEqual(before, (repo / '.gitignore').read_bytes())
        for rule in TRANSIENT_STORE_RULES:
            self.assertIn(rule, before.decode())
        for path in (receipt, candidate / 'CONTEXT.md'):
            result = subprocess.run(['git', '-C', str(repo), 'check-ignore', str(path)], capture_output=True)
            self.assertEqual(result.returncode, 0, path)
