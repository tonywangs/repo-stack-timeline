# Frozen public annual cohort

The prospective selection is in [cohort.json](cohort.json), frozen before annual
extraction on 2026-10-19. No member was substituted after observing coverage.
This is a small, purposeful sample of reusable infrastructure libraries, not a
random sample of GitHub. Four members share Pallets governance. See the
[aggregate report](../../results/annual/report.md) for conclusions and limitations.

Each `sources/<owner>--<repository>.json` shard contains seven annual samples,
acquired from the public GitHub Git endpoint without authentication. It records
acquisition time, URL, default branch, frozen head, complete first-parent history
count and digest, and the exact selected commit for each year. Selection follows
the first-parent topology from that frozen head, choosing the first commit with
committer time before January 1 UTC of the following year. It does not infer
historical branch names, release status, or first-use dates.

Each acquired sample preserves the original bytes of root metadata and licenses
in base64, SHA-256 and Git blob hashes, plus the raw Git commit and root tree.
Offline verification checks commit → root tree → file integrity and completeness
of the root evidence. A missing manifest can therefore be distinguished from
an omitted fixture. Complete history is kept in an external cache, not in this
repository; auditing the date/lineage selection requires reacquisition.

## Reproduce

```sh
# Offline: verify frozen objects, recompute statistics and render the viewer.
python3 scripts/annual_report.py --output /tmp/annual-trends
# Open /tmp/annual-trends/index.html.

# Offline: byte-for-byte comparison against checked-in report artifacts.
python3 scripts/annual_report.py --check

# NETWORK, optional: full public Git history audit against frozen heads.
# Existing evidence pins the heads and must reproduce byte-for-byte.
python3 scripts/acquire_annual.py --cache /tmp/annual-history
```

Python 3.11+ is sufficient for report reproduction; Git is needed for acquisition.
No package installation, account, API token, paid service, or GPU is needed.
The report command refuses an existing output directory. The acquisition command
fails on unavailable history, changed evidence, a shallow cache, or an unexpected
origin URL; it never silently drops or replaces a cohort member. Ordinary offline
reproduction does not need GitHub to stay available.

## Licenses and attribution

The four Pallets projects are BSD-3-Clause licensed: `pallets/flask`,
`pallets/click`, `pallets/jinja`, and `pallets/itsdangerous`. The JavaScript projects
are MIT licensed: `expressjs/express`, `koajs/koa`, `chalk/chalk`, and
`tj/commander.js`. Exact license bytes and upstream URLs are retained at **every
selected commit**, including original author notices. These third-party files
retain their original licenses, independently of this project's MIT license.

To inspect a frozen file without network access:

```sh
python3 - <<'PY'
import base64, json
from pathlib import Path
source = json.loads(Path('examples/annual/sources/pallets--flask.json').read_text())
for file in source['snapshots'][0]['files']:
    print(file['path'], file['url'])
    print(base64.b64decode(file['base64']).decode())
PY
```

Frozen source shards are research inputs, not reconstructed repositories or
synthetic commits. No upstream Python or JavaScript is executed. The annual
reader adds a deliberately conservative, study-specific legacy Python path
(literal AST keywords and static setup.cfg fields); this does not broaden the
main snapshot CLI's documented formats.

## Verification

`python3 scripts/verify_annual.py` runs focused annual tests, shared-parser and
installation regression tests with network syscalls denied, checks source-object
integrity and byte-identical report reproduction, exercises a fresh output path
and refuses output collisions, and checks publication size limits. Its 40 seeded
state tables test coverage/transition accounting; they are test fixtures, not
research observations. Linux `libseccomp.so.2` is required for syscall denial.

For optional browser checks, provision the same pinned tools outside the repo:

```sh
npm install --prefix /tmp/repo-stack-annual-browser --cache /tmp/repo-stack-npm-cache --no-audit --no-fund playwright@1.58.2
PLAYWRIGHT_BROWSERS_PATH=/tmp/repo-stack-annual-browser/cache node /tmp/repo-stack-annual-browser/node_modules/playwright/cli.js install chromium
PLAYWRIGHT_MODULE=/tmp/repo-stack-annual-browser/node_modules/playwright PLAYWRIGHT_BROWSERS_PATH=/tmp/repo-stack-annual-browser/cache python3 scripts/verify_annual.py --browser
```

Provisioning uses the network; verification does not install anything. Browser
checks exercise the local report offline, ecosystem/year selection, fixed-cohort
shares, change denominators, coverage, exact source links, search, keyboard input,
and a narrow viewport. Actual evidence is in
[annual-verification.json](../../results/annual-verification.json).
