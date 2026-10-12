"""JSON-lines stage log with elapsed seconds and peak RSS on every record."""
from __future__ import annotations

import json
import resource
import time
from pathlib import Path


def rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


class Log:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.t0 = time.time()

    def event(self, **kv):
        rec = {'t': round(time.time() - self.t0, 3), 'rss_mb': round(rss_mb(), 1), **kv}
        with open(self.path, 'a') as fh:
            fh.write(json.dumps(rec, sort_keys=True, default=str) + '\n')
        return rec
