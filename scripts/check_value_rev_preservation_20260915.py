"""Bounded first-vintage preservation proof; never parses raw source bodies."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time

SOURCE = Path('/home/malecada/master_thesis/TradingAgents')
MANIFEST = 'data/xsect/fees/2026-09-04/manifest.json'
RAW = 'data/xsect/fees_raw/2026-09-04'
ANCHOR = '89a9eb8ccbe073c1530047faa3bd64ca22085a79f933d782dcd2098a870d5151'
MAX_FILES, MAX_MEMBER, MAX_TOTAL = 4096, 64 * 1024**2, 2 * 1024**3


def directory(path):
    """Walk every component without following links, including ancestor paths."""
    p = Path(path)
    if not p.is_absolute() or '..' in p.parts:
        raise ValueError('absolute safe directory required')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in p.parts[1:]:
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = nxt
        return fd
    except BaseException:
        os.close(fd)
        raise


def metadata(dirfd, name):
    value = os.stat(name, dir_fd=dirfd, follow_symlinks=False)
    if not stat.S_ISREG(value.st_mode) or value.st_nlink != 1:
        raise ValueError('not an ordinary singly-linked regular file')
    if value.st_size > MAX_MEMBER:
        raise ValueError('member cap exceeded')
    return value


def identity(value):
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def stream(dirfd, name, expected_stat, collect=False):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=dirfd)
    try:
        if identity(os.fstat(fd)) != identity(expected_stat):
            raise ValueError('member changed before open')
        digest, total, chunks = hashlib.sha256(), 0, []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > expected_stat.st_size or total > MAX_MEMBER:
                raise ValueError('member grew beyond preflight bound')
            digest.update(chunk)
            if collect:
                chunks.append(chunk)
        if total != expected_stat.st_size or identity(os.fstat(fd)) != identity(expected_stat):
            raise ValueError('member changed during read')
        return digest.hexdigest(), b''.join(chunks) if collect else total
    finally:
        os.close(fd)


def verify():
    started = time.monotonic()
    report = {'kind': 'first-vintage-preservation-only', 'source_root': str(SOURCE),
              'manifest': MANIFEST, 'expected_manifest_sha256': ANCHOR,
              'caps': {'files': MAX_FILES, 'member_bytes': MAX_MEMBER, 'total_bytes': MAX_TOTAL},
              'raw_bodies_parsed': False, 'panels_read': False, 'empirical_claim': False,
              'source_mutations': False, 'members': [], 'pass': False,
              'completion_bound': None,
              'limitations': ['The manifest fetched_utc is capture start, not completion.',
                             'Filesystem timestamps are used only for concurrent-change detection, never to infer capture completion.',
                             'Preservation does not establish point-in-time availability, financial validity, panel reproduction or external backup.']}
    manifest_fd = raw_fd = None
    try:
        manifest_fd = directory(SOURCE / Path(MANIFEST).parent)
        ms = metadata(manifest_fd, 'manifest.json')
        if ms.st_size > 1024**2:
            raise ValueError('manifest exceeds 1MiB')
        sha, body = stream(manifest_fd, 'manifest.json', ms, True)
        if sha != ANCHOR:
            raise ValueError('manifest anchor mismatch')
        # Only bookkeeping metadata is parsed. Market response bodies remain opaque.
        manifest = json.loads(body)
        files = manifest['files']
        if type(files) is not dict or not 0 < len(files) <= MAX_FILES:
            raise ValueError('invalid manifest member count')
        expected_total = 0
        for name, item in files.items():
            if not re.fullmatch(r'[A-Za-z0-9_.+-]+\.json', name) or name.startswith('.'):
                raise ValueError('unsafe manifest member name')
            if type(item) is not dict or set(item) != {'bytes', 'sha256'}:
                raise ValueError('unexpected member metadata')
            if type(item['bytes']) is not int or not 0 <= item['bytes'] <= MAX_MEMBER:
                raise ValueError('invalid member bound')
            if not re.fullmatch('[0-9a-f]{64}', item['sha256']):
                raise ValueError('invalid digest')
            expected_total += item['bytes']
        if expected_total > MAX_TOTAL:
            raise ValueError('manifest total exceeds cap')
        report.update(manifest_sha256=sha, manifest_bytes=ms.st_size,
                      snapshot=manifest.get('snapshot'), capture_start=manifest.get('fetched_utc'),
                      declared_members=len(files), declared_bytes=expected_total)
        raw_fd = directory(SOURCE / RAW)
        # All member sizes/types are admitted before reading any raw response bytes.
        admitted = []
        actual_total = 0
        for name, item in sorted(files.items()):
            result = {'name': name, 'expected_bytes': item['bytes'], 'expected_sha256': item['sha256']}
            report['members'].append(result)
            try:
                st = metadata(raw_fd, name)
                actual_total += st.st_size
                result['observed_bytes'] = st.st_size
                if st.st_size != item['bytes']:
                    raise ValueError('size mismatch; body not read')
                admitted.append((name, item, st, result))
            except (OSError, ValueError) as exc:
                result['error'] = type(exc).__name__ + ': ' + str(exc)
                result['pass'] = False
        if actual_total > MAX_TOTAL:
            raise ValueError('actual total exceeds cap; raw bodies not read')
        for name, item, st, result in admitted:
            try:
                first, count = stream(raw_fd, name, st)
                second, _ = stream(raw_fd, name, st)
                result.update(observed_sha256=first, after_sha256=second,
                              bytes_hashed_per_pass=count,
                              unchanged=first == second, **{'pass': first == second == item['sha256']})
                if not result['pass']:
                    result['error'] = 'manifest digest mismatch or concurrent content change'
            except (OSError, ValueError) as exc:
                result.update(error=type(exc).__name__ + ': ' + str(exc), **{'pass': False})
        after, _ = stream(manifest_fd, 'manifest.json', ms)
        report['manifest_after_sha256'] = after
        report['verified_members'] = sum(v.get('pass', False) for v in report['members'])
        report['unavailable_or_mismatched_members'] = len(files) - report['verified_members']
        report['pass'] = after == ANCHOR and all(v.get('pass', False) for v in report['members'])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report['error'] = type(exc).__name__ + ': ' + str(exc)
    finally:
        for fd in (manifest_fd, raw_fd):
            if fd is not None:
                os.close(fd)
    report['elapsed_seconds'] = time.monotonic() - started
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise SystemExit('report already exists; refuse repeat')
    result = verify()
    with args.report.open('x') as output:
        json.dump(result, output, indent=2, sort_keys=True)
        output.write('\n')
    print(json.dumps({k: result.get(k) for k in ('pass', 'verified_members', 'declared_bytes', 'elapsed_seconds', 'error')}))
    raise SystemExit(0 if result['pass'] else 1)


if __name__ == '__main__':
    main()
