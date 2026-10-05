"""One-use concrete metadata preparation; no registration adoption or execution."""
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAP = Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-native-20261005-01/source')
OLD = Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source')
ANCHOR = '55e7d50431654aba952b4541ca506524d9feece1'
IDENTITY = 'original-import-canonical-held-success-20261005-01'
ROLES = ('runtime', 'software_environment', 'native_environment', 'native_policy',
         'original_import_index', 'original_evidence', 'matching', 'target_catalog')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() + b'\n'

def save(path, raw):
    assert len(raw) <= 4 * 1024**2
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())

assert Path.cwd() == CAP and not (HERE / 'metadata-draft01').exists()
assert not any(name in sys.modules for name in ('numpy', 'torch'))
expected = json.loads((HERE.parent / 'held-consumer-canonical-root-recipe02-2026-10-04/SOURCE_EXPECTATIONS02.json').read_bytes())
implementation = expected['candidate']
package = {name: pin for name, pin in implementation.items() if name.startswith('tradingagents/')}
assert len(implementation) == 199 and len(package) == 148
assert package['tradingagents/research/onchain_replication/original_dictionary.py'] == 'e05aa225b6bcf8f4e14a644d0a03f2a9aff6cb36ae4a5b02a3dded72d94580b9'
helper = CAP / 'fixture_tools/capsule_builder01.py'
helper_raw = helper.read_bytes()
assert sha(helper_raw) == implementation['fixture_tools/capsule_builder01.py']
spec = importlib.util.spec_from_file_location('canonical_role_metadata_original_builder', helper)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
origins = {}
roles = {}
for role in ROLES:
    source = CAP / 'fixture_inputs/held/roles01' / (role + '.json')
    raw = source.read_bytes()
    assert raw == (OLD / source.relative_to(CAP)).read_bytes()
    document = json.loads(raw)
    if role in ('native_environment', 'native_policy'):
        raw = raw.replace(str(OLD).encode(), str(CAP).encode())
        document = json.loads(raw)
        assert raw.replace(str(CAP).encode(), str(OLD).encode()) == source.read_bytes()
    if role == 'runtime':
        observation = builder.held_runtime_metadata(CAP, document)
        save(HERE / 'RUNTIME_ROLE_READBACK01.json', encode(observation))
    save(HERE / 'metadata-draft01/roles' / (role + '.json'), raw)
    origins[role] = {'original_path': str(source), 'original_sha256': sha(source.read_bytes()),
                     'draft_sha256': sha(raw), 'bytes': len(raw),
                     'root_only_rebind': role in ('native_environment', 'native_policy')}
    roles[role] = document

drafts = json.loads((HERE / 'ROOT_REBOUND_CASE_DRAFTS01.json').read_bytes())
deviations = []
for case in ('success', 'second_target_publication_failure'):
    draft = drafts[case]
    path = draft['experiment']['inputs']['pair_policy']['path']
    original = (OLD / path).read_bytes()
    old_policy = json.loads(original)
    policy = json.loads(original)
    policy['numerical_source'] = {'commit': ANCHOR, 'files': package}
    restored = dict(policy)
    restored['numerical_source'] = old_policy['numerical_source']
    assert restored == old_policy
    assert len(old_policy['numerical_source']['files']) == 148
    assert [name for name in sorted(package) if package[name] != old_policy['numerical_source']['files'][name]] == ['tradingagents/research/onchain_replication/original_dictionary.py']
    raw = encode(policy)
    save(HERE / 'metadata-draft01/inputs' / path, raw)
    contract = draft['case_contract']
    # Only success has a newly allocated identity. The second case remains a
    # protocol template, with no identity or new allocation manufactured here.
    contract['experiment_id'] = IDENTITY if case == 'success' else None
    contract['additional_inputs']['pair_policy']['reference'] = {'path': path, 'sha256': sha(raw), 'bytes': len(raw)}
    save(HERE / 'metadata-draft01/contracts' / (case + '.json'), encode(contract))
    deviations.append({'case': case, 'input': 'pair_policy', 'path': path,
                       'historical_sha256': sha(original), 'draft_sha256': sha(raw),
                       'old_anchor': old_policy['numerical_source']['commit'], 'new_anchor': ANCHOR,
                       'package_count': 148, 'changed_package_bodies': 1,
                       'all_other_policy_fields_equal': True})

assert not any(name in sys.modules for name in ('numpy', 'torch'))
save(HERE / 'METADATA_BINDING01.json', encode({
    'schema_version': 1, 'status': 'DRAFT_NOT_RELEASED', 'capsule_root': str(CAP),
    'package_anchor': ANCHOR, 'roles': origins, 'input_deviations': deviations,
    'case_templates': 2, 'allocated_fresh_identities': [IDENTITY],
    'deviation': 'Accepted canonical dictionary requires a fresh complete148 numerical anchor and new pair-policy hashes in addition to the earlier four root-specific input changes. Backend, limits, matching and original C6 provenance remain unchanged. Old Owner/checkpoint/log contexts cannot transfer.',
    'helper_source_adoption_pending': True, 'gate_adopted': False,
    'owner_created': False, 'claim_created': False, 'numerical_imports': False,
    'live_input_mutations': 0, 'execution_admitted': False}))
print(json.dumps({'status': 'DRAFT_NOT_RELEASED', 'roles': 8, 'pair_policy_rebindings': 2,
                  'runtime_records_verified': 251, 'numerical_imports': False}, sort_keys=True))
