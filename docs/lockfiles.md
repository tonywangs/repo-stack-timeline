# Recorded npm lockfile state

Add `--lockfiles` to the installed CLI (or source invocation). This enables
`repo-stack-timeline/2` JSON and an **Analysis** selector in the HTML viewer.
Choose **Recorded lockfile packages** and then snapshot or change view. Search
matches locations, recorded names, lockfile paths, and before/after metadata.
Changes show the changed fields, commits, and blob IDs. Declaration filters and
results remain separate. No npm installation is required to run the scanner.

```sh
repo-stack-timeline /path/to/repository BEFORE_HEX_ID AFTER_HEX_ID \
  --lockfiles --output /tmp/fresh-lockfile-report
```

## Frozen semantics: npm-lockfiles/1

Every committed regular `package-lock.json` and `npm-shrinkwrap.json` is read
independently, including nested projects. Identity is the exact pair **lockfile
path + package location**, never package name. Moving a lockfile or package
location produces an absence and addition. Two copies of the same named package
at different locations remain separate. The empty location denotes the root
record; it is retained even though it is not a dependency. Missing root records
are allowed. Alias records retain their installation location and explicit `name`
if present; names are never inferred from URLs, versions, or directory names.

Only integer lockfile versions 2 and 3 with a `packages` object are supported.
Version 2's legacy `dependencies` section is ignored. Top-level fields other than
`lockfileVersion` and `packages` are outside this projection. Differences in
lockfile version are visible in snapshot evidence, but do not themselves produce
package-change events. Hidden `node_modules/.package-lock.json` files are excluded.

npm gives a co-located shrinkwrap precedence over package-lock. This tool still
shows both recorded files and marks the package-lock with
`shrinkwrap_takes_precedence`; it does not claim to select an effective install
graph. A symlink or invalid shrinkwrap does not cause the scanner to follow it.
Nested files are independent recorded evidence, not npm's runtime project roots.

Supported record fields:

| Value type | Fields |
| --- | --- |
| String | `name`, `version`, `resolved`, `integrity`, `license`, `deprecated` |
| Boolean | `dev`, `optional`, `devOptional`, `peer`, `link`, `inBundle`, `hasInstallScript`, `hasShrinkwrap` |
| Object of strings | `dependencies`, `devDependencies`, `optionalDependencies`, `peerDependencies`, `engines`, `bin` |
| Array of strings | `os`, `cpu`, `libc`, `workspaces` |
| Structured object | `workspaces` also accepts `packages` / `nohoist` string arrays; `peerDependenciesMeta` maps names to objects containing an optional boolean `optional` |

Missing fields remain missing; they are not replaced with defaults. Empty objects
remain records. Values are literal, not semver-normalized; integrity strings are
not cryptographically verified. Object order and whitespace do not matter. Array
order and duplicates are preserved, so array reordering can be a metadata change.
Unknown fields produce `unmodeled_field` notices and are not compared. Thus `ok`
means complete for this **supported projection**, not complete npm semantics.

Links require a nonempty string `resolved`; their target is recorded but never
followed, resolved, merged with another record, or checked on disk. Parent-relative
external locations (for example `../shared`) are allowed as opaque identifiers.
Absolute locations, backslashes, drive prefixes, controls, empty or `.` path
components, and `..` after a normal component are ambiguous and rejected.

Malformed JSON, duplicate keys at any depth, nonfinite values, invalid record
shapes, unsupported versions, missing packages maps, or nonregular files make
that entire file `incomplete`. No records from that file are used. This is
intentionally conservative: a valid opposing file can produce `unknown` events,
but never a definite addition or absence against incomplete data. If neither
side has usable records, a comparison may have **zero events and still be
incomplete**. Check the top-level, per-file, and per-comparison status. CLI success output also includes `lockfile_status`; exit
0 means a bundle was published, even when its analysis is incomplete. A genuinely
missing file is known empty within the enumerated tree. Repeated/reversed
snapshots and branch comparisons follow the supplied selection order.

