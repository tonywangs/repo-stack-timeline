# Licensed npm lockfile fixtures

Six unmodified npm/cli Arborist test fixtures are frozen from commit
`dbe7d983d184fb00c85f7b34839a123057029c8b` (npm 10.8.2). npm, Inc.'s
[ISC license](LICENSE) applies. [sources.json](sources.json) records exact source
URLs, revision, SHA-256, byte count, original version, and package-entry count.

| Fixture | Version | Package entries | Purpose |
| --- | --- | --- | --- |
| workspaces-simple-virtual | 2 | 5 | Root, workspace object, links |
| workspaces-conflicting-versions-virtual | 2 | 8 | Duplicate package names at different locations |
| testing-peer-deps-nested | 2 | 9 | Nested and peer metadata |
| external-link-dep | 2 | 6 | Parent-relative external target records |
| engine-specification | 2 | 3 | Engine metadata |
| install-types | 1 | 0 in a packages map | Explicit unsupported-format negative control |

These are synthetic upstream test fixtures, not a representative sample of real
projects. Five supported files contain **31 records**. Verification additionally
makes five **synthetic v3 transformations** in temporary storage (change
`lockfileVersion`, remove the v2 compatibility section), adding another 31 records.
Those transformations are explicitly labeled and are not upstream v3 fixtures.

The pinned Arborist reader and scanner compare the supported projection across
10 supported inputs / 62 records. The sixth upstream fixture is a negative
control: Arborist converts v1, while this scanner reports incomplete. This
expected scope difference is reported separately, not counted as agreement.

To reacquire the exact fixtures explicitly with network access:

```sh
python3 scripts/acquire_lockfiles.py
```

Ordinary verification is offline and checks all saved file/license hashes. It
never runs fixture code, installs fixture dependencies, follows their links, or
fetches recorded resolved URLs.
