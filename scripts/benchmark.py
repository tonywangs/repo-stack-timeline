#!/usr/bin/env python3
"""Reproducible fixtures and measured local CLI runs; no network required."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import tempfile
import time
from demo import create_demo, ROOT


def benchmark(output):
    evidence={'schema_version':'local-benchmark/1','measured_at_utc':datetime.now(timezone.utc).isoformat(),
              'environment':{'python':platform.python_version(),'platform':platform.platform(),'git':subprocess.check_output(['git','--version'],text=True).strip()},
              'method':'Three fresh CLI subprocesses per fixture, sequential, warm OS cache possible. perf_counter elapsed includes process launch. Linux wait4 ru_maxrss reports peak RSS for the command process and reaped children (maximum, not summed concurrent process-tree RSS). Each CLI has socket/connect syscalls denied by seccomp. These small fixtures do not estimate large-repository performance.',
              'runs':[]}
    with tempfile.TemporaryDirectory(prefix='repo-stack-bench-') as tmp:
        root=Path(tmp)
        for name,public in [('synthetic-seed-42',False),('public-manifest-projection',True)]:
            repo,ids=create_demo(root/name,public=public)
            hashes=[]
            for repeat in range(3):
                destination=root/(name+'-'+str(repeat))
                args=[sys.executable,str(ROOT/'scripts/offline_exec.py'),sys.executable,'-m','repo_stack_timeline',str(repo.root),*ids,'--output',str(destination)]
                env=dict(os.environ,PYTHONPATH=str(ROOT/'src'))
                start=time.perf_counter()
                process=subprocess.Popen(args,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
                _,status,usage=os.wait4(process.pid,0)
                elapsed=time.perf_counter()-start
                process.returncode=os.waitstatus_to_exitcode(status)
                stderr=process.stderr.read();process.stderr.close()
                if process.returncode:raise RuntimeError(stderr.decode())
                files={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(destination.iterdir())}
                hashes.append(files)
                report=json.loads((destination/'report.json').read_text())
                evidence['runs'].append(dict(fixture=name,repeat=repeat,elapsed_seconds=elapsed,peak_rss_kib=usage.ru_maxrss,
                    snapshots=len(ids),selected_commits=ids,counts=report['counts'],files=files,
                    declaration_events=sum(len(c['events']) for c in report['comparisons'])))
            if not all(x==hashes[0] for x in hashes):raise AssertionError('Repeated output is not identical')
    evidence['identical_repeated_outputs']=True
    Path(output).write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'passed','runs':len(evidence['runs']),'identical_repeated_outputs':True}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True)
    benchmark(p.parse_args().output)
