"""Offline fixed transport binding; no constructor, network, or admission."""
import argparse
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import stat

HERE = Path(__file__).resolve().parent
LIMIT = 4 * 1024**2
CONNECTION = 'research/onchain-paper-replication-2026-09-24/storage/storage-box-2026-09-24-01/connection.json'
CONNECTION_SHA = 'd79023381eb9f2788709a7a4c043046d8998c30bb4abab678cb41caaf4dc70ef'


def need(value, message):
    if not value:
        raise ValueError(message)


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def sha(body):
    return hashlib.sha256(body).hexdigest()


def signature(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns)


def read_ref(root, ref):
    need(type(ref) is dict and set(ref) == {'path', 'bytes', 'sha256'}, 'exact input reference required')
    name = Path(ref['path'])
    need(not name.is_absolute() and '..' not in name.parts, 'relative input required')
    need(name.suffix == '.json' and not any(x in {'keys', 'apis', '.env', 'hf_token.txt'}
         or x.startswith('.env.') or 'private_key' in x for x in name.parts), 'metadata-only input required')
    path = root / name
    need(path.resolve() == path, 'redirected input refused')
    need(type(ref['bytes']) is int and 0 < ref['bytes'] <= LIMIT, 'bounded input required')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'regular unique input required')
        body = bytearray()
        while len(body) <= LIMIT:
            part = os.read(fd, min(65536, LIMIT + 1 - len(body)))
            if not part:
                break
            body.extend(part)
        need(signature(before) == signature(os.fstat(fd)) == signature(path.lstat()), 'input changed')
        need(len(body) == ref['bytes'] and sha(body) == ref['sha256'], 'input bytes/hash differ')
        return bytes(body)
    finally:
        os.close(fd)


def identity_helper(root):
    pins = json.loads((HERE / 'DEPENDENCIES01.json').read_text())
    bodies = {}
    for name, pin in pins.items():
        p = root / pin['path']
        need(p.resolve() == p and p.stat().st_size <= LIMIT, 'source path/extent differs')
        body = p.read_bytes()
        need(sha(body) == pin['sha256'], 'source dependency differs')
        bodies[name] = body.decode()
    # Execute only the exact pinned pure functions; no package/backend imports.
    tree = ast.parse(bodies['dispatch'])
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {'require', '_connection'}]
    need(len(nodes) == 2, 'pure helper seam differs')
    scope = dict(hashlib=hashlib, json=json, re=re)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), pins['dispatch']['path'], 'exec'), scope)
    return scope['_connection']


def transform(prepared, archive, ordinary, connection_identity):
    """In-memory binding; callers must not print the returned private body."""
    need(prepared.get('status') == 'DRAFT_NOT_REGISTERED_NOT_ADMITTED' and prepared.get('independent_approval') is False,
         'completed unapproved preparation required')
    result = prepared['builder03_result']
    need(result.get('status') == 'DRAFT_NOT_REGISTERED_NOT_ADMITTED', 'builder result required')
    docs = copy.deepcopy(result['inputs'])
    roles = prepared['builder03_spec']['template_roles']
    job = docs[roles['job']]
    need(len(job['payload']['representation_jobs']) == 1, 'single representation required')
    selected = next(iter(job['payload']['representation_jobs'].values()))
    need(selected['plan_input'] == roles['producer_plan'] and selected['compact_archive_input'] == roles['archive'], 'selected roles differ')
    item = docs[selected['plan_input']]['producers'][selected['producer']]
    tr_role = selected['compact_archive_transport_input']
    need(item['compact_archive_transport_input'] == tr_role and item['compact_archive_input'] == roles['archive'], 'producer transport join differs')
    need(selected['descriptor'] == item['descriptor'], 'job/producer descriptor differs')
    old_extension = selected['descriptor']['compact_archive_execution']
    need(set(old_extension) == {'backend', 'policy_sha256'} and old_extension['backend'] == 'compact-archive-events-v1'
         and re.fullmatch('[0-9a-f]{64}', old_extension['policy_sha256']), 'original archive descriptor required')
    transport = docs.pop(tr_role)
    fields = {'schema_version', 'format', 'connection', 'rate_kbit', 'max_seconds', 'max_payload_bytes',
              'max_commands', 'max_diagnostic_bytes', 'max_control_bytes', 'namespace', 'receipt_output',
              'terminal_output', 'typed_payload_input', 'control_history'}
    need(set(transport) == fields and transport['schema_version'] == 2 and transport['format'] == 'archive-dispatch-v1'
         and transport['connection'] is None, 'selected unbound dispatch required')
    need(transport['typed_payload_input'] in docs and archive['transport_identity'] is None
         and archive['backend'] == 'compact-archive-events-v1', 'unbound archive/typed route required')
    # Literal accepted ordinary transfer.py expressions; filenames only.
    key = ordinary['public_key_path'].removesuffix('.pub')
    known = str(Path(key).parent / ('known_hosts_storagebox_' + ordinary['user']))
    connection = {k: ordinary[k] for k in ('host', 'user', 'port')}
    connection.update(identity_file=key, known_hosts_file=known)
    identity = connection_identity(connection)
    transport['connection'] = connection
    policy = copy.deepcopy(archive)
    policy['transport_identity'] = identity
    policy_sha = sha(raw(policy))
    for value in (selected, item):
        value['descriptor']['compact_archive_execution'] = {'backend': archive['backend'], 'policy_sha256': policy_sha}
    need(roles['archive'] not in docs, 'archive role collision')
    docs[roles['archive']] = policy
    return docs, transport, {'transport_identity': identity, 'transport_role': tr_role,
                            'archive_role': roles['archive'], 'archive_policy_sha256': policy_sha,
                            'prior_descriptor_policy_sha256': old_extension['policy_sha256']}


