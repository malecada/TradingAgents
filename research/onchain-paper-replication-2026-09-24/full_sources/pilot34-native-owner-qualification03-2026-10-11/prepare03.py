"""Freeze exact third engineering command; never execute a numerical child."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
F = HERE.parent
ROOT = HERE.parents[3]
PREVIOUS = F / 'pilot34-native-owner-qualification02-2026-10-11'
CANDIDATE = F / 'matching-compiled-two-attribute-caller-candidate03-2026-10-11'


def pin(path):
    body = path.read_bytes()
    return dict(path=str(path), bytes=len(body), sha256=hashlib.sha256(body).hexdigest())


def write(name, value):
    with (HERE / name).open('x') as out:
        out.write(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    assert not (HERE / 'attempt01').exists()
    assert not (HERE / 'ROOT_LAUNCH03.json').exists()
    manifest_path = CANDIDATE / 'MANIFEST03.json'
    manifest = json.loads(manifest_path.read_bytes())
    for name, expected in manifest['files'].items():
        actual = pin(CANDIDATE / name)
        assert (actual['bytes'], actual['sha256']) == (expected['bytes'], expected['sha256']), name
    old_script = (PREVIOUS / 'qualify02.py').read_bytes()
    new_script = (HERE / 'qualify03.py').read_bytes()
    old_identity = b'edge-owner-and-kernel-qualification-20261011-02'
    new_identity = b'edge-owner-and-kernel-qualification-20261011-03'
    assert old_script.count(old_identity) == 1
    assert new_script == old_script.replace(old_identity, new_identity)
    ast.parse(new_script)
    policy = json.loads((CANDIDATE / 'POLICY_TEMPLATE01.json').read_bytes())
    policy['adapter_path'] = str(CANDIDATE / 'edge_chunk_adapter.py')
    roles = {}
    for role in ('source', 'adapter', 'library', 'runtime', 'abi'):
        actual = pin(Path(policy[role + '_path']))
        assert actual['sha256'] == policy[role + '_sha256'], role
        if role + '_bytes' in policy:
            assert actual['bytes'] == policy[role + '_bytes'], role
        roles[role] = actual
    assert roles['library']['bytes'] == 21920
    write('POLICY_ROLE03.json', policy)
    command = json.loads((PREVIOUS / 'COMMAND02.json').read_bytes())
    script = pin(HERE / 'qualify03.py')
    owner = pin(CANDIDATE / 'compiled_edge_owner.py')
    kernel = pin(CANDIDATE / 'matching_annealing.py')
    policy_pin = pin(HERE / 'POLICY_ROLE03.json')
    arguments = command['argv']
    arguments[2] = script['path']
    for key, value in (('--owner', owner['path']), ('--owner-sha256', owner['sha256']),
                       ('--kernel', kernel['path']), ('--kernel-sha256', kernel['sha256']),
                       ('--policy', policy_pin['path']), ('--policy-sha256', policy_pin['sha256'])):
        arguments[arguments.index(key) + 1] = value
    baseline = pin(ROOT / 'tradingagents/research/onchain_replication/matching_annealing.py')
    assert arguments[arguments.index('--baseline-sha256') + 1] == baseline['sha256']
    command.update(script=script, candidate_manifest=pin(manifest_path),
                   role_references=roles, predecessor_command=pin(PREVIOUS / 'COMMAND02.json'))
    command['required_before_launch'] = [
        'accepted actual failed34 outcome27 recovery and preserved failed native02 disposition',
        'independent exact caller03 and command03 source and entry acceptance',
        'actual committed current increment28 external recovery and independent acceptance',
        'fresh source/runtime/process/namespace/storage checks and one Root launcher',
    ]
    write('COMMAND03.json', command)
    write('SOURCE_CHECK03.json', dict(
        status='PASS_SOURCE_ONLY', numerical_execution=False,
        checks=['all candidate manifest bodies joined', 'identity-only full script inverse',
                'five actual public roles joined', 'actual library extent21920',
                'unchanged baseline numerical source', 'one-use namespace absent'],
        predecessor_script=pin(PREVIOUS / 'qualify02.py'), script=script,
        owner=owner, kernel=kernel, baseline=baseline,
    ))
    body_names = ['prepare03.py', 'qualify03.py', 'POLICY_ROLE03.json', 'COMMAND03.json',
                  'SOURCE_CHECK03.json', 'LITERAL_PATCH01.diff', 'LITERAL_INVERSE01.diff',
                  'DRAFT_NOT_RELEASED01.txt']
    write('MANIFEST03.json', dict(
        status='FROZEN_SOURCE_NOT_EXECUTION_RELEASED',
        format='finite-engineering-harness-source-successor-v1',
        predecessor_script=pin(PREVIOUS / 'qualify02.py'),
        predecessor_command=pin(PREVIOUS / 'COMMAND02.json'),
        bodies={name: pin(HERE / name) for name in body_names},
        qualification='Identity-only harness change; exact new backend roles and Linux compatible caller. No numerical execution.',
    ))
    print(json.dumps(dict(command=pin(HERE / 'COMMAND03.json'), manifest=pin(HERE / 'MANIFEST03.json'))))


if __name__ == '__main__':
    main()
