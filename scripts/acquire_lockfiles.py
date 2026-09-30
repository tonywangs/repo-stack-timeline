#!/usr/bin/env python3
"""Explicit network acquisition of immutable npm/cli test data; never run by verification."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'dbe7d983d184fb00c85f7b34839a123057029c8b'
BASE = 'https://raw.githubusercontent.com/npm/cli/' + REVISION + '/'
NAMES = ['workspaces-simple-virtual', 'workspaces-conflicting-versions-virtual',
         'testing-peer-deps-nested', 'external-link-dep', 'engine-specification', 'install-types']


def main():
    root = ROOT / 'examples/lockfiles'; root.mkdir(exist_ok=True)
    sources = []
    for name in NAMES:
        upstream = 'workspaces/arborist/test/fixtures/' + name + '/package-lock.json'
        with urllib.request.urlopen(BASE + upstream, timeout=30) as response:
            raw = response.read(1_048_577)
        if len(raw) > 1_048_576: raise ValueError('Fixture exceeds acquisition bound')
        path = name + '/package-lock.json'
        (root/path).parent.mkdir(exist_ok=True)
        (root/path).write_bytes(raw)
        data = json.loads(raw)
        sources.append(dict(path=path, url=BASE+upstream, revision=REVISION,
                            sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                            lockfile_version=data['lockfileVersion'], entries=len(data.get('packages', {}))))
    license_path = 'workspaces/arborist/LICENSE.md'
    license_data = urllib.request.urlopen(BASE+license_path, timeout=30).read(65536)
    (root/'LICENSE').write_bytes(license_data)
    manifest = dict(schema_version='lockfile-corpus/1', license=dict(url=BASE+license_path,
                    sha256=hashlib.sha256(license_data).hexdigest()), sources=sources)
    (root/'sources.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')


if __name__ == '__main__': main()
