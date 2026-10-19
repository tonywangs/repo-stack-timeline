#!/usr/bin/env python3
"""Focused offline annual-study checks; optional preinstalled Chromium integration."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify import publication_check


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', action='store_true')
    parser.add_argument('--record', action='store_true')
    args = parser.parse_args()
    env = dict(os.environ, PYTHONPATH=str(ROOT/'src') + os.pathsep + str(ROOT/'tests'))
    evidence = dict(schema='annual-verification/1', started_at=datetime.now(timezone.utc).isoformat(), steps=[], browser='not_run')
    def run(label, command, expect=0):
        start = time.monotonic()
        proc = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=300)
        print(label + ': ' + str(proc.returncode), flush=True)
        print(proc.stdout + proc.stderr, end='', flush=True)
        evidence['steps'].append(dict(label=label, command=command, exit_code=proc.returncode, expected_exit_code=expect, elapsed_seconds=time.monotonic()-start))
        if proc.returncode != expect:
            raise RuntimeError(label + ' failed')
    offline = [sys.executable, 'scripts/offline_exec.py', sys.executable]
    run('Annual coverage/oracle/provenance plus shared parser and installation checks',
        offline + ['-m', 'unittest', 'test_annual', 'test_extract', 'test_install', '-v'])
    run('Frozen artifact reproduction', offline + ['scripts/annual_report.py', '--check'])
    with tempfile.TemporaryDirectory(prefix='annual-verify-') as directory:
        destination = Path(directory)/'report'
        run('Fresh one-command offline launch', offline + ['scripts/annual_report.py', '--output', str(destination)])
        for file in (ROOT/'results/annual').iterdir():
            if file.is_file() and (destination/file.name).read_bytes() != file.read_bytes():
                raise AssertionError('fresh report differs: ' + file.name)
        # Existing destinations must fail before any output file can be replaced.
        run('Existing destination refusal', offline + ['scripts/annual_report.py', '--output', str(destination)], expect=1)
        if args.browser:
            run('Offline browser use case', ['node', 'tests/annual_browser.cjs', str(destination/'index.html')])
            evidence['browser'] = 'passed'
    evidence['publication_tree'] = publication_check()
    paths = sorted([* (ROOT/'examples/annual').rglob('*.json'), * (ROOT/'results/annual').glob('*'),
        ROOT/'src/repo_stack_timeline/annual.py', ROOT/'src/repo_stack_timeline/annual_report.py',
        ROOT/'src/repo_stack_timeline/annual_viewer.html', ROOT/'scripts/acquire_annual.py',
        ROOT/'scripts/annual_report.py', ROOT/'scripts/verify_annual.py', ROOT/'tests/test_annual.py', ROOT/'tests/annual_browser.cjs'])
    evidence['sha256'] = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
    evidence['status'] = 'passed'
    if args.record:
        (ROOT/'results/annual-verification.json').write_text(json.dumps(evidence, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(status='passed', browser=evidence['browser'], publication_tree=evidence['publication_tree'])))

if __name__ == '__main__':
    main()
