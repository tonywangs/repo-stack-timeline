from dataclasses import dataclass, asdict
import math
import time
from .errors import TimelineError


@dataclass(frozen=True)
class Limits:
    lockfile_bytes: int = 4_194_304
    package_entries: int = 100_000
    lockfile_work: int = 1_000_000
    tree_entries: int = 100_000
    manifests: int = 2_000
    blob_bytes: int = 1_048_576
    total_bytes: int = 16_777_216
    seconds: float = 120.0
    report_bytes: int = 8_388_608
    git_output_bytes: int = 16_777_216
    ancestry_commits: int = 100_000

    def __post_init__(self):
        for key, value in asdict(self).items():
            if isinstance(value, bool) or not math.isfinite(value) or value <= 0:
                raise TimelineError("invalid_limit", f"{key} must be finite and positive")
            if key != 'seconds' and not isinstance(value, int):
                raise TimelineError("invalid_limit", f"{key} must be an integer")


class Budget:
    def __init__(self, limits):
        self.limits = limits
        self.deadline = time.monotonic() + limits.seconds
        self.counts = dict(tree_entries=0, manifests=0, total_bytes=0)

    def check(self):
        if time.monotonic() >= self.deadline:
            raise TimelineError("runtime_limit", "Scan and publication exceeded the runtime limit")

    def consume(self, key, value=1):
        self.check()
        self.counts[key] += value
        if self.counts[key] > getattr(self.limits, key):
            raise TimelineError(key + "_limit", f"Exceeded {key} limit ({getattr(self.limits, key)})")
