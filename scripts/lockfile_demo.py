#!/usr/bin/env python3
"""Deterministic lockfile workload, independent of production extraction."""
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'src')]
from helpers import Repository


def create(root, size=220):
    repo = Repository(Path(root)/'repository')
    packages = {'':{'name':'sample-project','version':'1.0.0'},
                'node_modules/alias':{'name':'real-package','version':'1.2.3'},
                'node_modules/work':{'link':True,'resolved':'packages/work'},
                'packages/work':{'name':'work','version':'1.0.0'}}
    for i in range(size):
        packages[f'node_modules/lib-{i:04d}'] = {'version':'1.0.0','integrity':'sha512-recorded-only','dev':False}
    packages['node_modules/hostile'] = {'version':'</script><script>globalThis.PWNED=1</script>', 'resolved':'https://never-fetch.invalid/@@DATA@@'}
    def files(version):
        return {'package-lock.json':json.dumps({'lockfileVersion':version,'packages':packages}),
                'package.json':json.dumps({'dependencies':{'lib-0000':'^'+str(version)}})}
    a = repo.commit(files(2))
    packages['node_modules/lib-0000'].update(version='2.0.0',integrity='sha512-changed',optional=True)
    del packages['node_modules/lib-0001']
    packages['node_modules/new'] = {'version':'3','hasInstallScript':True}
    b = repo.commit(files(3),[a])
    c = repo.commit({'package-lock.json':'{"lockfileVersion":1}'},[b])
    return repo,[a,b,c]


def main():
    import argparse
    from repo_stack_timeline.scan import scan
    from repo_stack_timeline.report import publish
    from repo_stack_timeline.limits import Budget, Limits
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('output',type=Path)
    args=p.parse_args()
    if args.output.exists(): p.error('Choose a fresh demo directory')
    repo,ids=create(args.output)
    budget=Budget(Limits())
    report=scan(repo.root,ids,budget=budget,lockfiles=True)
    publish(report,args.output/'report',budget)
    print(json.dumps(dict(repository=str(repo.root),commits=ids,report=str(args.output/'report/index.html'),lockfile_status=report['lockfile_status']),indent=2))


if __name__=='__main__': main()
