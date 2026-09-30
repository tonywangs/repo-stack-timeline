#!/usr/bin/env python3
"""One-command offline lockfile milestone verification (requires provisioned tools)."""
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

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from repo_stack_timeline.lockfiles import FIELDS, extract_lockfile
from repo_stack_timeline.limits import Budget, Limits
from helpers import file_state
from lockfile_demo import create
from verify import publication_check

READER_HASH='1c00ae180692a9bebe977c183c6db02c50b3c2e293867600c376b6d5f0773716'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--record',action='store_true',help='Save evidence to results/lockfiles-verification.json; preserve historical evidence')
    p.add_argument('--skip-regressions',action='store_true',help='Development only; result is explicitly partial')
    args=p.parse_args()
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'))
    evidence=dict(schema_version='lockfile-verification/1',started_at_utc=datetime.now(timezone.utc).isoformat(),
                  environment=dict(python=platform.python_version(),platform=platform.platform(),
                                   git=subprocess.check_output(['git','--version'],text=True).strip(),
                                   node=subprocess.check_output(['node','--version'],text=True).strip()),steps=[])
    def run(label,command,quiet=False):
        print(label,flush=True);start=time.perf_counter()
        r=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True)
        if not quiet: print(r.stdout,end='',flush=True)
        evidence['steps'].append(dict(name=label,returncode=r.returncode,elapsed_seconds=time.perf_counter()-start,stdout=(r.stdout if not quiet else '[structured result summarized in reader evidence]'),stderr=r.stderr))
        if r.returncode: raise RuntimeError(label+' failed: '+r.stderr)
        return r.stdout
    def offline(command): return [sys.executable,str(ROOT/'scripts/offline_exec.py'),*command]
    try:
        if not args.skip_regressions:
            run('Full regressions, 200 declaration histories, 200 lockfile pairs, installed CLI, baseline browser',
                [sys.executable,'scripts/verify.py','--browser'])
        with tempfile.TemporaryDirectory(prefix='lockfile-verify-') as tmp:
            root=Path(tmp)
            corpus=ROOT/'examples/lockfiles'
            sources=json.loads((corpus/'sources.json').read_text())
            assert hashlib.sha256((corpus/'LICENSE').read_bytes()).hexdigest()==sources['license']['sha256']
            inputs=[]; projections=[]; labels=[]
            for source in sources['sources']:
                raw=(corpus/source['path']).read_bytes()
                assert hashlib.sha256(raw).hexdigest()==source['sha256']
                assert len(raw)==source['bytes']
                inputs.append(str(corpus/source['path']));labels.append(source['path'])
                budget=Budget(Limits());budget.counts['package_entries']=0
                projections.append(extract_lockfile(source['path'],'fixture',raw,budget))
                # Metamorphic v3 copies are NOT passed off as upstream fixtures.
                if source['lockfile_version']==2:
                    data=json.loads(raw);data['lockfileVersion']=3;data.pop('dependencies',None)
                    dest=root/('v3-'+source['path'].split('/')[0]+'.json')
                    dest.write_text(json.dumps(data))
                    inputs.append(str(dest));labels.append('synthetic-v3:'+source['path'])
                    budget=Budget(Limits());budget.counts['package_entries']=0
                    projections.append(extract_lockfile(str(dest.name),'fixture',dest.read_bytes(),budget))
            reader=json.loads(run('Pinned Arborist fixture comparison (network syscalls denied)',
                                  offline(['node','tests/lockfile_reader.cjs',*inputs]),quiet=True))
            assert reader['source_sha256']==READER_HASH
            comparisons=[]
            for label, parsed, independent in zip(labels,projections,reader['fixtures'],strict=True):
                if independent['original_version']==1:
                    assert parsed['status']=='incomplete'
                    comparisons.append(dict(fixture=label,status='expected_scope_difference',reason='v1 intentionally unsupported; Arborist converts legacy records',reader_entries=len(independent['records'])))
                    continue
                actual={r['location']:r['metadata'] for r in parsed['records']}
                expected={loc:{k:v for k,v in meta.items() if k in FIELDS} for loc,meta in independent['records'].items()}
                assert parsed['status']=='ok',(label,parsed['diagnostics'])
                assert actual==expected,label
                comparisons.append(dict(fixture=label,status='agree',records=len(actual),diagnostics=parsed['diagnostics']))
            evidence['reader']=dict(name=reader['reader'],version=reader['version'],source_sha256=reader['source_sha256'],
                comparisons=comparisons,upstream_files=len(sources['sources']),synthetic_v3_files=5,
                supported_files=sum(c['status']=='agree' for c in comparisons),compared_records=sum(c.get('records',0) for c in comparisons),unexpected_disagreements=0)
            repo,ids=create(root/'workload')
            original=file_state(repo.root)
            runs=[]
            for repeat in range(3):
                out=root/('report-'+str(repeat))
                command=offline([sys.executable,'-m','repo_stack_timeline',str(repo.root),*ids,'--lockfiles','--output',str(out)])
                start=time.perf_counter()
                process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
                _,status,usage=os.wait4(process.pid,0)
                process.returncode=os.waitstatus_to_exitcode(status)
                elapsed=time.perf_counter()-start
                stderr=process.stderr.read();process.stderr.close()
                assert process.returncode==0,stderr
                files={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(out.iterdir())}
                report=json.loads((out/'report.json').read_text())
                runs.append(dict(repeat=repeat,elapsed_seconds=elapsed,peak_rss_kib=usage.ru_maxrss,files=files,
                                 counts=report['counts'],lockfile_events=sum(len(c['lockfile_events']) for c in report['comparisons'])))
            assert all(r['files']==runs[0]['files'] for r in runs)
            assert file_state(repo.root)==original
            evidence['benchmark']=dict(method='Three sequential fresh CLI subprocesses; Linux wait4 ru_maxrss is command/reaped-child peak, not summed concurrent process-tree RSS. Warm cache possible. Synthetic 220-package workload, three selected snapshots, including one intentionally unsupported file.',
                selected_commits=ids,runs=runs,identical_repeated_reports=True,input_repository_unchanged=True)
            evidence['browser']=json.loads(run('Network-blocked Chromium lockfile UI',
                ['node','tests/lockfiles_browser.cjs',str(root/'report-0/index.html')]).strip().splitlines()[-1])
        evidence['publication']=publication_check()
        evidence['status']='partial' if args.skip_regressions else 'passed'
    except BaseException:
        evidence['status']='failed'
        raise
    finally:
        if args.record:
            (ROOT/'results/lockfiles-verification.json').write_text(json.dumps(evidence,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(status=evidence['status'],compared_records=evidence['reader']['compared_records'],benchmark_runs=3)))


if __name__=='__main__': main()
