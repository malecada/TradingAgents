"""Use the accepted opaque binder once; never inspect authentication files."""
import copy
import hashlib
import json
from pathlib import Path
import types

ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
F = HERE.parent
PUBLIC = F / 'real-data-pilot-full24-input-binding01-2026-10-09'
BINDER = F / 'real-data-pilot-transport-binding-preparation01-2026-10-06/bind01.py'
EXPECTED = 'bcca66a6c7daba762a629dff84b9f16e48e7b9c2ffe51f77511942816ee444cb'
NAME = 'eth-paper-real-data-end-to-end-resource-20261009-24'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def ref(path):
    return {'path':str(path.relative_to(ROOT)), 'sha256':sha(path), 'bytes':path.stat().st_size}


assert sha(BINDER) == EXPECTED
assert not (ROOT / 'research_runs' / NAME).exists()
assert not (HERE / 'BOUND02.json').exists()
module = types.ModuleType('accepted_opaque_binder')
module.__file__ = str(BINDER)
exec(compile(BINDER.read_bytes(), str(BINDER), 'exec'), vars(module))


def save(path, value):
    with path.open('xb') as out:
        out.write(module.raw(value))


manifest = load(PUBLIC / 'PUBLIC_MANIFEST04.json')
docs = {}
for role, pin in manifest['public_inputs'].items():
    path = ROOT / pin['path']
    assert sha(path) == pin['sha256']
    docs[role] = load(path)
archive = docs.pop('archive_policy')
archive['transport_identity'] = None
archive_path = HERE / 'UNBOUND_ARCHIVE02.json'
save(archive_path, archive)
for item in (docs['execution_job']['payload']['representation_jobs']['original32'],
             docs['producer_plan']['producers']['original32']):
    item['descriptor']['compact_archive_execution']['policy_sha256'] = sha(archive_path)
# Canonical policy bytes must be joined before the unchanged binder publishes.
# This corrects only two descriptive digests; the policy bodies remain exact.
selected = docs['execution_job']['payload']['representation_jobs']['original32']
for field, key, expected_role in (
        ('compact_policy_input', 'compact_execution', 'compact_policy'),
        ('pair_checkpoint_input', 'pair_execution', 'pair_policy')):
    assert selected[field] == expected_role
    policy_digest = module.sha(module.raw(docs[expected_role]))
    for item in (selected, docs['producer_plan']['producers']['original32']):
        item['descriptor'][key]['policy_sha256'] = policy_digest
roles = {'job':'execution_job', 'producer_plan':'producer_plan', 'archive':'archive_policy'}
prepared = {'status':'DRAFT_NOT_REGISTERED_NOT_ADMITTED', 'independent_approval':False,
    'builder03_spec':{'template_roles':roles,'references':{'archive_policy':ref(archive_path)}},
    'builder03_result':{'status':'DRAFT_NOT_REGISTERED_NOT_ADMITTED','inputs':docs},
    'preparation_origin':{'public_manifest':ref(PUBLIC/'PUBLIC_MANIFEST04.json'),
        'source':ref(Path(__file__)),
        'qualification':'Concrete current public04 data transformed to the accepted binder interface; no old metadata-builder execution or invented authority. Archive connection identity is deliberately unset until actual binding.'}}
prepared_path = HERE / 'PREPARED02.json'
save(prepared_path, prepared)
# Only stat the opaque connection here. The accepted binder consumes configuration
# internally, never emits its body, and never opens private key/known-hosts files.
connection_path = ROOT / module.CONNECTION
parent = ROOT / 'research_artifacts/real_pilot_runtime/pilot-transport-20261009-24-02'
parent.mkdir(mode=0o700, exist_ok=False)
request = {'prepared':ref(prepared_path), 'archive_policy':ref(archive_path),
    'connection':{'path':module.CONNECTION,'sha256':module.CONNECTION_SHA,
                  'bytes':connection_path.stat().st_size},
    'private_parent':str(parent.relative_to(ROOT)), 'private_leaf':'archive_transport01.json'}
save(HERE / 'REQUEST02.json', request)
bound = module.bind(ROOT, request)
save(HERE / 'BOUND02.json', bound)
destination = HERE / 'inputs02'
destination.mkdir(exist_ok=False)
for role, value in bound['inputs'].items():
    save(destination / (role + '.json'), value)
refs = copy.deepcopy(load(PUBLIC/'PUBLIC_INPUT_REFS04.json'))
for role in bound['inputs']:
    pin = ref(destination/(role+'.json'))
    refs[role] = {'path':pin['path'],'sha256':pin['sha256'],'dataset':'eth'}
for role, pin in bound['private_input'].items():
    refs[role] = {'path':pin['path'],'sha256':pin['sha256'],'dataset':'eth'}
save(HERE / 'ALL_INPUT_REFS02.json', refs)
save(HERE / 'BINDING_CHECK02.json', {
    'status':bound['status'], 'experiment':NAME, 'actual_opaque_input':bound['private_input'],
    'actual_public_documents':len(bound['inputs']), 'all_input_roles':len(refs),
    'binder':ref(BINDER), 'prepared':ref(prepared_path), 'request':ref(HERE/'REQUEST02.json'),
    'bound':ref(HERE/'BOUND02.json'), 'claim':False, 'network':False, 'launch':False,
    'qualification':'Actual accepted offline binder/publication only. Authentication files were not inspected; connection contents were consumed solely inside the accepted binder and were not printed/committed. No network or empirical authority.'})
print(json.dumps({'status':bound['status'],'public_inputs':len(bound['inputs']),
                  'all_roles':len(refs),'claim':False,'network':False}))