def publish_private(parent, leaf, body):
    """Atomic no-clobber visibility, 0600 body, retained scratch on uncertainty."""
    need(parent.resolve() == parent and parent.is_dir(), 'existing canonical private parent required')
    need(stat.S_IMODE(parent.stat().st_mode) == 0o700 and parent.stat().st_uid == os.getuid(), 'owned mode0700 parent required')
    need(type(leaf) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,79}', leaf), 'fixed leaf required')
    need(0 < len(body) <= LIMIT, 'private dispatch size bound')
    fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    tmp = leaf + '.pending'
    try:
        ino = os.fstat(fd)
        need(stat.S_IMODE(ino.st_mode) == 0o700 and ino.st_uid == os.getuid(), 'opened private parent differs')
        need(not os.path.lexists(parent / leaf), 'private target already exists')
        out = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=fd)
        try:
            view = memoryview(body)
            while view:
                n = os.write(out, view)
                need(n > 0, 'short private write')
                view = view[n:]
            os.fsync(out)
        finally:
            os.close(out)
        need(parent.resolve() == parent and (ino.st_dev, ino.st_ino) == (parent.lstat().st_dev, parent.lstat().st_ino), 'private parent changed')
        os.link(tmp, leaf, src_dir_fd=fd, dst_dir_fd=fd, follow_symlinks=False)
        os.fsync(fd)
        os.unlink(tmp, dir_fd=fd)
        os.fsync(fd)
        need(parent.resolve() == parent and (ino.st_dev, ino.st_ino) == (parent.lstat().st_dev, parent.lstat().st_ino), 'private parent changed')
    finally:
        os.close(fd)


def bind(root, request):
    root = Path(root).resolve()
    need(set(request) == {'prepared', 'archive_policy', 'connection', 'private_parent', 'private_leaf'}, 'exact Root bindings required')
    need(all(v is not None for v in request.values()), 'Root binding still missing')
    ref = request['connection']
    need(ref['path'] == CONNECTION and ref['sha256'] == CONNECTION_SHA, 'inherited opaque connection differs')
    helper = identity_helper(root)
    prepared = json.loads(read_ref(root, request['prepared']))
    archive = json.loads(read_ref(root, request['archive_policy']))
    expected = prepared['builder03_spec']['references'][prepared['builder03_spec']['template_roles']['archive']]
    need(request['archive_policy'] == expected, 'prepared archive reference differs')
    parent = root / request['private_parent']
    need(not Path(request['private_parent']).is_absolute() and '..' not in Path(request['private_parent']).parts
         and parent.is_relative_to(root / 'research_artifacts/real_pilot_runtime'), 'accounted private runtime parent required')
    ordinary = json.loads(read_ref(root, ref))
    docs, transport, bridge = transform(prepared, archive, ordinary, helper)
    body = raw(transport)
    publish_private(parent, request['private_leaf'], body)
    private_ref = {'path': str((parent / request['private_leaf']).relative_to(root)), 'bytes': len(body), 'sha256': sha(body)}
    return {'status': 'BOUND_DRAFT_NOT_REGISTERED_NOT_ADMITTED', 'inputs': docs,
            'private_input': {bridge['transport_role']: private_ref}, 'binding': bridge,
            'source_request': request, 'independent_approval': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    # Refuse existing output before the private publication; no implicit retry.
    need(not os.path.lexists(args.output), 'public output already exists')
    with args.request.open('rb') as stream:
        request_body = stream.read(LIMIT + 1)
    need(len(request_body) <= LIMIT, 'request too large')
    result = bind(args.root, json.loads(request_body))
    with args.output.open('xb') as stream:
        stream.write(raw(result)); stream.flush(); os.fsync(stream.fileno())
