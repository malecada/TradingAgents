"""One-use preservation hash pass over the three fresh recovered bodies only."""
import hashlib
import json
import os
from pathlib import Path
import stat
import time

ROOT = Path.cwd().resolve(strict=True)
HERE = Path(__file__).resolve().parent
STORE = ROOT / 'research/onchain-paper-replication-2026-09-24/storage/real-pilot-fifth-graph-failed-preservation-20261006-01'


def signature(s):
    return [s.st_dev, s.st_ino, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def main():
    output = HERE / 'RECOVERED_PAYLOAD_HASH01.json'
    attempt = HERE / 'attempt01.json'
    assert not output.exists() and not attempt.exists(), 'one-use pass already reserved'
    selection_bytes = (STORE / 'selection01.json').read_bytes()
    selection = json.loads(selection_bytes)
    basis_ref = selection['independent_body_hash']
    basis_bytes = (ROOT / basis_ref['path']).read_bytes()
    assert hashlib.sha256(basis_bytes).hexdigest() == basis_ref['sha256']
    basis = {r['path']: r for r in json.loads(basis_bytes)['files']}
    assert len(basis) == 3 and selection['count'] == 30
    terminal = json.loads((STORE / 'ROOT_TERMINAL01.json').read_bytes())
    assert terminal['actual_root_tool_exit_code'] == 0 and terminal['actual_current_cgroup_absent'] is True
    assert hashlib.sha256((STORE / 'complete.json').read_bytes()).hexdigest() == terminal['complete_sha256']
    rows = []
    began = time.monotonic()
    with attempt.open('x') as stream:
        json.dump({'identity': 'may30-failed-recovered-three-body-pass-20261006-01', 'expected_bytes': 3278655680, 'numerical_imports': False}, stream)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    for i, row in enumerate(selection['files']):
        if row['path'] not in basis:
            continue
        expected = basis[row['path']]
        assert row['bytes'] == expected['bytes'] and row['sha256'] == expected['sha256']
        path = STORE / f'{i:02d}-recovered.bin'
        before = path.lstat()
        assert path.resolve(strict=True) == path and stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size == row['bytes']
        digest = hashlib.sha256(); count = 0
        with path.open('rb') as stream:
            assert signature(os.fstat(stream.fileno())) == signature(before)
            while block := stream.read(1024**2):
                digest.update(block); count += len(block)
            assert signature(os.fstat(stream.fileno())) == signature(before)
        assert signature(path.lstat()) == signature(before) and count == row['bytes'] and digest.hexdigest() == row['sha256']
        rows.append({'index': i, 'original_path': row['path'], 'recovered_path': str(path.relative_to(ROOT)), 'bytes': count, 'sha256': digest.hexdigest(), 'stat_identity': [before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns], 'mode': stat.S_IMODE(before.st_mode)})
    assert len(rows) == 3 and sum(r['bytes'] for r in rows) == 3278655680
    result = {'kind': 'single-three-recovered-payload-streamed-hash-pass', 'decision': 'pass', 'files': rows, 'total_bytes': 3278655680, 'elapsed_seconds': time.monotonic() - began, 'selection_sha256': hashlib.sha256(selection_bytes).hexdigest(), 'original_body_pass_reused': basis_ref, 'one_streaming_pass_per_body': True, 'original_payload_reads': False, 'arrays_decoded': False, 'sqlite_queries': False, 'qualification': 'Fresh external BYTE recovery of FAILED ledger and two partial arrays only; no completed graph or database integrity claim.'}
    with output.open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({'decision': 'pass', 'files': len(rows), 'total_bytes': result['total_bytes'], 'elapsed_seconds': result['elapsed_seconds'], 'proof_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
