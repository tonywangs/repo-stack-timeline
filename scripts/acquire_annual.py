#!/usr/bin/env python3
"""Explicit public network acquisition; no credentials or upstream code execution.

Existing source records pin the lineage head; reacquisition never moves that head.
"""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from repo_stack_timeline.annual import canonical, git_hash, select_years


def git(cache, repo, *args):
    env = {'PATH': os.environ['PATH'], 'HOME': str(cache), 'LC_ALL': 'C',
           'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
           'GIT_TERMINAL_PROMPT': '0'}
    return subprocess.check_output(['git', '-c', 'credential.helper=',
        '--git-dir=' + str(repo), *args], env=env, timeout=600)


def acquire(cache, destination, cohort):
    cache.mkdir(parents=True, exist_ok=True)
    destination.mkdir(parents=True, exist_ok=True)
    for member in cohort['repositories']:
        name = member['repository']
        slug = name.replace('/', '--')
        repo = cache / slug
        url = f'https://github.com/{name}.git'
        old_path = destination / (slug + '.json')
        old = json.loads(old_path.read_text()) if old_path.exists() else None
        if not repo.exists():
            # Explicit clean environment prevents credential helpers/config rewrites.
            env = {'PATH': os.environ['PATH'], 'HOME': str(cache), 'LC_ALL': 'C',
                   'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
                   'GIT_TERMINAL_PROMPT': '0'}
            subprocess.run(['git', '-c', 'credential.helper=', 'clone', '--bare',
                '--single-branch', '--no-tags', url, str(repo)], env=env, check=True, timeout=600)
        if git(cache, repo, 'config', '--get', 'remote.origin.url').decode().strip() != url:
            raise ValueError('cache origin mismatch: ' + name)
        if git(cache, repo, 'rev-parse', '--is-shallow-repository').strip() != b'false':
            raise ValueError('full history required: ' + name)
        head = old['head'] if old else git(cache, repo, 'rev-parse', 'HEAD').decode().strip()
        try:
            git(cache, repo, 'cat-file', '-e', head + '^{commit}')
        except subprocess.CalledProcessError:
            git(cache, repo, 'fetch', '--no-tags', 'origin', head)
        history_raw = git(cache, repo, 'log', '--first-parent', '--format=%H %ct', head)
        history = [(h, int(t)) for h, t in (line.split() for line in history_raw.decode().splitlines())]
        selected = select_years(history, cohort['years'])
        records = []
        for year, commit in selected.items():
            if commit is None:
                records.append(dict(year=year, status='unavailable_history', commit=None))
                continue
            commit_raw = git(cache, repo, 'cat-file', 'commit', commit)
            tree = commit_raw.splitlines()[0].decode().split()[1]
            tree_raw = git(cache, repo, 'cat-file', 'tree', tree)
            files = []
            listing = git(cache, repo, 'ls-tree', '-z', commit)
            for entry in listing.split(b'\0'):
                if not entry:
                    continue
                meta, path = entry.split(b'\t', 1)
                mode, kind, blob = meta.decode().split()
                path = path.decode()
                if path not in ('package.json', 'pyproject.toml', 'setup.cfg', 'setup.py') and path.lower() not in ('license', 'license.txt', 'license.rst', 'license.md'):
                    continue
                if kind != 'blob':
                    raise ValueError('non-blob evidence: ' + path)
                raw = git(cache, repo, 'cat-file', 'blob', blob)
                if len(raw) > 1_048_576:
                    raise ValueError('source file exceeds 1 MiB')
                assert git_hash('blob', raw) == blob
                files.append(dict(path=path, mode=mode, blob=blob,
                    sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                    base64=base64.b64encode(raw).decode(),
                    url=f'https://github.com/{name}/blob/{commit}/{path}'))
            if not any(f['path'].lower().startswith('license') for f in files):
                raise ValueError('missing license evidence: ' + name)
            records.append(dict(year=year, status='acquired', commit=commit,
                committer_timestamp=dict(history)[commit],
                commit_base64=base64.b64encode(commit_raw).decode(), tree=tree,
                tree_base64=base64.b64encode(tree_raw).decode(), files=files))
        result = dict(schema='annual-sources/1', repository=name, ecosystem=member['ecosystem'],
            license=member['license'], acquisition_url=url, head=head,
            acquired_at=old['acquired_at'] if old else datetime.now(timezone.utc).isoformat(),
            default_branch_at_acquisition=old['default_branch_at_acquisition'] if old else git(cache, repo, 'symbolic-ref', 'HEAD').decode().strip(),
            cohort_sha256=hashlib.sha256(canonical(cohort)).hexdigest(),
            first_parent_history_count=len(history), first_parent_history_sha256=hashlib.sha256(history_raw).hexdigest(),
            snapshots=records)
        encoded = canonical(result)
        if old and encoded != canonical(old):
            raise ValueError('reacquisition differs from frozen evidence: ' + name)
        if len(encoded) > 10 * 1024 * 1024:
            raise ValueError('source shard exceeds publication limit')
        old_path.write_bytes(encoded)
        print(name, len(records), 'snapshots; frozen head', head, flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache', type=Path, required=True)
    p.add_argument('--sources', type=Path, default=ROOT / 'examples/annual/sources')
    args = p.parse_args()
    acquire(args.cache.resolve(), args.sources.resolve(), json.loads((ROOT / 'examples/annual/cohort.json').read_text()))

if __name__ == '__main__':
    main()
