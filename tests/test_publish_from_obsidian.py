import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublishWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.remote = self.root / 'remote.git'
        subprocess.run(['git', 'init', '--bare', '-q', str(self.remote)], check=True)
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(self.repo)], check=True)
        self.git('config', 'user.name', 'Test User')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('remote', 'add', 'origin', str(self.remote))
        (self.repo / 'scripts').mkdir()
        shutil.copy2(ROOT / 'scripts/publish_from_obsidian.py', self.repo / 'scripts')
        (self.repo / 'scripts/build_site.py').write_text('import sys\nassert sys.argv[1] in ("preview", "publish")\n')
        (self.repo / 'article.md').write_text('original')
        self.git('add', '.')
        self.git('commit', '-qm', 'base')
        self.git('push', '-q', '-u', 'origin', 'main')

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.repo, check=True, capture_output=True, text=True).stdout

    def run_workflow(self, *args):
        return subprocess.run(['python3', 'scripts/publish_from_obsidian.py', *args], cwd=self.repo,
                              capture_output=True, text=True, env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'})

    def test_confirmed_change_is_committed_and_pushed(self):
        (self.repo / 'article.md').write_text('updated')
        result = self.run_workflow('prepare')
        self.assertEqual(result.returncode, 0, result.stderr)
        snapshot = json.loads(result.stdout)
        self.assertIn('article.md', snapshot['status'])
        result = self.run_workflow('publish', snapshot['fingerprint'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git('status', '--porcelain'), '')
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(),
                         subprocess.check_output(['git', '--git-dir', str(self.remote), 'rev-parse', 'refs/heads/main'], text=True).strip())

    def test_changed_after_confirmation_is_not_committed(self):
        article = self.repo / 'article.md'
        article.write_text('first')
        result = self.run_workflow('prepare')
        snapshot = json.loads(result.stdout)
        before = self.git('rev-parse', 'HEAD')
        article.write_text('second')
        result = self.run_workflow('publish', snapshot['fingerprint'])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('文件发生了变化', result.stderr)
        self.assertEqual(self.git('rev-parse', 'HEAD'), before)
        self.assertEqual(article.read_text(), 'second')

    def test_existing_staged_changes_are_not_touched(self):
        (self.repo / 'article.md').write_text('staged')
        self.git('add', 'article.md')
        result = self.run_workflow('prepare')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('暂存区已有文件', result.stderr)
        self.assertIn('article.md', self.git('diff', '--cached', '--name-only'))


if __name__ == '__main__':
    unittest.main()
