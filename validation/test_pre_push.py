"""Only exact outgoing commits may pass the local publication preflight."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from pre_push import check_push, revisions

A, B, ZERO = 'a'*40, 'b'*40, '0'*40


class PrePushTest(unittest.TestCase):
    def test_outgoing_sha_not_worktree_head(self):
        runner = Mock(return_value=SimpleNamespace(returncode=0))
        check_push(f'refs/heads/work {A} refs/heads/work {B}\n', runner)
        command = runner.call_args.args[0]
        self.assertEqual(command[command.index('--revision')+1], A)
        self.assertNotIn('HEAD', command)

    def test_failure_blocks_push(self):
        with self.assertRaises(RuntimeError):
            check_push(f'HEAD {A} refs/heads/work {B}',
                Mock(return_value=SimpleNamespace(returncode=1)))

    def test_deletion_needs_no_build(self):
        runner = Mock()
        check_push(f'(delete) {ZERO} refs/heads/work {A}', runner)
        runner.assert_not_called()

    def test_duplicate_commit_runs_once(self):
        self.assertEqual(revisions(f'HEAD {A} refs/heads/a {B}\nHEAD {A} refs/heads/b {ZERO}'), [A])

    def test_bad_ref_input_rejected(self):
        for text in ('HEAD --help refs/heads/a '+ZERO, 'short',
                     f'HEAD {A} refs/heads/a no-hash'):
            with self.assertRaises(ValueError):
                revisions(text)

    def test_two_distinct_commits_both_checked(self):
        runner = Mock(return_value=SimpleNamespace(returncode=0))
        check_push(f'HEAD {A} refs/heads/a {ZERO}\nHEAD {B} refs/heads/b {ZERO}', runner)
        self.assertEqual(runner.call_count, 2)


if __name__ == '__main__':
    unittest.main()
