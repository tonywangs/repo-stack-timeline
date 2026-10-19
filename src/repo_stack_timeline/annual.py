"""Bounded annual root-runtime declaration study; independent of CLI schema 1/2."""
import ast
import base64
import configparser
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import tomllib
from .extract import extract, _unique_pairs, _invalid_constant
from ._vendor.packaging.requirements import Requirement
from ._vendor.packaging.utils import canonicalize_name


def canonical(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + '\n').encode()


def git_hash(kind, raw):
    return hashlib.sha1(kind.encode() + b' ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def select_years(history, years):
    """Topology order is authoritative, including non-monotonic commit timestamps."""
    return {year: next((commit for commit, stamp in history
        if stamp < int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp())), None)
        for year in years}


def tree_entries(raw):
    entries = {}
    while raw:
        end = raw.index(b'\0')
        mode, path = raw[:end].split(b' ', 1)
        if len(raw) < end + 21:
            raise ValueError('truncated tree')
        entries[path.decode()] = (mode.decode(), raw[end + 1:end + 21].hex())
        raw = raw[end + 21:]
    return entries


def verify_source(source, member, cohort):
    """Verify commit -> root tree -> manifest/license bytes, offline."""
    for key in ('repository', 'ecosystem', 'license'):
        if source[key] != member[key]:
            raise ValueError('cohort/source identity mismatch')
    if source['cohort_sha256'] != hashlib.sha256(canonical(cohort)).hexdigest():
        raise ValueError('cohort digest mismatch')
    if [s['year'] for s in source['snapshots']] != cohort['years']:
        raise ValueError('missing, duplicate or reordered annual samples')
    for snap in source['snapshots']:
        if snap['status'] == 'unavailable_history':
            if snap['commit'] is not None:
                raise ValueError('unavailable history has commit')
            continue
        if snap['status'] != 'acquired' or not re.fullmatch('[0-9a-f]{40}', snap['commit']):
            raise ValueError('invalid acquired snapshot')
        raw_commit = base64.b64decode(snap['commit_base64'], validate=True)
        raw_tree = base64.b64decode(snap['tree_base64'], validate=True)
        if git_hash('commit', raw_commit) != snap['commit'] or git_hash('tree', raw_tree) != snap['tree']:
            raise ValueError('Git object digest mismatch')
        if raw_commit.splitlines()[0] != b'tree ' + snap['tree'].encode():
            raise ValueError('commit tree mismatch')
        committer = next(line for line in raw_commit.split(b'\n\n', 1)[0].splitlines() if line.startswith(b'committer '))
        stamp = int(committer.rsplit(b' ', 2)[1])
        cutoff = int(datetime(snap['year'] + 1, 1, 1, tzinfo=timezone.utc).timestamp())
        if stamp != snap['committer_timestamp'] or stamp >= cutoff:
            raise ValueError('snapshot outside cutoff')
        entries = tree_entries(raw_tree)
        expected = {path for path in entries if path in ('package.json', 'pyproject.toml', 'setup.py', 'setup.cfg')
                    or path.lower() in ('license', 'license.txt', 'license.rst', 'license.md')}
        if len(snap['files']) != len(expected) or {f['path'] for f in snap['files']} != expected:
            raise ValueError('incomplete or duplicated root evidence')
        if not any(path.lower().startswith('license') for path in expected):
            raise ValueError('missing source license')
        for file in snap['files']:
            raw = base64.b64decode(file['base64'], validate=True)
            if len(raw) != file['bytes'] or hashlib.sha256(raw).hexdigest() != file['sha256']:
                raise ValueError('file digest mismatch')
            if git_hash('blob', raw) != file['blob'] or entries[file['path']] != (file['mode'], file['blob']):
                raise ValueError('blob tree mismatch')
            if file['url'] != f"https://github.com/{member['repository']}/blob/{snap['commit']}/{file['path']}":
                raise ValueError('source URL mismatch')


