"""Deterministic Markdown and self-contained HTML for the frozen annual study."""
import html
import json


def markdown(study):
    years = study['years']
    rows = study['snapshots']
    by_key = {(s['repository'], s['year']): s for s in rows}
    summaries = {(s['ecosystem'], s['mode'], s['year']): s for s in study['summaries']}
    def link(repo, year):
        s = by_key[repo, year]
        url = s['source_url'] or f"https://github.com/{repo}/tree/{s['commit']}"
        return f"[{repo} {year}]({url})"
    def dep(eco, mode, year, name):
        return next(d for d in summaries[eco, mode, year]['dependencies'] if d['name'] == name)
    def share(eco, mode, year, name):
        d = dep(eco, mode, year, name)
        return f"{d['numerator']}/{d['denominator']}"
    lines = ['# Declared dependency trends, 2019–2025', '',
        'Eight public repositories · seven year-end samples · root runtime declarations only', '',
        'This retrospective study answers how declared dependency names changed within a small, '
        'frozen convenience cohort. It does not estimate GitHub-wide popularity, installed packages, '
        'code usage, release history, or adoption dates. All counts are repository counts, not download counts.', '',
        '## Concrete findings', '',
        f"- Chalk's root runtime declaration count went from {len(by_key['chalk/chalk', 2020]['names'])} in "
        f"{link('chalk/chalk', 2020)} to {len(by_key['chalk/chalk', 2021]['names'])} in {link('chalk/chalk', 2021)}. "
        'The removed names are `ansi-styles` and `supports-color`. This does not establish that their functionality disappeared or that no code was vendored.',
        f"- Koa's root runtime declaration count fell from {len(by_key['koajs/koa', 2019]['names'])} in "
        f"{link('koajs/koa', 2019)} to {len(by_key['koajs/koa', 2025]['names'])} in {link('koajs/koa', 2025)}. "
        'These are net endpoint counts; the interval tables retain additions and removals separately.',
        f"- Flask first shows `blinker` in our {link('pallets/flask', 2023)} sample, absent in {link('pallets/flask', 2022)}. "
        f"Its 2023 prevalence is {share('python', 'available', 2023, 'blinker')} among observed Python repositories "
        f"and {share('python', 'fixed', 2023, 'blinker')} in the all-years-observed Python cohort. This brackets a declaration change, not the project's first use.",
        f"- Python `markupsafe` illustrates denominator sensitivity: observed-cohort prevalence is "
        f"{share('python', 'available', 2019, 'markupsafe')} in 2019 and {share('python', 'available', 2025, 'markupsafe')} in 2025; "
        f"the fixed cohort instead changes from {share('python', 'fixed', 2019, 'markupsafe')} to {share('python', 'fixed', 2025, 'markupsafe')}. "
        f"Compare {link('pallets/flask', 2024)} with {link('pallets/flask', 2025)} and {link('pallets/jinja', 2019)}. "
        'A stable available-case share can conceal a change when the denominator expands.',
        f"- Commander has zero root runtime declarations in all seven observed samples ({link('tj/commander.js', 2019)}; "
        f"{link('tj/commander.js', 2025)}). Early Click/ItsDangerous samples, in contrast, are unknown: omitted legacy "
        '`install_requires` is not interpreted as an observed zero.', '',
        '## Cohort and coverage', '', study['cohort']['selection_rule'], '',
        '**Exclusions.** ' + study['cohort']['exclusions'], '',
        '| Repository | Ecosystem | License | ' + ' | '.join(map(str, years)) + ' |',
        '| --- | --- | --- | ' + ' | '.join('---' for _ in years) + ' |']
    for r in study['cohort']['repositories']:
        cells = []
        for year in years:
            s = by_key[r['repository'], year]
            cells.append(str(len(s['names'])) if s['status'] == 'observed' else s['status'])
        lines.append(f"| {r['repository']} | {r['ecosystem']} | {r['license']} | " + ' | '.join(cells) + ' |')
    lines += ['', 'Numbers above are observed distinct runtime names. Unknown cells are excluded from prevalence and paired transitions.', '',
        '| Ecosystem / sample | ' + ' | '.join(map(str, years)) + ' |',
        '| --- | ' + ' | '.join('---' for _ in years) + ' |']
    for eco in ('npm', 'python'):
        for mode in ('available', 'fixed'):
            lines.append(f'| {eco} / {mode} observed | ' + ' | '.join(str(summaries[eco, mode, y]['observed']) for y in years) + ' |')
        lines.append(f'| {eco} adjacent-year comparable pairs | — | ' + ' | '.join(str(summaries[eco, 'available', y]['paired']) for y in years[1:]) + ' |')
    lines += ['', 'Fixed cohort requires an observed runtime set in **every** year. Membership is computed after extraction '
        'without replacing any original member. It is a coverage sensitivity analysis, not a representative subset.', '']
    for eco, members in study['fixed_members'].items():
        lines.append(f"- {eco}: " + (', '.join(members) or 'empty; prevalence undefined'))
    lines += ['', '## Annual prevalence', '',
        'Each cell is repositories declaring the name / repositories with observable runtime metadata in that ecosystem and sample. '
        'A repository counts once regardless of constraints or repeated declarations. Conditional Python requirements count as declared; '
        'markers and original strings remain in report.json. Ecosystems are never pooled.', '']
    for eco in ('npm', 'python'):
        for mode in ('available', 'fixed'):
            lines += [f'### {eco}: {mode}', '', '| Dependency | ' + ' | '.join(map(str, years)) + ' |',
                      '| --- | ' + ' | '.join('---' for _ in years) + ' |']
            for d in summaries[eco, mode, years[0]]['dependencies']:
                lines.append('| ' + d['name'] + ' | ' + ' | '.join(share(eco, mode, y, d['name']) for y in years) + ' |')
            lines.append('')
    lines += ['## Adoption, removal and persistence', '',
        'An adoption is absent→present; removal is present→absent; persistence is present→present between adjacent annual '
        'samples with both endpoints observed. Unknown endpoints never become removals or adoptions. The first year is only a baseline. '
        'The table sums repository–dependency events, so totals can exceed repository counts. The JSON and HTML provide each name, '
        'repository, and risk denominator: adoption / previously absent paired repositories; removal or persistence / previously present '
        'paired repositories. Zero risk denominators mean undefined rates, not zero percent.', '',
        '| Ecosystem / sample | Interval | Comparable repositories | Unknown pairs | Adoptions | Removals | Persistences |',
        '| --- | --- | --- | --- | --- | --- | --- |']
    for s in study['summaries']:
        if s['year'] == years[0]:
            continue
        totals = [sum(len(d[key]) for d in s['dependencies']) for key in ('adopted', 'removed', 'persisted')]
        lines.append(f"| {s['ecosystem']} / {s['mode']} | {s['year']-1}→{s['year']} | {s['paired']} | {s['unknown_pairs']} | " + ' | '.join(map(str, totals)) + ' |')
    lines += ['', '## Auditable annual observations', '',
        'Every link identifies an exact source commit. Original manifest and license bytes, Git commit and root-tree objects, '
        'blob IDs, and SHA-256 checksums are retained in the source shards. Unknown rows link to their commit tree.', '',
        '| Source | Commit | Status | Runtime names / coverage reason |', '| --- | --- | --- | --- |']
    for s in rows:
        content = ', '.join(s['names']) or ('observed empty' if s['status'] == 'observed' else s['reason'])
        lines.append(f"| {link(s['repository'], s['year'])} | `{s['commit']}` | {s['status']} | {content} |")
    lines += ['', '## Method and limitations', '', study['cohort']['sampling_rule'], '',
        'The sample was frozen before annual extraction on ' + study['cohort']['frozen_on'] + '. '
        'All eight histories were acquired anonymously from public GitHub repositories, with no upstream code execution. '
        'The frozen current default-branch lineage can include unreleased development: notably, Express samples are not a series of stable releases. '
        'Commit clocks can be wrong; first-parent topology determines the first qualifying commit, not the greatest timestamp. '
        'Repeated commits across years are allowed and mean no qualifying newer lineage snapshot.', '',
        'Python measurement precedence is static `[project].dependencies`, then an explicit literal `install_requires` '
        'keyword in a single top-level setup call, then explicit `[options] install_requires` in setup.cfg. Dynamic metadata, '
        'keyword expansion, nested/conditional setup calls and indirect requirements are unknown. AST extraction measures literal '
        'declarations only, not effective execution of arbitrary Python. A legacy omitted field is unknown; an omitted static '
        'PEP 621 dependency field is empty. JavaScript measures `dependencies`, excluding names overridden by `optionalDependencies`. '
        'Build, dev, extras, optional and peer dependencies and nested manifests are outside the study.', '',
        'The four Python repositories share Pallets governance and dependency relationships; the JavaScript members mix two web '
        'frameworks with two CLI libraries. Selection favors established surviving permissively licensed projects. Repository observations '
        'are not independent and the cohort is not random. There are no confidence intervals or extrapolated population claims. '
        'Annual sampling misses changes reversed within a year. Name changes, bundling, vendoring, conditional requirements, and changing '
        'metadata formats can change measured declarations without changing actual usage. The fixed cohort controls denominator membership, '
        'not these biases. There is no stochastic experiment or random seed: input objects and algorithms are deterministic.', '',
        '## Reproduce and inspect', '',
        'From the project root, with Python 3.11+: `python3 scripts/annual_report.py --output /tmp/annual-trends`. '
        'Open `/tmp/annual-trends/index.html`; Markdown and machine-readable JSON are beside it. This command is offline, verifies '
        'source objects, and refuses an existing output directory. `python3 scripts/annual_report.py --check` verifies checked-in results. '
        'For a full network history audit, use `python3 scripts/acquire_annual.py --cache /tmp/annual-history`: existing source records '
        'pin all heads and must reproduce byte-for-byte. Git is required only for acquisition. Offline object verification proves '
        'commit/tree/blob consistency; validating first-parent selection against the complete history requires the separate history audit.', '',
        '## Prior work and primary definitions', '',
        'No novelty or comparative accuracy claim is made. '
        '[GitHub dependency graph](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-graph) '
        'and [Dependabot Core](https://github.com/dependabot/dependabot-core) already analyze dependency metadata. '
        'This study adds a frozen cohort, annual sampling, and explicit coverage denominators to this offline tool.', '',
        'Definitions follow the [Python project metadata specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/), '
        '[setuptools declarative configuration](https://setuptools.pypa.io/en/latest/userguide/declarative_config.html), '
        '[npm package.json documentation](https://docs.npmjs.com/cli/v11/configuring-npm/package-json/), and '
        '[Git history traversal documentation](https://git-scm.com/docs/git-log). '
        'Python requirement grammar remains the vendored packaging 24.0 grammar. Source licenses are preserved per annual snapshot.', '']
    return '\n'.join(lines)


def viewer(study, report_md):
    data = json.dumps(study, sort_keys=True, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    template = ( __import__('pathlib').Path(__file__).with_name('annual_viewer.html')).read_text()
    return template.replace('__STUDY_DATA__', data).replace('__REPORT_TEXT__', html.escape(report_md))
