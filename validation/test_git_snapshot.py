"""Uncommitted fixes and ignored files must never repair a commit under test."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_git_snapshot import ROOT, export_snapshot


class SnapshotTest(unittest.TestCase):
    def setUp(self):
        folder = ROOT/'.build/git-snapshot-fixtures'
        folder.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=folder)
        self.root = Path(self.temp.name)
        self.run_git('init', '-q')
        (self.root/'input.txt').write_text('committed\n')
        self.commit()

    def tearDown(self):
        self.temp.cleanup()

    def run_git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root)

    def commit(self):
        self.run_git('add', '.')
        self.run_git('-c', 'user.name=fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')

    def test_worktree_repair_is_excluded(self):
        (self.root/'input.txt').write_text('uncommitted repair\n')
        (self.root/'local-only.txt').write_text('must not leak\n')
        out = self.root/'export'
        result = export_snapshot(self.root, 'HEAD', out)
        self.assertEqual((out/'input.txt').read_text(), 'committed\n')
        self.assertFalse((out/'local-only.txt').exists())
        self.assertEqual(result['verified_git_blobs'], 1)
        self.assertEqual(result['source_commit'], self.run_git('rev-parse', 'HEAD').decode().strip())

    def test_staged_repair_is_excluded(self):
        (self.root/'input.txt').write_text('staged repair\n')
        self.run_git('add', 'input.txt')
        out = self.root/'export'
        export_snapshot(self.root, 'HEAD', out)
        self.assertEqual((out/'input.txt').read_text(), 'committed\n')

    def test_symlink_is_rejected(self):
        (self.root/'link').symlink_to('input.txt'); self.commit()
        with self.assertRaises(ValueError):
            export_snapshot(self.root, 'HEAD', self.root/'export')

    def test_export_omission_is_rejected(self):
        (self.root/'.gitattributes').write_text('input.txt export-ignore\n'); self.commit()
        with self.assertRaises(ValueError):
            export_snapshot(self.root, 'HEAD', self.root/'export')

    def test_existing_destination_is_not_overwritten(self):
        out = self.root/'export'; out.mkdir()
        with self.assertRaises(FileExistsError):
            export_snapshot(self.root, 'HEAD', out)

    def test_revision_option_is_rejected(self):
        with self.assertRaises(ValueError):
            export_snapshot(self.root, '--help', self.root/'export')


if __name__ == '__main__':
    unittest.main()
