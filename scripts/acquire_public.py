#!/usr/bin/env python3
"""Explicit NETWORK acquisition, never called by the scanner or verification.

Fetch a tiny purposeful sample of upstream manifests and their licenses from
GitHub's unauthenticated HTTPS API/raw service. No credentials are read.
Once sources.json exists, its immutable source commits are used for reacquisition.
"""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1] / 'examples' / 'public'
SAMPLE = [('pallets/flask','3.0.0','pyproject.toml','LICENSE.rst'),
          ('pallets/flask','3.1.0','pyproject.toml','LICENSE.txt'),
          ('expressjs/express','4.18.2','package.json','LICENSE'),
          ('expressjs/express','4.19.2','package.json','LICENSE')]


def fetch(url):
    request = urllib.request.Request(url,headers={'User-Agent':'repo-stack-timeline-fixture/1'})
    with urllib.request.urlopen(request,timeout=30) as response:
        data = response.read(1_048_577)
    if len(data)>1_048_576:raise ValueError('acquisition byte limit')
    return data


def resolve(repo,tag):
    obj = json.loads(fetch(f'https://api.github.com/repos/{repo}/git/ref/tags/{tag}'))['object']
    for _ in range(5):
        if obj['type']=='commit': return obj['sha']
        if obj['type']!='tag':raise ValueError('expected commit or annotated tag')
        obj = json.loads(fetch(f'https://api.github.com/repos/{repo}/git/tags/{obj["sha"]}'))['object']
    raise ValueError('too many tag indirections')


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    sources_path=ROOT/'sources.json'
    old = json.loads(sources_path.read_text()) if sources_path.exists() else None
    records=[]
    for repo,tag,manifest,license_path in SAMPLE:
        previous=next((r for r in old['sources'] if r['repository']==repo and r['tag']==tag),None) if old else None
        commit=previous['commit'] if previous else resolve(repo,tag)
        label=repo.split('/')[1]+'-'+tag
        folder=ROOT/label; folder.mkdir(exist_ok=True)
        files=[]
        for source_path in (manifest,license_path):
            url=f'https://raw.githubusercontent.com/{repo}/{commit}/{source_path}'
            raw=fetch(url)
            sha=hashlib.sha256(raw).hexdigest()
            if previous:
                expected=next(f['sha256'] for f in previous['files'] if f['upstream_path']==source_path)
                if sha!=expected:raise ValueError('immutable fixture hash mismatch')
            (folder/source_path).write_bytes(raw)
            git_blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            files.append(dict(upstream_path=source_path,local_path=label+'/'+source_path,url=url,
                              sha256=sha,git_blob_sha1=git_blob,bytes=len(raw)))
        records.append(dict(repository=repo,tag=tag,commit=commit,files=files,
                            license='BSD-3-Clause' if repo=='pallets/flask' else 'MIT'))
    metadata=dict(schema_version='public-manifest-sample/1',sources=records,
        sampling='Purposeful four-snapshot convenience sample, two established projects; not random or representative. Only manifest and license bytes are frozen, not complete upstream trees or histories. Reconstructed demo commits are local projections, not upstream commit IDs.')
    sources_path.write_text(json.dumps(metadata,indent=2,sort_keys=True)+'\n')
    print('Fetched and hash-verified',len(records),'public manifest/license snapshots')

if __name__=='__main__':main()
