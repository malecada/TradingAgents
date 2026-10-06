"""One preservation-only body pass; no SQLite query or numerical import."""
from pathlib import Path
import ast
import hashlib
import json
import math
import os
import stat
import time

ROOT = Path.cwd().resolve(strict=True)
HERE = Path(__file__).resolve().parent
PREFIX = 'research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220530-20261005-01/'
EXPECTED = {
    PREFIX + 'aggregation/ledger.sqlite': 3189231616,
    PREFIX + 'graph-2022-05-30/edge_index.npy': 38817824,
    PREFIX + 'graph-2022-05-30/node_features.npy': 50606240,
}


def identity(s):
    return [s.st_dev, s.st_ino, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def main():
    output = HERE / 'BODY_HASH01.json'
    attempt = HERE / 'body-pass-attempt01.json'
    assert not output.exists() and not attempt.exists(), 'one-use pass already reserved'
    failed = ROOT / 'research_runs/eth-paper-real-pilot-graph-20220530-20261005-01/failed.json'
    assert hashlib.sha256(failed.read_bytes()).hexdigest() == 'f5e452d0352424a13db233a914ffb1ce742244a49de0481ef1b011459b2b569b'
    guard = json.loads((ROOT / 'research_artifacts/onchain-paper-replication-2026-09-24/runs/eth-paper-real-pilot-graph-20220530-20261005-01/guard/final.json').read_bytes())
    assert guard['phase'] == 'failed' and guard['cleanup_verified'] is True and not Path(guard['cgroup']).exists()
    assert not (ROOT / PREFIX / 'aggregation/complete.json').exists()
    started = time.monotonic()
    with attempt.open('x') as stream:
        json.dump({'identity': 'may30-failed-original-three-body-pass-20261006-01', 'expected_bytes': sum(EXPECTED.values()), 'numerical_imports': False}, stream)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    rows = []
    for name, size in sorted(EXPECTED.items()):
        path = ROOT / name
        before = path.lstat()
        assert path.resolve(strict=True) == path and stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size == size
        digest = hashlib.sha256(); prefix = b''; count = 0
        with path.open('rb') as stream:
            assert identity(os.fstat(stream.fileno())) == identity(before)
            while chunk := stream.read(1024 * 1024):
                if not prefix:
                    prefix = chunk[:65536]
                digest.update(chunk); count += len(chunk)
            assert identity(os.fstat(stream.fileno())) == identity(before)
        assert identity(path.lstat()) == identity(before) and count == size
        row = {'path': name, 'bytes': count, 'sha256': digest.hexdigest(), 'stat_identity': identity(before), 'mode': stat.S_IMODE(before.st_mode)}
        if name.endswith('.npy'):
            assert prefix[:6] == b'\x93NUMPY'
            version = list(prefix[6:8]); assert version in ([1, 0], [2, 0], [3, 0])
            offset = 10 if version == [1, 0] else 12
            length = int.from_bytes(prefix[8:offset], 'little'); assert offset + length <= len(prefix)
            header = ast.literal_eval(prefix[offset:offset+length].decode('utf-8' if version == [3, 0] else 'latin1'))
            assert set(header) == {'descr', 'fortran_order', 'shape'} and header['fortran_order'] is False
            dtype = header['descr']; shape = header['shape']
            assert dtype in ('<i8', '<f8') and type(shape) is tuple and all(type(n) is int and n >= 0 for n in shape)
            assert offset + length + math.prod(shape) * 8 == count
            assert (dtype == '<i8' and len(shape) == 2 and shape[0] == 2) if name.endswith('edge_index.npy') else (dtype == '<f8' and len(shape) == 2 and shape[1] == 4)
            row['npy_header'] = {'version': version, 'header_bytes': offset + length, **header}
        else:
            assert prefix[:16] == b'SQLite format 3\x00'
            row['sqlite_integrity'] = 'not queried; magic bytes only'
        rows.append(row)
        print(path.name, count, flush=True)
    result = {'decision': 'pass', 'index_sha256': None, 'files': rows, 'total_bytes': sum(row['bytes'] for row in rows), 'one_streaming_pass_per_body': True, 'headers_captured_same_pass': 2, 'numerical_imports': False, 'raw_daily_body_reads': False, 'sqlite_queries': False, 'elapsed_seconds': time.monotonic() - started, 'qualification': 'Actual FAILED retained ledger and two partial arrays only. No prior expected content hash exists; these are fresh preservation hashes and structural header checks, not a complete graph or SQLite integrity proof.'}
    assert result['total_bytes'] == 3278655680
    with output.open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({'decision': result['decision'], 'files': len(rows), 'total_bytes': result['total_bytes'], 'elapsed_seconds': result['elapsed_seconds'], 'proof_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
