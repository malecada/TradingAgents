"""Canonical identities and UTC clocks; no empirical I/O at import."""
from __future__ import annotations
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re


def canonical_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
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
