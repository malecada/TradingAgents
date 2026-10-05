"""Fixed reviewed prediction source adoption; unavailable proofs refuse before edits."""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path.cwd()
F = ROOT / 'research/onchain-paper-replication-2026-09-24/full_sources'
C = F / 'heartbeat-root-checkpoint10-2026-10-04'
PREP = F / 'financial-wrapper-serialized-prediction-preparation01-2026-10-05'
REVIEW = F / 'financial-wrapper-serialized-prediction-binding-review01-2026-10-05'
REMOTE = F / 'financial-wrapper-serialized-prediction-source-remote01-2026-10-05'
CALLER = F / 'financial-wrapper-serialized-prediction-parent-preparation01-2026-10-05'
CAP = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
OLD_PARENT = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-serialized-storage-root-launch-20261005-01')
PARENT = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-predict-serialized-storage-root-launch-20261005-01')
IDENTITY = 'financial-wrapper-classification-eager-predict-serialized-storage-successor-20261005-01'
SOURCE = '6b07c0f841e7d38102814aabb335751fd71fb7f7'
PREFIX = 'tradingagents/research/onchain_replication/'
INPUT_PREFIX = 'fixture_inputs/financial_wrapper_serialized_prediction01/'
REGISTRATION = 'fixture_inputs/financial_wrapper_serialized_storage01/gates.json'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def encode(v):
    return (json.dumps(v, sort_keys=True, indent=2) + '\n').encode()


def compact(v):
    return (json.dumps(v, sort_keys=True, separators=(',', ':')) + '\n').encode()


def put(p, b):
    assert not os.path.lexists(p) and len(b) <= 4 * 1024**2
    with p.open('xb') as w:
        w.write(b)
    assert p.read_bytes() == b


def git(args):
    return subprocess.run(['git', *args], cwd=CAP, check=True, capture_output=True).stdout


def insert_case(text, identity, case):
    decoder = json.JSONDecoder()
    start = text.index('{', text.index('"experiments"') + len('"experiments"'))
    old, end = decoder.raw_decode(text, start)
    assert old and identity not in old
    insertion = ',' + json.dumps(identity) + ':' + compact(case).decode().rstrip()
    new = text[:end - 1] + insertion + text[end - 1:]
    assert new[:end - 1] + new[end - 1 + len(insertion):] == text
    return new.encode()


