"""Regression checks for the real application coverage experiment."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('application_report', ROOT / 'scripts/application_report.py')
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)
from repo_stack_timeline.annual import verify_source


class ApplicationReportTests(unittest.TestCase):
    def test_real_missingness_and_comparison(self):
        data = report.build()
        rows = data['application_study']['snapshots']
        ether = [r for r in rows if r['repository'] == 'ether/etherpad']
        self.assertEqual([r['year'] for r in ether if r['status'] == 'missing_manifest'], [2019, 2021, 2022, 2023])
        self.assertEqual(sum(r['status'] == 'observed' for r in rows), 10)
        # Missing years must not become observed zero sets or comparable pairs.
        npm = [s for s in data['application_study']['summaries'] if s['ecosystem'] == 'npm' and s['mode'] == 'available']
        self.assertEqual([s['paired'] for s in npm], [None, 1, 1, 1, 1, 1, 2])
        self.assertEqual([r['members'] for r in data['comparison'] if r['stratum'] == 'library'], [4]*7)
        node = [r for r in rows if r['repository'] == 'node-red/node-red']
        self.assertEqual((len(node[0]['names']), len(node[-1]['names'])), (46, 56))

    def test_tampered_real_source_rejected(self):
        root = ROOT / 'examples/applications'
        cohort = json.loads((root / 'cohort.json').read_text())
        source = json.loads((root / 'sources/node-red--node-red.json').read_text())
        source = copy.deepcopy(source)
        source['snapshots'][0]['files'][0]['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'digest mismatch'):
            verify_source(source, cohort['repositories'][0], cohort)

    def test_fresh_cli_and_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / 'report'
            cmd = [sys.executable, str(ROOT / 'scripts/application_report.py'), '--output', str(destination)]
            first = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            for name, raw in report.artifacts().items():
                self.assertEqual((destination / name).read_bytes(), raw)
            page = (destination / 'index.html').read_text()
            self.assertIn('<table>', page)
            self.assertIn('href="https://github.com/node-red/node-red/blob/', page)
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)


if __name__ == '__main__':
    unittest.main()
