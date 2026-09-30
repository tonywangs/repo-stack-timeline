from dataclasses import asdict
from . import SCHEMA_VERSION, SEMANTICS_VERSION
from .limits import Limits, Budget
from .errors import TimelineError
from .gitio import ObjectRepository
from .extract import extract
from .compare import compare
from .lockfiles import extract_lockfile, compare_lockfiles


def scan(source, revisions, limits=None, object_format='sha1', budget=None, *, lockfiles=False):
    limits = limits or Limits()
    budget = budget or Budget(limits)
    if not 1 <= len(revisions) <= 32:
        raise TimelineError('snapshot_limit', 'Select between 1 and 32 commit identifiers in comparison order')
    if lockfiles:
        budget.counts.setdefault('package_entries', 0)
        budget.counts.setdefault('lockfile_work', 0)
    snapshots = []
    with ObjectRepository(source, budget, object_format) as repo:
        # Resolve once, before any tree is read. Repeats remain repeats in the report.
        ids = [repo.resolve(r) for r in revisions]
        metadata = {oid: repo.commit(oid) for oid in dict.fromkeys(ids)}
        for i, oid in enumerate(ids):
            budget.check()
            snapshot = dict(metadata[oid], index=i, manifests=[], diagnostics=[])
            if lockfiles:
                snapshot['lockfiles'] = []
            manifests, skipped = repo.manifests(snapshot['tree'], lockfiles)
            snapshot['diagnostics'].extend(skipped)
            manifest_paths = {p for p, *_ in manifests}
            for path, mode, kind, blob in manifests:
                budget.check()
                is_lock = path.rsplit('/', 1)[-1] in ('package-lock.json', 'npm-shrinkwrap.json')
                raw = repo.read_object(blob, 'blob', limits.lockfile_bytes if is_lock else limits.blob_bytes) if mode in ('100644', '100755') and kind == 'blob' else b''
                if is_lock:
                    record = extract_lockfile(path, blob, raw, budget, mode)
                    sibling = path.rsplit('/', 1)[0] + '/npm-shrinkwrap.json' if '/' in path else 'npm-shrinkwrap.json'
                    if path.endswith('package-lock.json') and sibling in manifest_paths:
                        record['diagnostics'].append({'code': 'shrinkwrap_takes_precedence', 'path': sibling})
                    snapshot['lockfiles'].append(record)
                else:
                    snapshot['manifests'].append(extract(path, blob, raw, mode))
            snapshots.append(snapshot)
        comparisons = []
        for i in range(1, len(snapshots)):
            budget.check()
            relation = repo.relation(ids[i-1], ids[i])
            comparisons.append(dict(before_index=i-1, after_index=i, ancestry=relation,
                                    diagnostics=[{'code': 'ancestry_incomplete'}] if relation == 'unknown' else [],
                                    events=compare(snapshots[i-1], snapshots[i])))
            if lockfiles:
                events, diagnostics = compare_lockfiles(snapshots[i-1], snapshots[i], budget)
                comparisons[-1].update(lockfile_events=events, lockfile_diagnostics=diagnostics,
                                       lockfile_status='incomplete' if diagnostics else 'ok')
    budget.check()
    result = dict(schema_version=SCHEMA_VERSION, semantics_version=SEMANTICS_VERSION,
                object_format=object_format, selection_order='as_supplied',
                scope='Declared dependencies only; no resolution, installation, usage or popularity inference. Timestamps are not adoption dates.',
                limits=asdict(limits), counts=budget.counts.copy(),
                snapshots=snapshots, comparisons=comparisons)

    if lockfiles:
        result.update(schema_version='repo-stack-timeline/2', lockfile_semantics_version='npm-lockfiles/1',
                      lockfile_status='incomplete' if any(f['status'] != 'ok' for s in snapshots for f in s['lockfiles']) else 'ok',
                      scope='Declarations and recorded lockfile state only; not installed packages, usage, vulnerability status or verified contents.')
    else:
        for key in ('lockfile_bytes', 'package_entries', 'lockfile_work'):
            result['limits'].pop(key)
    return result
