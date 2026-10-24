"""Check public measurements and conservative description classification."""
from pathlib import Path
import unittest
import subprocess
import sys
import tempfile
from repo_stack_timeline.categories import build, classify, description

ROOT = Path(__file__).resolve().parents[1]


class CategoryTests(unittest.TestCase):
    def test_unmatched_and_ambiguous_are_unknown(self):
        self.assertEqual(classify('a generic package'), 'unknown')
        self.assertEqual(classify('web framework and command-line toolkit'), 'unknown')
        self.assertEqual(classify('A framework for WEB applications'), 'web-framework')

    def test_static_metadata_only(self):
        self.assertEqual(description('setup.py', b'setup(description="web framework")'), 'web framework')
        for code in [b'setup(description=compute())', b'if True:\n setup(description="web framework")',
                     b'setup(description="a"); setup(description="b")']:
            self.assertIsNone(description('setup.py', code))
        self.assertIsNone(description('pyproject.toml', b'[project]\ndynamic=["description"]\n'))
        self.assertIsNone(description('setup.cfg', b'[metadata]\ndescription=file: README.md\n'))

    def test_launch_reproduces_artifacts_and_refuses_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'report'
            command = [sys.executable, str(ROOT / 'scripts/category_report.py'), '--output', str(output)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in ('report.md', 'report.json'):
                self.assertEqual((output / name).read_bytes(), (ROOT / 'results/categories' / name).read_bytes())
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)

    def test_real_annual_evidence_and_counts(self):
        data = build(ROOT / 'examples/annual')
        expected = {'pallets/flask': 'web-framework', 'expressjs/express': 'web-framework',
                    'koajs/koa': 'web-framework', 'pallets/click': 'command-line-toolkit',
                    'tj/commander.js': 'command-line-toolkit', 'chalk/chalk': 'terminal-styling',
                    'pallets/jinja': 'template-engine', 'pallets/itsdangerous': 'data-signing'}
        self.assertEqual(len(data['rows']), 56)
        self.assertEqual((data['comparable_pairs'], data['changed_pairs'], data['unknown_pairs']), (48, 0, 0))
        self.assertEqual(sum(r['stack_status'] != 'observed' for r in data['rows']), 6)
        for row in data['rows']:
            self.assertEqual(row['category'], expected[row['repository']])
            self.assertTrue(row['description'])
            self.assertTrue(row['source_url'].startswith('https://github.com/' + row['repository'] + '/blob/'))
            self.assertEqual(len(row['source_sha256']), 64)
        for year in data['years']:
            self.assertEqual(sum(s['members'] for s in data['summaries'] if s['year'] == year), 8)
        web = {s['year']: s for s in data['summaries'] if s['category'] == 'web-framework' and s['ecosystem'] == 'npm'}
        self.assertEqual(web[2019]['repository_name_pairs'], 55)
        self.assertEqual(web[2025]['repository_name_pairs'], 46)
        click = next(s for s in data['summaries'] if s['year'] == 2019 and s['category'] == 'command-line-toolkit' and s['ecosystem'] == 'python')
        self.assertEqual((click['stack_observed'], click['stack_unknown']), (0, 1))


if __name__ == '__main__':
    unittest.main()
