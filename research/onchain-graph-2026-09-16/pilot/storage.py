"""Immutable, bounded anonymous archive capture; no credential discovery or retries."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

import zstandard as zstd

MAX_RAW = 64 * 1024 * 1024
MAX_STORED = MAX_RAW + 1024 * 1024


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def _publish(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        os.link(temporary, path)  # Atomic, fails rather than replacing existing evidence.
        os.unlink(temporary)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_json(path, value):
    _publish(path, (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())


def write_blob(path, raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_RAW:
        raise ValueError('raw bytes exceed bounded storage contract')
    started = time.perf_counter()
    stored = zstd.ZstdCompressor(level=3, write_checksum=True, write_content_size=True).compress(raw)
    seconds = time.perf_counter() - started
    metadata = dict(path=Path(path).name, raw_bytes=len(raw), raw_sha256=sha(raw),
                    stored_bytes=len(stored), stored_sha256=sha(stored), codec='zstd', level=3,
                    compression_seconds=seconds, base64_theoretical_bytes=4 * ((len(raw) + 2) // 3))
    _publish(path, stored)
    if read_blob(path, metadata) != raw:
        raise ValueError('roundtrip mismatch')
    return metadata


def read_blob(path, metadata):
    n, stored_n = metadata['raw_bytes'], metadata['stored_bytes']
    if (type(n) is not int or not 0 <= n <= MAX_RAW or type(stored_n) is not int
            or not 0 <= stored_n <= MAX_STORED or metadata.get('codec') != 'zstd'
            or metadata.get('level') != 3):
        raise ValueError('invalid bounded blob metadata')
    with Path(path).open('rb') as source:
        stored = source.read(stored_n + 1)
    if len(stored) != stored_n or sha(stored) != metadata['stored_sha256']:
        raise ValueError('stored blob size/hash mismatch')
    if zstd.frame_content_size(stored) != n:
        raise ValueError('frame content size mismatch')
    raw = zstd.ZstdDecompressor().decompress(stored, max_output_size=max(1, n), allow_extra_data=False)
    if len(raw) != n or sha(raw) != metadata['raw_sha256']:
        raise ValueError('raw blob size/hash mismatch')
    return raw


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class BinaryCapture:
    def __init__(self, spec, directory):
        self.spec, self.directory = dict(spec), Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.count, self.total, self.denied, self.records = 0, 0, False, []
        for key, maximum in [('max_requests', 2100), ('max_response_bytes', 32 * 1024 * 1024),
                             ('max_total_bytes', 2 * 1024 ** 3), ('timeout_seconds', 30)]:
            value = self.spec.setdefault(key, maximum)
            if type(value) not in (int, float) or not 0 < value <= maximum:
                raise ValueError('invalid limit: ' + key)
            if key != 'timeout_seconds' and type(value) is not int:
                raise ValueError('byte/request limits must be integers')
        self._url(self.spec['base_url'])
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def _url(self, url):
        base, target = urllib.parse.urlsplit(self.spec['base_url']), urllib.parse.urlsplit(url)
        if (target.scheme != 'https' or target.username is not None or target.password is not None
                or target.fragment or target.hostname != base.hostname or target.port != base.port
                or not target.hostname
                or not (target.path == base.path or target.path.startswith(base.path.rstrip('/') + '/'))
                or any(part in ('.', '..') for part in urllib.parse.unquote(target.path).split('/'))
                or '\\' in urllib.parse.unquote(target.path)):
            raise ValueError('unregistered anonymous HTTPS host/path')
        if any(k.lower().startswith(('x-amz-', 'x-goog-')) or k.lower() in
               {'authorization', 'token', 'api_key', 'apikey', 'signature', 'awsaccesskeyid'}
               for k, _ in urllib.parse.parse_qsl(target.query)):
            raise ValueError('credential-bearing query prohibited')

    def get(self, url, headers=None):
        self._url(url)
        headers = dict(headers or {})
        if any(k.lower() not in {'range', 'if-match', 'if-none-match', 'accept', 'user-agent'}
               or '\r' in str(v) or '\n' in str(v) for k, v in headers.items()):
            raise ValueError('unapproved request header')
        # Calls after a stop still receive immutable local evidence, without consuming network budget.
        number = len(self.records) + 1
        stem = f'request-{number:04d}'
        record = dict(url=url, request_headers=headers, requested_at=now(), request_number=number,
                      status=None, response_headers={})
        atomic_json(self.directory / (stem + '-intent.json'), dict(record, method='GET', status='intent'))
        body, response = b'', None
        try:
            if self.denied:
                raise ValueError('source denied; acquisition stopped')
            if self.count >= self.spec['max_requests']:
                raise ValueError('request budget exhausted')
            # Reserve a sentinel byte while respecting the hard aggregate ceiling.
            cap = min(self.spec['max_response_bytes'], self.spec['max_total_bytes'] - self.total - 1)
            if cap <= 0:
                raise ValueError('total byte budget exhausted')
            self.count += 1
            request = urllib.request.Request(url, headers=headers)
            try:
                response = self.opener.open(request, timeout=self.spec['timeout_seconds'])
            except urllib.error.HTTPError as exc:
                response = exc
            record['status'] = response.status
            record['response_headers'] = {k.lower(): v for k, v in response.headers.items()
                if k.lower() in {'etag', 'content-length', 'content-range', 'last-modified', 'date', 'content-type'}}
            if response.status in {401, 403, 429}:
                self.denied = True
            chunks, length = [], 0
            try:
                while length <= cap:
                    amount = min(65536, cap + 1 - length)
                    try:
                        # read1 preserves received prefixes when a later socket read times out.
                        chunk = getattr(response, 'read1', response.read)(amount)
                    except http.client.IncompleteRead as exc:
                        chunks.append(exc.partial[:amount])
                        raise
                    if not chunk:
                        break
                    chunks.append(chunk)
                    length += len(chunk)
            finally:
                body = b''.join(chunks)
            if len(body) > cap:
                raise ValueError('response byte limit exceeded; retained prefix incomplete')
            expected = record['response_headers'].get('content-length')
            if expected is not None and len(body) != int(expected):
                raise ValueError('response body length mismatch')
            if response.status not in {200, 206}:
                raise ValueError(f'HTTP {response.status}')
        except Exception as exc:
            record['error'] = f'{type(exc).__name__}: {exc}'
        finally:
            if response is not None:
                try:
                    response.close()
                except Exception as exc:
                    record.setdefault('error', f'close {type(exc).__name__}: {exc}')
        self.total += len(body)
        blob = write_blob(self.directory / (stem + '.body.zst'), body)
        record.update(retrieved_at=now(), bytes=len(body), sha256=sha(body), blob=blob)
        atomic_json(self.directory / (stem + '.json'), record)
        self.records.append(record)
        return (None if 'error' in record else body), record
