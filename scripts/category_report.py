#!/usr/bin/env python3
"""Reproduce the exploratory annual category appendix without network access."""
import argparse
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from repo_stack_timeline.annual import canonical
from repo_stack_timeline.categories import build, markdown


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--output', type=Path)
    args = parser.parse_args()
    data = build(ROOT / 'examples/annual')
    files = {'report.json': canonical(data), 'report.md': markdown(data).encode()}
    if args.check:
        for name, raw in files.items():
            if (ROOT / 'results/categories' / name).read_bytes() != raw:
                raise ValueError('category report mismatch: ' + name)
        print(f"Verified {len(data['rows'])} category observations and deterministic artifacts.")
    else:
        args.output.mkdir(parents=True, exist_ok=False)
        for name, raw in files.items():
            (args.output / name).write_bytes(raw)
        print(args.output / 'report.md')


if __name__ == '__main__':
    main()