def main():
    assert shutil.disk_usage(CAP).free >= 10 * 1024**3
    assert git(['rev-parse', 'HEAD']).decode().strip() == SOURCE
    assert git(['status', '--short', '--untracked-files=no']) == b''
    assert not os.path.lexists(PARENT) and not os.path.lexists(CAP / INPUT_PREFIX)
    assert not os.path.lexists(CAP / 'research_runs' / IDENTITY)
    assert not os.path.lexists(CAP / 'research_artifacts/financial_wrapper_engineering' / IDENTITY)
    assert not os.path.lexists(C / 'SERIALIZED_PREDICTION_ADOPTION_INTENT01.json')
    draft_raw = (C / 'SERIALIZED_PREDICTION_BOUND_PARENT_DRAFT01.json').read_bytes()
    assert sha(draft_raw) == '301d1b891e4f8807516a2cd6163cbbc6f4d51c61bf0121e54899715770447bf3'
    draft = json.loads(draft_raw)
    case = draft['gate_literal_insert'][IDENTITY]
    edge_raw = draft['new_input_bodies'][INPUT_PREFIX + 'prediction-edge.json'].encode()
    edge = json.loads(edge_raw)
    proof_raw = {}
    expected = {
        'schema_version': 1,
        'decision': 'accepted',
        'policy_sha256': sha(edge_raw),
        'continuation_policy_sha256': edge['continuation_policy_sha256'],
        'historical_map_sha256': sha(json.dumps(json.loads((CAP / case['inputs']['continuation_source_successor']['path']).read_bytes())['installed'], sort_keys=True, separators=(',', ':')).encode()),
        'target_map_sha256': sha(json.dumps(edge['installed'], sort_keys=True, separators=(',', ':')).encode()),
        'checker_sha256': edge['installed'][PREFIX + 'operational_source_compatibility.py'],
        'parent_recovery_sha256': case['inputs']['prediction_parent_recovery']['sha256'],
    }
    for suffix, name in [('review', 'SOURCE_REVIEW_PROOF01.json'), ('recovery', 'SOURCE_RECOVERY_PROOF01.json')]:
        role = 'prediction_source_successor_' + suffix
        raw = (REVIEW / name).read_bytes()
        assert json.loads(raw) == dict(expected, kind=role)
        proof_raw[role] = raw
    remote_raw = (REMOTE / 'REMOTE_RECOVERY01.json').read_bytes()
    remote = json.loads(remote_raw)
    accepted = json.loads((REVIEW / 'SOURCE_REMOTE_CHECK01.json').read_bytes())
    assert accepted['decision'] == 'accepted-actual-serialized-prediction-source-byte-recovery'
    assert accepted['receipt_sha256'] == sha(remote_raw)
    assert remote['selected_count'] == 11 and remote['selected_logical_bytes'] == 831068
    assert remote['remote_commit'] == '5642fcb3842cfb38bfa82927b5dd532d2340ecee'
    assert json.loads((REMOTE / 'ACTUAL_ROOT_EXIT01.json').read_bytes())['actual_exit'] == 0
    for row in remote['selected_blobs']:
        original = ROOT / row['path']
        recovered = REMOTE / 'selected' / row['path']
        assert sha(original.read_bytes()) == row['sha256'] and recovered.read_bytes() == original.read_bytes()
    assert (REMOTE / 'selected' / (C / 'SERIALIZED_PREDICTION_BOUND_PARENT_DRAFT01.json').relative_to(ROOT)).read_bytes() == draft_raw
    caller_raw = (CALLER / 'parent01.py').read_bytes()
    assert sha(caller_raw) == 'ca52dd65245754cf6ab84f9bea0e94dc7bf791de91124f0ef59d9dec971d512a'
    assert sha((PREP / 'preclaim01.py').read_bytes()) == '5f7ae415804cc482dbc5b3538160688d8f4e4fe494abb4696ca047da90a994c3'
    for row in edge['allowed_delta']:
        assert sha((CAP / row['path']).read_bytes()) == row['old_sha256']
        body = (PREP / Path(row['path']).name).read_bytes()
        assert sha(body) == row['new_sha256']
        ast.parse(body)
    assert len(edge['allowed_delta']) == 3 and len(edge['installed']) == 195
    original_gate = (CAP / REGISTRATION).read_bytes()
    assert sha(original_gate) == draft['gate_base']['sha256']
    historical = json.loads(original_gate)['experiments']
    assert len(historical) == 6 and IDENTITY not in historical
    assert case['parent'] == 'financial-wrapper-classification-eager-continue100-serialized-storage-successor-20261005-01'
    assert len(case['inputs']) == 29 and len(case['source_files']) == 381
    assert {x.name for x in (CAP / 'research_runs').iterdir()} == {
        '.lock',
        'financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01',
        'financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01',
        'financial-wrapper-classification-eager-complete100-20261003-01',
        'financial-wrapper-classification-eager-complete100-compatibility-20261004-01',
        'financial-wrapper-classification-eager-continue100-serialized-storage-successor-20261005-01',
    }
    bodies = dict(draft['new_input_bodies'])
    for role, raw in proof_raw.items():
        path = case['inputs'][role]['path']
        assert bodies[path] is None
        bodies[path] = raw.decode()
        case['inputs'][role]['sha256'] = case['source_files'][path] = sha(raw)
    assert len(bodies) == 7 and all(v is not None for v in bodies.values())
    for path, body in bodies.items():
        assert path.startswith(INPUT_PREFIX) and '/' not in path[len(INPUT_PREFIX):]
        assert case['source_files'][path] == sha(body.encode())
    for role, ref in case['inputs'].items():
        raw = bodies[ref['path']].encode() if ref['path'] in bodies else (CAP / ref['path']).read_bytes()
        assert sha(raw) == ref['sha256']
    new_gate = insert_case(original_gate.decode(), IDENTITY, case)
    parsed = json.loads(new_gate)
    assert {k: v for k, v in parsed['experiments'].items() if k != IDENTITY} == historical
    put(C / 'SERIALIZED_PREDICTION_ADOPTION_INTENT01.json', encode({'schema_version': 1, 'source_before': SOURCE, 'identity': IDENTITY, 'source_review_sha256': sha(proof_raw['prediction_source_successor_review']), 'source_recovery_sha256': sha(proof_raw['prediction_source_successor_recovery']), 'source_remote_receipt_sha256': sha(remote_raw), 'numerical_execution': False, 'launch_authority': False}))
    for row in edge['allowed_delta']:
        (CAP / row['path']).write_bytes((PREP / Path(row['path']).name).read_bytes())
    directory = CAP / INPUT_PREFIX
    directory.mkdir(mode=0o700)
    for path, body in bodies.items():
        put(CAP / path, body.encode())
    (CAP / REGISTRATION).write_bytes(new_gate)
    for path, pin in case['source_files'].items():
        assert sha((CAP / path).read_bytes()) == pin
    git(['add', '--', REGISTRATION, *[r['path'] for r in edge['allowed_delta']], *sorted(bodies)])
    git(['diff', '--cached', '--check'])
    git(['commit', '-q', '-m', 'engineering: register dependent serialized prediction'])
    source = git(['rev-parse', 'HEAD']).decode().strip()
    tracked = git(['ls-tree', '-r', '--name-only', 'HEAD']).decode().splitlines()
    assert len(tracked) == 382 and set(tracked) == set(case['source_files']) | {REGISTRATION}
    PARENT.mkdir(mode=0o700)
    for name in ('supervisor01.py', 'descendants01.py', 'recovery04.py', 'owned_io.py', 'bounded_git01.py', 'PROTOCOL_PINS01.json'):
        put(PARENT / name, (OLD_PARENT / name).read_bytes())
    put(PARENT / 'preclaim01.py', (PREP / 'preclaim01.py').read_bytes())
    reuse = json.loads((OLD_PARENT / 'proof_reuse_contract01.json').read_bytes())
    reuse['consumer'] = IDENTITY
    reuse['current_source'] = source
    put(PARENT / 'proof_reuse_contract01.json', compact(reuse))
    binding = {'source': source, 'registration_sha256': sha(new_gate), 'source_map_sha256': sha(encode(case['source_files'])), 'source_count': 381, 'tracked_count': 382}
    caller = caller_raw.decode()
    assert caller.count('SOURCE_BINDING=None') == 1
    caller = caller.replace('SOURCE_BINDING=None', 'SOURCE_BINDING=' + repr(binding))
    ast.parse(caller)
    put(PARENT / 'parent01.py', caller.encode())
    request = json.loads((OLD_PARENT / 'REQUEST_FINAL01.json').read_bytes())
    request.update(status='DRAFT_NOT_RELEASED', parent_root=str(PARENT), identity=IDENTITY, source=source, design_source=source, registration_sha256=binding['registration_sha256'], source_files=case['source_files'], input_hashes={k: v['sha256'] for k, v in case['inputs'].items()}, caller_sha256=sha(caller.encode()), helper_hashes={name: sha((PARENT / name).read_bytes()) for name in request['helper_hashes']}, proofs={role: None for role in request['proofs']}, final_review=None, expected_phase='predict')
    put(PARENT / 'REQUEST_SOURCE_BOUND_DRAFT01.json', compact(request))
    record = dict(binding, schema_version=1, status='SOURCE_GATE_ADOPTED_DRAFT_NOT_RELEASED', identity=IDENTITY, design_source=source, input_count=29, installed_count=195, changed_installed=3, historical_definitions_unchanged=6, registration=REGISTRATION, caller_sha256=sha(caller.encode()), current_proofs_available=False, genuine_admission=False, numerical_execution=False, launch_authority=False)
    put(C / 'SERIALIZED_PREDICTION_SOURCE_GATE_ADOPTION01.json', encode(record))
    print(json.dumps(record, sort_keys=True))


if __name__ == '__main__':
    main()
