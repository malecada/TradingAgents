"""Seal exact reviewed evidence references; no payload/credential reads or admission."""
from pathlib import Path
import hashlib,json
ROOT=Path.cwd();F=Path('research/onchain-paper-replication-2026-09-24/full_sources');HERE=F/'real-data-pilot-final-binding-review01-2026-10-06';FINAL=F/'real-data-pilot-final01-2026-10-06';NAME='eth-paper-real-data-end-to-end-resource-20261005-01'
def read(p):return json.loads(Path(p).read_bytes())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
evidence={}
def add(ref):
 p=ref['path'];h=ref['sha256'];assert not Path(p).is_absolute() and '..' not in Path(p).parts
 assert p not in evidence or evidence[p]==h,(p,'conflicting pin')
 evidence[p]=h
def local(p):
 p=Path(p);assert p.stat().st_size<=4*1024**2
 add({'path':str(p),'sha256':digest(p)})
b=read(FINAL/'BINDING01.json');old=read(FINAL/'BINDING_DRAFT03.json');br=HERE/'BINDING_REVIEW01.json';expected=dict(old);expected['binding_review']={'path':str(br),'sha256':digest(br),'bytes':br.stat().st_size};assert b==expected
assert digest(FINAL/'BINDING01.json')=='28230ea4e80ef13e5c5337cb0ee02ed031811d010cb1f7a5442e34c9fa631628'
g=read(FINAL/'gate01.json');e=g['experiments'][NAME];proof=read(br)
assert proof['decision']=='accepted' and proof['identity']==NAME
assert all(proof['evidence'][b[k]['path']]==b[k]['sha256'] for k in ('gate','draft','preparation','baseline','transport','transport_binding'))
for p,h in e['source_files'].items():add({'path':p,'sha256':h})
for r in e['inputs'].values():add(r) # inherited payload pins; do NOT hash/decode bodies
for r in b.values():
 if isinstance(r,dict) and 'path'in r:add(r)
for r in e['cumulative_budget_extension'].values():add(r)
add(e['charter']);local(FINAL/'BINDING01.json')
# Pinned direct+transitive entry code, all public and already accepted.
for dirname,table in [('real-data-pilot-packed-feature-successor02-2026-10-06','DEPENDENCIES02.json'),('real-data-pilot-transport-binding-preparation01-2026-10-06','DEPENDENCIES01.json')]:
 p=F/dirname/table;local(p)
 for ref in read(p).values():add(ref)
allocation=F/'real-data-pilot-resource-buffer-allocation01-2026-10-06/allocation01.py';assert digest(allocation)=='3912e68c232553f1fab5e39a92c0741c2c0ddab49316321c1189781d19611dfd';local(allocation)
d=read(b['draft']['path']);prepared=read(b['preparation']['path']);baseline=read(b['baseline']['path']);add(baseline['metadata_adapter_basis'])
for ref in d['protocol']['references'].values():add(ref)
for rec in d['graphs'].values():
 add(rec['manifest']);add(rec['node_count']);add(read(rec['node_count']['path'])['evidence'])
for ref in prepared['builder03_spec']['references'].values():add(ref)
for p in [FINAL/'INPUT_REFS02.json',FINAL/'RUNTIME_OBSERVATION01.json',FINAL/'ORIGINAL26_MAIN_OBJECT_READBACK01.json',F/'real-data-pilot-seven-graph-packed-input03-2026-10-06/NUMERICAL_ANCHOR_REBIND06.json',F/'real-data-pilot-seven-graph-packed-input03-2026-10-06/OUTPUT_DECLARATION05.json',F/'real-data-pilot-final-preflight-source-review03-2026-10-06/REVIEW03.json',F/'real-data-pilot-final-preflight-source-review03-2026-10-06/MANIFEST03.json',F/'real-data-pilot-final-preflight-source-review01-2026-10-06/successor02/REVIEW02.json',F/'real-data-pilot-final-preflight-preparation03-2026-10-06/MANIFEST03.json',F/'real-data-pilot-root-io-preparation01-2026-10-06/MANIFEST01.json',F/'real-data-pilot-root-io-preparation01-2026-10-06/CHECK01.json',F/'real-data-pilot-final-gate-composition01-2026-10-06/CURRENT_SOURCE_ROSTER01.json',HERE/'check01.py',HERE/'CHECKS01.json',HERE/'CHECKER_FAILURE01.json']:
 local(p)
# Fixed private path occurs only as the archive_transport input and binding ref.
private=b['transport'];assert evidence[private['path']]==private['sha256'];assert [k for k,v in e['inputs'].items() if v['path']==private['path']]==['archive_transport'];assert private['path'] not in e['source_files']
result={'schema_version':1,'identity':NAME,'decision':'accepted','scope':'EXACT_CONDITIONAL_SOURCE_AND_METADATA_ENTRY_RELEASE','evidence':dict(sorted(evidence.items())),'binding_sha256':digest(FINAL/'BINDING01.json'),'binding_review_sha256':digest(br),'preflight_sha256':digest(FINAL/'preflight01.py'),'root_io_sha256':digest(FINAL/'root_io.py'),'cardinality':{'gate_source_pins':194,'current_numerical_package_pins':178,'gate_input_roles':59,'outputs':8,'released_unique_references':len(evidence),'sole_opaque_private_exceptions':1},'conditionality':'Accepted exact source/input/binding and Root entry composition only. No actual current physical eligibility is granted. Mandatory preflight must authenticate final committed public bodies, genuine admission/effective72, unchanged Torch runtime and source, unused identity, absent competing native/claim, fresh union plus growth, diskfloor and at least9GiB MemAvailable. Root-reported current RAM below9GiB must still refuse. No direct worker/Owner/start bypass accepted.','protected_input':'Only exact archive_transport path/hash reference released. Body checked through accepted bounded validate_opaque helper without decode/print/stage; remains uncommitted and private.','review_basis':'Actual bounded metadata/source composition check230e63 exit0, accepted source03 one-Torch-flag review, prior accepted science/runtime/graph/residual/packed proofs; earlier failed/unadmitted drafts preserved.','runtime_outcomes':None,'scientific_or_capacity_claim':False,'not_tested':['No Git commit authentication independently rerun; final preflight must authenticate actual final HEAD/release bodies','No numerical/price/label/dictionary/sample/graph-array bodies, fitting or financial accounting tested','No network/native/ResearchRun/Owner/launch; no throughput, RAM/storage peak or future remote-byte availability claim']}
p=HERE/'RELEASE_REVIEW01.json';assert not p.exists();p.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':digest(p),'released_references':len(evidence)},sort_keys=True))
