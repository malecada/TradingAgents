"""One finite, reviewed cold-file move; old job identities are never rerun."""
from pathlib import Path
import fcntl
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
GIB = 1024**3


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk := stream.read(1024**2):digest.update(chunk)
    return digest.hexdigest()


def identity(st):
    return [st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns]


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def publish(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())
    sync_directory(Path(path).parent)


def validate_source(source, row):
    st = source.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
        raise ValueError('source must be an exclusive regular file')
    if identity(st) != row['stat_identity'] or sha(source) != row['sha256']:
        raise ValueError('source identity changed')
    if identity(source.lstat()) != row['stat_identity']:
        raise ValueError('source changed during verification')


def offload_one(root, here, row, number, remote, transport):
    source = root / row['path']
    validate_source(source, row)
    verified = here / f'{number:02d}-verified.json'
    sidecar = source.with_name(source.name + '.remote.json')
    if verified.exists() or sidecar.exists():
        raise FileExistsError('identity already attempted; reconcile instead of repeating')
    body = remote + f'/{number:02d}.bin'
    recovery = here / f'{number:02d}-recovered.bin'
    metadata = here / f'{number:02d}-restore.json'
    recovered_metadata = here / f'{number:02d}-recovered-restore.json'
    with os.fdopen(os.open(source, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as retained:
        fcntl.flock(retained, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if identity(os.fstat(retained.fileno())) != row['stat_identity']:
            raise ValueError('opened file identity differs')
        transport.put(source, body)
        transport.get(body, recovery)
        if recovery.stat().st_size != row['bytes'] or sha(recovery) != row['sha256']:
            raise ValueError('body round-trip mismatch; original retained')
        validate_source(source, row)
        record = {**row, 'remote_object':body, 'remote_restore':remote+f'/{number:02d}-restore.json',
                  'body_roundtrip_verified':True,
                  'restoration':'Download remote_object to a new temporary file; verify bytes and SHA-256; restore original path only when absent. Never launch the old job.'}
        publish(metadata, record)
        transport.put(metadata, record['remote_restore'])
        transport.get(record['remote_restore'], recovered_metadata)
        if sha(metadata) != sha(recovered_metadata):
            raise ValueError('restoration metadata round-trip mismatch; original retained')
        publish(verified, record)
        publish(sidecar, record)
        validate_source(source, row)
        if identity(os.fstat(retained.fileno())) != row['stat_identity']:
            raise ValueError('opened source drifted')
        source.unlink()
        sync_directory(source.parent)
    publish(here / f'{number:02d}-evicted.json', record)
    recovery.unlink()  # Successful verification scratch only; failed scratch is retained.
    sync_directory(here)
    return record


def finish(here, record, remote, transport):
    candidate = here/'completion-candidate.json'
    recovered = here/'recovered-complete.json'
    publish(candidate, record)
    transport.put(candidate,remote+'/complete.json')
    transport.get(remote+'/complete.json',recovered)
    if sha(candidate) != sha(recovered):
        raise ValueError('completion metadata round-trip mismatch')
    publish(here/'complete.json', record)


def worker():
    from tradingagents.research.onchain_replication.resources import assert_guarded_worker
    bindings = json.loads((HERE/'bindings.json').read_text())
    for path, expected in bindings.items():
        if sha(ROOT/path) != expected:raise ValueError('bound source changed: '+path)
    c = json.loads((HERE/'manifest.json').read_text())
    policy_path = ROOT/c['disk_policy']
    if sha(policy_path) != c['disk_policy_sha256']:
        raise ValueError('disk policy changed')
    policy = json.loads(policy_path.read_text())
    if policy['schema_version'] != 1 or policy['disk_floor_bytes'] != 10*GIB:
        raise ValueError('unexpected prospective disk policy')
    assert_guarded_worker(HERE/'guard01', sys.orig_argv, required_paths=[ROOT],
                          wall_seconds=7200, memory_max_bytes=256*1024**2,
                          memory_high_bytes=192*1024**2,disk_floor_bytes=policy['disk_floor_bytes'])
    prior_path = ROOT/c['predecessor_final']
    if sha(prior_path) != c['predecessor_final_sha256']:
        raise ValueError('predecessor receipt changed')
    prior = json.loads(prior_path.read_text())
    if prior['phase'] != 'failed' or prior['cleanup_verified'] is not True or Path(prior['cgroup']).exists():
        raise ValueError('predecessor offload still owns work')
    prior_here = prior_path.parent.parent
    if list(prior_here.glob('*-evicted.json')) or list(prior_here.glob('*-verified.json')):
        raise ValueError('predecessor has per-file results; reconcile rather than resend')
    for kind in ('connection', 'transport'):
        if sha(ROOT/c[kind+'_path']) != c[kind+'_sha256']:
            raise ValueError(kind+' binding changed')
    if len(c['files']) != 9 or sum(r['bytes'] for r in c['files']) != c['total_bytes']:
        raise ValueError('target set differs')
    if max(r['bytes'] for r in c['files']) > 512*1024**2:
        raise ValueError('per-file scratch bound exceeded')
    if shutil.disk_usage(ROOT).free < 10*GIB + 512*1024**2 + 16*1024**2:
        raise ValueError('insufficient verification scratch')
    for row in c['files']:
        path = Path(row['path'])
        if path.is_absolute() or '..' in path.parts or not str(path).startswith('research/onchain-paper-replication-2026-09-24/storage/'):
            raise ValueError('out-of-scope target')
        if subprocess.check_output(['git','ls-files','--',row['path']], cwd=ROOT):
            raise ValueError('tracked target refused')
        validate_source(ROOT/path, row)
        owner = ROOT/row['owner']
        if sha(owner) != row['owner_sha256']:raise ValueError('owner receipt changed')
        terminal = json.loads(owner.read_text())
        if terminal['phase'] != 'failed' or terminal['cleanup_verified'] is not True or Path(terminal['cgroup']).exists():
            raise ValueError('old owner not closed')
    spec = importlib.util.spec_from_file_location('retained_transport', ROOT/c['transport_path'])
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    transport = module.Transport(json.loads((ROOT/c['connection_path']).read_text()),
                                 rate=262144, maximum_payload_bytes=8*GIB)
    if transport.available() < c['total_bytes']+GIB:
        raise ValueError('remote capacity insufficient')
    publish(HERE/'intent.json', {'manifest_sha256':sha(HERE/'manifest.json'),
            'remote':c['remote'],'files':len(c['files']),'bytes':c['total_bytes'],
            'no_automatic_retry':True,'before_disk_free_bytes':shutil.disk_usage(ROOT).free})
    try:
        transport.mkdir(c['remote'])  # Exclusive creation: refuses an existing remote identity.
        transport.put(HERE/'manifest.json', c['remote']+'/manifest.json')
        transport.get(c['remote']+'/manifest.json', HERE/'recovered-manifest.json')
        if sha(HERE/'manifest.json') != sha(HERE/'recovered-manifest.json'):
            raise ValueError('inventory round-trip mismatch')
        records=[]
        for number,row in enumerate(c['files']):
            records.append(offload_one(ROOT,HERE,row,number,c['remote'],transport))
            print(json.dumps({'files_complete':len(records),'bytes_moved':sum(r['bytes'] for r in records)}),flush=True)
        finish(HERE, {'files':records,'bytes_moved':c['total_bytes'],
                'after_disk_free_bytes':shutil.disk_usage(ROOT).free,
                'qualification':'Remote cold tier, verified by full byte round-trip; local original bodies removed only after durable remote restoration metadata. Raw inputs unchanged.'}, c['remote'], transport)
    except BaseException as error:
        publish(HERE/'failed.json', {'error':type(error).__name__+': '+str(error),
                'no_automatic_retry':True,'action':'Reconcile per-file verified/evicted receipts and sidecars; never blindly retry or delete failed scratch.'})
        raise


if __name__ == '__main__':
    sys.path.insert(0,str(ROOT))
    if sys.argv[1:] == ['--worker']:
        worker()
    elif sys.argv[1:]:raise ValueError('unexpected argument')
    else:
        from tradingagents.research.onchain_replication.resources import guarded_run
        result=guarded_run([str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__).resolve()),'--worker'],
            cwd=ROOT,receipt_dir=HERE/'guard01',memory_max_bytes=256*1024**2,
            memory_high_bytes=192*1024**2,memory_swap_max_bytes=0,reserve_bytes=3*GIB,
            start_reserve_bytes=int(3.5*GIB),disk_paths=[ROOT],disk_floor_bytes=10*GIB,wall_seconds=7200)
        print(json.dumps({k:result.get(k) for k in ('phase','child_exit_code','cleanup_verified','limit_reason','elapsed_seconds')}),flush=True)
        sys.exit(0 if result['phase']=='complete' and result['cleanup_verified'] and result['child_exit_code']==0 else 1)
