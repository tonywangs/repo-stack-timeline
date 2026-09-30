# Reproducing validation

The main command is:

```sh
python3 scripts/verify.py --browser
```

It runs the following sequentially, stopping on any failure:

1. Unit, safety, and independent-oracle tests with `socket`/`connect` syscalls
   denied by an inherited Linux seccomp filter. The installed-CLI test builds
   two equal wheels, creates a fresh venv without pip, validates wheel RECORD
   hashes, installs locally, and runs the CLI twice from an unrelated working
   directory with a hostile PYTHONPATH. It asserts identical artifacts and
   unchanged source files.
2. Three measured CLI runs each for synthetic seed 42 and the four-snapshot
   public manifest projection. Source acquisition is never part of verification.
   Runtime, Linux wait4 peak RSS, artifact bytes and hashes are recorded and
   repeated outputs must match exactly.
3. An offline Chromium session against a generated hostile-text report, with all
   non-file requests aborted and a restrictive report CSP. Navigation, filtering,
   baseline behavior, category moves, provenance, keyboard controls, pagination,
   dynamic/malformed notices, inert imported strings and mobile overflow are
   asserted. Browser errors and attempted network requests fail the check.
4. Publication bounds: at most 10 MiB per file, 32 MiB total, 1,000 files, and no
   `.log` files other than `results/tests.log`, excluding ignored development
   caches. Credentials/session transcripts/control handoffs are never artifacts.

`--record` refreshes `results/tests.log` and `results/verification.json` with actual
outputs, times and versions. Without it, verification uses temporary directories
and preserves checked-in evidence. Run without `--browser` when browser tools are
unavailable; that result explicitly says the browser was not run and is weaker
than full verification. Nothing is silently skipped in a `--browser` run.

## Browser tool setup (separate network operation)

If not already available, provision these free development tools explicitly:

```sh
npm install --prefix /tmp/stack-browser --cache /tmp/stack-npm-cache playwright@1.51.1
PLAYWRIGHT_BROWSERS_PATH=/tmp/stack-browser/cache \
  /tmp/stack-browser/node_modules/.bin/playwright install chromium
export PLAYWRIGHT_MODULE=/tmp/stack-browser/node_modules/playwright
export PLAYWRIGHT_BROWSERS_PATH=/tmp/stack-browser/cache
python3 scripts/verify.py --browser
```

Chromium also needs its normal host shared libraries. The application has no Node,
Playwright or browser runtime dependency to create reports. Browser caches and
node_modules are outside the project tree. Linux libseccomp is a verification
prerequisite only; tests fail visibly if it is absent.

## Independent oracle design

`tests/helpers.py::seed_history` creates the expected identity/string model before
serializing any manifest. The production extractor, parser, canonicalizer and
comparator are never used to create expectations. Each of 200 deterministic seeds
creates a root, two branches, a merge and a malformed/dynamic successor, then
selects a backward transition and a repeated merge. Seed variation changes
names, Python constraints/extras and nested Unicode paths. All histories include
category changes and path moves. Timestamps intentionally disagree with ancestry.

`oracle_events` is a separate set-based model comparison. The test checks all
extracted raw strings and all event identities/kinds/before/after values against
that model, plus selected commit provenance and ancestry relations. Focused tests
cover parsed extras, markers, direct URLs, invalid section shapes, duplicate keys,
name normalization, reordered requirements, incomplete categories, SHA-256,
non-UTF-8 paths, missing objects, symlinks and submodules.

This oracle does not prove complete PEP 508 parser correctness: the generator
uses a bounded grammar and hand-written cases. It does not randomly sample every
possible DAG topology (the branch/merge skeleton is intentionally fixed), every
Git implementation, or hostile filesystem race. Those are validation limits, not
negative results to conceal.

## Measurements and failure findings

Read actual numerical results from `results/verification.json`. Every benchmark
uses the same deterministic input but a new process/output directory; caches may
be warm. Elapsed time includes process launch. Linux `ru_maxrss` is the largest
RSS measured for the command process/reaped children, not the sum of simultaneous
memory across the process tree. Numbers are local observations and may vary on
rerun. JSON/HTML/checksum hashes must not vary within a repeated benchmark.

A safety test found that `git merge-base --is-ancestor` could short-circuit without
noticing an unavailable parent. The implementation instead reads a bounded
reachable parent graph and reports incomplete ancestry as unknown. The regression
test remains. The first browser harness also aborted local file navigation; its
routing rule was corrected to allow local files while blocking all other requests.
These were observed failures during development, not evidence that the initial
versions passed.

## Lockfile extension

Historical evidence above remains unchanged. The combined current verification
uses Playwright 1.58.2 and pinned Arborist 7.5.4; see
[lockfile verification](lockfile-verification.md) for its single command, exact
setup, current evidence, and limitations.
