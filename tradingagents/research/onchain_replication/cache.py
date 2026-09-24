"""Content-addressed immutable publication, with explicit provenance checks."""
from __future__ import annotations
from pathlib import Path
import json
import os
import shutil
import tempfile
from .provenance import canonical_bytes, digest, file_hash, require_hash


def cache_key(fields) -> str:
    return digest(canonical_bytes(fields))


def _member(name):
    if not isinstance(name, str) or Path(name).name != name or name in {'', '.', '..', 'manifest.json'}:
        raise ValueError('invalid artifact member name')


def publish(root: Path, key: str, members: dict[str, bytes], provenance: dict) -> Path:
    require_hash(key)
    if not members:
        raise ValueError('empty artifact')
    for name, value in members.items():
        _member(name)
        if not isinstance(value, bytes):
            raise ValueError('artifact members must be bytes')
    canonical_bytes(provenance)
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    destination = root / key
    # Reserve identity atomically. Failed publications retain a visible claim;
    # never recycle an artifact ID after a crash.
    destination.mkdir()
    temp = Path(tempfile.mkdtemp(prefix='.publish-', dir=root))
    try:
        manifest = {'schema_version': 1, 'key': key, 'provenance': provenance,
                    'members': {name: {'sha256': digest(value), 'size': len(value)}
                                for name, value in sorted(members.items())}}
        for name, value in members.items():
            path = temp / name
            with path.open('xb') as stream:
                stream.write(value)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(path, destination / name)
        encoded = canonical_bytes(manifest)
        with (temp / 'manifest.json').open('xb') as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temp / 'manifest.json', destination / 'manifest.json')
        fd = os.open(destination, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        return destination / 'manifest.json'
    finally:
        shutil.rmtree(temp)


def read_artifact(manifest_path: Path, expected_provenance: dict) -> dict[str, bytes]:
    manifest_path = Path(manifest_path)
    try:
        manifest = json.loads(manifest_path.read_bytes())
    except (FileNotFoundError, json.JSONDecodeError) as error:
        raise ValueError('missing or corrupt artifact manifest') from error
    if set(manifest) != {'schema_version', 'key', 'provenance', 'members'} or manifest['schema_version'] != 1:
        raise ValueError('invalid manifest schema')
    if manifest['key'] != manifest_path.parent.name:
        raise ValueError('artifact identity mismatch')
    require_hash(manifest['key'])
    if canonical_bytes(manifest['provenance']) != canonical_bytes(expected_provenance):
        raise ValueError('artifact provenance mismatch')
    if not isinstance(manifest['members'], dict) or not manifest['members']:
        raise ValueError('missing members')
    out = {}
    for name, metadata in manifest['members'].items():
        _member(name)
        path = manifest_path.parent / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('missing or symlink artifact member')
        require_hash(metadata['sha256'])
        data = path.read_bytes()
        if len(data) != metadata['size'] or digest(data) != metadata['sha256']:
            raise ValueError('artifact hash mismatch')
        out[name] = data
    return out


def artifact_key(key) -> str:
    """Hash the mandatory scientific dependency set, including explicit weights.

    Non-applicable components use the hash of a declared no-component manifest,
    never an omitted field or an empty string.
    """
    from dataclasses import asdict
    from .contracts import ArtifactKey
    import re
    if not isinstance(key, ArtifactKey):
        raise ValueError('typed ArtifactKey required')
    if not key.source_hashes or key.schema_version != 1 or not key.fold_id:
        raise ValueError('missing artifact dependency')
    for value in (*key.source_hashes, key.config_hash, key.train_member_hash,
                  key.dictionary_hash, key.weight_hash):
        require_hash(value)
    if re.fullmatch('[0-9a-f]{40}', key.transform_commit) is None:
        raise ValueError('full source commit required')
    if type(key.seed) is not int or key.seed < 0:
        raise ValueError('invalid seed')
    return cache_key(asdict(key))