## JSON version 2

The default invocation still emits the version 1 schema and unchanged declaration
semantics. Opt-in version 2 retains all its declaration fields and adds:

- Top-level `lockfile_semantics_version: "npm-lockfiles/1"`, and `lockfile_status`
  (`ok` or `incomplete`). `schema_version` becomes `repo-stack-timeline/2`.
- Each snapshot has `lockfiles`: records with `path`, `blob`, `mode`,
  `lockfile_version` (2/3 or null), `status`, `diagnostics`, and `records`.
  A package record contains `location` and a `metadata` object with supported
  present fields. Commit/tree provenance is inherited from the snapshot.
- Each comparison adds `lockfile_status`, `lockfile_diagnostics`, and
  `lockfile_events`. Events contain `path`, `location`, `kind`, `before`, `after`,
  `changed_fields`, and both `before_` / `after_` `commit` and `blob` IDs.
  `kind` is `added`, `absent`, `changed`, or `unknown`. A null side means no usable
  record, not necessarily absence; consult kind/status. Unknown events have no
  claimed changed fields. Known events list all differing present fields,
  including additions/removals of metadata. Empty records can yield additions
  with an empty changed-fields array.
- `limits` adds `lockfile_bytes`, `package_entries`, and `lockfile_work`; `counts`
  adds aggregate `package_entries` and `lockfile_work`. The shared manifests count includes lockfile candidates,
  and `total_bytes` includes all read manifest/lockfile blobs, including repeats.

Path and location arrays/events are sorted. JSON serialization is canonical;
identical inputs, order, limits, and software produce byte-identical bundles.

## Bounds and security

Defaults: 4 MiB per lockfile (`--max-lockfile-bytes`), 100,000 aggregate package
entries (`--max-package-entries`), 1,000,000 aggregate work units
(`--max-lockfile-work`), 16 MiB total blob reads, 100,000 tree entries,
2,000 manifest/lockfile candidates, 32 snapshots, 120 seconds for CLI analysis and
publication, and 8 MiB for the entire report bundle. Existing Git-output and
ancestry limits also apply. A work unit is an extracted package, metadata field,
immediate metadata container entry, comparison path/location, or compared field
on either side (even for unchanged records). Byte bounds also cover JSON parsing
and unmodeled nested values. Runtime checks and the CLI alarm bound parsing,
comparison, and serialization. A bound failure exits with an error and publishes
no report; it is not silently truncated into an `ok` analysis. The per-lockfile
size failure uses the existing `blob_bytes_limit` error code.

No resolved URL is fetched; no package is installed; no lifecycle script or
repository code is executed. Object reads use the existing isolated Git object
view. The worktree, index, refs, and configuration remain unchanged. This is not
hard memory isolation. Use lower limits or external isolation for hostile inputs.

Reports describe recorded state, **not installed packages, actual usage,
vulnerabilities, verified package contents, or an effective resolution graph**.
Unmodeled fields and malformed records reduce coverage. The small fixture corpus
and bounded synthetic workloads do not establish compatibility with every npm
release or performance on arbitrary repositories.

## Prior work and independent reader

The format and shrinkwrap precedence are documented in the
[npm package-lock specification](https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json/).
The pinned independent implementation is
[Arborist 7.5.4's Shrinkwrap reader at npm/cli dbe7d983](https://github.com/npm/cli/blob/dbe7d983d184fb00c85f7b34839a123057029c8b/workspaces/arborist/lib/shrinkwrap.js).
Its `load()` retains v2/v3 packages and its `get()` exposes records by location;
it also converts legacy lockfiles, which this project intentionally rejects.
The scanner does not depend on or embed that reader. This is a bounded offline
history view built on established formats, with no novelty claim.

See [the licensed corpus](../examples/lockfiles/README.md) and
[verification instructions](lockfile-verification.md) for exact reproduction.
