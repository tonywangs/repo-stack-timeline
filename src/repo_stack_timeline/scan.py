from dataclasses import asdict
from . import SCHEMA_VERSION, SEMANTICS_VERSION
from .limits import Limits, Budget
from .errors import TimelineError
from .gitio import ObjectRepository
from .extract import extract
from .compare import compare


def scan(source, revisions, limits=None, object_format='sha1', budget=None):
    limits = limits or Limits()
    budget = budget or Budget(limits)
    if not 1 <= len(revisions) <= 32:
        raise TimelineError('snapshot_limit', 'Select between 1 and 32 commit identifiers in comparison order')
    snapshots = []
    with ObjectRepository(source, budget, object_format) as repo:
        # Resolve once, before any tree is read. Repeats remain repeats in the report.
        ids = [repo.resolve(r) for r in revisions]
        metadata = {oid: repo.commit(oid) for oid in dict.fromkeys(ids)}
        for i, oid in enumerate(ids):
            budget.check()
            snapshot = dict(metadata[oid], index=i, manifests=[], diagnostics=[])
            manifests, skipped = repo.manifests(snapshot['tree'])
            snapshot['diagnostics'].extend(skipped)
            for path, mode, kind, blob in manifests:
                budget.check()
                raw = repo.read_object(blob, 'blob', limits.blob_bytes) if mode in ('100644', '100755') and kind == 'blob' else b''
                snapshot['manifests'].append(extract(path, blob, raw, mode))
            snapshots.append(snapshot)
        comparisons = []
        for i in range(1, len(snapshots)):
            budget.check()
            relation = repo.relation(ids[i-1], ids[i])
            comparisons.append(dict(before_index=i-1, after_index=i, ancestry=relation,
                                    diagnostics=[{'code': 'ancestry_incomplete'}] if relation == 'unknown' else [],
                                    events=compare(snapshots[i-1], snapshots[i])))
    budget.check()
    return dict(schema_version=SCHEMA_VERSION, semantics_version=SEMANTICS_VERSION,
                object_format=object_format, selection_order='as_supplied',
                scope='Declared dependencies only; no resolution, installation, usage or popularity inference. Timestamps are not adoption dates.',
                limits=asdict(limits), counts=budget.counts.copy(),
                snapshots=snapshots, comparisons=comparisons)
