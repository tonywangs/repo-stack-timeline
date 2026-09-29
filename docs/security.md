# Read-only Git object boundary

The supported runtime is Linux, Python 3.11+, and a trusted Git executable on
PATH. Verification was performed on the versions in `results/verification.json`.

The scanner recognizes a regular repository root containing a `.git` directory,
or a bare Git directory containing `HEAD` and `objects`. Gitfiles, linked
worktrees, and nonempty `objects/info/alternates` are explicitly unsupported.
For a SHA-256 repository, select `--object-format sha256`.

All Git commands run in a fresh temporary bare directory with a fixed config,
empty refs, and `GIT_OBJECT_DIRECTORY` pointing to the source object store. No
Git command is invoked inside the source worktree or with its Git directory.
Source hooks, config includes, aliases, filters, credential helpers, remote
settings, replace refs, grafts, and fsmonitor are not loaded. An environment
allowlist excludes caller-supplied Git settings. System/global config is disabled,
protocols are denied, lazy fetching is disabled, and the isolated repository has
no remotes. Incomplete/promisor clones cannot fetch missing objects.

The only plumbing operations used are `rev-parse`, `cat-file`, `ls-tree`, and
`rev-list`. There is no checkout, index operation, network operation, interpreter
invocation from the scanned project, submodule traversal, textconv, or build.
Manifests are parsed as data with JSON, TOML, and a vendored requirement parser.

Subprocess stdout/stderr are read with bounded nonblocking pipes. Each subprocess
has its own process group, killed and reaped in `finally` on failure/cancellation.
Total scan time and output budgets apply while subprocesses are running. These
bounds do not sandbox vulnerabilities in Git/Python or cap all of Git's internal
memory allocation. Use an OS container/cgroup for untrusted adversarial object
stores requiring a hard memory/security boundary. Concurrent source modification
is unsupported; immutable object IDs prevent ref drift, but concurrent deletion,
object corruption, or alternate-store changes can cause failure. The tool does
not claim to authenticate a repository's origin or public/private visibility.

Safety tests hash all source files, including config, index, refs, dirty worktree
and untracked contents, before/after scanning. They install hostile config and
environment canaries and assert no execution. This verifies preservation for the
fixtures, not every Git/filesystem version. Access-time updates caused by reads
are excluded. A production scan does not recursively hash unrelated worktree
files; it avoids writing them in the first place.

## Output transaction

Choose a new output directory outside the scanned repository, with an existing
parent. JSON serialization and HTML rendering complete and pass the combined
size limit before file creation. Three files are written and fsynced in a sibling
temporary directory, then published with Linux `renameat2(RENAME_NOREPLACE)`.
Existing directories, files, symlinks (including dangling links), and race-winning
outputs are never replaced. There is no unsafe overwrite fallback on unsupported
platforms. A signal during writes removes the temporary directory. SIGKILL, power
loss, or a process crash may leave an unpublished `.repo-stack-tmp-*` directory;
it can be removed after confirming no scan is running. After the atomic rename,
a late cancellation or parent-directory fsync failure can return an error while
a complete bundle already exists. Inspect it; choose a fresh path to retry.

## HTML

Reports are self-contained files with no external scripts, CSS, fonts, or images.
Manifest strings are escaped inside an inert JSON script element and rendered
only with DOM `textContent`. They are never interpolated into HTML markup,
JavaScript source, URLs, CSS, or event handlers. Embedded script/style hashes are
whitelisted by a Content Security Policy whose default and connection policies
deny all sources. There is no HTML/JSON upload execution feature.

The Chromium test uses an offline browser context, aborts all non-file requests,
checks zero attempted external requests and page/console errors, and exercises
literal closing-script tags, script bodies, image/onerror markup, Unicode,
quotation marks and template tokens. It also checks filtering, pagination,
keyboard interactions and narrow-screen overflow. This is functional security
coverage, not a formal audit or full accessibility certification.

`report.json` preserves committed dependency strings and paths, including any
secrets an upstream author may have put in a URL. Treat the generated bundle with
the same confidentiality as its source manifests. Nothing uploads it.
