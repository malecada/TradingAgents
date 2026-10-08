"""One-use, finite fresh external reconstruction; never retire original data."""
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
import time

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def require(ok, why):
    if not ok:
        raise ValueError(why)


def checked(ref):
    require(type(ref) is dict and set(ref) == {'path', 'bytes', 'sha256'}, 'unbound input')
    path = ROOT / ref['path']
    require(path.is_relative_to(ROOT) and path.resolve(strict=True) == path, 'redirected input')
    require(path.stat().st_size == ref['bytes'], 'input extent differs')
    body = path.read_bytes()
    require(hashlib.sha256(body).hexdigest() == ref['sha256'], 'input hash differs')
    return body


def emit(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def validate_selection(contract):
    """Join the complete actual backup, every ordered batch and member manifest."""
    backup_contract = json.loads(checked(contract['backup_contract_ref']))
    complete = json.loads(checked(contract['backup_complete_ref']))
    rows = json.loads(checked(backup_contract['input_refs']['CONTENT_ROWS01.json']))
    directories = json.loads(checked(backup_contract['input_refs']['DIRECTORIES01.json']))
    batches = json.loads(checked(backup_contract['input_refs']['BATCHES01.json']))['batches']
    require(backup_contract['identity'] == contract['backup_identity'], 'backup identity differs')
    require(backup_contract['source_root'] == contract['original_root'], 'original root differs')
    require(complete['status'] == 'complete' and complete['originals_preserved'] is True,
            'whole backup incomplete')
    require(len(rows) == complete['files'] == contract['expected_files'] and
            sum(row['bytes'] for row in rows) == complete['raw_bytes'] == contract['expected_raw_bytes'],
            'whole payload denominator differs')
    require(len(directories) == contract['expected_directories'], 'directory denominator differs')
    require(len(batches) == len(contract['selection']) == len(complete['batches']) ==
            contract['expected_batches'], 'batch denominator differs')
    results = []
    for index, (batch, selected, recorded) in enumerate(zip(
            batches, contract['selection'], complete['batches'], strict=True)):
        require(batch['index'] == selected['index'] == recorded['index'] == index,
                'batch order differs')
        receipt_body = checked(selected['receipt_ref'])
        receipt = json.loads(receipt_body)
        require(hashlib.sha256(receipt_body).hexdigest() == recorded['receipt_sha256'],
                'whole backup does not join batch receipt')
        require(receipt['status'] == 'complete' and all(receipt[k] is True for k in
                ('originals_preserved', 'downloaded_members_verified', 'source_hashes_verified')),
                'unverified backup batch')
        require(receipt['start_index'] == batch['start'] and
                receipt['files'] == batch['stop'] - batch['start'] and
                receipt['raw_bytes'] == batch['raw_bytes'], 'batch denominator differs')
        for key, value in receipt.items():
            require(recorded[key] == value, 'whole backup batch differs')
        remote = backup_contract['remote'] + f'/batch-{index:04d}'
        require(receipt['remote'] == remote, 'remote namespace differs')
        manifest_body = checked(selected['manifest_ref'])
        require(hashlib.sha256(manifest_body).hexdigest() == receipt['manifest_sha256'],
                'manifest does not join original receipt')
        manifest = json.loads(manifest_body)
        expected = [{**row, 'member': f'files/{i:08d}'} for i, row in
                    enumerate(rows[batch['start']:batch['stop']], batch['start'])]
        require(json.dumps(manifest['members'], sort_keys=True, allow_nan=False) ==
                json.dumps(expected, sort_keys=True, allow_nan=False), 'ordered members differ')
        for key in ('files', 'raw_bytes', 'archive_bytes', 'archive_sha256'):
            require(manifest[key] == receipt[key], 'manifest extent/hash differs')
        require(0 < manifest['archive_bytes'] <= contract['max_archive_bytes'],
                'archive capacity exceeds fixed bound')
        results.append((batch, receipt, manifest))
    return rows, directories, results


def eligibility(contract, remaining_allocated_bytes):
    parent = Path(contract['target_root']).parent
    require(parent.resolve(strict=True) == parent and
            parent.stat().st_dev == ROOT.stat().st_dev and
            os.statvfs(parent).f_frsize == contract['allocation_block_bytes'],
            'target filesystem or allocation block differs')
    terminal = json.loads(checked(contract['native_terminal_ref']))
    guard = json.loads(checked(contract['native_final_ref']))
    require(terminal['identity'] == contract['native_identity'] and
            type(terminal['actual_root_exit_code']) is int and
            terminal['original_process_paths_absent'] is True, 'native Root closure missing')
    require(guard['phase'] in ('failed', 'complete') and guard['cleanup_verified'] is True and
            type(guard['child_exit_code']) is int, 'native cleanup missing')
    require(contract['native_identity'] in guard['command'], 'wrong native command')
    require(guard['cgroup'] == contract['native_cgroup'] and
            not Path(guard['cgroup']).exists(), 'native cgroup active or differs')
    require(not any(Path(f'/proc/{pid}').exists() for pid in contract['original_native_pids']),
            'original native PID still present')
    require(not Path(f"/proc/{contract['backup_driver_pid']}").exists(), 'backup driver active')
    backup_terminal = json.loads(checked(contract['backup_terminal_ref']))
    require(backup_terminal['identity'] == contract['backup_identity'] and
            backup_terminal['actual_root_exit_code'] == 0, 'backup Root closure missing')
    free = shutil.disk_usage(ROOT).free
    required = (contract['disk_floor_bytes'] + remaining_allocated_bytes +
                contract['max_archive_bytes'] + contract['metadata_and_allocation_slack_bytes'])
    available = next(int(line.split()[1]) * 1024 for line in
                     Path('/proc/meminfo').read_text().splitlines()
                     if line.startswith('MemAvailable:'))
    require(free >= required, 'recovery allocation plus disk floor unavailable')
    require(available >= contract['host_reserve_bytes'] +
            contract['max_owned_local_processes'] * contract['address_space_limit_bytes'],
            'recovery memory headroom unavailable')
    return {'disk_free_bytes': free, 'required_free_bytes': required,
            'available_memory_bytes': available}


def transport_for(contract):
    from tradingagents.research.lifecycle import _immutable
    nodes = [node for node in ast.parse(checked(contract['legacy_transport_ref'])).body
             if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and
             node.name in {'Transport', 'receive_diagnostic'}]
    require(len(nodes) == 2, 'transport definitions missing')
    scope = dict(globals(), _immutable=_immutable)
    exec(compile(ast.Module(body=nodes, type_ignores=[]),
                 contract['legacy_transport_ref']['path'], 'exec'), scope)
    helper = {'__name__': 'xsect_recovery_owned_transport',
              '__file__': str(ROOT / contract['owned_transport_ref']['path'])}
    exec(compile(checked(contract['owned_transport_ref']), helper['__file__'], 'exec'), helper)
    helper['install'](scope)
    return scope['Transport'](json.loads(checked(contract['connection_ref'])),
                             contract['rate_kbit'], contract['maximum_network_payload_bytes'])


def main():
    contract_body = (HERE / 'CONTRACT_FINAL01.json').read_bytes()
    contract = json.loads(contract_body)
    release = json.loads((HERE / 'RELEASE01.json').read_bytes())
    require(contract['status'] == 'READY' and release['decision'] == 'accepted',
            'entry not released')
    require(release['identity'] == contract['identity'] and
            release['contract_sha256'] == hashlib.sha256(contract_body).hexdigest() and
            release['source_sha256'] == digest(Path(__file__)), 'release join differs')
    require(not (HERE / 'INTENT01.json').exists(), 'recovery identity already reserved')
    target = Path(contract['target_root'])
    require(target.parent.resolve(strict=True) == target.parent and not target.exists(),
            'target occupied or parent redirected')
    require(not (HERE / 'downloads').exists(), 'download namespace occupied')
    for ref in contract['source_refs'].values():
        checked(ref)
    rows, directories, selection = validate_selection(contract)
    initial = eligibility(contract, contract['restore_allocation_bound_bytes'])
    os.nice(10)
    os.sched_setaffinity(0, {contract['cpu']})
    for kind, bound in ((resource.RLIMIT_AS, contract['address_space_limit_bytes']),
                        (resource.RLIMIT_FSIZE, contract['file_size_limit_bytes'])):
        resource.setrlimit(kind, (bound, bound))
    helper = {'__name__': 'xsect_recovery', '__file__': str(ROOT / contract['recovery_ref']['path'])}
    exec(compile(checked(contract['recovery_ref']), helper['__file__'], 'exec'), helper)
    transport = transport_for(contract)
    began = time.monotonic()
    def deadline(signum, frame):
        raise TimeoutError('fixed recovery deadline')
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, contract['wall_seconds'])
    emit(HERE / 'INTENT01.json', {'identity': contract['identity'], 'pid': os.getpid(),
         'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'contract_sha256': hashlib.sha256(contract_body).hexdigest(),
         'headroom': initial, 'originals_preserved': True, 'automatic_retry': False})
    completed = []
    common = {'directories': directories, 'original_root': contract['original_root'],
              'max_files': contract['expected_files'],
              'max_total_bytes': contract['expected_raw_bytes'],
              'max_file_bytes': contract['max_file_bytes']}
    try:
        create_common = dict(common)
        create_common.pop('directories')
        root_pin = helper['create_new_tree'](target, rows, directories, **create_common)
        emit(HERE / 'ROOT_PIN01.json', {'root_pin': root_pin, 'target_root': str(target)})
        downloads = HERE / 'downloads'
        downloads.mkdir()
        remaining = contract['restore_allocation_bound_bytes']
        for batch, receipt, manifest in selection:
            # Reconstructed files consume free space already. Reserve only the
            # remaining fixed rounded-file allowance plus directory/slack bound.
            observed = eligibility(contract, remaining)
            work = downloads / f"batch-{batch['index']:04d}"
            work.mkdir()
            for name, size, wanted in (
                    ('manifest.json', contract['selection'][batch['index']]['manifest_ref']['bytes'],
                     receipt['manifest_sha256']),
                    ('bundle.tar', receipt['archive_bytes'], receipt['archive_sha256'])):
                remote = receipt['remote'] + '/' + name
                transport.sizes[remote] = size
                transport.get(remote, work / name)
                require(digest(work / name) == wanted, 'fresh external body differs')
            require(json.loads((work / 'manifest.json').read_bytes()) == manifest,
                    'fresh manifest differs')
            result = helper['recover_bundle'](work / 'bundle.tar', manifest, rows, target,
                root_pin=root_pin, batch=batch, max_archive_bytes=contract['max_archive_bytes'],
                **common)
            emit(work / 'RESTORED01.json', {'index': batch['index'], 'headroom': observed,
                 'result': result, 'fresh_remote_bytes_verified': True,
                 'originals_preserved': True})
            # Only this generated and verified archive is removed. Failed
            # downloads/extractions remain intact; no original file is removed.
            (work / 'bundle.tar').unlink()
            completed.append({'index': batch['index'], 'result': result})
            block = contract['allocation_block_bytes']
            remaining -= sum(((row['bytes'] + block - 1) // block) * block
                             for row in rows[batch['start']:batch['stop']])
            emit(HERE / f"PROGRESS_{batch['index']:04d}.json", {
                 'completed_batches': len(completed), 'elapsed_seconds': time.monotonic() - began})
        eligibility(contract, remaining)
        first = helper['verify_new_tree'](target, rows, root_pin=root_pin,
                    restore_directories=True, **common)
        final = helper['verify_new_tree'](target, rows, root_pin=root_pin, **common)
        emit(HERE / 'COMPLETE01.json', {'status': 'complete', 'identity': contract['identity'],
             'batches': completed, 'finalized': first, 'verified': final,
             'elapsed_seconds': time.monotonic() - began, 'originals_preserved': True,
             'deletion_authorized': False, 'writer_exclusion_proved': False})
    except BaseException as error:
        emit(HERE / 'FAILED01.json', {'status': 'failed', 'error_type': type(error).__name__,
             'reason': str(error), 'completed_batches': completed,
             'originals_preserved': True, 'automatic_retry': False})
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == '__main__':
    main()
