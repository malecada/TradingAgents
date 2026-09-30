"""Fail closed until the exact predecessor preservation is independently reconciled.

Checks compact receipts only. The new gate must bind closure-review.json and all
its evidence. This does not repeat the remote body transfer or its verification.
"""
import hashlib
import json
from pathlib import Path

STORAGE = Path('research/onchain-paper-replication-2026-09-24/storage/closed-ledger-offload-2026-09-30-01')
REQUIRED = ('manifest.json', 'guard01/final.json', 'complete.json',
            'completion-candidate.json', 'recovered-complete.json',
            '00-verified.json', '00-evicted.json', '00-restore.json',
            '00-recovered-restore.json', 'CLOSURE_REVIEW.md')


def compact(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size >= 2_000_000:
        raise ValueError('compact regular evidence required: '+str(path))
    return path.read_bytes()


def verify(root, *, storage=STORAGE):
    root = Path(root)
    here = root / storage
    review_bytes = compact(here/'closure-review.json')
    review = json.loads(review_bytes)
    if review.get('decision') != 'accepted' or review.get('scope') != 'closed-ledger-preservation-terminal':
        raise ValueError('independent preservation closure acceptance required')
    if set(review.get('evidence', {})) != set(REQUIRED):
        raise ValueError('preservation evidence set differs')
    bodies = {name:compact(here/name) for name in REQUIRED}
    for name, body in bodies.items():
        if hashlib.sha256(body).hexdigest() != review['evidence'][name]:
            raise ValueError('reviewed preservation evidence changed: '+name)
    final = json.loads(bodies['guard01/final.json'])
    if (final['phase'] != 'complete' or final['child_exit_code'] != 0
            or final['cleanup_verified'] is not True
            or Path(final['cgroup']).exists()
            or Path('/proc',str(final['monitor_pid'])).exists()):
        raise ValueError('successful terminal preservation and absent owner required')
    manifest = json.loads(bodies['manifest.json'])
    if len(manifest['files']) != 1:
        raise ValueError('exact single-file preservation required')
    row = manifest['files'][0]
    path = Path(row['path'])
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('invalid source path')
    source = root/path
    if source.exists() or source.is_symlink():
        raise ValueError('source still present; reconcile before proceeding')
    record = json.loads(bodies['00-verified.json'])
    if (any(record.get(k) != v for k,v in row.items())
            or record.get('body_roundtrip_verified') is not True
            or record.get('remote_object') != manifest['remote']+'/00.bin'
            or record.get('remote_restore') != manifest['remote']+'/00-restore.json'):
        raise ValueError('verified preservation identity differs')
    for name in ('00-evicted.json','00-restore.json','00-recovered-restore.json'):
        if json.loads(bodies[name]) != record:
            raise ValueError('restoration or eviction record differs')
    if json.loads(compact(source.with_name(source.name+'.remote.json'))) != record:
        raise ValueError('restoration sidecar differs')
    complete = json.loads(bodies['complete.json'])
    if (complete['files'] != [record] or complete['bytes_moved'] != row['bytes']
            or manifest['total_bytes'] != row['bytes']
            or any(bodies[n] != bodies['complete.json'] for n in
                   ('completion-candidate.json','recovered-complete.json'))):
        raise ValueError('completion roundtrip differs')
    return {'closure_review_sha256':hashlib.sha256(review_bytes).hexdigest(),
            'evidence_hashes_verified':len(REQUIRED), 'bytes_preserved':row['bytes'],
            'qualification':'Compact independently reviewed closure evidence only; no repeated remote body verification.'}


STORAGES = tuple(STORAGE.with_name('closed-ledger-offload-2026-09-30-'+suffix)
                 for suffix in ('01', '02', '03'))


def verify_chain(root):
    """Require actual accepted closure of each separately owned preservation."""
    records = [{'path': str(storage), **verify(root, storage=storage)}
               for storage in STORAGES]
    return {'preservations': records,
            'total_bytes_preserved': sum(r['bytes_preserved'] for r in records),
            'qualification': 'Compact closure evidence only; no remote body replay or inference of current free space.'}
