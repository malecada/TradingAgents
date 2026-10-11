"""Canonical identities and UTC clocks; no empirical I/O at import."""
from __future__ import annotations
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re


def canonical_bytes(value) -> bytes:
    return json.dumps(thaw(value), sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def current_canonical_bytes(value):
    """Fresh exact-JSON domain scan avoids thaw's copied container tree.

    No eligibility or validation result is retained. Frozen mappings, custom
    containers/keys and unsupported values use the original serializer intact.
    Exact dict/list/tuple/scalars have no user iteration hooks in this domain.
    """
    import json
    def plain(item):
        kind=type(item)
        if kind is str or kind is int or kind is float or kind is bool or kind is type(None):return True
        if kind is dict:
            for key,child in item.items():
                if type(key) is not str or not plain(child):return False
            return True
        if kind is list or kind is tuple:
            for child in item:
                if not plain(child):return False
            return True
        return False
    if not plain(value):return canonical_bytes(value)
    return json.dumps(value,sort_keys=True,separators=(',', ':'),ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def require_hash(value: str) -> None:
    if not isinstance(value, str) or re.fullmatch('[0-9a-f]{64}', value) is None:
        raise ValueError('invalid SHA256')


def utc(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError('UTC timestamp must be a string')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (TypeError, ValueError) as error:
        raise ValueError('invalid UTC timestamp') from error
    if result.tzinfo is None or result.utcoffset() != timedelta(0):
        raise ValueError('explicit UTC required')
    return result


def sync_directory(path: Path) -> None:
    import os
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def durable_mkdir(path: Path) -> None:
    """Make missing ancestors durable before reserving child identities."""
    path=Path(path)
    missing=[]
    cursor=path
    while not cursor.exists():
        missing.append(cursor);cursor=cursor.parent
    for directory in reversed(missing):
        directory.mkdir(exist_ok=True)
        sync_directory(directory.parent)


def thaw(value):
    from collections.abc import Mapping
    if isinstance(value,Mapping):return {key:thaw(item) for key,item in value.items()}
    if isinstance(value,(tuple,list)):return [thaw(item) for item in value]
    return value


def freeze(value):
    from collections.abc import Mapping
    from types import MappingProxyType
    if isinstance(value,Mapping):return MappingProxyType({key:freeze(item) for key,item in value.items()})
    if isinstance(value,(tuple,list)):return tuple(freeze(item) for item in value)
    return value
