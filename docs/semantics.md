# Declaration semantics v1

The JSON `schema_version` is `repo-stack-timeline/1`; `semantics_version` is
`declarations/1`. This document freezes the extraction and comparison contract.
Changing these rules requires a new semantics version. The parser implementation
for Python requirement strings is the vendored, unmodified `packaging` 24.0.
There is no resolver, installer, build backend execution, marker evaluation,
network call, or import/usage analysis.

## Selection and provenance

Supply **1–32 hexadecimal object identifiers**, 4–40 characters for SHA-1 or
4–64 with `--object-format sha256`. IDs must unambiguously resolve to commits;
an annotated tag object's hexadecimal ID may peel to a commit. Ref names,
`HEAD`, ranges, revision expressions, and paths are rejected. Resolve convenient
names yourself in a trusted shell, then pass the resulting IDs. The scanner does
not inspect source refs. The object format is explicit; it does not read the
repository's config to discover it.

Every supplied ID is resolved once at scan start. Full commit and tree IDs are
recorded; repeated selections remain repeated. No sorting by date or ancestry
occurs. Only adjacent **selected** snapshots are compared. The first snapshot is
a baseline and emits no events. Commits between selections may contain changes
that cancel out and are invisible here. The committer timestamp is provenance,
never an adoption date. Author identity/message are omitted.

The `ancestry` field describes the previous selected commit relative to the next:
`same`, `ancestor`, `descendant`, `diverged_or_unrelated`, or `unknown`. It is
computed from a bounded reachable parent graph, ignoring grafts, replace refs,
and source shallow boundaries. Missing parent objects yield `unknown` and an
`ancestry_incomplete` diagnostic; they do not turn into a claim of unrelatedness.
An exhausted ancestry budget aborts with an explicit error. No merge-parent
selection or merge-specific dependency attribution is inferred.

Each manifest has its exact tree path, mode, ecosystem, and blob ID. Each event
also carries before/after commit and blob IDs. Non-UTF-8 path bytes round-trip in
JSON as surrogate escapes; browsers may display replacement glyphs for those
bytes. The JSON path plus tree/blob IDs are the authoritative evidence. File
contents must be UTF-8 without a BOM. Symlinks and gitlinks are never followed.
Manifest-like names with nonregular modes are recorded as unsupported.

## npm / package.json

Recognized categories (kept separate): `dependencies`, `devDependencies`,
`optionalDependencies`, `peerDependencies`. Each must be a JSON object with
nonempty string names and string values. Names are case-sensitive and retained
literally; npm name and range validation is intentionally outside scope. All
constraint strings are opaque: aliases, URLs, workspace/file references,
tags, empty strings, and semver expressions are preserved without following or
interpreting them. An empty string is a declaration, not a missing value.

A dependency declared in multiple categories remains multiple declarations.
In particular, npm's optional-dependency override behavior is **not** simulated.
`bundleDependencies`, `bundledDependencies`, `overrides`, `resolutions`,
`peerDependenciesMeta`, and `packageExtensions` produce `unsupported_metadata`
notices when present. They are not folded into the four supported categories.
Other package metadata, scripts, lockfiles, workspace expansion, and transitive
dependencies are outside the extraction scope. Nested manifests are discovered
by enumerating the entire selected tree, not by interpreting workspace patterns.

Duplicate JSON keys anywhere, nonfinite numbers, invalid JSON, non-object roots,
and invalid UTF-8 make the entire manifest invalid. A mistyped dependency section
or non-string dependency value marks its category uncertain, but valid siblings
are retained as observations. JSON recursion failures are malformed input.

## Python / pyproject.toml

Recognized categories:

- `[project].dependencies` → `project.dependencies`.
- `[project.optional-dependencies].EXTRA` → `project.optional-dependencies.EXTRA`.
- `[build-system].requires` → `build-system.requires`.

Each section is an array of PEP 508 strings. Each valid string retains its **exact
raw value**, declared name, sorted extras as parsed (case preserved), normalized
specifier rendering, marker rendering, and direct URL. Markers are not evaluated.
Package identity uses PEP 503 normalization: lowercase and collapse runs of `.`,
`_`, `-` to `-`. Raw text remains authoritative. Extras in category names are
retained literally. Invalid or PEP 685-colliding optional group names make the
whole optional group namespace uncertain.

Multiple requirements with the same normalized name/category are grouped into a
sorted **multiset** of raw strings. Duplicates are retained. Reordering an array
or reformatting TOML does not change a declaration. Changing requirement whitespace,
name spelling, marker text, or constraint spelling does count as a textual
change, even if a resolver would treat it as equivalent. The JSON's parsed
components aid inspection; comparison uses the full sorted declaration records.

