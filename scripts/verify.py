#!/usr/bin/env python3
"""One-command offline verification. Never installs or downloads dependencies."""
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

ROOT=Path(__file__).resolve().parents[1]


def publication_check():
    # Include untracked project files, excluding documented development caches.
    names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).split(b'\0')
    paths=sorted(set(os.fsdecode(n) for n in names if n))
    total=0
    for name in paths:
        path=ROOT/name
        if not path.is_file():continue
        size=path.stat().st_size
        if size>10*1024*1024:raise AssertionError('File exceeds 10 MiB: '+name)
        if name.endswith('.log') and name!='results/tests.log':raise AssertionError('Unpublishable log: '+name)
        total+=size
    if len(paths)>1000 or total>32*1024*1024:raise AssertionError('Publication tree limit exceeded')
    return {'files':len(paths),'bytes':total}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--browser',action='store_true',help='Require preinstalled Node/Playwright/Chromium and exercise viewer')
    p.add_argument('--record',action='store_true',help='Replace results/tests.log and results/verification.json with actual evidence')
    args=p.parse_args()
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'))
    evidence={'schema_version':'verification/1','started_at_utc':datetime.now(timezone.utc).isoformat(),'steps':[]}
    logs=[]
    def run(label,command):
        print(label,flush=True);start=time.perf_counter()
        result=subprocess.run(command,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        logs.append(result.stdout);print(result.stdout,end='',flush=True)
        evidence['steps'].append({'name':label,'command':command,'returncode':result.returncode,'elapsed_seconds':time.perf_counter()-start})
        if result.returncode:raise RuntimeError(label+' failed')
        return result.stdout
    passed=False
    try:
        # Every Python test, fixture Git operation, and installed CLI inherits this filter.
        run('Unit, safety, independent oracle, and installed CLI tests (network syscalls denied)',
            [sys.executable,'scripts/offline_exec.py',sys.executable,'-m','unittest','discover','-s','tests','-v'])
        with tempfile.TemporaryDirectory(prefix='repo-stack-verify-') as tmp:
            root=Path(tmp)
            run('Public fixture integrity and reproducible CLI benchmark',
                [sys.executable,'scripts/offline_exec.py',sys.executable,'scripts/benchmark.py','--output',str(root/'benchmark.json')])
            evidence['benchmark']=json.loads((root/'benchmark.json').read_text())
            if args.browser:
                run('Create hostile-text browser fixture',[sys.executable,'scripts/offline_exec.py',sys.executable,'scripts/demo.py',str(root/'browser'),'--hostile'])
                output=run('Network-blocked Chromium navigation, filters, keyboard, and hostile text',
                    ['node','tests/browser.cjs',str(root/'browser/report/index.html')])
                evidence['browser']=json.loads(output.strip().splitlines()[-1])
            else:
                evidence['browser']={'status':'not_run','reason':'Use --browser with preinstalled Playwright and Chromium for complete milestone verification'}
        evidence['publication']=publication_check()
        passed=True
    finally:
        evidence['status']='passed' if passed else 'failed'
        if args.record:
            (ROOT/'results').mkdir(exist_ok=True)
            (ROOT/'results/tests.log').write_text(''.join(logs))
            (ROOT/'results/verification.json').write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'passed','browser':evidence['browser']['status'],'publication':evidence['publication']}))


if __name__=='__main__':main()
