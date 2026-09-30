"""Recorded npm lockfile state; frozen projection npm-lockfiles/1.

No dependency resolution, path traversal, URL access, or npm execution.
"""
import json
import re
from .extract import _unique_pairs, _invalid_constant

STRINGS = frozenset('name version resolved integrity license deprecated'.split())
BOOLEANS = frozenset('dev optional devOptional peer link inBundle hasInstallScript hasShrinkwrap'.split())
MAPS = frozenset('dependencies devDependencies optionalDependencies peerDependencies engines bin'.split())
ARRAYS = frozenset('os cpu libc workspaces'.split())
FIELDS = STRINGS | BOOLEANS | MAPS | ARRAYS | {'peerDependenciesMeta'}


def extract_lockfile(path, blob, raw, budget, mode='100644'):
    budget.counts.setdefault('lockfile_work', 0)
    result = dict(path=path, blob=blob, mode=mode, status='ok', lockfile_version=None,
                  records=[], diagnostics=[])

    def fail(code):
        result.update(status='incomplete', records=[])
        result['diagnostics'].append(dict(code=code))
        return result

    if mode not in ('100644', '100755'):
        return fail('lockfile_not_regular_file')
    try:
        data = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_pairs,
                          parse_constant=_invalid_constant)
        if not isinstance(data, dict):
            raise ValueError()
    except (ValueError, UnicodeError, RecursionError):
        return fail('malformed_lockfile')
    version = data.get('lockfileVersion')
    if type(version) is not int or version not in (2, 3):
        return fail('unsupported_lockfile_version')
    result['lockfile_version'] = version
    packages = data.get('packages')
    if not isinstance(packages, dict):
        return fail('missing_or_invalid_packages')
    budget.counts.setdefault('package_entries', 0)
    budget.consume('package_entries', len(packages))
    for location, record in sorted(packages.items()):
        budget.consume('lockfile_work')
        # Parent-relative external targets are legitimate npm records. They are
        # opaque identities here, never paths used for filesystem access.
        if location and (location.startswith('/') or '\\' in location or
                         re.match(r'^[A-Za-z]:', location) or
                         any(p in ('', '.') for p in location.split('/')) or
                         any(ord(c) < 32 for c in location)):
            return fail('ambiguous_package_location')
        parts = location.split('/')
        seen_normal = False
        for part in parts:
            if part == '..' and seen_normal:
                return fail('ambiguous_package_location')
            if part != '..':
                seen_normal = True
        if not isinstance(record, dict):
            return fail('invalid_package_record')
        selected = {}
        for key, value in sorted(record.items()):
            budget.consume('lockfile_work', 1 + (len(value) if isinstance(value, (dict, list)) else 0))
            valid = True
            if key == 'workspaces' and isinstance(value, dict):
                valid = set(value) <= {'packages', 'nohoist'} and all(isinstance(v, list) and all(isinstance(x, str) for x in v) for v in value.values())
            elif key == 'peerDependenciesMeta':
                valid = isinstance(value, dict) and all(isinstance(v, dict) and set(v) <= {'optional'} and all(type(x) is bool for x in v.values()) for v in value.values())
            elif key in STRINGS:
                valid = isinstance(value, str)
            elif key in BOOLEANS:
                valid = type(value) is bool
            elif key in MAPS:
                valid = isinstance(value, dict) and all(isinstance(v, str) for v in value.values())
            elif key in ARRAYS:
                valid = isinstance(value, list) and all(isinstance(v, str) for v in value)
            else:
                result['diagnostics'].append(dict(code='unmodeled_field', location=location, field=key))
                continue
            if not valid:
                return fail('invalid_package_metadata')
            selected[key] = value
        if selected.get('link') is True and not selected.get('resolved'):
            return fail('link_target_missing')
        result['records'].append(dict(location=location, metadata=selected))
    return result


def compare_lockfiles(before, after, budget):
    budget.counts.setdefault('lockfile_work', 0)
    left = {f['path']: f for f in before['lockfiles']}
    right = {f['path']: f for f in after['lockfiles']}
    events, diagnostics = [], []
    for path in sorted(left.keys() | right.keys()):
        budget.consume('lockfile_work')
        a, b = left.get(path), right.get(path)
        incomplete = any(f is not None and f['status'] != 'ok' for f in (a, b))
        if incomplete:
            diagnostics.append(dict(code='lockfile_comparison_incomplete', path=path))
        aa = {r['location']: r['metadata'] for r in a['records']} if a else {}
        bb = {r['location']: r['metadata'] for r in b['records']} if b else {}
        for location in sorted(aa.keys() | bb.keys()):
            budget.consume('lockfile_work')
            old, new = aa.get(location), bb.get(location)
            budget.consume('lockfile_work', len(old or {}) + len(new or {}))
            if old == new and not incomplete:
                continue
            changed = sorted(k for k in (old or {}).keys() | (new or {}).keys()
                             if (k in (old or {})) != (k in (new or {})) or (old or {}).get(k) != (new or {}).get(k))
            kind = 'unknown' if incomplete else 'added' if old is None else 'absent' if new is None else 'changed'
            events.append(dict(path=path, location=location, kind=kind, before=old, after=new,
                               changed_fields=[] if incomplete else changed,
                               before_commit=before['commit'], after_commit=after['commit'],
                               before_blob=a['blob'] if a else None, after_blob=b['blob'] if b else None))
    return events, diagnostics
