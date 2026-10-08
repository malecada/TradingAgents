"""One-use opaque xsect backup; original files are never removed or decoded."""
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import select
import shutil
import signal
import stat
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def emit(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def checked(ref):
    path = ROOT / ref['path']
    assert path.resolve(strict=True) == path and path.stat().st_size == ref['bytes']
    body = path.read_bytes()
    assert hashlib.sha256(body).hexdigest() == ref['sha256'], ref['path']
    return body


def headroom(contract):
    mem = next(line for line in Path('/proc/meminfo').read_text().splitlines()
               if line.startswith('MemAvailable:'))
    available = int(mem.split()[1]) * 1024
    required = sum(contract[key] for key in (
        'active_native_modeled_extra_allocated_bytes', 'disk_floor_bytes',
        'max_additional_local_staging_bytes', 'metadata_and_allocation_slack_bytes'))
    free = shutil.disk_usage(ROOT).free
    assert available >= contract['host_reserve_bytes'] + (
        contract['max_owned_local_processes'] * contract['address_space_limit_bytes'])
    assert free >= required, 'shared disk reserve unavailable'
    return {'available_memory_bytes': available, 'disk_free_bytes': free,
            'required_free_bytes': required}


def current(rows, directories, source_root):
    for row in [*rows, *directories]:
        path = Path(row['source_path'])
        assert path.resolve(strict=True) == path and path.is_relative_to(source_root)
        observed = path.lstat()
        assert (observed.st_dev, observed.st_ino, observed.st_mode,
                observed.st_mtime_ns, observed.st_ctime_ns, observed.st_nlink) == (
                    row['device'], row['inode'], row['mode'], row['mtime_ns'],
                    row['ctime_ns'], row['nlink']), str(path)
        if row['kind'] == 'regular':
            assert stat.S_ISREG(observed.st_mode) and observed.st_nlink == 1
            assert observed.st_size == row['bytes']
        else:
            assert row['kind'] == 'directory' and stat.S_ISDIR(observed.st_mode)


def main():
    contract_body = (HERE / 'CONTRACT03.json').read_bytes()
    contract = json.loads(contract_body)
    release = json.loads((HERE / 'RELEASE03.json').read_bytes())
    assert release['decision'] == 'accepted' and release['identity'] == contract['identity']
    assert release['contract_sha256'] == hashlib.sha256(contract_body).hexdigest()
    assert release['source_sha256'] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    assert not (HERE / 'INTENT01.json').exists(), 'backup identity already reserved'
    assert not (HERE / contract['working_directory']).exists()
    for ref in contract['source_refs'].values():
        checked(ref)
    rows = json.loads(checked(contract['input_refs']['CONTENT_ROWS01.json']))
    directories = json.loads(checked(contract['input_refs']['DIRECTORIES01.json']))
    batch_document = json.loads(checked(contract['input_refs']['BATCHES01.json']))
    checked(contract['input_refs']['MANIFEST02.json'])
    assert len(rows) == contract['expected_files']
    assert sum(row['bytes'] for row in rows) == contract['expected_raw_bytes']
    assert len(directories) == contract['expected_directories']
    assert len(batch_document['batches']) == contract['expected_batches']
    source_root = Path(contract['source_root'])
    current(rows, directories, source_root)
    initial = headroom(contract)
    os.nice(10)
    os.sched_setaffinity(0, {contract['cpu']})
    for kind, bound in ((resource.RLIMIT_AS, contract['address_space_limit_bytes']),
                        (resource.RLIMIT_FSIZE, contract['file_size_limit_bytes'])):
        resource.setrlimit(kind, (bound, bound))
    from tradingagents.research.lifecycle import _immutable
    from tradingagents.research.onchain_replication.preservation import (
        plan_batches, sha256, transfer_bundle)
    batches = plan_batches(rows, max_raw_bytes=contract['maximum_batch_raw_bytes'],
                           max_members=contract['maximum_batch_members'])
    assert batches == batch_document['batches']
    # Execute only the two exact previously reviewed transport definitions.
    legacy = next(ref for path, ref in contract['source_refs'].items()
                  if path.endswith('/transfer.py'))
    tree = ast.parse(checked(legacy))
    nodes = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))
             and node.name in {'Transport', 'receive_diagnostic'}]
    assert len(nodes) == 2
    scope = dict(globals(), _immutable=_immutable)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(ROOT / legacy['path']), 'exec'), scope)
    helper_ref = contract['source_refs'][contract['owned_transport_path']]
    helper_scope = {'__name__': 'xsect_owned_transport02', '__file__': str(ROOT / helper_ref['path'])}
    exec(compile(checked(helper_ref), str(ROOT / helper_ref['path']), 'exec'), helper_scope)
    helper_scope['install'](scope)
    connection = json.loads(checked(contract['connection_ref']))
    transport = scope['Transport'](connection, contract['rate_kbit'],
                                    contract['maximum_network_payload_bytes'])
    began = time.monotonic()
    def deadline(signum, frame):
        raise TimeoutError('fixed7200second backup deadline')
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, contract['wall_seconds'])
    emit(HERE / 'INTENT01.json', {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'identity': contract['identity'], 'contract_sha256': sha256(HERE / 'CONTRACT03.json'),
         'pid': os.getpid(), 'initial_headroom': initial, 'originals_preserved': True})
    completed = []
    try:
        free = transport.available()
        assert free >= contract['expected_raw_bytes'] + 1024**3
        transport.mkdir(contract['remote'])  # no -p; existing namespace refuses
        metadata = HERE / 'returned-metadata'
        metadata.mkdir()
        selected = [HERE / name for name in contract['root_metadata_files']] + [
            ROOT / ref['path'] for ref in contract['input_refs'].values()] + [
            ROOT / path for path in contract['selected_source_paths']]
        for original in selected:
            remote = contract['remote'] + '/' + original.name
            returned = metadata / original.name
            before = sha256(original)
            transport.put(original, remote)
            transport.get(remote, returned)
            assert sha256(returned) == before == sha256(original)
        work = HERE / contract['working_directory']
        work.mkdir()
        for batch in batches:
            observed = headroom(contract)
            for ref in contract['source_refs'].values():
                checked(ref)
            current(rows, directories, source_root)
            index = batch['index']
            result = transfer_bundle(rows[batch['start']:batch['stop']],
                work / f'batch-{index:04d}', remote=contract['remote'] + f'/batch-{index:04d}',
                transport=transport, allowed_roots=[source_root], start_index=batch['start'])
            current(rows, directories, source_root)
            assert not any((work / f'batch-{index:04d}' / name).exists()
                           for name in ('bundle.tar', 'recovered.tar'))
            completed.append({'index': index, 'receipt_sha256': sha256(
                work / f'batch-{index:04d}' / 'complete.json'), 'headroom': observed, **result})
            emit(HERE / f'PROGRESS_{index:04d}.json', {
                'elapsed_seconds': time.monotonic() - began, 'completed_batches': completed,
                'originals_preserved': True, 'restart_permitted': False})
        assert sum(row['files'] for row in completed) == len(rows)
        assert sum(row['raw_bytes'] for row in completed) == contract['expected_raw_bytes']
        current(rows, directories, source_root)
        emit(HERE / 'COMPLETE01.json', {'status': 'complete', 'batches': completed,
             'files': len(rows), 'raw_bytes': contract['expected_raw_bytes'],
             'elapsed_seconds': time.monotonic() - began,
             'originals_preserved': True, 'deletion_authorized': False,
             'qualification': contract['qualification']})
    except BaseException as error:
        emit(HERE / 'FAILED01.json', {'status': 'failed', 'error_type': type(error).__name__,
             'reason': str(error), 'completed_batches': completed,
             'originals_preserved': True, 'restart_permitted': False})
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == '__main__':
    main()
