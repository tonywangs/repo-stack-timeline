#!/usr/bin/env python3
"""Reproduce the frozen 2019–2025 public cohort report, entirely offline."""
import argparse
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from repo_stack_timeline.annual import canonical, load_study
from repo_stack_timeline.annual_report import markdown, viewer


def artifacts():
    study = load_study(ROOT / 'examples/annual')
    md = markdown(study)
    files = {'report.json': canonical(study), 'report.md': md.encode(), 'index.html': viewer(study, md).encode()}
    files['SHA256SUMS'] = ''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n'
                               for name, data in sorted(files.items())).encode()
    return files


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output', type=Path, help='fresh destination directory')
    mode.add_argument('--check', action='store_true', help='compare frozen results byte-for-byte')
    args = p.parse_args()
    files = artifacts()
    if args.check:
        for name, data in files.items():
            if (ROOT / 'results/annual' / name).read_bytes() != data:
                raise ValueError('frozen report mismatch: ' + name)
        print('Verified 56 annual source observations and all deterministic report artifacts.')
    else:
        args.output.mkdir(parents=False, exist_ok=False)
        for name, data in files.items():
            (args.output / name).write_bytes(data)
        print('Open ' + str(args.output.resolve() / 'index.html'))

if __name__ == '__main__':
    main()
