"""Compare adjacent *selected* snapshots; never infer install/removal dates."""


def index(snapshot):
    return {(m['path'], m['ecosystem'], d['category'], d['name']): d['values']
            for m in snapshot['manifests'] for d in m['declarations']}


def known_absence(snapshot, key):
    path, ecosystem, category, _ = key
    manifest = next((m for m in snapshot['manifests'] if m['path'] == path), None)
    if manifest is None:
        return True  # Tree enumeration must finish before any report is built.
    if manifest['uncertain_all']:
        return False
    return not any(category == x or (x.endswith('.*') and category.startswith(x[:-1]))
                   for x in manifest['uncertain_categories'])


def compare(before, after):
    left, right = index(before), index(after)
    blobs = [{m['path']: m['blob'] for m in s['manifests']} for s in (before, after)]
    events = []
    for key in sorted(left.keys() | right.keys()):
        a, b = left.get(key), right.get(key)
        if a == b:
            continue
        kind = 'changed' if a is not None and b is not None else 'added' if a is None else 'absent'
        # Even a present name can have additional unreadable declarations in
        # the same category. Show the observed difference as uncertain.
        if not known_absence(before, key) or not known_absence(after, key):
            kind = 'unknown'
        path, ecosystem, category, name = key
        events.append(dict(kind=kind, path=path, ecosystem=ecosystem, category=category, name=name,
                           before=a, after=b, before_commit=before['commit'], after_commit=after['commit'],
                           before_blob=blobs[0].get(path), after_blob=blobs[1].get(path)))
    return events
