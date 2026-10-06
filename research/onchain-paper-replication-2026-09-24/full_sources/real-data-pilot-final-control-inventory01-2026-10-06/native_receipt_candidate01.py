"""Uninstalled narrow resources._native_write candidate. Caller must bind limit.

Exact encoding parity; oversize raises before birth, never truncates/coerces state.
This covers receipt bytes only. It does not bound journald/outer logs or caches.
"""
import json
import os

def _native_write(path, state, io, *, max_bytes):
    if type(max_bytes) is not int or not 0 < max_bytes < 2**63:
        raise ValueError('explicit admitted native receipt byte limit required')
    raw=bytearray()
    for part in json.JSONEncoder(indent=2,sort_keys=True).iterencode(state):
        encoded=part.encode()
        if len(encoded)>max_bytes-len(raw)-1:
            raise ValueError('native receipt encoded byte limit exceeded; state not published')
        raw.extend(encoded)
    raw.extend(b'\n')
    with io._opened(path,'xb') as stream:
        count=stream.write(raw)
        if count!=len(raw):
            raise OSError('native receipt short write; partial retained')
        stream.flush();os.fsync(stream.fileno())
