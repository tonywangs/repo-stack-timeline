# Scope and related work

This project makes no claim to invent dependency extraction or dependency-history
analysis. Its narrow contribution is a small offline implementation combining
explicit ordered commit selection, declaration-level evidence, uncertainty, and
an independently checked synthetic history generator.

Primary references inspected during implementation:

- [Git ls-tree](https://git-scm.com/docs/git-ls-tree) specifies NUL-delimited tree
  enumeration; [cat-file](https://git-scm.com/docs/git-cat-file) provides object
  type/size/content reads. These are the scanner's data boundary.
- [Python pyproject specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
  defines static project dependencies, optional dependency groups, build
  requirements, and dynamic metadata. [Dependency specifiers](https://packaging.python.org/en/latest/specifications/dependency-specifiers/)
  describe requirement strings. Our implementation freezes packaging 24.0
  acceptance instead of silently adopting future grammar changes.
- [npm package.json](https://docs.npmjs.com/cli/v11/configuring-npm/package-json/)
  documents dependency categories and constraints. This tool preserves their
  literal declarations; it does not reproduce npm installation semantics.
- [GitHub dependency graph](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-graph)
  and [dependency review](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-review)
  already expose dependencies and changes in a hosted workflow. This CLI instead
  reads local objects and emits a portable static report with an explicit scope.
- [ScanCode Toolkit](https://github.com/aboutcode-org/scancode-toolkit) is a broader
  code/package/license inventory implementation. It is relevant prior work for
  manifest parsing; it is not used here as a dependency or experimental baseline.
- [Dependabot Core](https://github.com/dependabot/dependabot-core) implements
  ecosystem-aware dependency update workflows. Update resolution and PR creation
  are deliberately outside this application's scope.

These are scope comparisons, not measured accuracy or performance rankings. The
validation baseline here is a generated ground-truth declaration model, not a
claim that these existing tools are less accurate. Public fixtures are a tiny
convenience sample and do not support ecosystem-popularity or adoption claims.

## npm lockfile comparison

See [lockfile related work](lockfiles.md#prior-work-and-independent-reader) for the
primary npm specification and pinned Arborist 7.5.4 independent reader.
