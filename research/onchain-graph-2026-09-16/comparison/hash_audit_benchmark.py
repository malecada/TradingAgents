"""Synthetic maximum-bucket benchmark; no research source data are opened."""
import hashlib
import json
from pathlib import Path
import platform
import sys

import numpy as np

from hash_audit import audit_hashes


def main():
    here = Path(__file__).resolve().parent
    output = Path(sys.argv[1])
    scratch = Path(sys.argv[2])
    distinct, repeats = 2**20, 8
    identities = np.zeros((distinct, 32), dtype=np.uint8)
    identities[:, 24:] = np.arange(distinct, dtype=">u8").view(np.uint8).reshape(-1, 8)
    chunk = identities.tobytes()
    del identities
    digest = hashlib.sha256()
    for _ in range(repeats):
        digest.update(chunk)
    expected = dict(total=distinct*repeats, unique=distinct,
                    duplicate_excess=distinct*(repeats-1),
                    input_bytes=len(chunk)*repeats, input_stream_sha256=digest.hexdigest())
    result = audit_hashes((chunk for _ in range(repeats)), scratch_parent=scratch,
                          max_total_hashes=distinct*repeats,
                          max_total_bytes=len(chunk)*repeats,
                          max_bucket_bytes=256*1024**2)
    for key, value in expected.items():
        if result[key] != value:
            raise AssertionError((key, result[key], value))
    if result["buckets"][0]["bytes"] != 256*1024**2:
        raise AssertionError("fixture did not reach maximum configured bucket")
    report = dict(synthetic_only=True, expected=expected, result=result,
                  python=platform.python_version(), numpy=np.__version__,
                  source_sha256={name: hashlib.sha256((here/name).read_bytes()).hexdigest()
                                 for name in ("hash_audit.py", "hash_audit_benchmark.py")},
                  qualification="One maximum-sized bucket, repeated exact identities; not full-panel integration or capacity proof.")
    with output.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps(dict(synthetic_only=True, **expected)))


if __name__ == "__main__":
    main()
