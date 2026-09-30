# Reproduce lockfile verification

From the repository root, with the tools below already provisioned, run:

```sh
env RST_ARBORIST=/tmp/repo-stack-tools/package/node_modules/@npmcli/arborist \
  PLAYWRIGHT_MODULE=/tmp/repo-stack-browser/node_modules/playwright \
  PLAYWRIGHT_BROWSERS_PATH=/tmp/repo-stack-browser/cache \
  python3 scripts/verify_lockfiles.py
```

This command requires Linux, Python 3.11+, Git, Node.js, libseccomp, the pinned
Arborist reader, Playwright 1.58.2, and its Chromium. It does not download anything.
`--record` saves actual test, reader, browser and benchmark results to
`results/lockfiles-verification.json`, preserving historical declaration evidence
in `results/verification.json` and `results/tests.log`. `--skip-regressions` is for
development only and explicitly reports **partial**, never passed milestone
verification.

## One-time optional tool provisioning

The CLI itself needs neither Node nor these verification packages. Provision them
outside the project and outside scanned repositories. No npm credentials are
needed. The npm tarball bundles the reader's dependencies; no package install or
lifecycle execution is necessary for Arborist.

```sh
mkdir -p /tmp/repo-stack-tools
curl -fsSL https://registry.npmjs.org/npm/-/npm-10.8.2.tgz -o /tmp/repo-stack-tools/npm.tgz
printf '%s\n' 'c8c61ba0fa0ab3b5120efd5ba97fdaf0e0b495eef647a97c4413919eda0a878b  /tmp/repo-stack-tools/npm.tgz' | sha256sum -c -
# Extract only after the hash check succeeds.
tar -xzf /tmp/repo-stack-tools/npm.tgz -C /tmp/repo-stack-tools
npm install --prefix /tmp/repo-stack-browser --ignore-scripts --no-audit --no-fund playwright@1.58.2
PLAYWRIGHT_BROWSERS_PATH=/tmp/repo-stack-browser/cache \
  node /tmp/repo-stack-browser/node_modules/playwright/cli.js install chromium
```

The harness checks `@npmcli/arborist` version 7.5.4 and its `lib/shrinkwrap.js`
SHA-256 `1c00ae180692a9bebe977c183c6db02c50b3c2e293867600c376b6d5f0773716`.
Do not substitute a global npm reader silently. Reader calls run with network
syscalls denied, only against temporary fixture copies, using `load` and `get`;
there is no install, save, or link traversal. The production scanner never calls
this reader.

## Coverage and interpretation

The full command includes the original verification suite and new lockfile tests:
200 existing seeded declaration histories / 1,400 selected snapshots, plus 200
seeded lockfile pairs / 400 snapshots compared with a separate dictionary-join
reference model. Lockfile seeds include repeated/scoped names at different
locations, aliases, roots, links, missing fields, JSON reordering, simultaneous
declaration changes, and 60 deliberately incomplete pairs. Additional tests cover
duplicate keys, malformed types, absent files, symlinks, bounds, source/index/ref/
config preservation, installed CLI use, and byte-identical repeated bundles.
Existing cancellation, process-group cleanup, interrupted writes, serialization
failure and output-collision regressions remain enabled.

The public fixture check compares 62 projected records across five upstream v2
files and five labeled synthetic v3 conversions, against pinned Arborist. One
upstream v1 file is an expected scope disagreement. The corpus is not statistically
representative; the oracle shares the documented contract but no production
comparison/parser implementation.

Network-blocked Chromium checks both the existing declaration view and lockfile
view: snapshot navigation, filtering, pagination, keyboard controls, evidence,
mobile layout and hostile imported strings. The context is offline, remote
requests are aborted, and report CSP prevents connections. This is browser-level
network isolation; Python, CLI and reader checks use syscall denial.

Three fresh lockfile CLI subprocesses use a deterministic 220-generated-package
workload (225 total records in each valid snapshot) plus an unsupported snapshot.
They record wall time, Linux `wait4` peak RSS, counts, sizes and SHA-256 hashes.
RSS is the command/reaped-child peak, not summed simultaneous process-tree RSS.
Warm caches are possible. These are local observations, not a performance claim
about large repositories. The report bundle includes incomplete outcomes, and
all three repetitions must match byte for byte. Historical declaration benchmarks
are also rerun, without rewriting their old saved results.
