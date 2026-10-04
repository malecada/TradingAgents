"""Seal a killed representation journal after verified owned-process death.

No computation, process action or continuation is performed. Only the durable
contiguous event prefix is eligible; incomplete component directories remain
untouched. A registered successor must separately admit the resulting closure.
"""
import json
from pathlib import Path

from ..lifecycle import _immutable, _lock, _encode
from .feature_journal import read_feature_journal
from .provenance import canonical_bytes, digest, file_hash


def _read(path, expected):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('symlink recovery evidence forbidden')
    raw = path.read_bytes()
    if digest(raw) != expected:
        raise ValueError('recovery evidence hash differs')
    return json.loads(raw)


def _publish_once(path, record):
    if path.exists():
        if path.is_symlink() or path.read_bytes() != _encode(record):
            raise ValueError('retained recovery publication differs; review required')
    else:
        _immutable(path, record)


def _death(root, owner, proof):
    experiment = owner['experiment']
    run = root/'research_runs'/experiment
    claim = _read(run/'claim.json', proof['claim_sha256'])
    failed = _read(run/'failed.json', proof['failed_sha256'])
    if failed.get('status') != 'failed' or failed.get('experiment_id') != experiment or failed.get('claim_sha256') != proof['claim_sha256']:
        raise ValueError('failed terminal does not bind the exact owner claim')
    if (run/'complete.json').exists() or claim['source'] != owner['source_commit'] or claim['experiment_id'] != experiment:
        raise ValueError('journal parent must be the terminal failed owner run')
    # This path is the new generic executor's ownership contract; unrelated
    # historical/pilot guard receipts cannot authorize reconciliation here.
    base = root/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/experiment
    launch_owner = _read(base/'owner.json', proof['owner_sha256'])
    guard_file = proof.get('guard_file', 'final.json')
    if guard_file not in ('final.json', 'observer-death.json'):
        raise ValueError('unexpected guard death proof')
    guard = _read(base/'guard'/guard_file, proof['guard_sha256'])
    if launch_owner.get('experiment') != experiment or launch_owner.get('source_commit') != owner['source_commit']:
        raise ValueError('guard belongs to a different experiment/source')
    if guard.get('owner_identity') != launch_owner or guard.get('monitor_pid') != launch_owner.get('monitor_pid'):
        raise ValueError('guard launch ownership differs')
    if guard.get('cleanup_verified') is not True or guard.get('phase') not in ('complete', 'failed'):
        raise ValueError('guard has no verified terminal cleanup')
    if guard.get('boot_id') != Path('/proc/sys/kernel/random/boot_id').read_text().strip():
        raise ValueError('guard boot differs; separate cross-boot review required')
    cgroup = Path(guard['cgroup'])
    if not cgroup.is_absolute() or not cgroup.is_relative_to('/sys/fs/cgroup') or cgroup.name != guard['unit'] or not cgroup.name.startswith('onchain-replication-'):
        raise ValueError('guard cgroup ownership path differs')
    if cgroup.exists():
        events = dict(line.split() for line in (cgroup/'cgroup.events').read_text().splitlines())
        if events.get('populated') != '0':
            raise ValueError('owned cgroup remains populated; no journal mutation')
    return guard


def reconcile_feature_journal(root, directory, expected_owner, proof, *, max_array_bytes):
    """Validate and append closure only, never overwrite or resume a journal."""
    root, directory = Path(root).resolve(), Path(directory).resolve()
    expected = root/'research_artifacts/onchain_representations'/expected_owner['workflow_identity']/expected_owner['experiment']
    if directory != expected:
        raise ValueError('journal path differs from exclusive owner')
    with _lock(root):
        _death(root, expected_owner, proof)
        if (directory/'complete.json').exists() or (directory/'failed.json').exists():
            raise FileExistsError('journal already terminal; do not reconcile twice')
        start_path = directory/'start.json'
        start = _read(start_path, proof['start_sha256'])
        owner = json.loads((directory/'owner.json').read_bytes())
        if start['schema_version'] != 1 or canonical_bytes(start['owner']) != canonical_bytes(expected_owner) or owner != expected_owner:
            raise ValueError('journal starting ownership differs')
        events = []
        for number, path in enumerate(sorted(directory.glob('event-*.json'))):
            if path.name != f'event-{number:06d}.json' or path.is_symlink():
                raise ValueError('journal durable event prefix has a gap')
            events.append(json.loads(path.read_bytes()))
        identity = events[-1]['context']['workflow_identity'] if events else start['workflow_identity']
        if identity is not None and identity != expected_owner['workflow_identity']:
            raise ValueError('journal workflow differs from exclusive owner')
        complete = bool(events) and events[-1]['stage'] == 'representation_complete'
        status = 'complete' if complete else 'failed'
        record = {'schema_version': 1, 'status': status,
                  'reason': 'owned worker terminated; retained durable event prefix reconciled without computation',
                  'owner': owner, 'workflow_identity': identity, 'events': events,
                  'parent': start['parent'], 'required_graphs': start['required_graphs']}
        # The candidate is itself retained even if validation rejects a corrupt
        # checkpoint; that rejection never creates a usable terminal journal.
        candidate = directory/'recovery-candidate.json'
        _publish_once(candidate, record)
        state, binding = read_feature_journal(candidate, file_hash(candidate), owner,
            required_graphs=start['required_graphs'], max_array_bytes=max_array_bytes)
        if complete and binding is None:
            raise ValueError('numerical completion lacks verified final binding')
        _publish_once(directory/'recovery-evidence.json', {'proof': proof, 'candidate_sha256': file_hash(candidate),
            'status': status, 'durable_events': len(events),
            'retained_unpublished_components': sorted(p.name for p in directory.glob('checkpoint-*')
                if p.is_dir() and p.name not in {Path(e['path']).parent.name for e in events}),
            'computation_repeated': False, 'continuation_admitted': False})
        terminal = directory/(status+'.json')
        _immutable(terminal, record)
        return terminal
