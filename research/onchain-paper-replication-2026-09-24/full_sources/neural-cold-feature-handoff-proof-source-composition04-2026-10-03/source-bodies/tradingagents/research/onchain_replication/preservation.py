"""Bounded byte-preserving bundles; no decoding, source mutation or network.

Manifests retain original locations and expected raw hashes. Archive member names
are generated numeric identifiers, never filesystem paths supplied by sources.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import stat
import tarfile


BLOCK = 1024 * 1024


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        while chunk := handle.read(BLOCK):
            digest.update(chunk)
    return digest.hexdigest()


def plan_batches(rows, *, max_raw_bytes, max_members):
    if max_raw_bytes <= 0 or max_members <= 0 or not rows:
        raise ValueError('positive limits and nonempty inventory required')
    seen = set()
    batches = []
    start = size = 0
    for index, row in enumerate(rows):
        path = row['resolved_path']
        if path in seen:
            raise ValueError('duplicate resolved source')
        seen.add(path)
        n = row['bytes']
        if not isinstance(n, int) or n < 0 or n > max_raw_bytes:
            raise ValueError('source exceeds bundle size limit')
        if not re.fullmatch('[0-9a-f]{64}', row['expected_sha256']):
            raise ValueError('invalid expected source hash')
        if index > start and (size + n > max_raw_bytes or index - start >= max_members):
            batches.append({'index': len(batches), 'start': start, 'stop': index, 'raw_bytes': size})
            start, size = index, 0
        size += n
    batches.append({'index': len(batches), 'start': start, 'stop': len(rows), 'raw_bytes': size})
    return batches


class _HashReader:
    def __init__(self, handle):
        self.handle = handle
        self.digest = hashlib.sha256()
        self.count = 0

    def read(self, size):
        data = self.handle.read(size)
        self.digest.update(data)
        self.count += len(data)
        return data


def build_bundle(rows, archive, *, allowed_roots, start_index=0):
    roots = [Path(p).resolve(strict=True) for p in allowed_roots]
    members = []
    # Exclusive output means neither a completed nor a failed attempt is overwritten.
    with Path(archive).open('xb') as output:
        with tarfile.open(fileobj=output, mode='w', format=tarfile.USTAR_FORMAT) as tar:
            for index, row in enumerate(rows, start_index):
                source = Path(row['source_path']).resolve(strict=True)
                if str(source) != row['resolved_path']:
                    raise ValueError('source resolved path changed')
                if not any(source.is_relative_to(root) for root in roots):
                    raise ValueError('source outside allowed root')
                # The recorded resolved target must remain a regular file.
                fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
                with os.fdopen(fd, 'rb') as handle:
                    before = os.fstat(handle.fileno())
                    if (not stat.S_ISREG(before.st_mode) or before.st_size != row['bytes']
                            or before.st_mtime_ns != row['mtime_ns']):
                        raise ValueError('source metadata changed')
                    name = f'files/{index:08d}'
                    info = tarfile.TarInfo(name)
                    info.size = before.st_size
                    info.mode = 0o600
                    reader = _HashReader(handle)
                    tar.addfile(info, reader)
                    after = os.fstat(handle.fileno())
                    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                        raise ValueError('source changed during read')
                    if reader.count != row['bytes'] or reader.digest.hexdigest() != row['expected_sha256']:
                        raise ValueError('source hash mismatch')
                members.append({**row, 'member': name})
        output.flush()
        os.fsync(output.fileno())
    return {'members': members, 'files': len(members), 'raw_bytes': sum(r['bytes'] for r in rows),
            'archive_bytes': Path(archive).stat().st_size, 'archive_sha256': sha256(archive)}


def verify_bundle(archive, manifest):
    if Path(archive).stat().st_size != manifest['archive_bytes'] or sha256(archive) != manifest['archive_sha256']:
        raise ValueError('archive identity mismatch')
    expected = manifest['members']
    count = raw_bytes = 0
    with tarfile.open(archive, 'r:') as tar:
        for member in tar:
            if count >= len(expected):
                raise ValueError('extra archive member')
            row = expected[count]
            if not member.isfile() or member.name != row['member'] or member.size != row['bytes']:
                raise ValueError('unexpected archive member')
            digest = hashlib.sha256()
            with tar.extractfile(member) as handle:
                while chunk := handle.read(BLOCK):
                    digest.update(chunk)
            if digest.hexdigest() != row['expected_sha256']:
                raise ValueError('recovered member hash mismatch')
            count += 1
            raw_bytes += member.size
    if count != len(expected) or count != manifest['files'] or raw_bytes != manifest['raw_bytes']:
        raise ValueError('archive member denominator differs')
    return {'files': count, 'raw_bytes': raw_bytes}


def transfer_bundle(rows, work, *, remote, transport, allowed_roots, start_index):
    """One exclusive batch. Only verified generated archive copies are removed."""
    from tradingagents.research.lifecycle import _immutable
    work = Path(work)
    work.mkdir(exist_ok=False)
    from .provenance import sync_directory
    sync_directory(work.parent)
    try:
        archive = work / 'bundle.tar'
        manifest = build_bundle(rows, archive, allowed_roots=allowed_roots, start_index=start_index)
        _immutable(work/'manifest.json', manifest)
        transport.mkdir(remote)
        for local_name, remote_name, recovered_name in [
                ('bundle.tar', 'bundle.tar', 'recovered.tar'),
                ('manifest.json', 'manifest.json', 'recovered-manifest.json')]:
            original, recovered = work/local_name, work/recovered_name
            before = sha256(original)
            transport.put(original, remote+'/'+remote_name)
            transport.get(remote+'/'+remote_name, recovered)
            if sha256(recovered) != before or sha256(original) != before:
                raise ValueError('round-trip hash mismatch')
        verified = verify_bundle(work/'recovered.tar', manifest)
        result = {'status': 'complete', **verified, 'remote': remote,
                  'archive_sha256': manifest['archive_sha256'],
                  'archive_bytes': manifest['archive_bytes'],
                  'manifest_sha256': sha256(work/'manifest.json'),
                  'source_hashes_verified': True, 'downloaded_members_verified': True,
                  'originals_preserved': True, 'start_index': start_index}
        _immutable(work/'completion-payload.json', result)
        transport.put(work/'completion-payload.json', remote+'/complete.json')
        transport.get(remote+'/complete.json', work/'recovered-complete.json')
        if sha256(work/'completion-payload.json') != sha256(work/'recovered-complete.json'):
            raise ValueError('completion marker round-trip mismatch')
        _immutable(work/'complete.json', result)
    except BaseException as error:
        _immutable(work/'failed.json', {'status': 'failed', 'error_type': type(error).__name__,
                                       'originals_preserved': True, 'retry': False})
        raise
    # Completion remains true even if temporary-copy cleanup cannot finish.
    cleanup = {}
    for name in ('bundle.tar', 'recovered.tar'):
        try:
            (work/name).unlink()
            cleanup[name] = 'removed verified temporary copy'
        except OSError as error:
            cleanup[name] = type(error).__name__
    sync_directory(work)
    _immutable(work/'cleanup.json', cleanup)
    return result


def receive_bounded(command, destination, *, expected_bytes, max_seconds, bytes_per_second):
    """Stream a finite child response, refusing extra bytes before writing them."""
    import select
    import subprocess
    import time
    if expected_bytes < 0 or max_seconds <= 0 or bytes_per_second <= 0:
        raise ValueError('invalid receive bounds')
    began = time.monotonic()
    received = 0
    with Path(destination).open('xb') as output:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            fd = proc.stdout.fileno()
            os.set_blocking(fd, False)
            while True:
                remaining = max_seconds-(time.monotonic()-began)
                if remaining <= 0:
                    raise TimeoutError('bounded download deadline')
                if not select.select([fd], [], [], min(1., remaining))[0]:
                    continue
                chunk = os.read(fd, min(BLOCK, expected_bytes-received+1))
                if not chunk:
                    break
                received += len(chunk)
                if received > expected_bytes:
                    raise ValueError('download size exceeds expected bytes')
                output.write(chunk)
                delay = received/bytes_per_second-(time.monotonic()-began)
                if delay > 0:
                    time.sleep(min(delay, remaining))
            remaining = max_seconds-(time.monotonic()-began)
            if remaining <= 0:
                raise TimeoutError('bounded download deadline')
            if proc.wait(timeout=remaining):
                raise RuntimeError('bounded download process failed')
            if received != expected_bytes:
                raise ValueError('download size shorter than expected bytes')
            output.flush()
            os.fsync(output.fileno())
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=10)
            proc.stdout.close()