Malformed TOML or encoding makes the whole manifest invalid. Invalid section
shapes and invalid PEP 508 entries produce diagnostics and uncertainty for that
category, while valid sibling strings remain observable. This is not a general
`pyproject.toml` validator; unrelated metadata (e.g. project version) need not be
valid for dependency extraction.

`project.dynamic` mentioning dependencies or optional dependencies marks that
category/namespace uncertain. Static values conflicting with `dynamic` are not
extracted. An invalid `dynamic` value makes all categories uncertain. Missing
`[project]` means project dependency metadata is unavailable, not empty. Missing
`[build-system]` declares no build requirements in this scope; default backend
requirements are not inferred. A present build table without `requires` is
uncertain. An explicitly empty static array is known empty.

`dependency-groups` and recognized tool tables (`poetry`, `pdm`, `uv`, `hatch`,
`flit`, `setuptools`) are flagged but not evaluated. Neither setup.py nor backend
plugins, requirements.txt, Poetry tables, lockfiles, generated metadata, editable
installs, nor environment-dependent build requirements are resolved. Parser
acceptance follows packaging 24.0, not future extensions to requirement syntax.

## Comparison and coverage

The identity tuple is `(manifest path, ecosystem, category, normalized name)`.
Moves are path disappearance/appearance, even if blob IDs match. A category move
similarly produces separate absence/addition events. There is no rename guess.

- `added`: a supported declaration is observed after known prior absence.
- `absent`: a prior supported declaration is absent from the later supported scope.
- `changed`: both complete categories have differing declaration records.
- `unknown`: observed records differ, but either category is incomplete.

Before/after values are lists, or `null` when no supported declaration was
extracted. For `unknown`, `null` does **not** establish absence. Even non-null
lists may be incomplete. Identical observed records emit no event; coverage
notices still apply. Two unreadable manifests may therefore emit no events while
both carry explicit diagnostics. An empty event list is not evidence of a
complete or unchanged installed environment.

A path missing from a completely enumerated tree establishes absence in this
scope. Failure to enumerate a tree or read a required object aborts the scan;
there is no silently truncated report. A malformed manifest is nonfatal and
visible. Snapshot diagnostics also expose skipped submodules.

## Determinism and budgets

JSON sorts object keys, uses ASCII escapes, two-space indentation and a final
newline. Arrays use input selection order, lexicographically sorted paths and
identities, and sorted requirement values. Reports omit current time, local
source/output paths, timing measurements, Git version, and machine details.
Repeated runs with identical objects, selection, limits, semantics, and renderer
produce identical JSON, HTML, and checksums. Changing a configured limit changes
the report even when extraction is the same. Byte-identical output across future
Python/TOML implementations is not promised; test and record the environment.

Default limits are explicit in each JSON report and available as CLI flags:

| Flag | Default | Accounting |
| --- | ---: | --- |
| `--max-tree-entries` | 100,000 | Directories, files, symlinks and gitlinks across selected snapshots, repeats included |
| `--max-manifests` | 2,000 | Manifest-name candidates across selections, repeats included |
| `--max-blob-bytes` | 1,048,576 | Each supported regular manifest blob |
| `--max-total-bytes` | 16,777,216 | Sum of manifest reads, repeats included |
| `--max-seconds` | 120 | CLI scan, extraction, rendering and publication |
| `--max-report-bytes` | 8,388,608 | Combined JSON, HTML and checksum file |
| `--max-git-output-bytes` | 16,777,216 | Each tree/ancestry plumbing output; stderr is separately capped at 16 KiB |
| `--max-ancestry-commits` | 100,000 | Reachable commits per adjacent non-identical comparison |

Commit object reads have an additional 1 MiB ceiling. `rev-parse` output is capped
at 256 bytes and size-query output at 64 bytes. All positive limits are user
configurable; lowering them may reject a previously successful scan. The library
API checks a cooperative wall-clock budget; the Linux CLI additionally uses a
real-time alarm. Scheduling and kernel I/O can delay signal delivery; this is
not a hard real-time or memory-isolation guarantee.

Fatal errors are a single JSON diagnostic on stderr and exit code 2. SIGINT or
SIGTERM produces `cancelled` and exit 130. There is no success bundle for an
exhausted budget. Missing snapshot/tree/blob objects are fatal `git_object_error`;
missing ancestry alone is explicitly unknown. Git's raw stderr is not copied to
the report. A successful scan with coverage notices still exits zero.

## Optional lockfile analysis

The exclusions above describe the default declaration projection. `--lockfiles`
adds [npm-lockfiles/1 semantics](lockfiles.md) under report schema version 2.