def runtime(files, ecosystem):
    """Conservative measurement of explicit declarations, never execute setup.py.

    Legacy AST support reports literal keywords only. Omission is unknown because
    setuptools may load other configuration. Marker conditions are preserved,
    not evaluated; presence means declared under at least one condition.
    """
    def result(status, reason, path=None, declarations=None):
        return dict(status=status, reason=reason, manifest=path, declarations=declarations or [])

    def requirements(values, path, category):
        if not isinstance(values, list) or any(not isinstance(x, str) for x in values):
            return result('unsupported_metadata', 'runtime requirements are not a literal string list', path)
        declarations = []
        for value in values:
            req = Requirement(value)
            declarations.append(dict(name=canonicalize_name(req.name), raw=value, category=category,
                marker=str(req.marker) if req.marker else None, extras=sorted(req.extras)))
        return result('observed', 'explicit runtime declarations', path, declarations)

    try:
        if ecosystem == 'npm':
            if 'package.json' not in files:
                return result('missing_manifest', 'no root package.json')
            data = json.loads(files['package.json'], object_pairs_hook=_unique_pairs, parse_constant=_invalid_constant)
            if not isinstance(data, dict):
                raise ValueError('package.json is not an object')
            parsed = extract('package.json', '', files['package.json'])
            if parsed['uncertain_all'] or 'dependencies' in parsed['uncertain_categories']:
                return result('unsupported_metadata', 'invalid runtime dependencies', 'package.json')
            # npm optionalDependencies overrides dependencies of the same name.
            # Those names are outside this study's required-runtime scope.
            optional = data.get('optionalDependencies', {})
            if not isinstance(optional, dict):
                return result('unsupported_metadata', 'invalid optionalDependencies override', 'package.json')
            rows = [dict(name=d['name'], raw=d['values'][0]['raw'], category='dependencies', marker=None, extras=[])
                    for d in parsed['declarations'] if d['category'] == 'dependencies' and d['name'] not in optional]
            return result('observed', 'root dependencies excluding optional overrides', 'package.json', rows)
        if 'pyproject.toml' in files:
            data = tomllib.loads(files['pyproject.toml'].decode())
            if 'project' in data:
                parsed = extract('pyproject.toml', '', files['pyproject.toml'])
                if parsed['uncertain_all'] or 'project.dependencies' in parsed['uncertain_categories']:
                    return result('unsupported_metadata', 'dynamic or invalid project.dependencies', 'pyproject.toml')
                return requirements(data['project'].get('dependencies', []), 'pyproject.toml', 'project.dependencies')
        # Prefer explicit setup.py keyword over setup.cfg; it can override it.
        if 'setup.py' in files:
            tree = ast.parse(files['setup.py'])
            calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and
                     (isinstance(n.func, ast.Name) and n.func.id == 'setup' or
                      isinstance(n.func, ast.Attribute) and n.func.attr == 'setup')]
            if len(calls) != 1:
                return result('unsupported_metadata', 'ambiguous setup call', 'setup.py')
            call = calls[0]
            if not any(isinstance(n, ast.Expr) and n.value is call for n in tree.body) or any(k.arg is None for k in call.keywords):
                return result('unsupported_metadata', 'conditional/nested setup or keyword expansion', 'setup.py')
            values = [k.value for k in call.keywords if k.arg == 'install_requires']
            if len(values) == 1:
                try:
                    literal = ast.literal_eval(values[0])
                except (ValueError, TypeError):
                    return result('unsupported_metadata', 'nonliteral install_requires', 'setup.py')
                return requirements(literal, 'setup.py', 'install_requires (literal AST)')
            if len(values) > 1:
                return result('unsupported_metadata', 'duplicate install_requires', 'setup.py')
        if 'setup.cfg' in files:
            config = configparser.ConfigParser(interpolation=None)
            config.read_string(files['setup.cfg'].decode())
            if config.has_option('options', 'install_requires'):
                value = config.get('options', 'install_requires')
                if value.strip().startswith(('file:', 'attr:')):
                    return result('unsupported_metadata', 'indirect install_requires', 'setup.cfg')
                return requirements([x.strip() for x in value.splitlines() if x.strip() and not x.lstrip().startswith('#')],
                                    'setup.cfg', 'options.install_requires')
        if any(p in files for p in ('setup.py', 'setup.cfg', 'pyproject.toml')):
            return result('unsupported_metadata', 'no explicit supported runtime dependency field')
        return result('missing_manifest', 'no supported root Python metadata file')
    except (ValueError, TypeError, SyntaxError, UnicodeError, configparser.Error, RecursionError) as error:
        return result('unsupported_metadata', 'invalid metadata: ' + type(error).__name__)


