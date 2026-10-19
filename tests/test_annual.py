import base64
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import unittest

from repo_stack_timeline.annual import (analyze, canonical, load_study, runtime,
    select_years, summarize, verify_source)

ROOT = Path(__file__).resolve().parents[1]


class AnnualTests(unittest.TestCase):
    def test_cutoff_utc_topology_not_clock_sort(self):
        cutoff = int(datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp())
        history = [('exact', cutoff), ('first', cutoff-50), ('older-topology', cutoff-1)]
        self.assertEqual(select_years(history, [2019, 2020, 2021]),
                         {2019: None, 2020: 'first', 2021: 'exact'})

    def test_runtime_scope_and_unknowns(self):
        def py(**files):
            return runtime({k.replace('_', '.'): v.encode() for k, v in files.items()}, 'python')
        self.assertEqual(runtime({}, 'npm')['status'], 'missing_manifest')
        self.assertEqual(py()['status'], 'missing_manifest')
        self.assertEqual(py(setup_py='setup(name="x")')['status'], 'unsupported_metadata')
        self.assertEqual(py(setup_py='setup(install_requires=[])')['status'], 'observed')
        self.assertEqual(py(setup_py='setup(install_requires=load())')['status'], 'unsupported_metadata')
        for text in ('if True:\n setup(install_requires=[])', 'setup(**kwargs)', 'setup(); setup()',
                     'def f():\n setup(install_requires=[])'):
            self.assertEqual(py(setup_py=text)['status'], 'unsupported_metadata')
        self.assertEqual(py(pyproject_toml='[project]\ndynamic=["dependencies"]',
                            setup_py='setup(install_requires=["incorrect-fallback"])')['status'], 'unsupported_metadata')
        self.assertEqual(py(pyproject_toml='[project]\nname="x"')['declarations'], [])
        self.assertEqual(py(setup_cfg='[options]\ninstall_requires = file: requirements.txt')['status'], 'unsupported_metadata')
        row = py(setup_cfg='[options]\ninstall_requires =\n My_Pkg>=1; python_version < "3.12"\n other[extra]>=2')
        self.assertEqual([d['name'] for d in row['declarations']], ['my-pkg', 'other'])
        self.assertEqual(row['declarations'][0]['marker'], 'python_version < "3.12"')
        row = runtime({'package.json': b'{"dependencies":{"a":"1","b":"2"},"optionalDependencies":{"b":"3"},"devDependencies":{"c":"4"}}'}, 'npm')
        self.assertEqual([d['name'] for d in row['declarations']], ['a'])
        for blob in (b'[]', b'{bad', b'{"dependencies":null}', b'{"dependencies":{"bad":2}}', b'{"dependencies":{},"dependencies":{}}'):
            self.assertEqual(runtime({'package.json': blob}, 'npm')['status'], 'unsupported_metadata')

    def test_frozen_real_source_and_findings(self):
        study = load_study(ROOT / 'examples/annual')
        self.assertEqual(len(study['snapshots']), 56)
        self.assertEqual(sum(s['status'] == 'observed' for s in study['snapshots']), 50)
        self.assertEqual(study['fixed_members']['python'], ['pallets/flask', 'pallets/jinja'])
        snaps = {(s['repository'], s['year']): s for s in study['snapshots']}
        self.assertEqual(snaps['chalk/chalk', 2020]['names'], ['ansi-styles', 'supports-color'])
        self.assertEqual(snaps['chalk/chalk', 2021]['names'], [])
        self.assertEqual(len(snaps['koajs/koa', 2019]['names']), 24)
        self.assertEqual(len(snaps['koajs/koa', 2025]['names']), 18)
        self.assertNotIn('blinker', snaps['pallets/flask', 2022]['names'])
        self.assertIn('blinker', snaps['pallets/flask', 2023]['names'])
        self.assertEqual(snaps['pallets/itsdangerous', 2022]['status'], 'unsupported_metadata')
        self.assertEqual(snaps['pallets/itsdangerous', 2023]['status'], 'observed')
        self.assertEqual(snaps['pallets/itsdangerous', 2023]['names'], [])
        for s in study['summaries']:
            if s['ecosystem'] == 'python' and s['year'] in (2019, 2025):
                d = next(d for d in s['dependencies'] if d['name'] == 'markupsafe')
                expected = (1, 2) if s['year'] == 2019 else (2, 2 if s['mode'] == 'fixed' else 4)
                self.assertEqual((d['numerator'], d['denominator']), expected)

    def test_provenance_rejects_tampering_and_omission(self):
        cohort = json.loads((ROOT/'examples/annual/cohort.json').read_text())
        source = json.loads((ROOT/'examples/annual/sources/pallets--flask.json').read_text())
        for kind in ('blob', 'commit', 'tree', 'omit', 'duplicate', 'year', 'url', 'cohort', 'stamp'):
            bad = copy.deepcopy(source)
            snap = bad['snapshots'][0]
            if kind == 'blob': snap['files'][0]['base64'] = base64.b64encode(b'changed').decode()
            if kind == 'commit': snap['commit'] = '0'*40
            if kind == 'tree': snap['tree'] = '0'*40
            if kind == 'omit': snap['files'].pop()
            if kind == 'duplicate': snap['files'].append(snap['files'][0])
            if kind == 'year': snap['year'] = 2000
            if kind == 'url': snap['files'][0]['url'] = 'https://example.invalid'
            if kind == 'cohort': bad['cohort_sha256'] = '0'*64
            if kind == 'stamp': snap['committer_timestamp'] = 0
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                verify_source(bad, cohort['repositories'][0], cohort)

    def test_unknown_not_absence_and_fixed_cohort(self):
        cohort = dict(years=[2019, 2020, 2021], repositories=[dict(repository=r, ecosystem='python') for r in ('a', 'b', 'c')])
        states = {'a': [set(), {'x'}, {'x'}], 'b': [{'x'}, None, set()], 'c': [{'x'}, set(), {'x'}]}
        snapshots = [dict(repository=r, ecosystem='python', year=y, names=sorted(states[r][i] or []),
                          status='observed' if states[r][i] is not None else 'missing_manifest')
                     for r in states for i, y in enumerate(cohort['years'])]
        study = summarize(cohort, snapshots)
        self.assertEqual(study['fixed_members']['python'], ['a', 'c'])
        s = next(s for s in study['summaries'] if s['ecosystem'] == 'python' and s['mode'] == 'available' and s['year'] == 2020)
        self.assertEqual((s['observed'], s['paired'], s['unknown_pairs']), (2, 2, 1))
        d = s['dependencies'][0]
        self.assertEqual(d['adopted'], ['a'])
        self.assertEqual(d['removed'], ['c'])
        self.assertEqual((d['adoption_denominator'], d['removal_denominator']), (1, 1))
        self.assertEqual(d['persisted'], [])

    def test_seeded_transition_accounting(self):
        # Independent state-count oracle includes missing observations and empty sets.
        for seed in range(40):
            rng = random.Random(seed)
            years = [2019, 2020, 2021, 2022]
            repos = ['a', 'b', 'c', 'd']
            states = {(r, y): rng.choice([None, set(), {'x'}, {'y'}, {'x', 'y'}]) for r in repos for y in years}
            cohort = dict(years=years, repositories=[dict(repository=r, ecosystem='npm') for r in repos])
            rows = [dict(repository=r, ecosystem='npm', year=y, names=sorted(v or []), status='observed' if v is not None else 'unavailable_history') for (r, y), v in states.items()]
            study = summarize(cohort, rows)
            for s in study['summaries']:
                if s['ecosystem'] != 'npm': continue
                eligible = repos if s['mode'] == 'available' else [r for r in repos if all(states[r,y] is not None for y in years)]
                y = s['year']
                self.assertEqual(s['observed'], sum(states[r,y] is not None for r in eligible))
                for d in s['dependencies']:
                    n = d['name']
                    self.assertEqual(d['numerator'], sum(states[r,y] is not None and n in states[r,y] for r in eligible))
                    if y == years[0]:
                        self.assertIsNone(d['adoption_denominator'])
                        continue
                    counts = {(False, False): 0, (False, True): 0, (True, False): 0, (True, True): 0}
                    for r in eligible:
                        if states[r,y-1] is not None and states[r,y] is not None:
                            counts[n in states[r,y-1], n in states[r,y]] += 1
                    self.assertEqual(len(d['adopted']), counts[False, True])
                    self.assertEqual(len(d['removed']), counts[True, False])
                    self.assertEqual(len(d['persisted']), counts[True, True])
                    self.assertEqual(d['adoption_denominator'], counts[False, False]+counts[False, True])
                    self.assertEqual(d['removal_denominator'], counts[True, False]+counts[True, True])

if __name__ == '__main__':
    unittest.main()
