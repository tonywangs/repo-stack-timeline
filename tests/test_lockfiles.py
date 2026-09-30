import json
from pathlib import Path
import random
import tempfile
import unittest
from helpers import Repository, file_state
from repo_stack_timeline.lockfiles import extract_lockfile
from repo_stack_timeline.limits import Budget, Limits
from repo_stack_timeline.scan import scan
from repo_stack_timeline.errors import TimelineError
from repo_stack_timeline.report import publish


def parse(data, limits=None, mode='100644'):
    budget = Budget(limits or Limits())
    budget.counts['package_entries'] = 0
    return extract_lockfile('package-lock.json', 'a'*40,
                            data if isinstance(data, bytes) else json.dumps(data).encode(), budget, mode)


def lock(records, version=3):
    return json.dumps({'lockfileVersion': version, 'packages': records})


def reference(left, right):
    # Independent dictionary join, separate from production traversal and parser.
    # None is an invalid document. Empty dict is a valid missing/empty file.
    output = {}
    for location in set(left or {}) | set(right or {}):
        old = (left or {}).get(location)
        new = (right or {}).get(location)
        if left is None or right is None:
            output[location] = ('unknown', old, new, [])
        elif old != new:
            fields = []
            for field in set(old or {}) | set(new or {}):
                if (field, (old or {}).get(field)) not in (new or {}).items() or field not in (old or {}):
                    fields.append(field)
            output[location] = ('absent' if new is None else 'added' if old is None else 'changed', old, new, sorted(fields))
    return output


