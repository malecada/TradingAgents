"""Bounded public digest and exact final delta review; never runs pilot code."""
from pathlib import Path
import copy
import hashlib
import json
import os
import stat

ROOT = Path.cwd()
F = Path('research/onchain-paper-replication-2026-09-24/full_sources')
D = F/'real-data-pilot-final01-2026-10-06'
OLD = F/'real-data-pilot-final-binding-review01-2026-10-06'
HERE = F/'real-data-pilot-final-release-completion01-2026-10-06'
NAME = 'eth-paper-real-data-end-to-end-resource-20261005-01'
LIMIT = 4*1024**2


def raw(path):
    p = ROOT/path
    before = p.lstat()
    assert p.resolve(strict=True) == p and stat.S_ISREG(before.st_mode)
    assert before.st_nlink == 1 and before.st_size <= LIMIT
    body = p.read_bytes()
    after = p.lstat()
    signature = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_nlink,
                           s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    assert signature(before) == signature(after) and len(body) == before.st_size
    return body


def digest(path):
    return hashlib.sha256(raw(path)).hexdigest()


def read(path):
    # Scientific payloads and private connection bodies must never be decoded.
    assert str(path).startswith('research/')
    return json.loads(raw(path))


def write(name, value):
    p = HERE/name
    with p.open('x') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2)+'\n')
    return p


gate_hash = '629db998922868d386b4bdaabf118c9c7070519f3f921ca3aa3febab5ff2af07'
binding_hash = '8fd67338cd13b888c10146df4226def150d443dbaf821cda1f7e90893c4f32cf'
review_hash = 'd838a5f877e1c7ba418a0467d7d9e36a41099f1973f7f251f3c31ef587bb5eac'
assert digest(D/'gate01.json') == gate_hash
assert digest(D/'BINDING01.json') == binding_hash
assert digest(OLD/'BINDING_REVIEW02.json') == review_hash
assert digest(OLD/'RELEASE_REVIEW01.json') == '491d85a11ebab01b0bb1d509c9d0a817e121d5837b8a32ad933272a11c22dbd7'
old_release = read(OLD/'RELEASE_REVIEW01.json')
old_gate = read(D/'gate_PREDECESSOR03.json')
gate = read(D/'gate01.json')
experiment = gate['experiments'][NAME]
binding = read(D/'BINDING01.json')
review = read(OLD/'BINDING_REVIEW02.json')
addendum = read(D/'GATE_SOURCE_PIN_ADDENDUM04.json')
added = {ref['path']: ref['sha256'] for ref in addendum['exact_added_source_pins']}
assert len(added) == 4
inverse = copy.deepcopy(gate)
for path, pin in added.items():
    assert path not in old_gate['experiments'][NAME]['source_files']
    assert inverse['experiments'][NAME]['source_files'].pop(path) == pin
assert inverse == old_gate
assert digest(D/'gate_PREDECESSOR03.json') == addendum['prior_gate_sha256']
assert addendum['new_gate']['sha256'] == gate_hash
assert len(experiment['source_files']) == 198 and len(experiment['inputs']) == 59
assert experiment['cells'] == ['real-eth-one-update'] and len(experiment['outputs']) == 8
old_binding = read(D/'BINDING_DRAFT03.json')
expected_binding = copy.deepcopy(old_binding)
expected_binding['gate'] = addendum['new_gate']
expected_binding['binding_review'] = {'path':str(OLD/'BINDING_REVIEW02.json'),
                                    'sha256':review_hash,
                                    'bytes':(OLD/'BINDING_REVIEW02.json').stat().st_size}
assert binding == expected_binding
assert review['decision'] == 'accepted' and review['identity'] == NAME
assert review['source_pins'] == 198 and review['inputs'] == 59 and review['outputs'] == 8
for role in ('gate','draft','preparation','baseline','transport','transport_binding'):
    assert review['evidence'][binding[role]['path']] == binding[role]['sha256']
