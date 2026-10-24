"""Exploratory category measurement from frozen annual self-descriptions.

Rules were chosen after inspecting the cohort, not preregistered. They describe
package purpose, not an inferred GitHub population or actual runtime usage.
"""
import ast
import base64
import configparser
import json
import re
import tomllib
from .annual import load_study

RULES = {
    'web-framework': r'(?=.*\bweb\b)(?=.*\bframework\b)',
    'command-line-toolkit': r'command[ -]line',
    'terminal-styling': r'terminal.*styl',
    'template-engine': r'template engine',
    'data-signing': r'(untrusted environments|cryptographically sign)',
}


def classify(description):
    matches = [name for name, pattern in RULES.items()
               if re.search(pattern, description.lower(), re.DOTALL)]
    return matches[0] if len(matches) == 1 else 'unknown'


def description(path, raw):
    """Read static description only; never execute upstream Python."""
    if path == 'package.json':
        value = json.loads(raw).get('description')
    elif path == 'pyproject.toml':
        project = tomllib.loads(raw.decode()).get('project', {})
        value = None if 'description' in project.get('dynamic', []) else project.get('description')
    elif path == 'setup.cfg':
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.read_string(raw.decode())
        value = cfg.get('metadata', 'description', fallback=None)
        if value and value.startswith(('file:', 'attr:')):
            value = None
    elif path == 'setup.py':
        tree = ast.parse(raw)
        calls = [node.value for node in tree.body if isinstance(node, ast.Expr)
                 and isinstance(node.value, ast.Call)
                 and isinstance(node.value.func, ast.Name) and node.value.func.id == 'setup']
        values = [kw.value.value for call in calls for kw in call.keywords
                  if kw.arg == 'description' and isinstance(kw.value, ast.Constant)
                  and isinstance(kw.value.value, str)]
        value = values[0] if len(calls) == 1 and len(values) == 1 else None
    else:
        value = None
    return value if isinstance(value, str) and value.strip() else None


def build(root):
    study = load_study(root)  # verifies every source object before reading text
    observations = {(s['repository'], s['year']): s for s in study['snapshots']}
    rows = []
    for member in study['cohort']['repositories']:
        source = json.loads((root / 'sources' / (member['repository'].replace('/', '--') + '.json')).read_text())
        for snap in source['snapshots']:
            files = {f['path']: f for f in snap.get('files', [])}
            evidence = None
            text = None
            paths = ['package.json'] if member['ecosystem'] == 'npm' else ['pyproject.toml', 'setup.cfg', 'setup.py']
            for path in paths:
                if path in files:
                    text = description(path, base64.b64decode(files[path]['base64']))
                    if text:
                        evidence = files[path]
                        break
            obs = observations[member['repository'], snap['year']]
            rows.append(dict(repository=member['repository'], ecosystem=member['ecosystem'], year=snap['year'],
                category=classify(text) if text else 'unknown', description=text,
                source_url=evidence['url'] if evidence else None,
                source_sha256=evidence['sha256'] if evidence else None,
                stack_status=obs['status'], names=obs['names']))
    summaries = []
    for year in study['years']:
        for category in sorted(set(RULES) | {'unknown'}):
            for eco in ['npm', 'python']:
                selected = [r for r in rows if (r['year'], r['category'], r['ecosystem']) == (year, category, eco)]
                known = [r for r in selected if r['stack_status'] == 'observed']
                summaries.append(dict(year=year, category=category, ecosystem=eco,
                    members=len(selected), stack_observed=len(known), stack_unknown=len(selected)-len(known),
                    declared_names=sorted({n for r in known for n in r['names']}),
                    repository_name_pairs=sum(len(r['names']) for r in known)))
    pairs = [(a, b) for a in rows for b in rows if a['repository'] == b['repository'] and b['year'] == a['year']+1]
    comparable = [(a,b) for a,b in pairs if 'unknown' not in (a['category'], b['category'])]
    return dict(schema='annual-categories/1', rules=RULES, years=study['years'], rows=rows, summaries=summaries,
                comparable_pairs=len(comparable), unknown_pairs=len(pairs)-len(comparable),
                changed_pairs=sum(a['category'] != b['category'] for a,b in comparable))


def markdown(data):
    lines = ['# Annual project categories and declared stacks', '',
        'Exploratory appendix to the eight-repository 2019–2025 [dependency study](../annual/report.md).', '',
        'Categories measure annual package self-descriptions with disclosed keyword rules, chosen after inspecting the cohort. '
        'They are not independent human labels, a validated classifier, or evidence of GitHub-wide category prevalence. '
        'Ambiguous or unmatched descriptions are unknown. Each row retains the exact description and immutable source link.', '',
        f"Observed category changes: **{data['changed_pairs']}/{data['comparable_pairs']}** comparable adjacent-year repository pairs; "
        f"{data['unknown_pairs']} pairs have unknown categories. A stable label does not prove stable functionality.", '',
        'All 8/8 members were selected from surviving projects at acquisition; 4/8 share Pallets governance. '
        'This design includes zero deleted/inaccessible repositories and zero applications. Survival probability and '
        'GitHub-wide category coverage cannot be estimated from this sample. Fixed membership makes category shares '
        'insensitive to projects entering or leaving GitHub. Unknown runtime metadata remains unknown even when a category is measurable.', '',
        '## Annual category / ecosystem counts', '',
        'Pairs counts distinct declared dependency names per repository, summed across observed members; '
        'it is not a usage, installation, or unique-package count. Ecosystems remain separate.', '',
        '| Year | Category | Ecosystem | Members | Stack observed | Stack unknown | Pairs |',
        '| --- | --- | --- | ---: | ---: | ---: | ---: |']
    for s in data['summaries']:
        if s['members']:
            lines.append('| ' + ' | '.join(str(s[k]) for k in ['year','category','ecosystem','members','stack_observed','stack_unknown','repository_name_pairs']) + ' |')
    lines += ['', '## Annual classification evidence', '', '| Repository / year | Category | Exact description |', '| --- | --- | --- |']
    for r in data['rows']:
        label = f"{r['repository']} {r['year']}"
        if r['source_url']:
            label = f"[{label}]({r['source_url']})"
        desc = (r['description'] or 'unknown').replace('|', '\\|').replace('\n', ' ')
        lines.append(f"| {label} | {r['category']} | {desc} |")
    lines += ['', '## Reproduce', '',
        '`python3 scripts/category_report.py --check` verifies source objects and byte-identical results. '
        '`python3 scripts/category_report.py --output /tmp/annual-categories` creates fresh Markdown and JSON. '
        'The JSON includes rule expressions, source hashes, annual declared names, and all zero-member cells. '
        'The original acquisition and missing-data rules remain in [the source documentation](../../examples/annual/README.md).', '',
        'This checkpoint adds category evidence to the existing convenience sample. A broader study of changing project '
        'types still needs a defined sampling frame that includes applications, entry/exit, and independent governance. '
        'Do not treat this appendix as answering those population questions.', '']
    return '\n'.join(lines)
