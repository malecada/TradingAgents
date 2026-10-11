"""Final exact binding/ref-only release. No execution of the entry or data input reads."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'real-data-pilot-full33-entry-preparation01-2026-10-11';checks={}
def body(p):
 assert not ({'.git','.venv','research_artifacts','research_runs','keys','apis'}&set(p.parts));return p.read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):
 b=body(p);return {'path':str(p.relative_to(R)),'sha256':sha(b),'bytes':len(b)}
def load(p):return json.loads(body(p))
def ck(v,n):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
review=load(P/'BINDING_REVIEW01.json');ck(ref(P/'BINDING_REVIEW01.json')['sha256']=='944cd6eee798b232fe84bace1777c70146c3100fe7519e6c5b8a63951d6dc5f2','frozen accepted binding review')
binding=load(D/'BINDING01.json');draft=load(D/'BINDING_DRAFT01.json');expected=load(P/'EXPECTED_FINAL_BINDING01.json');ck(ref(D/'BINDING01.json')==expected,'Root exact actual binding body')
ck(binding['binding_review']==ref(P/'BINDING_REVIEW01.json'),'actual final review ref')
inverse=dict(binding);inverse['binding_review']=draft['binding_review'];inverse['status']=draft['status'];ck(inverse==draft and binding['status']=='BOUND_NOT_RELEASED','literal final binding two-field inverse')
gate=load(D/'gate01.json');exp=gate['experiments'][binding['identity']];evidence=dict(exp['source_files']);ck(len(evidence)==678 and all(review['evidence'].get(p)==v for p,v in evidence.items()),'678 reviewed exact source pins')
actual={k:{q:v[q] for q in ('path','sha256')} for k,v in exp['inputs'].items()};ck(len(actual)==67 and actual==binding['input_refs']==review['input_refs'],'67 exact inputs')
for v in actual.values():evidence[v['path']]=v['sha256']
for role,v in binding.items():
 if type(v) is dict and {'path','sha256'}<=set(v):
  ck(role=='binding_review' or review['evidence'].get(v['path'])==v['sha256'],'binding ref independently authenticated '+role);evidence[v['path']]=v['sha256']
for name in ('BINDING01.json','preflight33_01.py','root_io33_01.py'):
 v=ref(D/name);ck(name=='BINDING01.json' or review['evidence'].get(v['path'])==v['sha256'],'final exact entry source '+name);evidence[v['path']]=v['sha256']
core=load(R/binding['core_manifest']['path'])
for v in core['inputs'].values():ck(review['evidence'].get(v['path'])==v['sha256'],'exact core policy ref '+v['path']);evidence[v['path']]=v['sha256']
binder='research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full29-transport-binding01-2026-10-09/binder02/bind01.py';evidence[binder]=review['evidence'][binder]
v=ref(P/'BINDING_FAILED01.json');evidence[v['path']]=v['sha256']
ck(exp['cumulative_budget_extension']['review']==binding['budget_review'],'strict genuine104review equality')
admission_expected=load(P/'EXPECTED_ADMISSION01.json')
for name,row in admission_expected['files'].items():ck(ref(D/name)==row,'original admission evidence '+name);evidence[row['path']]=row['sha256']
admission=load(D/admission_expected['stdout']);operation=load(D/admission_expected['operation'])
ck(admission=={'experiment':binding['identity'],'stage':'development','ready':True,'status':'metadata_admitted','empirical_inputs_opened':False,'run_started':False},'actual genuine metadata admission ready only')
ck(operation['exit_code']==0 and operation['source']==admission_expected['source'],'actual Root admission source and exit0')
ck(operation['stdout_sha256']==ref(D/admission_expected['stdout'])['sha256'] and operation['stderr_sha256']==sha(b'') and body(D/admission_expected['stderr'])==b'','actual raw admission stdout stderr hashes')
out={'schema_version':1,'decision':'accepted','identity':binding['identity'],'scope':'Exact fixed33 source/capacity/gate01/public67 binding and Root caller release; conditional on genuine live entry and complete externally recovered current preparation.','reviewer':'independent outcome16_release_review','gate':binding['gate'],'binding':expected,'binding_review':binding['binding_review'],'source_count':678,'input_count':67,'evidence':evidence,'checks':checks,'exact_root_command':['.venv/bin/python','-B',str((D/'root_io33_01.py').relative_to(R))],'exact_read_only_preflight_command':['.venv/bin/python','-B',str((D/'preflight33_01.py').relative_to(R))],'required_root_before_launch_conditions':['Install these exact RELEASE_REVIEW01 bytes at fixed entry RELEASE_REVIEW01.json and commit/freeze the complete current entry/source/references.','After final freeze, preserve complete declared public current preparation externally, fresh-recover it and obtain independent actual returned-body acceptance; prior outcome23 recovery does not substitute.','Run genuine current whole-caller preflight: committed source/input/runtime, strict budget104, private dispatch, fresh namespace, no active claim/native job, actual storage/RAM capacity and kernel guards must pass. Root alone may execute one unused fixed33 attempt.'],'limits':review['limits']+['Accepted32 source/capacity invariants and independent33 numerical source authentication reused;123 focused current binding checks passed. Reviewer path/hash transcription failure retained unchanged.','This review does not reopen prior32 or spent samples, change scientific selection/caps, prove real throughput, financial validity or full-run feasibility.','The release evidence records historical numerical and opaque input hashes by unchanged reference; these bodies were not independently reopened.'],'correction_summary':'Selected compact_mcm beca removes discarded legacy scope construction from imported branch; accepted source review reused, actual saving unknown. Existing f65 preload and all three e93 boundaries,60-second lease and resource/scientific caps unchanged. Genuine104 proposal is budget-only; fresh entry recovery and live preflight remain required.'}
with (P/'RELEASE_REVIEW01.json').open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'decision':'accepted','checks':len(checks),'sha256':ref(P/'RELEASE_REVIEW01.json')['sha256'],'bytes':ref(P/'RELEASE_REVIEW01.json')['bytes'],'evidence_count':len(evidence)},sort_keys=True))
