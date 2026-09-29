# Repository stack timeline

Trace **declared Python and JavaScript dependencies** across explicitly selected
Git commits. Generate deterministic JSON evidence and a self-contained HTML
viewer, without checking out files, running repository code, installing its
dependencies, or contacting a network service.

The report keeps paths, categories, constraints, Python extras/markers, and
commit/tree/blob provenance. It distinguishes additions, absences, textual
changes, and unknown comparisons caused by malformed or dynamic metadata.
Selections can cross branches, include merges, repeat commits, or run backwards.
Commit timestamps are never interpreted as adoption dates.

## Try it offline

Requirements: **Linux, Python 3.11+, Git**. No third-party Python installation is
required; the requirement parser is vendored with its licenses. An ordinary
repository or a bare repository must already be present locally.

```sh
# Create a fresh isolated installation; no pip, registry or network is used.
python3 scripts/install.py --venv /tmp/stack-timeline-env

# Produce a complete synthetic demo, including its local Git repository.
python3 scripts/demo.py /tmp/stack-timeline-demo

# Open /tmp/stack-timeline-demo/report/index.html in your browser.
# commits.json contains the explicit immutable selection used by this demo.
```

For your own repository, pass 1–32 **hexadecimal commit IDs** in comparison order:

```sh
/tmp/stack-timeline-env/bin/repo-stack-timeline /path/to/repository \
  0123456789ab fedcba987654 --output /tmp/my-stack-report
```

Replace the example IDs with actual commits from your repository. `HEAD`, branch
names and revision expressions are not accepted. Use `--object-format sha256`
for a SHA-256 repository. The output directory must be fresh, outside the scanned
repository, with an existing parent. Source refs, index, config and worktree are
not modified. Each complete bundle contains `index.html`, `report.json`, and
`SHA256SUMS`; existing outputs are never overwritten.

The viewer supports snapshot navigation, dependency/path/constraint search,
ecosystem/category/change filters, before/after evidence, keyboard controls and
pagination. Open it directly as a local file; there is no server, upload, telemetry,
external stylesheet, or CDN. The first snapshot is a baseline; switch to “All
declarations in snapshot” to inspect it.

Other installation options:

```sh
# Source invocation, also offline:
PYTHONPATH=src python3 -m repo_stack_timeline --help

# Build a deterministic pure-Python wheel with the stdlib-only PEP 517 backend:
python3 scripts/wheel_backend.py --output /tmp/stack-wheels
# If pip is already available in your target environment:
python3 -m pip install --no-index --no-deps /tmp/stack-wheels/repo_stack_timeline-1.0.0-py3-none-any.whl
```

## Supported scope

| Format | Extracted declarations |
| --- | --- |
| `package.json` | dependencies, devDependencies, optionalDependencies, peerDependencies |
| `pyproject.toml` | static project dependencies, optional dependency groups, build-system requirements |

Constraints are preserved without resolution. Nested manifests are enumerated
from committed trees. Path moves are reported as path changes; names are never
guessed across manifests. Python names are normalized for identity while raw
requirement strings remain available. npm constraints are opaque strings.

These are **declared dependencies**, not installed versions, actual usage,
transitive graphs, ecosystem popularity, or evidence of when a library was first
adopted. Lockfiles, setup.py, backend execution, requirements.txt, Poetry-specific
dependencies, and dependency groups are outside this version's scope. Relevant
unsupported and dynamic fields carry explicit notices. Two unreadable snapshots
can have no comparable events; inspect coverage notices before interpreting
empty results.

The frozen [semantics and limits](docs/semantics.md), [JSON format](docs/report-format.md),
and [security boundary](docs/security.md) explain the exact rules. Runtime and
byte limits fail explicitly; no truncated success report is published. Gitfiles,
linked worktrees and alternate object stores are unsupported. Hard memory
isolation and origin/visibility authentication are not provided by the scanner.

## Verify

Run the complete check with one command after provisioning the optional browser
test tools:

```sh
python3 scripts/verify.py --browser
```

Verification never installs or downloads anything. It requires Linux
`libseccomp.so.2` for the network-denied subprocess checks, and Node.js, Playwright
1.51.1 plus its Chromium for `--browser`. For an existing external installation,
set `PLAYWRIGHT_MODULE` to its absolute `playwright` package directory and
`PLAYWRIGHT_BROWSERS_PATH` to its browser cache. Without browser tools,
`python3 scripts/verify.py` runs all Python checks and benchmarks and explicitly
records the browser as not run. See [verification details](docs/verification.md)
for one-time tool setup and reproduction commands.

The suite compares 200 seeded Git histories (1,400 selected snapshots and 1,200
comparisons) with an independent expected-declaration model. It also checks
malformed/dynamic input, unchanged source state, bounded reads, process cleanup,
signals, interrupted writes, racing output collisions, SHA-256 objects, packed
objects, hostile text, and an isolated installed CLI with network syscalls denied.
Chromium exercises navigation, filters, keyboard controls, pagination, provenance,
narrow screens and injected markup in an offline context.

Actual test and benchmark evidence is in [results/verification.json](results/verification.json)
and [results/tests.log](results/tests.log). Measurements are local observations,
not ecosystem-wide conclusions. The benchmark records elapsed time, peak RSS,
artifact sizes and SHA-256 hashes, and checks three identical runs per fixture.

## Frozen public sample and prior work

```sh
python3 scripts/demo.py /tmp/stack-public-demo --public
```

This reconstructs local **manifest projections** from four licensed snapshots:
Flask 3.0.0/3.1.0 (BSD-3-Clause) and Express 4.18.2/4.19.2 (MIT). Their exact source
revisions, source/blob hashes, licenses and acquisition instructions live in
[examples/public](examples/public/README.md). Projection commits are synthetic,
not upstream history; their upstream mapping is saved separately. The sample is
purposeful and small, with no claim of representativeness.

Dependency extraction and review already have substantial prior art. See
[related work](docs/related-work.md) for the primary specifications and relevant
GitHub, ScanCode and Dependabot implementations. This project makes no novelty
or comparative performance claim.

MIT licensed. Vendored `packaging` and public fixtures retain their own licenses.
