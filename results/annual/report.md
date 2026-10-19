# Declared dependency trends, 2019–2025

Eight public repositories · seven year-end samples · root runtime declarations only

This retrospective study answers how declared dependency names changed within a small, frozen convenience cohort. It does not estimate GitHub-wide popularity, installed packages, code usage, release history, or adoption dates. All counts are repository counts, not download counts.

## Concrete findings

- Chalk's root runtime declaration count went from 2 in [chalk/chalk 2020](https://github.com/chalk/chalk/blob/ca330532ecfb83e46efa9e94d1c0630a058ff1ba/package.json) to 0 in [chalk/chalk 2021](https://github.com/chalk/chalk/blob/4d5c4795ad24c326ae16bfe0c39c826c732716a9/package.json). The removed names are `ansi-styles` and `supports-color`. This does not establish that their functionality disappeared or that no code was vendored.
- Koa's root runtime declaration count fell from 24 in [koajs/koa 2019](https://github.com/koajs/koa/blob/ed84ee50da8ae3cd08056f944d061e00d06ed87f/package.json) to 18 in [koajs/koa 2025](https://github.com/koajs/koa/blob/0a6afa5a6107c0c8baf4722e29de7566f33d1651/package.json). These are net endpoint counts; the interval tables retain additions and removals separately.
- Flask first shows `blinker` in our [pallets/flask 2023](https://github.com/pallets/flask/blob/708d62d7172a30c5b0ace1d212c5a3bc2b53b98c/pyproject.toml) sample, absent in [pallets/flask 2022](https://github.com/pallets/flask/blob/74e5263c88e51bb442879ab863a5d03292fc0a33/setup.py). Its 2023 prevalence is 1/4 among observed Python repositories and 1/2 in the all-years-observed Python cohort. This brackets a declaration change, not the project's first use.
- Python `markupsafe` illustrates denominator sensitivity: observed-cohort prevalence is 1/2 in 2019 and 2/4 in 2025; the fixed cohort instead changes from 1/2 to 2/2. Compare [pallets/flask 2024](https://github.com/pallets/flask/blob/6b054f8f3876ff4c31580b014d344c4cf491059d/pyproject.toml) with [pallets/flask 2025](https://github.com/pallets/flask/blob/2579ce9f18e67ec3213c6eceb5240310ccd46af8/pyproject.toml) and [pallets/jinja 2019](https://github.com/pallets/jinja/blob/4fe03dafcdf251739e1fa27843d7167a7b2f2031/setup.py). A stable available-case share can conceal a change when the denominator expands.
- Commander has zero root runtime declarations in all seven observed samples ([tj/commander.js 2019](https://github.com/tj/commander.js/blob/dd23b4c7f553a5f12b60ef5a81e527431750b03e/package.json); [tj/commander.js 2025](https://github.com/tj/commander.js/blob/63eed4aa05435575d515311bb5efaf6d88b6be84/package.json)). Early Click/ItsDangerous samples, in contrast, are unknown: omitted legacy `install_requires` is not interpreted as an observed zero.

## Cohort and coverage

Prospectively frozen before annual extraction: four established Pallets Python libraries and four established JavaScript server/CLI libraries, selected for small public Git histories, permissive licensing, and relevance to reusable application infrastructure. Purposeful convenience sample, not random. No substitution based on observed trends or coverage.

**Exclusions.** All repositories outside the eight named members; forks, applications, private repositories, transitive dependencies, development/build/optional/peer requirements, nested packages, and non-default-branch history. Unsupported historical metadata remains unknown, never a reason to replace a member.

| Repository | Ecosystem | License | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pallets/flask | python | BSD-3-Clause | 4 | 4 | 4 | 5 | 6 | 6 | 6 |
| pallets/click | python | BSD-3-Clause | unsupported_metadata | unsupported_metadata | 2 | 2 | 1 | 1 | 1 |
| pallets/jinja | python | BSD-3-Clause | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| pallets/itsdangerous | python | BSD-3-Clause | unsupported_metadata | unsupported_metadata | unsupported_metadata | unsupported_metadata | 0 | 0 | 0 |
| expressjs/express | npm | MIT | 31 | 31 | 31 | 32 | 32 | 30 | 28 |
| koajs/koa | npm | MIT | 24 | 23 | 20 | 20 | 20 | 19 | 18 |
| chalk/chalk | npm | MIT | 2 | 2 | 0 | 0 | 0 | 0 | 0 |
| tj/commander.js | npm | MIT | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Numbers above are observed distinct runtime names. Unknown cells are excluded from prevalence and paired transitions.

| Ecosystem / sample | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| npm / available observed | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| npm / fixed observed | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| npm adjacent-year comparable pairs | — | 4 | 4 | 4 | 4 | 4 | 4 |
| python / available observed | 2 | 2 | 3 | 3 | 4 | 4 | 4 |
| python / fixed observed | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| python adjacent-year comparable pairs | — | 2 | 2 | 3 | 3 | 4 | 4 |

Fixed cohort requires an observed runtime set in **every** year. Membership is computed after extraction without replacing any original member. It is a coverage sensitivity analysis, not a representative subset.

- npm: expressjs/express, koajs/koa, chalk/chalk, tj/commander.js
- python: pallets/flask, pallets/jinja

## Annual prevalence

Each cell is repositories declaring the name / repositories with observable runtime metadata in that ecosystem and sample. A repository counts once regardless of constraints or repeated declarations. Conditional Python requirements count as declared; markers and original strings remain in report.json. Ecosystems are never pooled.

### npm: available

| Dependency | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accepts | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| ansi-styles | 1/4 | 1/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| array-flatten | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 0/4 | 0/4 |
| body-parser | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| cache-content-type | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 0/4 |
| content-disposition | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| content-type | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| cookie | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| cookie-signature | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| cookies | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| debug | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 1/4 |
| delegates | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| depd | 2/4 | 2/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| destroy | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| encodeurl | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| error-inject | 1/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| escape-html | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| etag | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| finalhandler | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| fresh | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| http-assert | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| http-errors | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 2/4 | 2/4 |
| is-generator-function | 1/4 | 1/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| koa-compose | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| koa-convert | 1/4 | 1/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| merge-descriptors | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| methods | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 0/4 |
| mime-types | 0/4 | 0/4 | 0/4 | 1/4 | 1/4 | 1/4 | 2/4 |
| on-finished | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| once | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 1/4 | 1/4 |
| only | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 0/4 | 0/4 |
| parseurl | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| path-is-absolute | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 0/4 | 0/4 |
| proxy-addr | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| qs | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| range-parser | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| router | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| safe-buffer | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 0/4 | 0/4 |
| send | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| serve-static | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| setprototypeof | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 0/4 | 0/4 |
| statuses | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| supports-color | 1/4 | 1/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| type-is | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| utils-merge | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 0/4 |
| vary | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |

### npm: fixed

| Dependency | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accepts | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| ansi-styles | 1/4 | 1/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| array-flatten | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 0/4 | 0/4 |
| body-parser | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| cache-content-type | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 0/4 |
| content-disposition | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| content-type | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| cookie | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| cookie-signature | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| cookies | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| debug | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 1/4 |
| delegates | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| depd | 2/4 | 2/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| destroy | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| encodeurl | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| error-inject | 1/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| escape-html | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| etag | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| finalhandler | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| fresh | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| http-assert | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| http-errors | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 2/4 | 2/4 |
| is-generator-function | 1/4 | 1/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| koa-compose | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| koa-convert | 1/4 | 1/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| merge-descriptors | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| methods | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 0/4 |
| mime-types | 0/4 | 0/4 | 0/4 | 1/4 | 1/4 | 1/4 | 2/4 |
| on-finished | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| once | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 1/4 | 1/4 |
| only | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 0/4 | 0/4 |
| parseurl | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| path-is-absolute | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 0/4 | 0/4 |
| proxy-addr | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| qs | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| range-parser | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| router | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| safe-buffer | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 0/4 | 0/4 |
| send | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| serve-static | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 |
| setprototypeof | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 0/4 | 0/4 |
| statuses | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| supports-color | 1/4 | 1/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| type-is | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |
| utils-merge | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 0/4 |
| vary | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 | 2/4 |

### python: available

| Dependency | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| blinker | 0/2 | 0/2 | 0/3 | 0/3 | 1/4 | 1/4 | 1/4 |
| click | 1/2 | 1/2 | 1/3 | 1/3 | 1/4 | 1/4 | 1/4 |
| colorama | 0/2 | 0/2 | 1/3 | 1/3 | 1/4 | 1/4 | 1/4 |
| importlib-metadata | 0/2 | 0/2 | 1/3 | 2/3 | 1/4 | 1/4 | 0/4 |
| itsdangerous | 1/2 | 1/2 | 1/3 | 1/3 | 1/4 | 1/4 | 1/4 |
| jinja2 | 1/2 | 1/2 | 1/3 | 1/3 | 1/4 | 1/4 | 1/4 |
| markupsafe | 1/2 | 1/2 | 1/3 | 1/3 | 1/4 | 1/4 | 2/4 |
| werkzeug | 1/2 | 1/2 | 1/3 | 1/3 | 1/4 | 1/4 | 1/4 |

### python: fixed

| Dependency | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| blinker | 0/2 | 0/2 | 0/2 | 0/2 | 1/2 | 1/2 | 1/2 |
| click | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 |
| colorama | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| importlib-metadata | 0/2 | 0/2 | 0/2 | 1/2 | 1/2 | 1/2 | 0/2 |
| itsdangerous | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 |
| jinja2 | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 |
| markupsafe | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 | 2/2 |
| werkzeug | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 | 1/2 |

## Adoption, removal and persistence

An adoption is absent→present; removal is present→absent; persistence is present→present between adjacent annual samples with both endpoints observed. Unknown endpoints never become removals or adoptions. The first year is only a baseline. The table sums repository–dependency events, so totals can exceed repository counts. The JSON and HTML provide each name, repository, and risk denominator: adoption / previously absent paired repositories; removal or persistence / previously present paired repositories. Zero risk denominators mean undefined rates, not zero percent.

| Ecosystem / sample | Interval | Comparable repositories | Unknown pairs | Adoptions | Removals | Persistences |
| --- | --- | --- | --- | --- | --- | --- |
| npm / available | 2019→2020 | 4 | 0 | 0 | 1 | 56 |
| npm / available | 2020→2021 | 4 | 0 | 0 | 5 | 51 |
| npm / available | 2021→2022 | 4 | 0 | 1 | 0 | 51 |
| npm / available | 2022→2023 | 4 | 0 | 0 | 0 | 52 |
| npm / available | 2023→2024 | 4 | 0 | 2 | 5 | 47 |
| npm / available | 2024→2025 | 4 | 0 | 1 | 4 | 45 |
| npm / fixed | 2019→2020 | 4 | 0 | 0 | 1 | 56 |
| npm / fixed | 2020→2021 | 4 | 0 | 0 | 5 | 51 |
| npm / fixed | 2021→2022 | 4 | 0 | 1 | 0 | 51 |
| npm / fixed | 2022→2023 | 4 | 0 | 0 | 0 | 52 |
| npm / fixed | 2023→2024 | 4 | 0 | 2 | 5 | 47 |
| npm / fixed | 2024→2025 | 4 | 0 | 1 | 4 | 45 |
| python / available | 2019→2020 | 2 | 2 | 0 | 0 | 5 |
| python / available | 2020→2021 | 2 | 2 | 0 | 0 | 5 |
| python / available | 2021→2022 | 3 | 1 | 1 | 0 | 7 |
| python / available | 2022→2023 | 3 | 1 | 1 | 1 | 7 |
| python / available | 2023→2024 | 4 | 0 | 0 | 0 | 8 |
| python / available | 2024→2025 | 4 | 0 | 1 | 1 | 7 |
| python / fixed | 2019→2020 | 2 | 0 | 0 | 0 | 5 |
| python / fixed | 2020→2021 | 2 | 0 | 0 | 0 | 5 |
| python / fixed | 2021→2022 | 2 | 0 | 1 | 0 | 5 |
| python / fixed | 2022→2023 | 2 | 0 | 1 | 0 | 6 |
| python / fixed | 2023→2024 | 2 | 0 | 0 | 0 | 7 |
| python / fixed | 2024→2025 | 2 | 0 | 1 | 1 | 6 |

## Auditable annual observations

Every link identifies an exact source commit. Original manifest and license bytes, Git commit and root-tree objects, blob IDs, and SHA-256 checksums are retained in the source shards. Unknown rows link to their commit tree.

| Source | Commit | Status | Runtime names / coverage reason |
| --- | --- | --- | --- |
| [pallets/flask 2019](https://github.com/pallets/flask/blob/38eb5d3b49d628785a470e2e773fc5ac82e3c8e4/setup.py) | `38eb5d3b49d628785a470e2e773fc5ac82e3c8e4` | observed | click, itsdangerous, jinja2, werkzeug |
| [pallets/flask 2020](https://github.com/pallets/flask/blob/de0af038627fd4f45bfe61ca9aed36b8e10770d5/setup.py) | `de0af038627fd4f45bfe61ca9aed36b8e10770d5` | observed | click, itsdangerous, jinja2, werkzeug |
| [pallets/flask 2021](https://github.com/pallets/flask/blob/660994efc761efdfd49ca442b73f6712dc77b6cf/setup.py) | `660994efc761efdfd49ca442b73f6712dc77b6cf` | observed | click, itsdangerous, jinja2, werkzeug |
| [pallets/flask 2022](https://github.com/pallets/flask/blob/74e5263c88e51bb442879ab863a5d03292fc0a33/setup.py) | `74e5263c88e51bb442879ab863a5d03292fc0a33` | observed | click, importlib-metadata, itsdangerous, jinja2, werkzeug |
| [pallets/flask 2023](https://github.com/pallets/flask/blob/708d62d7172a30c5b0ace1d212c5a3bc2b53b98c/pyproject.toml) | `708d62d7172a30c5b0ace1d212c5a3bc2b53b98c` | observed | blinker, click, importlib-metadata, itsdangerous, jinja2, werkzeug |
| [pallets/flask 2024](https://github.com/pallets/flask/blob/6b054f8f3876ff4c31580b014d344c4cf491059d/pyproject.toml) | `6b054f8f3876ff4c31580b014d344c4cf491059d` | observed | blinker, click, importlib-metadata, itsdangerous, jinja2, werkzeug |
| [pallets/flask 2025](https://github.com/pallets/flask/blob/2579ce9f18e67ec3213c6eceb5240310ccd46af8/pyproject.toml) | `2579ce9f18e67ec3213c6eceb5240310ccd46af8` | observed | blinker, click, itsdangerous, jinja2, markupsafe, werkzeug |
| [pallets/click 2019](https://github.com/pallets/click/tree/6c454c88b76f7a0be396dba72513bd316cd141e6) | `6c454c88b76f7a0be396dba72513bd316cd141e6` | unsupported_metadata | no explicit supported runtime dependency field |
| [pallets/click 2020](https://github.com/pallets/click/tree/58a25939f0c4594dd5c487eec8906a79539e2810) | `58a25939f0c4594dd5c487eec8906a79539e2810` | unsupported_metadata | no explicit supported runtime dependency field |
| [pallets/click 2021](https://github.com/pallets/click/blob/051d57cef4ce59212dc1175ad4550743bf47d840/setup.py) | `051d57cef4ce59212dc1175ad4550743bf47d840` | observed | colorama, importlib-metadata |
| [pallets/click 2022](https://github.com/pallets/click/blob/5e75fe7f9c1b820d71f482599cd6996523332d06/setup.py) | `5e75fe7f9c1b820d71f482599cd6996523332d06` | observed | colorama, importlib-metadata |
| [pallets/click 2023](https://github.com/pallets/click/blob/cab9483a30379f9b8e3ddb72d5a4e88f88d517b6/pyproject.toml) | `cab9483a30379f9b8e3ddb72d5a4e88f88d517b6` | observed | colorama |
| [pallets/click 2024](https://github.com/pallets/click/blob/8a47580a00f3404e7071b9ecfec3692a1e18309f/pyproject.toml) | `8a47580a00f3404e7071b9ecfec3692a1e18309f` | observed | colorama |
| [pallets/click 2025](https://github.com/pallets/click/blob/1f0e6a2ecd3dd95c22290836981a38922c192596/pyproject.toml) | `1f0e6a2ecd3dd95c22290836981a38922c192596` | observed | colorama |
| [pallets/jinja 2019](https://github.com/pallets/jinja/blob/4fe03dafcdf251739e1fa27843d7167a7b2f2031/setup.py) | `4fe03dafcdf251739e1fa27843d7167a7b2f2031` | observed | markupsafe |
| [pallets/jinja 2020](https://github.com/pallets/jinja/blob/81911fdb3065f1156d84ca52ee3a257c229ebc59/setup.py) | `81911fdb3065f1156d84ca52ee3a257c229ebc59` | observed | markupsafe |
| [pallets/jinja 2021](https://github.com/pallets/jinja/blob/11065b55a0056905a8973efec12a15dc658ef46f/setup.py) | `11065b55a0056905a8973efec12a15dc658ef46f` | observed | markupsafe |
| [pallets/jinja 2022](https://github.com/pallets/jinja/blob/36b601f24b30a91fe2fdc857116382bcb7655466/setup.py) | `36b601f24b30a91fe2fdc857116382bcb7655466` | observed | markupsafe |
| [pallets/jinja 2023](https://github.com/pallets/jinja/blob/d594969d722ceb4e8f3da8861befc9c0ac87ae1b/pyproject.toml) | `d594969d722ceb4e8f3da8861befc9c0ac87ae1b` | observed | markupsafe |
| [pallets/jinja 2024](https://github.com/pallets/jinja/blob/6aeab5d1da0bc0793406d7b402693e779b6cca7a/pyproject.toml) | `6aeab5d1da0bc0793406d7b402693e779b6cca7a` | observed | markupsafe |
| [pallets/jinja 2025](https://github.com/pallets/jinja/blob/5ef70112a1ff19c05324ff889dd30405b1002044/pyproject.toml) | `5ef70112a1ff19c05324ff889dd30405b1002044` | observed | markupsafe |
| [pallets/itsdangerous 2019](https://github.com/pallets/itsdangerous/tree/64048c1106eb4e0ed70e64d16e230553a464087b) | `64048c1106eb4e0ed70e64d16e230553a464087b` | unsupported_metadata | no explicit supported runtime dependency field |
| [pallets/itsdangerous 2020](https://github.com/pallets/itsdangerous/tree/5dc90166c3df22f1ce4d5d5eba0e2e7a90204382) | `5dc90166c3df22f1ce4d5d5eba0e2e7a90204382` | unsupported_metadata | no explicit supported runtime dependency field |
| [pallets/itsdangerous 2021](https://github.com/pallets/itsdangerous/tree/233527d38bfe35b5c28a11a580555b6e8dda34c3) | `233527d38bfe35b5c28a11a580555b6e8dda34c3` | unsupported_metadata | no explicit supported runtime dependency field |
| [pallets/itsdangerous 2022](https://github.com/pallets/itsdangerous/tree/931237a806f430dc9461f2b8159338ad100d846e) | `931237a806f430dc9461f2b8159338ad100d846e` | unsupported_metadata | no explicit supported runtime dependency field |
| [pallets/itsdangerous 2023](https://github.com/pallets/itsdangerous/blob/7c6286ed2125c87662eeb102b32fb3d68611a5d6/pyproject.toml) | `7c6286ed2125c87662eeb102b32fb3d68611a5d6` | observed | observed empty |
| [pallets/itsdangerous 2024](https://github.com/pallets/itsdangerous/blob/62fde54d4ff717fa1c4af688dbebf97845fed495/pyproject.toml) | `62fde54d4ff717fa1c4af688dbebf97845fed495` | observed | observed empty |
| [pallets/itsdangerous 2025](https://github.com/pallets/itsdangerous/blob/672971d66a2ef9f85151e53283113f33d642dabd/pyproject.toml) | `672971d66a2ef9f85151e53283113f33d642dabd` | observed | observed empty |
| [expressjs/express 2019](https://github.com/expressjs/express/blob/121fe9982b62d2b1760ec9cb148c19bc5f17255b/package.json) | `121fe9982b62d2b1760ec9cb148c19bc5f17255b` | observed | accepts, array-flatten, body-parser, content-disposition, content-type, cookie, cookie-signature, debug, depd, encodeurl, escape-html, etag, finalhandler, fresh, merge-descriptors, methods, on-finished, parseurl, path-is-absolute, proxy-addr, qs, range-parser, router, safe-buffer, send, serve-static, setprototypeof, statuses, type-is, utils-merge, vary |
| [expressjs/express 2020](https://github.com/expressjs/express/blob/8aabecaf1f6343ec9a39fcdeff2deb3b4544f35f/package.json) | `8aabecaf1f6343ec9a39fcdeff2deb3b4544f35f` | observed | accepts, array-flatten, body-parser, content-disposition, content-type, cookie, cookie-signature, debug, depd, encodeurl, escape-html, etag, finalhandler, fresh, merge-descriptors, methods, on-finished, parseurl, path-is-absolute, proxy-addr, qs, range-parser, router, safe-buffer, send, serve-static, setprototypeof, statuses, type-is, utils-merge, vary |
| [expressjs/express 2021](https://github.com/expressjs/express/blob/450c468d0469ea79c878084c623cd18642d7ad7d/package.json) | `450c468d0469ea79c878084c623cd18642d7ad7d` | observed | accepts, array-flatten, body-parser, content-disposition, content-type, cookie, cookie-signature, debug, depd, encodeurl, escape-html, etag, finalhandler, fresh, merge-descriptors, methods, on-finished, parseurl, path-is-absolute, proxy-addr, qs, range-parser, router, safe-buffer, send, serve-static, setprototypeof, statuses, type-is, utils-merge, vary |
| [expressjs/express 2022](https://github.com/expressjs/express/blob/318fd4b543ffbebf97bf0b6c49188afae45741f5/package.json) | `318fd4b543ffbebf97bf0b6c49188afae45741f5` | observed | accepts, array-flatten, body-parser, content-disposition, content-type, cookie, cookie-signature, debug, depd, encodeurl, escape-html, etag, finalhandler, fresh, merge-descriptors, methods, mime-types, on-finished, parseurl, path-is-absolute, proxy-addr, qs, range-parser, router, safe-buffer, send, serve-static, setprototypeof, statuses, type-is, utils-merge, vary |
| [expressjs/express 2023](https://github.com/expressjs/express/blob/318fd4b543ffbebf97bf0b6c49188afae45741f5/package.json) | `318fd4b543ffbebf97bf0b6c49188afae45741f5` | observed | accepts, array-flatten, body-parser, content-disposition, content-type, cookie, cookie-signature, debug, depd, encodeurl, escape-html, etag, finalhandler, fresh, merge-descriptors, methods, mime-types, on-finished, parseurl, path-is-absolute, proxy-addr, qs, range-parser, router, safe-buffer, send, serve-static, setprototypeof, statuses, type-is, utils-merge, vary |
| [expressjs/express 2024](https://github.com/expressjs/express/blob/43020ff2753477a5abc75a72931a807503d31bbf/package.json) | `43020ff2753477a5abc75a72931a807503d31bbf` | observed | accepts, body-parser, content-disposition, content-type, cookie, cookie-signature, debug, depd, encodeurl, escape-html, etag, finalhandler, fresh, http-errors, merge-descriptors, methods, mime-types, on-finished, once, parseurl, proxy-addr, qs, range-parser, router, send, serve-static, statuses, type-is, utils-merge, vary |
| [expressjs/express 2025](https://github.com/expressjs/express/blob/c2fb76e99f7379b706a5510b4b2dd08a1b710b7b/package.json) | `c2fb76e99f7379b706a5510b4b2dd08a1b710b7b` | observed | accepts, body-parser, content-disposition, content-type, cookie, cookie-signature, debug, depd, encodeurl, escape-html, etag, finalhandler, fresh, http-errors, merge-descriptors, mime-types, on-finished, once, parseurl, proxy-addr, qs, range-parser, router, send, serve-static, statuses, type-is, vary |
| [koajs/koa 2019](https://github.com/koajs/koa/blob/ed84ee50da8ae3cd08056f944d061e00d06ed87f/package.json) | `ed84ee50da8ae3cd08056f944d061e00d06ed87f` | observed | accepts, cache-content-type, content-disposition, content-type, cookies, debug, delegates, depd, destroy, encodeurl, error-inject, escape-html, fresh, http-assert, http-errors, is-generator-function, koa-compose, koa-convert, on-finished, only, parseurl, statuses, type-is, vary |
| [koajs/koa 2020](https://github.com/koajs/koa/blob/b4398f5d68f9546167419f394a686afdcb5e10e2/package.json) | `b4398f5d68f9546167419f394a686afdcb5e10e2` | observed | accepts, cache-content-type, content-disposition, content-type, cookies, debug, delegates, depd, destroy, encodeurl, escape-html, fresh, http-assert, http-errors, is-generator-function, koa-compose, koa-convert, on-finished, only, parseurl, statuses, type-is, vary |
| [koajs/koa 2021](https://github.com/koajs/koa/blob/910585d12bd8c530f0956a72cf3ddcb2e3a1a188/package.json) | `910585d12bd8c530f0956a72cf3ddcb2e3a1a188` | observed | accepts, cache-content-type, content-disposition, content-type, cookies, debug, delegates, destroy, encodeurl, escape-html, fresh, http-assert, http-errors, koa-compose, on-finished, only, parseurl, statuses, type-is, vary |
| [koajs/koa 2022](https://github.com/koajs/koa/blob/14dec599b4f51fd06ab2b04d13cbf2ce77f760e2/package.json) | `14dec599b4f51fd06ab2b04d13cbf2ce77f760e2` | observed | accepts, cache-content-type, content-disposition, content-type, cookies, debug, delegates, destroy, encodeurl, escape-html, fresh, http-assert, http-errors, koa-compose, on-finished, only, parseurl, statuses, type-is, vary |
| [koajs/koa 2023](https://github.com/koajs/koa/blob/5ba533f83117316486a55f097a764dac9e7c140a/package.json) | `5ba533f83117316486a55f097a764dac9e7c140a` | observed | accepts, cache-content-type, content-disposition, content-type, cookies, debug, delegates, destroy, encodeurl, escape-html, fresh, http-assert, http-errors, koa-compose, on-finished, only, parseurl, statuses, type-is, vary |
| [koajs/koa 2024](https://github.com/koajs/koa/blob/71902b1f2154469be4daaee8ffe9dc2b8cbbc5a0/package.json) | `71902b1f2154469be4daaee8ffe9dc2b8cbbc5a0` | observed | accepts, cache-content-type, content-disposition, content-type, cookies, debug, delegates, destroy, encodeurl, escape-html, fresh, http-assert, http-errors, koa-compose, on-finished, parseurl, statuses, type-is, vary |
| [koajs/koa 2025](https://github.com/koajs/koa/blob/0a6afa5a6107c0c8baf4722e29de7566f33d1651/package.json) | `0a6afa5a6107c0c8baf4722e29de7566f33d1651` | observed | accepts, content-disposition, content-type, cookies, delegates, destroy, encodeurl, escape-html, fresh, http-assert, http-errors, koa-compose, mime-types, on-finished, parseurl, statuses, type-is, vary |
| [chalk/chalk 2019](https://github.com/chalk/chalk/blob/0e6fecc7f7fd8158d3c96fb89608b8dfb744fdfa/package.json) | `0e6fecc7f7fd8158d3c96fb89608b8dfb744fdfa` | observed | ansi-styles, supports-color |
| [chalk/chalk 2020](https://github.com/chalk/chalk/blob/ca330532ecfb83e46efa9e94d1c0630a058ff1ba/package.json) | `ca330532ecfb83e46efa9e94d1c0630a058ff1ba` | observed | ansi-styles, supports-color |
| [chalk/chalk 2021](https://github.com/chalk/chalk/blob/4d5c4795ad24c326ae16bfe0c39c826c732716a9/package.json) | `4d5c4795ad24c326ae16bfe0c39c826c732716a9` | observed | observed empty |
| [chalk/chalk 2022](https://github.com/chalk/chalk/blob/a370f468a43999e4397094ff5c3d17aadcc4860e/package.json) | `a370f468a43999e4397094ff5c3d17aadcc4860e` | observed | observed empty |
| [chalk/chalk 2023](https://github.com/chalk/chalk/blob/f7b29ae8ef4fd2048e08aa361778d290ed10ce7a/package.json) | `f7b29ae8ef4fd2048e08aa361778d290ed10ce7a` | observed | observed empty |
| [chalk/chalk 2024](https://github.com/chalk/chalk/blob/5dbc1e2633f3874f43c144fa4919934bc934c495/package.json) | `5dbc1e2633f3874f43c144fa4919934bc934c495` | observed | observed empty |
| [chalk/chalk 2025](https://github.com/chalk/chalk/blob/51557784b829c87ff8d138206598764f2eb957b1/package.json) | `51557784b829c87ff8d138206598764f2eb957b1` | observed | observed empty |
| [tj/commander.js 2019](https://github.com/tj/commander.js/blob/dd23b4c7f553a5f12b60ef5a81e527431750b03e/package.json) | `dd23b4c7f553a5f12b60ef5a81e527431750b03e` | observed | observed empty |
| [tj/commander.js 2020](https://github.com/tj/commander.js/blob/5173665dd22c6ff5262b3b3eb6bb81f48ccd678a/package.json) | `5173665dd22c6ff5262b3b3eb6bb81f48ccd678a` | observed | observed empty |
| [tj/commander.js 2021](https://github.com/tj/commander.js/blob/35a028b6253a38d00c16dca2a36b69c5888c022a/package.json) | `35a028b6253a38d00c16dca2a36b69c5888c022a` | observed | observed empty |
| [tj/commander.js 2022](https://github.com/tj/commander.js/blob/5f3f004b8e62c46b6e90d0f79baf89bc52a0322f/package.json) | `5f3f004b8e62c46b6e90d0f79baf89bc52a0322f` | observed | observed empty |
| [tj/commander.js 2023](https://github.com/tj/commander.js/blob/47f740cbcdf6b8a88ee316d5999461422e366471/package.json) | `47f740cbcdf6b8a88ee316d5999461422e366471` | observed | observed empty |
| [tj/commander.js 2024](https://github.com/tj/commander.js/blob/d6bcb0b6e144d8854360a5c3c2759fadf0e4edb3/package.json) | `d6bcb0b6e144d8854360a5c3c2759fadf0e4edb3` | observed | observed empty |
| [tj/commander.js 2025](https://github.com/tj/commander.js/blob/63eed4aa05435575d515311bb5efaf6d88b6be84/package.json) | `63eed4aa05435575d515311bb5efaf6d88b6be84` | observed | observed empty |

## Method and limitations

Freeze the acquired default branch head. Walk its full first-parent chain in topology order; select the first commit with committer timestamp strictly before January 1 UTC of the following year. This is a retrospective branch-lineage sample, not a reconstruction of historical default branches. No eligible commit in a complete history is unavailable_history, not an empty declaration set.

The sample was frozen before annual extraction on 2026-10-19. All eight histories were acquired anonymously from public GitHub repositories, with no upstream code execution. The frozen current default-branch lineage can include unreleased development: notably, Express samples are not a series of stable releases. Commit clocks can be wrong; first-parent topology determines the first qualifying commit, not the greatest timestamp. Repeated commits across years are allowed and mean no qualifying newer lineage snapshot.

Python measurement precedence is static `[project].dependencies`, then an explicit literal `install_requires` keyword in a single top-level setup call, then explicit `[options] install_requires` in setup.cfg. Dynamic metadata, keyword expansion, nested/conditional setup calls and indirect requirements are unknown. AST extraction measures literal declarations only, not effective execution of arbitrary Python. A legacy omitted field is unknown; an omitted static PEP 621 dependency field is empty. JavaScript measures `dependencies`, excluding names overridden by `optionalDependencies`. Build, dev, extras, optional and peer dependencies and nested manifests are outside the study.

The four Python repositories share Pallets governance and dependency relationships; the JavaScript members mix two web frameworks with two CLI libraries. Selection favors established surviving permissively licensed projects. Repository observations are not independent and the cohort is not random. There are no confidence intervals or extrapolated population claims. Annual sampling misses changes reversed within a year. Name changes, bundling, vendoring, conditional requirements, and changing metadata formats can change measured declarations without changing actual usage. The fixed cohort controls denominator membership, not these biases. There is no stochastic experiment or random seed: input objects and algorithms are deterministic.

## Reproduce and inspect

From the project root, with Python 3.11+: `python3 scripts/annual_report.py --output /tmp/annual-trends`. Open `/tmp/annual-trends/index.html`; Markdown and machine-readable JSON are beside it. This command is offline, verifies source objects, and refuses an existing output directory. `python3 scripts/annual_report.py --check` verifies checked-in results. For a full network history audit, use `python3 scripts/acquire_annual.py --cache /tmp/annual-history`: existing source records pin all heads and must reproduce byte-for-byte. Git is required only for acquisition. Offline object verification proves commit/tree/blob consistency; validating first-parent selection against the complete history requires the separate history audit.

## Prior work and primary definitions

No novelty or comparative accuracy claim is made. [GitHub dependency graph](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-graph) and [Dependabot Core](https://github.com/dependabot/dependabot-core) already analyze dependency metadata. This study adds a frozen cohort, annual sampling, and explicit coverage denominators to this offline tool.

Definitions follow the [Python project metadata specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/), [setuptools declarative configuration](https://setuptools.pypa.io/en/latest/userguide/declarative_config.html), [npm package.json documentation](https://docs.npmjs.com/cli/v11/configuring-npm/package-json/), and [Git history traversal documentation](https://git-scm.com/docs/git-log). Python requirement grammar remains the vendored packaging 24.0 grammar. Source licenses are preserved per annual snapshot.
