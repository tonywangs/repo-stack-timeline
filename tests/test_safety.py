from dataclasses import replace
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from repo_stack_timeline.errors import TimelineError
from repo_stack_timeline.limits import Limits, Budget
from repo_stack_timeline.scan import scan
from repo_stack_timeline.gitio import ObjectRepository, Runner
from repo_stack_timeline.report import publish, json_bytes
from helpers import Repository, file_state

ROOT = Path(__file__).resolve().parents[1]


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = Repository(self.root/'repo')
        self.oid = self.repo.commit({'package.json':'{"dependencies":{"a":"1"}}',
                                     'nested/pyproject.toml':'[project]\ndependencies=["b>=1"]'})
    def tearDown(self):
        self.temp.cleanup()

    def assert_code(self, code, operation):
        with self.assertRaises(TimelineError) as cm:
            operation()
        self.assertEqual(cm.exception.code,code)

    def test_repository_entire_state_unchanged_and_config_not_executed(self):
        self.repo.git('update-ref','refs/heads/main',self.oid)
        self.repo.git('symbolic-ref','HEAD','refs/heads/main')
        self.repo.git('read-tree',self.oid)
        (self.repo.root/'package.json').write_text('{"dependencies":{"DIRTY":"*"}}')
        (self.repo.root/'untracked').write_text('keep me')
        canary = self.root/'EXECUTED'
        hook = self.root/'hook'
        hook.write_text(f'#!/bin/sh\ntouch {canary}\n')
        hook.chmod(0o755)
        config = self.repo.root/'.git/config'
        with config.open('a') as f:
            f.write(f'\n[core]\n fsmonitor = {hook}\n hooksPath = {self.root}\n pager = {hook}\n[alias]\n cat-file = !{hook}\n[include]\n path = /does/not/exist\n[remote "evil"]\n url = ext::{hook}\n promisor = true\n[extensions]\n partialClone = evil\n')
        before = file_state(self.repo.root)
        with patch.dict(os.environ, {'GIT_CONFIG_PARAMETERS':"'core.fsmonitor=/bad'",'GIT_TRACE':str(canary),'GIT_DIR':'/bad','GIT_ALTERNATE_OBJECT_DIRECTORIES':'/bad'}):
            report = scan(self.repo.root,[self.oid,self.oid[:12]])
        self.assertEqual(report['comparisons'][0]['events'],[])
        self.assertEqual(file_state(self.repo.root),before)
        self.assertFalse(canary.exists())
        self.assertEqual(report['snapshots'][0]['manifests'][1]['declarations'][0]['name'],'a')

    def test_all_resource_limits(self):
        for kwargs,code in [({'tree_entries':1},'tree_entries_limit'),({'manifests':1},'manifests_limit'),
                             ({'blob_bytes':8},'blob_bytes_limit'),({'total_bytes':30},'total_bytes_limit'),
                             ({'git_output_bytes':8},'git_output_limit'),({'seconds':1e-9},'runtime_limit')]:
            with self.subTest(kwargs=kwargs):
                self.assert_code(code,lambda:scan(self.repo.root,[self.oid],replace(Limits(),**kwargs)))
        for kwargs in ({'seconds':float('nan')},{'seconds':float('inf')},{'manifests':0},{'blob_bytes':-1}):
            self.assert_code('invalid_limit',lambda:Limits(**kwargs))
        self.assert_code('snapshot_limit',lambda:scan(self.repo.root,[self.oid]*33))
        self.assert_code('snapshot_limit',lambda:scan(self.repo.root,[]))
        for bad in ('HEAD','main','HEAD~1','--help','a'*65,'xyz'):
            self.assert_code('invalid_revision',lambda:scan(self.repo.root,[bad]))
        child=self.repo.commit({'package.json':'{}'},[self.oid])
        self.assert_code('ancestry_commits_limit',lambda:scan(self.repo.root,[self.oid,child],Limits(ancestry_commits=1)))

    def test_packed_objects_and_replacement_refs(self):
        replacement=self.repo.commit({'package.json':'{"dependencies":{"REPLACED":"*"}}'})
        self.repo.git('update-ref','refs/heads/main',self.oid)
        self.repo.git('replace',self.oid,replacement)
        self.repo.git('repack','-a','-d')
        before=file_state(self.repo.root)
        report=scan(self.repo.root,[self.oid])
        names={d['name'] for m in report['snapshots'][0]['manifests'] for d in m['declarations']}
        self.assertEqual(names,{'a','b'})
        self.assertEqual(before,file_state(self.repo.root))

    def test_missing_object_and_parent(self):
        self.assert_code('git_object_error',lambda:scan(self.repo.root,['a'*40]))
        tree = self.repo.git('rev-parse',self.oid+'^{tree}').decode().strip()
        raw = f'tree {tree}\nparent {"b"*40}\nauthor Test <t@example.invalid> 1700000000 +0000\ncommitter Test <t@example.invalid> 1700000000 +0000\n\nmissing parent\n'.encode()
        dangling = self.repo.git('hash-object','-t','commit','-w','--stdin',data=raw).decode().strip()
        report = scan(self.repo.root,[self.oid,dangling])
        self.assertEqual(report['comparisons'][0]['ancestry'],'unknown')
        manifest_blob = self.repo.git('rev-parse',self.oid+':package.json').decode().strip()
        (self.repo.root/'.git/objects'/manifest_blob[:2]/manifest_blob[2:]).unlink()
        self.assert_code('git_object_error',lambda:scan(self.repo.root,[self.oid]))

    def test_symlinks_and_submodules_not_followed(self):
        blob = self.repo.git('hash-object','-w','--stdin',data=b'/etc/passwd').decode().strip()
        oid = self.repo.commit({'package.json':('120000','blob',blob), 'vendor':('160000','commit',self.oid)})
        report = scan(self.repo.root,[oid])
        snap = report['snapshots'][0]
        self.assertEqual(len(snap['manifests']),1)
        self.assertEqual(snap['manifests'][0]['status'],'unsupported')
        self.assertEqual(snap['diagnostics'],[{'code':'submodule_skipped','path':'vendor'}])
        self.assertEqual(report['counts']['total_bytes'],0)

    def test_bare_sha256_and_non_utf8_paths(self):
        sha = Repository(self.root/'sha256','sha256')
        oid = sha.commit({'weird\udcff/package.json':'{"dependencies":{"x":"*"}}'})
        report = scan(sha.root/'.git',[oid],object_format='sha256')
        self.assertEqual(len(report['snapshots'][0]['commit']),64)
        raw = json_bytes(report,8_000_000)
        self.assertIn(b'weird\\udcff/package.json',raw)
        self.assertEqual(json.loads(raw)['snapshots'][0]['manifests'][0]['path'],'weird\udcff/package.json')

    def test_alternates_and_gitfile_rejected(self):
        (self.repo.root/'.git/objects/info/alternates').write_text('/tmp/other\n')
        self.assert_code('unsupported_repository',lambda:scan(self.repo.root,[self.oid]))
        linked = self.root/'linked'; linked.mkdir(); (linked/'.git').write_text('gitdir: /elsewhere')
        self.assert_code('unsupported_repository',lambda:scan(linked,[self.oid]))

    def test_identical_reports_and_atomic_collision(self):
        report = scan(self.repo.root,[self.oid,self.oid])
        a,b = self.root/'a',self.root/'b'
        publish(report,a,Budget(Limits()))
        publish(scan(self.repo.root,[self.oid,self.oid]),b,Budget(Limits()))
        self.assertEqual(file_state(a),file_state(b))
        self.assertEqual(sorted(x.name for x in a.iterdir()),['SHA256SUMS','index.html','report.json'])
        before = file_state(a)
        self.assert_code('output_exists',lambda:publish(report,a,Budget(Limits())))
        self.assertEqual(file_state(a),before)
        link = self.root/'link'; link.symlink_to(self.root/'missing')
        self.assert_code('output_exists',lambda:publish(report,link,Budget(Limits())))
        # A competitor wins after our initial existence check. No replacement allowed.
        from repo_stack_timeline.report import rename_exclusive
        def race(source,target):
            target.mkdir(); (target/'sentinel').write_text('competitor')
            return rename_exclusive(source,target)
        with patch('repo_stack_timeline.report.rename_exclusive',side_effect=race):
            self.assert_code('output_exists',lambda:publish(report,self.root/'race',Budget(Limits())))
        self.assertEqual((self.root/'race/sentinel').read_text(),'competitor')
        self.assertEqual(list(self.root.glob('.repo-stack-tmp-*')),[])

    def test_interrupted_writes_and_serialization_failures(self):
        report = scan(self.repo.root,[self.oid])
        for error in (OSError('disk full'),KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__):
                with patch('repo_stack_timeline.report.os.fsync',side_effect=error):
                    with self.assertRaises(type(error)):
                        publish(report,self.root/'failed',Budget(Limits()))
                self.assertFalse((self.root/'failed').exists())
                self.assertEqual(list(self.root.glob('.repo-stack-tmp-*')),[])
        with self.assertRaises(TypeError):
            publish({'bad':object()},self.root/'failed',Budget(Limits()))
        with self.assertRaises(ValueError):
            publish({'bad':float('nan')},self.root/'failed',Budget(Limits()))
        self.assertFalse((self.root/'failed').exists())
        self.assert_code('report_bytes_limit',lambda:publish(report,self.root/'failed',Budget(Limits(report_bytes=50))))
        self.assert_code('report_bytes_limit',lambda:publish(report,self.root/'failed',Budget(Limits(report_bytes=10_000))))

    def test_runner_timeout_output_limit_and_process_group_cleanup(self):
        # A trusted test executable stands in for a wedged Git plus a child.
        fake = self.root/'fake-git'
        pidfile = self.root/'child.pid'
        fake.write_text(f'#!{sys.executable}\nimport os,time\npid=os.fork()\nif pid:\n open({str(pidfile)!r},"w").write(str(pid))\nwhile True: time.sleep(1)\n')
        fake.chmod(0o755)
        runner = Runner(self.root,{'PATH':os.environ['PATH']},Budget(Limits(seconds=.3)))
        runner.git = str(fake)
        self.assert_code('runtime_limit',lambda:runner.run(['ignored']))
        pid = int(pidfile.read_text())
        # Zombie is dead but may await the container's init reaper.
        status = Path(f'/proc/{pid}/stat')
        self.assertTrue(not status.exists() or status.read_text().split()[2] == 'Z')
        fake.write_text(f'#!{sys.executable}\nimport os\nwhile True: os.write(1,b"x"*65536)\n')
        runner.budget = Budget(Limits(seconds=2))
        self.assert_code('git_output_limit',lambda:runner.run(['ignored'],cap=64))

    def test_cli_signal_cancellation_leaves_no_output(self):
        bindir = self.root/'bin'; bindir.mkdir()
        fake = bindir/'git'; started = self.root/'started'
        fake.write_text(f'#!{sys.executable}\nimport time\nopen({str(started)!r},"w").write("ready")\ntime.sleep(60)\n')
        fake.chmod(0o755)
        env = dict(os.environ,PYTHONPATH=str(ROOT/'src'),PATH=str(bindir)+':'+os.environ['PATH'])
        for sig in (signal.SIGTERM,signal.SIGINT):
            started.unlink(missing_ok=True)
            proc = subprocess.Popen([sys.executable,'-m','repo_stack_timeline',str(self.repo.root),self.oid,'--output',str(self.root/'cancelled')],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            try:
                deadline=time.monotonic()+5
                while not started.exists() and time.monotonic()<deadline:
                    time.sleep(.01)
                self.assertTrue(started.exists())
                proc.send_signal(sig)
                _,stderr=proc.communicate(timeout=5)
                self.assertEqual(proc.returncode,130,stderr)
                self.assertEqual(json.loads(stderr)['code'],'cancelled')
                self.assertFalse((self.root/'cancelled').exists())
            finally:
                if proc.poll() is None: proc.kill();proc.wait()

    def test_cli_output_cannot_modify_repository(self):
        proc = subprocess.run([sys.executable,'-m','repo_stack_timeline',str(self.repo.root),self.oid,'--output',str(self.repo.root/'result')],
                              env=dict(os.environ,PYTHONPATH=str(ROOT/'src')),capture_output=True)
        self.assertEqual(proc.returncode,2)
        self.assertEqual(json.loads(proc.stderr)['code'],'output_inside_repository')
        self.assertFalse((self.repo.root/'result').exists())
