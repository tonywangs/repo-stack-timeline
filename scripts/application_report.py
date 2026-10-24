#!/usr/bin/env python3
"""Reproduce the application-extension coverage experiment offline."""
import argparse
import base64
import html
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from repo_stack_timeline.annual import canonical, load_study
from repo_stack_timeline.categories import description
import json
import re


def build():
    app = load_study(ROOT / 'examples/applications')
    library = load_study(ROOT / 'examples/annual')
    observations = []
    for member in app['cohort']['repositories']:
        source = json.loads((ROOT / 'examples/applications/sources' /
                            (member['repository'].replace('/', '--') + '.json')).read_text())
        for snap in source['snapshots']:
            manifest = next((f for f in snap.get('files', []) if f['path'] == 'package.json'), None)
            observations.append(dict(repository=member['repository'], year=snap['year'],
                selection_stratum=member['selection_stratum'],
                description=description('package.json', base64.b64decode(manifest['base64'])) if manifest else None,
                source_url=manifest['url'] if manifest else None))
    comparison = []
    for year in app['years']:
        for label, study in [('application', app), ('library', library)]:
            # Compare the same ecosystem; never pool Python and npm denominators.
            rows = [s for s in study['snapshots'] if s['year'] == year and s['ecosystem'] == 'npm']
            known = [s for s in rows if s['status'] == 'observed']
            comparison.append(dict(year=year, stratum=label, members=len(rows), observed=len(known),
                unknown=len(rows)-len(known), zero_root_sets=sum(not r['names'] for r in known),
                repository_name_pairs=sum(len(r['names']) for r in known)))
    return dict(schema='application-extension/1', application_study=app,
                annual_descriptions=observations, comparison=comparison)


