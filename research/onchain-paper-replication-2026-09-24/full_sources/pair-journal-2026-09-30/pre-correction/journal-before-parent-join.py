"""Isolated durable pair-reference journal, not empirical admission.

Caller must admit run/lease, exact workload purposes, numerical compatibility and
failed-owner death before construction. This layer records logical reservations;
it neither inspects numerical arrays nor proves physical allocation or guard bounds.
Unpublished reservations require separate reconciliation; no recovery is guessed.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import re

LIMIT = 65536


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def require(value, reason):
    if not value:
        raise ValueError(reason)


def hash_value(value):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'hash identity')


def sync(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write(path, value):
    data = encode(value)
    require(len(data) <= LIMIT, 'compact metadata limit')
    with path.open('xb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())
    sync(path.parent)
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest()}


def read(reference, root):
    require(isinstance(reference, dict) and set(reference) == {'path', 'sha256'}, 'reference schema')
    hash_value(reference['sha256'])
    p = Path(reference['path'])
    require(p.is_absolute() and p.resolve() == p and p.is_relative_to(root)
            and p.is_file() and p.stat().st_size <= LIMIT, 'reference containment/size')
    raw = p.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == reference['sha256'], 'reference hash differs')
    return p, json.loads(raw)


def policy(value):
    require(isinstance(value, dict) and set(value) == {'max_reserved_bytes', 'max_reservations', 'max_events'}, 'quota schema')
    require(all(type(v) is int and v > 0 for v in value.values()), 'positive quota required')
    return copy.deepcopy(value)


def empty():
    return {'reserved_bytes': 0, 'reservations': 0, 'events': 0, 'pairs': {}, 'pending': None}


def quota(state, limits):
    require(state['reserved_bytes'] <= limits['max_reserved_bytes']
            and state['reservations'] <= limits['max_reservations']
            and state['events'] + (1 if state['pending'] is not None else 0) <= limits['max_events'], 'cumulative journal quota exceeded')


def artifact(record, reference, root):
    require(reference['path'] == record['path'], 'publication differs from pending reservation')
    path, value = read(reference, root)
    require(path.stat().st_size <= record['artifact_bytes'], 'artifact allowance')
    require(value.get('owner') == record['artifact_owner']
            and digest(value.get('identity')) == record['identity_sha256'], 'artifact owner/identity differs')
    require(value.get('kind') in ('progress', 'complete'), 'artifact phase')
    return value['kind']


def target(state, directory, owner, workflow, purpose):
    artifact_owner = digest({'owner': owner, 'journal': directory.name,
                             'workflow': workflow, 'purpose': purpose})
    session = directory.parent/'pairs'/artifact_owner
    prior = state['pairs'].get(digest(purpose))
    index = 0
    if prior is not None:
        old = Path(prior['reference']['path'])
        if old.parent.parent == session:
            index = int(old.parent.name.removeprefix('artifact-'))+1
    return {'artifact_owner': artifact_owner,
            'path': str(session/f'artifact-{index:06d}'/'manifest.json')}


def apply(state, event, directory, owner, workflow, limits):
    result = copy.deepcopy(state)
    require(set(event) == {'kind', 'previous', 'payload'}, 'event schema')
    record = event['payload']
    if event['kind'] == 'reserve':
        require(result['pending'] is None, 'pending reservation requires reconciliation')
        require(set(record) == {'purpose', 'key', 'path', 'identity_sha256', 'artifact_owner', 'artifact_bytes', 'predecessor'}, 'reservation schema')
        require(isinstance(record['purpose'], dict) and bool(record['purpose']), 'explicit pair purpose required')
        require(record['key'] == digest(record['purpose']), 'purpose key differs')
        hash_value(record['identity_sha256'])
        prior = result['pairs'].get(record['key'])
        require(prior is None or prior['kind'] != 'complete', 'completed pair cannot repeat')
        require(record['predecessor'] == (None if prior is None else prior['reference']), 'stale predecessor')
        expected = target(result, directory, owner, workflow, record['purpose'])
        require(record['artifact_owner'] == expected['artifact_owner'], 'reservation owner differs')
        path = Path(record['path'])
        require(str(path) == expected['path'] and path.resolve() == path, 'reserved path containment/sequence')
        require(prior is None or record['identity_sha256'] == prior['identity_sha256'], 'pair numerical identity changed')
        require(type(record['artifact_bytes']) is int and record['artifact_bytes'] > 0, 'positive artifact reservation')
        result['reserved_bytes'] += record['artifact_bytes'] + 2*LIMIT
        if path.parent.name == 'artifact-000000':
            result['reserved_bytes'] += LIMIT  # one PairSession owner manifest
        result['reservations'] += 1
        result['pending'] = record
    elif event['kind'] == 'publish':
        require(result['pending'] is not None, 'no pending reservation')
        pending = result['pending']
        kind = artifact(pending, record, directory.parent/'pairs')
        result['pairs'][pending['key']] = {'kind': kind, 'reference': copy.deepcopy(record),
                                           'identity_sha256': pending['identity_sha256']}
        result['pending'] = None
    else:
        raise ValueError('unknown event')
    result['events'] += 1
    quota(result, limits)
    return result


def load(root, reference, workflow, limits, ancestors=()):
    path, terminal = read(reference, root)
    require(path.name == 'failed.json' and terminal.get('status') == 'failed', 'failed parent required')
    require(path.parent.parent == root and path not in ancestors and len(ancestors) < 8, 'parent containment/cycle/depth')
    require(set(terminal) == {'schema_version', 'status', 'start', 'events'}, 'terminal schema')
    require(type(terminal['schema_version']) is int and terminal['schema_version'] == 1, 'terminal version')
    start_path, start = read(terminal['start'], path.parent)
    require(start_path == path.parent/'start.json', 'start path differs')
    require(set(start) == {'schema_version', 'owner', 'workflow', 'policy', 'parent'}, 'start schema')
    require(type(start['schema_version']) is int and start['schema_version'] == 1
            and start['workflow'] == workflow and start['policy'] == limits, 'parent workflow/policy differs')
    hash_value(start['owner'])
    state = empty() if start['parent'] is None else load(root, start['parent'], workflow, limits, (*ancestors, path))
    require(state['pending'] is None, 'ancestor requires reconciliation')
    state['reserved_bytes'] += 2*LIMIT
    quota(state, limits)
    events = terminal['events']
    require(isinstance(events, list) and len(events) <= limits['max_events'], 'event denominator')
    actual = sorted(p.name for p in path.parent.glob('event-*.json'))
    require(actual == [f'event-{i:06d}.json' for i in range(len(events))], 'event inventory differs')
    previous = terminal['start']['sha256']
    for i, ref in enumerate(events):
        event_path, event = read(ref, path.parent)
        require(event_path == path.parent/f'event-{i:06d}.json' and event['previous'] == previous, 'event sequence/predecessor differs')
        state = apply(state, event, path.parent, start['owner'], workflow, limits)
        previous = ref['sha256']
    return state


class Journal:
    def __init__(self, root, name, owner, workflow, limits, *, parent=None):
        root = Path(root).absolute()
        require(root.is_dir() and root.resolve() == root, 'existing nonsymlink root required')
        require(isinstance(name, str) and re.fullmatch('[A-Za-z0-9_-]{1,100}', name), 'exclusive local journal name')
        hash_value(owner);hash_value(workflow)
        self.policy = policy(limits)
        state = empty() if parent is None else load(root, parent, workflow, self.policy)
        require(state['pending'] is None, 'parent reservation requires reconciliation')
        state['reserved_bytes'] += 2*LIMIT
        quota(state, self.policy)
        self.root, self.directory = root, root/name
        self.owner, self.workflow = owner, workflow
        self.records = [];self.safe = True;self.sealed = False
        self.state = state
        self.directory.mkdir(exist_ok=False);sync(root)
        self.start = write(self.directory/'start.json', {'schema_version': 1, 'owner': owner,
            'workflow': workflow, 'policy': self.policy, 'parent': copy.deepcopy(parent)})
        self.previous = self.start['sha256']

    @property
    def reservations(self):
        return self.state['reservations']

    @property
    def reserved_bytes(self):
        return self.state['reserved_bytes']

    def active(self):
        require(self.safe and not self.sealed, 'closed or poisoned journal')

    def latest(self, purpose):
        self.active()
        value = self.state['pairs'].get(digest(purpose))
        return None if value is None else copy.deepcopy(value['reference'])

    def append(self, kind, payload):
        self.active()
        event = {'kind': kind, 'previous': self.previous, 'payload': copy.deepcopy(payload)}
        state = apply(self.state, event, self.directory, self.owner, self.workflow, self.policy)
        try:
            ref = write(self.directory/f'event-{len(self.records):06d}.json', event)
        except BaseException:
            self.safe = False
            raise
        self.state = state;self.records.append(ref);self.previous = ref['sha256']

    def target(self, purpose):
        self.active()
        return target(self.state, self.directory, self.owner, self.workflow, purpose)

    def reserve(self, purpose, path, identity_sha256, artifact_bytes):
        self.active()
        path = Path(path)
        require(not path.exists() and not path.is_symlink(), 'existing artifact path cannot be reserved')
        key = digest(purpose)
        prior = self.state['pairs'].get(key)
        record = {'purpose': copy.deepcopy(purpose), 'key': key, 'path': str(path),
            'identity_sha256': identity_sha256, 'artifact_bytes': artifact_bytes,
            'artifact_owner': self.target(purpose)['artifact_owner'],
            'predecessor': None if prior is None else prior['reference']}
        self.append('reserve', record)
        return copy.deepcopy(record)

    def publish(self, reference):
        self.append('publish', reference)

    def seal(self, status):
        self.active()
        require(status in ('failed', 'complete'), 'terminal status')
        require(status != 'complete' or self.state['pending'] is None, 'pending reservation')
        try:
            ref = write(self.directory/(status+'.json'), {'schema_version': 1, 'status': status,
                        'start': self.start, 'events': self.records})
        except BaseException:
            self.safe = False
            raise
        self.sealed = True
        return ref