class LockfileTests(unittest.TestCase):
    def test_200_seeded_snapshot_pairs(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Repository(Path(tmp)/'input')
            for seed in range(200):
                rng = random.Random(seed)
                left = {'': {'name':'fixture','version':'1.0.0'},
                        'node_modules/@scope/pkg': {'version':str(rng.randrange(10)), 'integrity':'sha512-before'},
                        'node_modules/a/node_modules/@scope/pkg': {'version':'2'},
                        'node_modules/alias': {'name':'actual-name','version':'1','dev':True},
                        'node_modules/work': {'link':True,'resolved':'packages/work'},
                        'packages/work': {'name':'work'},
                        'node_modules/empty': {}}
                right = json.loads(json.dumps(left))
                right['node_modules/@scope/pkg'].update(version=str(rng.randrange(10)), integrity='sha512-after',optional=True)
                right.pop('node_modules/empty')
                right['node_modules/new'] = {'resolved':'https://never-fetch.invalid/x','hasInstallScript':True}
                right['node_modules/alias'].pop('dev')
                right['packages/work']['version'] = '2'
                right['node_modules/work']['resolved'] = '../outside'
                # Reordered input, a v2 compatibility section that MUST be ignored,
                # repeated names, aliases, roots, missing fields, hostile strings.
                old = {'packages':dict(reversed(list(left.items()))),'lockfileVersion':rng.choice([2,3]),'dependencies':{'ignored':{'version':'99'}}}
                new = {'lockfileVersion':rng.choice([2,3]),'packages':right}
                case = seed % 10
                if case == 1: new['packages']['node_modules/new'] = None
                if case == 2: new['lockfileVersion'] = 1
                if case == 3: new['packages']['node_modules/new']['optional'] = 'yes'
                if case == 4: right = left; new = {'lockfileVersion':3,'packages':dict(reversed(list(left.items())))}
                if case == 5: new['packages']['node_modules/new']['version'] = '</script><script>globalThis.PWNED=1</script>'
                if case in (1,2,3): right = None
                a = repo.commit({'package-lock.json':json.dumps(old), 'package.json':'{"dependencies":{"x":"1"}}'})
                b = repo.commit({'package-lock.json':json.dumps(new,sort_keys=True), 'package.json':'{"dependencies":{"x":"2"}}'},[a])
                report = scan(repo.root,[a,b],lockfiles=True)
                actual = {e['location']:(e['kind'],e['before'],e['after'],e['changed_fields']) for e in report['comparisons'][0]['lockfile_events']}
                self.assertEqual(actual, reference(left,right),seed)
                self.assertEqual(report['comparisons'][0]['events'][0]['kind'],'changed')
                self.assertEqual(report['lockfile_status'],'incomplete' if right is None else 'ok')
                for event in report['comparisons'][0]['lockfile_events']:
                    self.assertEqual((event['before_commit'],event['after_commit']),(a,b))
                    self.assertEqual(event['before_blob'],report['snapshots'][0]['lockfiles'][0]['blob'])
        print('LOCKFILE ORACLE: 200 seeds, 400 Git snapshots, 200 pairs, 60 incomplete pairs; independent reference agrees')

    def test_strict_parsing(self):
        for raw in [b'{', b'{"lockfileVersion":3,"packages":{"a":{},"a":{}}}',
                    b'{"lockfileVersion":3,"packages":{"a":{"version":NaN}}}',
                    {'lockfileVersion':True,'packages':{}}, {'lockfileVersion':4,'packages':{}},
                    {'lockfileVersion':3}, {'lockfileVersion':3,'packages':{'node_modules/a':{'link':True}}},
                    {'lockfileVersion':3,'packages':{'/absolute':{}}},
                    {'lockfileVersion':3,'packages':{'a/./b':{}}},
                    {'lockfileVersion':3,'packages':{'a/../b':{}}},
                    {'lockfileVersion':3,'packages':{'a':{'dependencies':{'b':None}}}}]:
            self.assertEqual(parse(raw)['status'],'incomplete',raw)
        self.assertEqual(parse({},mode='120000')['status'],'incomplete')
        result = parse({'lockfileVersion':2,'packages':{'../outside':{'name':'external','future':{'a':1}}}})
        self.assertEqual(result['status'],'ok')
        self.assertEqual(result['diagnostics'][0]['code'],'unmodeled_field')
        self.assertEqual(result['records'][0]['metadata'],{'name':'external'})

    def test_limits_state_paths_and_determinism(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); repo = Repository(root/'repo')
            files = {'package-lock.json':lock({'node_modules/a':{'version':'1'}}),
                     'npm-shrinkwrap.json':lock({'node_modules/a':{'version':'9'}}),
                     'sub/package-lock.json':lock({'node_modules/a':{'version':'3'}})}
            a = repo.commit(files); b = repo.commit({'sub/package-lock.json':files['sub/package-lock.json']},[a])
            repo.git('update-ref','refs/heads/main',a)
            repo.git('symbolic-ref','HEAD','refs/heads/main')
            repo.git('read-tree',a)
            (repo.root/'package-lock.json').write_text('dirty worktree must be ignored')
            (repo.root/'untracked').write_text('preserve')
            with (repo.root/'.git/config').open('a') as f:
                f.write('\n[core]\n fsmonitor = /never-run-this\n[include]\n path = /never-read-this\n')
            state = file_state(repo.root)
            report = scan(repo.root,[a,b],lockfiles=True)
            self.assertEqual(len(report['comparisons'][0]['lockfile_events']),2)
            self.assertTrue(all(e['kind']=='absent' for e in report['comparisons'][0]['lockfile_events']))
            self.assertIn('shrinkwrap_takes_precedence',[d['code'] for f in report['snapshots'][0]['lockfiles'] for d in f['diagnostics']])
            for limit in [Limits(lockfile_bytes=1), Limits(package_entries=1),Limits(lockfile_work=1),Limits(total_bytes=1),Limits(seconds=1e-9)]:
                with self.assertRaises(TimelineError): scan(repo.root,[a,b],limit,lockfiles=True)
            with self.assertRaises(TimelineError): publish(report,root/'small',Budget(Limits(report_bytes=100)))
            self.assertFalse((root/'small').exists())
            for label in ['one','two']: publish(scan(repo.root,[a,b],lockfiles=True),root/label,Budget(Limits()))
            self.assertEqual(file_state(root/'one'),file_state(root/'two'))
            self.assertEqual(file_state(repo.root),state)
            legacy = scan(repo.root,[a,b])
            self.assertEqual(legacy['schema_version'],'repo-stack-timeline/1')
            self.assertNotIn('lockfiles',legacy['snapshots'][0])
            self.assertNotIn('package_entries',legacy['counts'])

    def test_incomplete_empty_and_symlink_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Repository(Path(tmp)/'repo')
            a = repo.commit({'package-lock.json':'{}'})
            b = repo.commit({})
            report = scan(repo.root,[a,b],lockfiles=True)
            self.assertEqual(report['comparisons'][0]['lockfile_status'],'incomplete')
            self.assertEqual(report['comparisons'][0]['lockfile_events'],[])
            blob=repo.git('hash-object','-w','--stdin',data=b'/etc/passwd').decode().strip()
            c=repo.commit({'package-lock.json':('120000','blob',blob)})
            self.assertEqual(scan(repo.root,[c],lockfiles=True)['snapshots'][0]['lockfiles'][0]['diagnostics'][0]['code'],'lockfile_not_regular_file')