admission_path = D/'ACTUAL_READONLY_ADMISSION02.json'
assert digest(admission_path) == review['actual_readonly_admission']['sha256']
assert read(admission_path) == {'Owner_or_Binding_born':False, 'ResearchRun_start':False,
    'decision':'passed','effective_attempt_budget':72,'input_roles':59,
    'kind':'compact_resource','ready':True,
    'source':'04d6e5b588f1d3202d68b7f4d472cb87c9b53a91','source_pins':198}
assert read(OLD/'SUPERSESSION02.json')['current_binding_review_sha256'] == review_hash

# Preserve every inherited pin except the two declared replaced live bodies.
evidence = dict(old_release['evidence'])
for path, pin in ((str(D/'gate01.json'),gate_hash),(str(D/'BINDING01.json'),binding_hash)):
    evidence[path] = pin


def add(ref):
    path, pin = ref['path'], ref['sha256']
    p = Path(path)
    assert not p.is_absolute() and '..' not in p.parts and str(p) == path
    assert path not in evidence or evidence[path] == pin
    evidence[path] = pin


def local(path):
    add({'path':str(path),'sha256':digest(path)})


for path, pin in experiment['source_files'].items():
    add({'path':path,'sha256':pin})
for ref in experiment['inputs'].values():
    add(ref)
for ref in binding.values():
    if isinstance(ref,dict) and 'path' in ref:
        add(ref)
for ref in experiment['cumulative_budget_extension'].values():
    add(ref)
add(experiment['charter'])
for path, pin in review['review_evidence'].items():
    add({'path':path,'sha256':pin})
for path in (admission_path,D/'ACTUAL_READONLY_ADMISSION01.json',
             D/'GATE_SOURCE_PIN_ADDENDUM04.json',D/'gate_PREDECESSOR03.json',
             OLD/'RELEASE_REVIEW01.json',OLD/'SUPERSESSION02.json',HERE/'complete01.py'):
    local(path)

# Check the exact transitive public entry helper closures without importing them.
for directory, name in (('real-data-pilot-packed-feature-successor02-2026-10-06','DEPENDENCIES02.json'),
                        ('real-data-pilot-transport-binding-preparation01-2026-10-06','DEPENDENCIES01.json')):
    path = F/directory/name
    assert evidence[str(path)] == digest(path)
    for ref in read(path).values():
        assert evidence[ref['path']] == ref['sha256']

private = binding['transport']
private_path = Path(private['path'])
assert private_path.is_relative_to(Path('research_artifacts/real_pilot_runtime'))
assert [role for role, ref in experiment['inputs'].items()
        if ref['path'] == private['path']] == ['archive_transport']
assert private['path'] not in experiment['source_files']
assert evidence[private['path']] == private['sha256']
private_stat = private_path.lstat()
parent_stat = private_path.parent.lstat()
assert private_path.resolve() == ROOT/private_path
assert private_path.parent.resolve() == ROOT/private_path.parent
assert stat.S_ISREG(private_stat.st_mode) and private_stat.st_nlink == 1
assert private_stat.st_size == private['bytes'] == 925
assert stat.S_IMODE(private_stat.st_mode) == 0o600 and private_stat.st_uid == os.getuid()
assert stat.S_IMODE(parent_stat.st_mode) == 0o700 and parent_stat.st_uid == os.getuid()
assert read(OLD/'CHECKS01.json')['opaque_validation'] == 'accepted helper stat/hash only; no decode/print'

public = {p:h for p,h in evidence.items() if p != private['path']}
total = 0
for path, pin in public.items():
    body = raw(Path(path))  # Hash only: never decode scientific public payloads.
    assert hashlib.sha256(body).hexdigest() == pin, path
    total += len(body)
