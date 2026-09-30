"""Exact committed-source and compact-input checks for a single fresh verifier."""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import time

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RECEIPT = HERE/'verification01'
KIND = 'legacy-saved-array-verification01'
PREPARATION = HERE.parent/'legacy-graph-array-preparation-2026-09-30/inputs.json'
PREPARATION_SHA = 'a070b530842873b78fe144402405f613fe8a2e6625bf97600b5512b8dc0eb62e'


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def signature(path):
    path = Path(path)
    require(path.is_relative_to(ROOT), 'outside checkout')
    for parent in (path, *path.parents):
        require(not parent.is_symlink(), 'symlink input component')
        if parent == ROOT:
            break
    s = path.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, 'regular single-link input required')
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def compact(path, expected=None, maximum=65536):
    before = signature(path)
    require(before[2] <= maximum, 'compact input cap')
    raw = path.read_bytes()
    require(signature(path) == before, 'compact input changed')
    require(expected is None or sha(raw) == expected, 'compact hash mismatch')
    return raw, before


def committed(path, source):
    raw = path.read_bytes()
    require(subprocess.check_output(['git','show',source+':'+str(path.relative_to(ROOT))],cwd=ROOT) == raw,
            'committed bytes differ: ' + str(path))
    return raw


def source_check(source):
    require(re.fullmatch('[0-9a-f]{40}', source) is not None, 'full source commit required')
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == source, 'HEAD changed')
    raw = committed(HERE/'source-bindings.json', source)
    bindings = json.loads(raw)
    acceptance = json.loads(committed(HERE/'release-acceptance.json', source))
    require(acceptance['status'] == 'accepted' and acceptance['bindings_sha256'] == sha(raw), 'release acceptance binding')
    review = HERE/'RELEASE_REVIEW_V2.md'
    require(sha(committed(review, source)) == acceptance['review_sha256'], 'release review binding')
    for name, expected in bindings['files'].items():
        p = ROOT/name
        require(sha(committed(p, source)) == expected, 'source hash changed: ' + name)
    require(bindings['runtime'] == {'python':platform.python_version(), 'numpy':np.__version__}, 'runtime versions differ')
    return sha(raw)


def process_identity(pid):
    fields = Path('/proc',str(pid),'stat').read_text().rpartition(')')[2].split()
    require(fields[0] not in ('Z','X'), 'monitor is not live')
    return {'pid':pid,'start_ticks':fields[19],
            'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def live_guard(source, binding_hash):
    from tradingagents.research.onchain_replication.resources import assert_guarded_worker
    command = [str(ROOT/'.venv/bin/python'),'-B',str(HERE/'verify_saved.py'),'--source',source]
    live = assert_guarded_worker(RECEIPT/'guard',command,required_paths=[ROOT],
        wall_seconds=1800,memory_max_bytes=3*1024**3,memory_high_bytes=2*1024**3,
        disk_floor_bytes=10*1024**3)
    reservation = json.loads(compact(RECEIPT/'reservation.json')[0])
    observed = process_identity(live['monitor_pid'])
    require(all(reservation[k] == observed[k] for k in ('pid','start_ticks','boot_id'))
            and reservation['source_commit'] == source
            and reservation['bindings_sha256'] == binding_hash, 'launcher monitor reservation differs')
    require(live['owner_identity'] == {'kind':KIND,'source_commit':source,'bindings_sha256':binding_hash},
            'guard identity')
    require(live['boot_id'] == reservation['boot_id'] and live['lease_seconds'] <= 15,
            'guard boot/lease differs')
    require(live['memory_max_bytes'] == 3*1024**3 and live['memory_high_bytes'] == 2*1024**3
            and live['memory_swap_max_bytes'] == 0 and live['disk_floor_bytes'] == 10*1024**3
            and live['wall_seconds'] == 1800 and live['reserve_bytes'] == 3*1024**3
            and live['start_reserve_bytes'] == 6*1024**3 and live['disk_paths'] == [str(ROOT)],
            'guard limits differ')
    return live


def load_metadata():
    from metadata import validate, CONFIG
    raw, sig = compact(PREPARATION, PREPARATION_SHA)
    prep = json.loads(raw)
    require(len(prep['files']) == 31, 'compact inventory size')
    objects = {}; signatures = {PREPARATION:sig}
    for name, entry in prep['files'].items():
        relative = Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts and relative.suffix == '.json', 'compact path')
        p = ROOT/relative
        objects[name], signatures[p] = compact(p, entry['sha256'])
        require(len(objects[name]) == entry['bytes'], 'compact extent')
    config, signatures[ROOT/CONFIG] = compact(ROOT/CONFIG)
    return validate(prep, objects, config, str(ROOT)), signatures


def unchanged(signatures):
    require(all(signature(p) == s for p,s in signatures.items()), 'bound compact inputs changed')


def reserve_dir(path):
    path.mkdir()
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
