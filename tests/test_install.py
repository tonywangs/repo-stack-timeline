import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from helpers import Repository, file_state

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from install import install
from wheel_backend import build_wheel


class InstallationTests(unittest.TestCase):
    def test_deterministic_wheel_and_isolated_offline_installed_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            first=root/'wheel-a'; second=root/'wheel-b'
            a=first/build_wheel(first);b=second/build_wheel(second)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            executable=install(root/'env')
            repo=Repository(root/'input')
            before=repo.commit({'package.json':'{"dependencies":{"widget":"^1"}}'})
            after=repo.commit({'package.json':'{"dependencies":{"widget":"^2","new":"*"}}'},[before])
            state=file_state(repo.root)
            # -I launcher must ignore a hostile PYTHONPATH and working-directory module.
            cwd=root/'unrelated';cwd.mkdir()
            (cwd/'repo_stack_timeline.py').write_text('raise RuntimeError("source shadowed installed package")')
            env={'PATH':os.environ['PATH'],'HOME':str(cwd),'PYTHONPATH':str(cwd),
                 'http_proxy':'http://127.0.0.1:1','https_proxy':'http://127.0.0.1:1','ALL_PROXY':'http://127.0.0.1:1'}
            for label in ('first','second'):
                run=subprocess.run([sys.executable,str(ROOT/'scripts/offline_exec.py'),str(executable),str(repo.root),before,after,'--output',str(root/label)],env=env,cwd=cwd,capture_output=True)
                self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(file_state(root/'first'),file_state(root/'second'))
            self.assertEqual(file_state(repo.root),state)
            import json
            report=json.loads((root/'first/report.json').read_text())
            self.assertEqual({x['kind'] for x in report['comparisons'][0]['events']},{'added','changed'})
            location=subprocess.check_output([str(root/'env/bin/python'),'-I','-c','import repo_stack_timeline;print(repo_stack_timeline.__file__)'],cwd=cwd,text=True)
            self.assertTrue(location.strip().startswith(str(root/'env')))

    def test_installed_lockfile_analysis(self):
        from lockfile_demo import create
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); executable=install(root/'env')
            repo,ids=create(root/'fixture',size=10)
            state=file_state(repo.root)
            for label in ['first','second']:
                run=subprocess.run([sys.executable,str(ROOT/'scripts/offline_exec.py'),str(executable),str(repo.root),*ids,'--lockfiles','--output',str(root/label)],cwd=root,capture_output=True)
                self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(file_state(root/'first'),file_state(root/'second'))
            self.assertEqual(file_state(repo.root),state)
            import json
            report=json.loads((root/'first/report.json').read_text())
            self.assertEqual(report['schema_version'],'repo-stack-timeline/2')
            self.assertEqual({e['kind'] for e in report['comparisons'][0]['lockfile_events']},{'added','absent','changed'})
            self.assertEqual(report['comparisons'][1]['lockfile_status'],'incomplete')