assert evidence[str(D/'preflight01.py')] == old_release['preflight_sha256']
assert evidence[str(D/'root_io.py')] == old_release['root_io_sha256']
checks = {'schema_version':1,'decision':'passed','identity':NAME,
    'gate_sha256':gate_hash,'binding_sha256':binding_hash,'binding_review_sha256':review_hash,
    'gate_source_pins':198,'input_roles':59,'cells':1,'outputs':8,
    'exact_four_source_delta':added,'all_other_gate_fields_equal':True,
    'binding_only_gate_and_review_replaced':True,
    'public_references_verified':len(public),'public_bytes_hashed':total,
    'private_body_read':False,'private_stat_mode_checked':True,
    'private_hash_basis':{'path':str(OLD/'CHECKS01.json'),'sha256':digest(OLD/'CHECKS01.json')},
    'actual_readonly_admission_reused':review['actual_readonly_admission'],
    'admission_rerun':False,'financial_experiment_run':False,'numerical_imports':False,
    'scientific_payloads_decoded':False,'git_or_network_or_native_invoked':False,
    'physical_eligibility_checked':False,'conditional_only':True}
checks_path = write('CHECKS01.json',checks)
local(checks_path)
result = copy.deepcopy(old_release)
result.update({'evidence':dict(sorted(evidence.items())),
    'binding_sha256':binding_hash,'binding_review_sha256':review_hash,
    'cardinality':{'gate_source_pins':198,'current_numerical_package_pins':178,
        'gate_input_roles':59,'outputs':8,'released_unique_references':len(evidence),
        'sole_opaque_private_exceptions':1},
    'supersedes':{'path':str(OLD/'RELEASE_REVIEW01.json'),
        'sha256':digest(OLD/'RELEASE_REVIEW01.json')},
    'completion_check':{'path':str(checks_path),'sha256':digest(checks_path)},
    'conditionality':'Exact source/input/binding composition only. Final preflight must authenticate committed public bodies against final HEAD, genuine admission/effective72, unchanged Torch runtime/source, unused identity, absent competing native job or claim, fresh complete writable union plus modeled growth, 10GiB disk floor and at least9GiB MemAvailable. Fresh native controls and genuine Owner/Binding remain mandatory. No physical eligibility, capacity, successful outcome or bypass is granted.',
    'protected_input':'Sole exact archive_transport path and public digest preserved. Previous accepted opaque hash proof reused; only mode/size/ownership/link/path stat checked here. No private body opened or decoded. Final preflight must validate its exact bytes under accepted bounded opaque helper.',
    'review_basis':'Independent inverse comparison of current198 gate against preserved194 gate, exact binding gate/review-only replacement, all public released source/control/payload digests checked locally without numerical imports or scientific payload decoding. Earlier230e63 composition and5a71a3 delta proofs reused; actual Root readonly admission02 readyTrue/effective72 joined. Superseded release and failed admission retained.',
    'not_tested':['Final Git commit authentication and final fresh physical/process/namespace/native eligibility remain mandatory preflight checks.',
        'No scientific payload values decoded; no timing, leakage, return/cashflow, fees/funding, financial denominator or predictive claim tested. Public scientific payloads received hash-only verification.',
        'No protected private body read; accepted prior opaque hash proof reused with current stat checks.',
        'No numerical package imports, fitting, experiment, network, native launch, ResearchRun.start or Owner/Binding construction; no measured capacity, throughput, future remote availability or runtime-success claim.']})
release_path = write('RELEASE_REVIEW02.json',result)
manifest = {'schema_version':1,'identity':NAME,'decision':'accepted',
    'scope':'Exact conditional final release completion; Root owns adoption and final launch eligibility.',
    'files':{str(path):{'sha256':digest(path),'bytes':path.stat().st_size}
             for path in (HERE/'complete01.py',checks_path,release_path)}}
manifest_path = write('MANIFEST01.json',manifest)
print(json.dumps({'release':str(release_path),'release_sha256':digest(release_path),
                  'manifest':str(manifest_path),'manifest_sha256':digest(manifest_path),
                  'references':len(evidence),'public_verified':len(public),
                  'public_bytes_hashed':total,'decision':'accepted'},sort_keys=True))
