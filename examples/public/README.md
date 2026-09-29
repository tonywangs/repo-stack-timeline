# Frozen, licensed public manifest sample

`sources.json` lists four purposefully selected snapshots of two established
projects. Each record contains the repository, human-readable tag, **immutable
upstream commit ID**, exact raw source URL, content SHA-256, Git blob SHA-1,
byte count, and license. Included upstream license files apply to their adjacent
manifest; the project-level MIT license does not replace them.

| Source | Snapshots | License |
| --- | --- | --- |
| [Pallets Flask](https://github.com/pallets/flask) | 3.0.0, 3.1.0 | BSD-3-Clause; included LICENSE.rst / LICENSE.txt |
| [Express](https://github.com/expressjs/express) | 4.18.2, 4.19.2 | MIT; included LICENSE |

Acquisition is a separate, explicit **network** operation:

```sh
python3 scripts/acquire_public.py
```

It reads only public unauthenticated HTTPS endpoints, with no token or credential
lookup. Existing `sources.json` pins immutable commits; reacquisition verifies
its stored hashes before replacing a file. Ordinary scanning, demos, benchmarks,
and verification never invoke this acquisition script.

Offline demonstration:

```sh
python3 scripts/demo.py /tmp/stack-public-demo --public
```

The demo verifies the saved hashes and creates a **synthetic local repository**
containing manifest/license projections. It first updates Flask, then adds and
updates Express. Its commits/trees are local projections, not the original
upstream commit IDs or full trees. `projection.json` maps these local commits to
the original source revision and selected paths. The report's commit/blob
provenance refers to this reconstructed local repository; the raw manifest blobs
match the upstream evidence in `sources.json`.

This is a convenience sample for reproducibility and real-format smoke testing.
It omits other manifests, lockfiles, source code, upstream parents and histories.
It does not measure general extraction accuracy, dependency adoption dates,
installation behavior, prevalence, or popularity. The seeded synthetic oracle is
the controlled correctness experiment; this sample is a complementary check.
