#!/usr/bin/env python3
"""Create a deterministic local demo repository without acquiring or executing code."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from helpers import Repository, seed_history
from repo_stack_timeline.limits import Limits, Budget
from repo_stack_timeline.scan import scan
from repo_stack_timeline.report import publish


def create_demo(destination, public=False, hostile=False):
    destination=Path(destination)
    destination.mkdir(parents=True,exist_ok=False)
    repo=Repository(destination/'repository')
    if public:
        metadata=json.loads((ROOT/'examples/public/sources.json').read_text())
        files={}; ids=[]; sources=[]
        for record in metadata['sources']:
            local_paths=[]
            for file in record['files']:
                raw=(ROOT/'examples/public'/file['local_path']).read_bytes()
                if hashlib.sha256(raw).hexdigest()!=file['sha256']:raise ValueError('Public fixture checksum mismatch')
                target=record['repository'].split('/')[1]+'/'+file['upstream_path']
                files[target]=raw
                local_paths.append(target)
            oid=repo.commit(files,ids[-1:] if ids else (),message='Manifest projection: '+record['repository']+' '+record['commit'])
            ids.append(oid);sources.append(dict(projected_commit=oid,upstream_commit=record['commit'],repository=record['repository'],paths=local_paths))
        (destination/'projection.json').write_text(json.dumps(sources,indent=2,sort_keys=True)+'\n')
    else:
        ids,_=seed_history(repo,42)
    if hostile:
        hostile_name='</script><script>globalThis.PWNED=1</script><img src="https://example.invalid/leak" onerror="globalThis.PWNED=2">'
        entries={f'package-{i:03}':str(i) for i in range(205)}
        entries[hostile_name]='@@DATA@@ <&> " \\ \u2028'
        oid=repo.commit({'hostile/雪/package.json':json.dumps({'dependencies':entries}),
                         'pyproject.toml':'[project]\ndynamic=["dependencies"]'},ids[-1:])
        ids.append(oid)
    (destination/'commits.json').write_text(json.dumps(ids,indent=2)+'\n')
    return repo,ids


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path)
    p.add_argument('--public',action='store_true');p.add_argument('--hostile',action='store_true')
    args=p.parse_args()
    repo,ids=create_demo(args.destination,args.public,args.hostile)
    budget=Budget(Limits());report=scan(repo.root,ids,budget=budget)
    publish(report,args.destination/'report',budget)
    print(json.dumps(dict(repository=str(repo.root),commits=ids,report=str(args.destination/'report/index.html')),indent=2))

if __name__=='__main__':main()