def markdown(data):
    study = data['application_study']
    rows = study['snapshots']
    lines = ['# Applications alongside the library cohort', '',
        'A bounded 2019–2025 public-data extension. Two application cases supplement the eight-library study; '
        'the comparison below uses only its four JavaScript libraries. No GitHub-wide estimates are made.', '',
        '## Findings', '',
        f"Of {len(rows)} application snapshots, {sum(r['status'] == 'observed' for r in rows)} have observable root declarations; "
        f"{sum(r['status'] != 'observed' for r in rows)} are unknown. Counts and changes below concern only that root scope.", '',
        '## Design and limits', '', study['cohort']['selection_rule'], '',
        'Application purpose was used to select cases before extracting annual manifests. These current selection '
        'strata must not be interpreted as annual labels: the exact annual descriptions below are evidence for '
        'inspection, not a validated project-type classifier. Neither separate owner names nor these two cases '
        'establish statistical independence of governance.', '',
        'Both added cases (2/2) are surviving public projects at acquisition. Together with the prior study, '
        '10/10 cases are selected survivors; 4/10 share Pallets governance. There are zero sampled deleted or '
        'inaccessible projects. Inclusion probabilities, survival probabilities, entry/exit rates and coverage '
        'of all GitHub project categories remain unidentifiable. This expansion does not repair population sampling.', '',
        'Root runtime declarations omit nested application packages, plugins, optional and development dependencies. '
        'An observed zero means zero required names in that root manifest, not a dependency-free application. '
        'A missing root manifest is unknown. Root structure changes can therefore dominate apparent stack changes.', '',
        '## Annual comparison', '',
        'Pairs are sums of distinct declared names per repository, not unique ecosystem packages or installations. '
        'Different stratum sizes and missing coverage make raw totals unsuitable for popularity comparisons.', '',
        '| Year | Selection stratum | Members | Observed | Unknown | Zero root sets | Repository/name pairs |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for r in data['comparison']:
        lines.append('| ' + ' | '.join(str(r[k]) for k in ['year','stratum','members','observed','unknown','zero_root_sets','repository_name_pairs']) + ' |')
    lines += ['', '## Application observations', '', '| Repository / year | Status | Root names | Annual description |',
              '| --- | --- | ---: | --- |']
    descriptions = {(r['repository'], r['year']): r for r in data['annual_descriptions']}
    for r in rows:
        desc = descriptions[r['repository'], r['year']]['description'] or 'unknown'
        url = r['source_url'] or f"https://github.com/{r['repository']}/tree/{r['commit']}"
        name = f"[{r['repository']} {r['year']}]({url})" if r['commit'] else f"{r['repository']} {r['year']}"
        count = str(len(r['names'])) if r['status'] == 'observed' else 'unknown'
        lines.append(f"| {name} | {r['status']} | {count} | {desc.replace('|', chr(92)+'|').replace(chr(10), ' ')} |")
    lines += ['', '## Adjacent-year declaration changes', '',
              'Only pairs with observed root declarations at both endpoints are compared. These are changes '
              'in declarations at annual snapshots, not dates of first technology use.', '',
              '| Repository | Interval | Added names | Removed names |', '| --- | --- | --- | --- |']
    for member in study['cohort']['repositories']:
        rr = [r for r in rows if r['repository'] == member['repository']]
        for a, b in zip(rr, rr[1:]):
            known = a['status'] == b['status'] == 'observed'
            added = ', '.join(sorted(set(b['names'])-set(a['names']))) or 'none'
            removed = ', '.join(sorted(set(a['names'])-set(b['names']))) or 'none'
            lines.append(f"| {member['repository']} | {a['year']}–{b['year']} | {added if known else 'unknown'} | {removed if known else 'unknown'} |")
    lines += ['', '## Reproduce and inspect', '',
        '`python3 scripts/application_report.py --check` verifies preserved Git objects and all report artifacts. '
        '`python3 scripts/application_report.py --output /tmp/application-report` creates a fresh report. '
        'Open `index.html` locally or inspect `report.json` for declarations and coverage denominators. '
        'See [source documentation](../../examples/applications/README.md) for acquisition and licenses.', '',
        'The original project-population question remains open. Next evidence needed: a historical sampling frame '
        'that can represent entry/exit, and nested-manifest measurement before interpreting application stacks. '
        'No independent review is claimed for this extension.', '']
    return '\n'.join(lines)


def render(md):
    """Small renderer for this report's controlled Markdown structure."""
    def inline(text):
        escaped = html.escape(text)
        escaped = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', escaped)
        return re.sub(r'`([^`]+)`', r'<code>\1</code>', escaped)
    output = []
    table = False
    for line in md.splitlines():
        if line.startswith('| '):
            if not table:
                output.append('<table>')
                table = True
                tag = 'th'
            else:
                tag = 'td'
            if re.fullmatch(r'[| :\-]+', line):
                continue
            cells = line.strip('| ').split(' | ')
            output.append('<tr>' + ''.join(f'<{tag}>{inline(c)}</{tag}>' for c in cells) + '</tr>')
        else:
            if table:
                output.append('</table>')
                table = False
            if line.startswith('#'):
                depth = len(line)-len(line.lstrip('#'))
                output.append(f'<h{depth}>{inline(line[depth:].strip())}</h{depth}>')
            elif line:
                output.append('<p>' + inline(line) + '</p>')
    if table:
        output.append('</table>')
    return '\n'.join(output)


def artifacts():
    data = build()
    md = markdown(data)
    page = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Application extension</title><style>body{max-width:1100px;margin:2rem auto;padding:1rem;font:16px system-ui;line-height:1.5}table{border-collapse:collapse;display:block;overflow:auto}td,th{padding:.5rem;border:1px solid #bbb;text-align:left}code{background:#eee}a{color:#1455a0}</style><p><a href="report.md">Markdown</a> · <a href="report.json">Auditable JSON</a></p>' + render(md) + '</html>\n'
    return {'report.json': canonical(data), 'report.md': md.encode(), 'index.html': page.encode()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--output', type=Path)
    args = p.parse_args()
    files = artifacts()
    if args.check:
        for name, raw in files.items():
            if (ROOT / 'results/applications' / name).read_bytes() != raw:
                raise ValueError('application report mismatch: ' + name)
        print('Verified application source objects and byte-identical report artifacts.')
    else:
        args.output.mkdir(parents=True, exist_ok=False)
        for name, raw in files.items():
            (args.output / name).write_bytes(raw)
        print(args.output / 'index.html')


if __name__ == '__main__':
    main()
