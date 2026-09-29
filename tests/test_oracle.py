import os
from pathlib import Path
import tempfile
import unittest
from repo_stack_timeline.scan import scan
from repo_stack_timeline.limits import Limits
from helpers import Repository, seed_history, oracle_events


class OracleTests(unittest.TestCase):
    def test_seeded_histories(self):
        count = int(os.environ.get('RST_ORACLE_SEEDS','200'))
        self.assertGreaterEqual(count,200,'The milestone oracle must cover at least 200 histories')
        with tempfile.TemporaryDirectory() as tmp:
            repo = Repository(Path(tmp)/'repo')
            for seed in range(count):
                with self.subTest(seed=seed):
                    ids, models = seed_history(repo,seed)
                    report = scan(repo.root,ids,Limits(seconds=120))
                    for snap, model in zip(report['snapshots'],models):
                        got = {(m['path'],m['ecosystem'],d['category'],d['name']):[v['raw'] for v in d['values']]
                               for m in snap['manifests'] for d in m['declarations']}
                        self.assertEqual(got,model[0])
                    for i, comparison in enumerate(report['comparisons']):
                        got = {(e['path'],e['ecosystem'],e['category'],e['name']):(e['kind'],
                               None if e['before'] is None else [v['raw'] for v in e['before']],
                               None if e['after'] is None else [v['raw'] for v in e['after']]) for e in comparison['events']}
                        self.assertEqual(got,oracle_events(models[i],models[i+1]))
                        for event in comparison['events']:
                            self.assertEqual(event['before_commit'],ids[i])
                            self.assertEqual(event['after_commit'],ids[i+1])
                    self.assertEqual([x['ancestry'] for x in report['comparisons']],
                        ['ancestor','diverged_or_unrelated','ancestor','ancestor','descendant','same'])
                    self.assertEqual(report['snapshots'][0]['commit'],ids[0])
                    self.assertGreater(report['snapshots'][0]['committer_time']['unix'],report['snapshots'][1]['committer_time']['unix'])
        print(f'ORACLE: {count} seeds, {count*7} snapshots, {count*6} adjacent comparisons checked independently')
