# Frozen application extension

This two-case extension was defined in [cohort.json](cohort.json) before annual
extraction. It supplements, rather than rewrites, the eight-library convenience
cohort. See [the findings](../../results/applications/report.md) and
[local viewer](../../results/applications/index.html).

Primary repositories inspected when selecting the cases:
[Node-RED](https://github.com/node-red/node-red) (visual event-driven programming)
and [Etherpad](https://github.com/ether/etherpad) (collaborative document editing).
Etherpad's former `ether/etherpad-lite` URL redirects to the recorded canonical
name. These sources justify current application-purpose strata, not historical
category labels or independent governance. This is not a new sampling method
and makes no novelty claim.

## Reproduce

Python 3.11+ suffices for offline analysis; acquisition additionally needs Git.
No account, package installation, paid service, or upstream code execution is used.

```sh
python3 scripts/application_report.py --check
python3 scripts/application_report.py --output /tmp/application-report
# Open /tmp/application-report/index.html, report.md, or report.json.

# Optional NETWORK audit: reuse the frozen heads; do not move them.
python3 scripts/acquire_annual.py --cohort examples/applications/cohort.json --sources examples/applications/sources --cache /tmp/application-history
```

Acquisition uses anonymous public Git transport, not the GitHub REST/GraphQL API,
so no API token or API quota is used. Git transport throttling/network failures
abort visibly; there is no automatic retry or backoff. Each subprocess has a
600-second timeout. Completed repository shards survive failure; rerunning the
same command checks those shards byte-for-byte and resumes other repositories.
Do not delete source shards to retry: their heads and acquisition timestamps pin
the experiment. A failed member is never replaced or silently omitted.

As in [the original acquisition](../annual/README.md), selection walks the full
first-parent chain of the frozen default-branch head. It chooses the first
commit before the next January 1 UTC for each year. This is retrospective branch
lineage, not historical releases/default branches or actual deployment history.
Snapshots preserve commit, root tree, manifest and license objects with hashes.
Offline checks verify those objects; auditing selection requires full Git history.
No eligible commit is unavailable history, missing root metadata is unknown, and
an explicit observable empty root set would be zero. Nested manifests are outside
this checkpoint's measurement scope, even when the root is missing.

Both projects' root license evidence is preserved at every selected commit;
these source bytes retain their upstream Apache-2.0 licenses and notices.
The cohort license field is a selection-time label; the exact per-snapshot text
is authoritative. Third-party source files are encoded research evidence, not
relicensed project code.

## Result and remaining measurement work

Node-RED has seven observable root snapshots, with 46 names in 2019 and 56 in
2025. Etherpad has four missing root manifests and three observable root sets
of one name each. This is a root-measurement coverage result, not a claim that
Etherpad uses only one technology. Its nested application manifests must be
measured before interpreting its stack. The extension adds 14 snapshots, 10
observable and four unknown; current application-purpose selection covers two
cases but cannot establish annual project-category trends.

All ten combined cases are surviving public projects selected today. A historical
sampling frame including entry/exit and inaccessible projects is still needed
to investigate a changing population. No survival or inclusion probabilities can
be estimated here. The extension has not received independent fresh review.