def analyze(cohort, sources):
    snapshots = []
    for member in cohort['repositories']:
        source = sources[member['repository']]
        verify_source(source, member, cohort)
        for snap in source['snapshots']:
            if snap['status'] == 'unavailable_history':
                row = dict(status='unavailable_history', reason='no eligible commit in frozen complete lineage', manifest=None, declarations=[])
            else:
                relevant = [f for f in snap['files'] if f['path'] in ('package.json', 'pyproject.toml', 'setup.py', 'setup.cfg')]
                if any(f['mode'] not in ('100644', '100755') for f in relevant):
                    row = dict(status='unsupported_metadata', reason='nonregular metadata file', manifest=None, declarations=[])
                else:
                    row = runtime({f['path']: base64.b64decode(f['base64']) for f in relevant}, member['ecosystem'])
            row.update(repository=member['repository'], ecosystem=member['ecosystem'], year=snap['year'], commit=snap['commit'])
            row['names'] = sorted({d['name'] for d in row['declarations']})
            row['source_url'] = (f"https://github.com/{member['repository']}/blob/{snap['commit']}/{row['manifest']}"
                                 if row['manifest'] else None)
            snapshots.append(row)
    return summarize(cohort, snapshots)


def summarize(cohort, snapshots):
    years = cohort['years']
    fixed = {eco: [r['repository'] for r in cohort['repositories'] if r['ecosystem'] == eco and
             all(s['status'] == 'observed' for s in snapshots if s['repository'] == r['repository'])]
             for eco in ('npm', 'python')}
    indexes = {(s['repository'], s['year']): s for s in snapshots}
    summaries = []
    for eco in ('npm', 'python'):
        members = [r['repository'] for r in cohort['repositories'] if r['ecosystem'] == eco]
        universe = sorted({name for s in snapshots if s['ecosystem'] == eco for name in s['names']})
        for mode in ('available', 'fixed'):
            eligible = members if mode == 'available' else fixed[eco]
            for year in years:
                rows = [indexes[r, year] for r in eligible]
                known = [s for s in rows if s['status'] == 'observed']
                previous = years[years.index(year)-1] if year != years[0] else None
                pairs = [(indexes[s['repository'], previous], s) for s in known
                         if previous is not None and indexes[s['repository'], previous]['status'] == 'observed']
                dependencies = []
                for name in universe:
                    present = [s['repository'] for s in known if name in s['names']]
                    adopted = [b['repository'] for a, b in pairs if name not in a['names'] and name in b['names']]
                    removed = [b['repository'] for a, b in pairs if name in a['names'] and name not in b['names']]
                    persisted = [b['repository'] for a, b in pairs if name in a['names'] and name in b['names']]
                    absent_before = sum(name not in a['names'] for a, _ in pairs)
                    present_before = len(pairs) - absent_before
                    dependencies.append(dict(name=name, present=present, numerator=len(present), denominator=len(known),
                        share=len(present)/len(known) if known else None,
                        adopted=adopted, removed=removed, persisted=persisted,
                        adoption_denominator=absent_before if previous else None,
                        removal_denominator=present_before if previous else None,
                        persistence_denominator=present_before if previous else None))
                summaries.append(dict(ecosystem=eco, mode=mode, year=year, cohort_size=len(eligible),
                    observed=len(known), unknown=len(rows)-len(known), paired=len(pairs) if previous else None,
                    unknown_pairs=len(eligible)-len(pairs) if previous else None,
                    dependencies=dependencies))
    return dict(schema='annual-trends/1', years=years, cohort=cohort, fixed_members=fixed,
                snapshots=snapshots, summaries=summaries)


def load_study(root):
    cohort = json.loads((root / 'cohort.json').read_text())
    sources = {r['repository']: json.loads((root / 'sources' / (r['repository'].replace('/', '--') + '.json')).read_text())
               for r in cohort['repositories']}
    return analyze(cohort, sources)
