"""Release only an actual exact final binding, never construct Root's binding."""
import copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
ENTRY=HERE.parent/'real-data-pilot-full38-entry-preparation01-2026-10-12'
NAME='eth-paper-real-data-end-to-end-resource-20261012-38'
def load(p):return json.loads(p.read_bytes())
def pin(p):
    assert p.resolve(strict=True)==p and p.is_file() and p.stat().st_nlink==1
    body=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)}
request=load(ENTRY/'BINDING_REQUEST03.json');review=load(HERE/'BINDING_REVIEW01.json')
assert pin(HERE/'BINDING_REVIEW01.json')['sha256']=='cd2111561c5a550d464a4812f53d6a5fd0086a2bd12e4385e1ac660f7cb27200'
expected=copy.deepcopy(request['binding']);expected['binding_review']=pin(HERE/'BINDING_REVIEW01.json')
binding=load(ENTRY/'BINDING01.json');assert binding==expected
assert pin(ENTRY/'BINDING01.json')['sha256']=='4b1419e0b9de72903bbadca84ca2a30e9aa33d61f7d48196a3f4b2ff233cdac2'
assert all(v is not None for v in binding.values())
gate=load(ROOT/binding['gate']['path']);experiment=gate['experiments'][NAME]
evidence=dict(review['evidence']);known={}
for p in sorted(HERE.iterdir()):
    if p.is_file() and p.name not in {'RELEASE_REVIEW01.json','RELEASE_CHECK01.json','RELEASE_CHECK01.stdout','RELEASE_CHECK01.stderr'}:
        v=pin(p);evidence[v['path']]=v['sha256'];known[v['path']]={k:v[k] for k in ('sha256','bytes')}
for p in (ENTRY/'BINDING01.json',ENTRY/'BINDING_REQUEST03.json',ENTRY/'preflight38_01.py',ENTRY/'root_io38_01.py'):
    v=pin(p);evidence[v['path']]=v['sha256'];known[v['path']]={k:v[k] for k in ('sha256','bytes')}
for role,ref in binding.items():
    if isinstance(ref,dict) and {'path','sha256'}<=set(ref):
        assert evidence[ref['path']]==ref['sha256']
        if role!='binding_review':assert review['evidence'][ref['path']]==ref['sha256']
assert review['input_refs']==binding['input_refs']=={r:{k:v[k] for k in ('path','sha256')} for r,v in experiment['inputs'].items()}
assert all(evidence[p]==d for p,d in experiment['source_files'].items())
assert evidence['research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full29-transport-binding01-2026-10-09/binder02/bind01.py']=='bcca66a6c7daba762a629dff84b9f16e48e7b9c2ffe51f77511942816ee444cb'
assert len(experiment['source_files'])==1036 and len(review['input_refs'])==73
assert binding['budget_review']==experiment['cumulative_budget_extension']['review']
assert experiment['cells']==['real-eth-first-graph-entry-preparation-resource38']
opaque=binding['transport']['path'];assert evidence[opaque]==binding['transport']['sha256']
for p,d in evidence.items():
    # Hash-only final currentness authentication; no body interpretation.
    assert pin(ROOT/p)['sha256']==d,p
job=load(ROOT/experiment['inputs']['execution_job']['path'])
result={'schema_version':1,'decision':'accepted','identity':NAME,'reviewer':'Independent pilot38 concrete binding and source/entry reviewer','scope':'Conditional exact fixed38 preparation-only source/entry release after accepted actual33/34 returned scopes and concrete machine binding. Fresh actual whole preflight and Root-only one-use launch remain mandatory. Whole39/scientific/paper-fit authority excluded.','binding':pin(ENTRY/'BINDING01.json'),'binding_review':pin(HERE/'BINDING_REVIEW01.json'),'gate':binding['gate'],'admission':request['actual_job_metadata_admission'],'source_count':1036,'input_count':73,'limits':job['resources'],'command_cwd':str(ROOT),'exact_read_only_preflight_command':['.venv/bin/python','-B',str((ENTRY/'preflight38_01.py').relative_to(ROOT))],'exact_root_command':['.venv/bin/python','-B',str((ENTRY/'root_io38_01.py').relative_to(ROOT))],'checks':{'final_binding_exact_request03_plus_actual_review':True,'source_input_binding_evidence_closure':True,'budget_reference_exact_gate_equality':True,'corrected_one_cell_identity':True,'increment33_and34_scope_reviews_joined':True,'local_capacity428_ancestor_and_current_git_bodies':True,'sole_opaque_dispatch_exception':True,'genuine_whole_preflight_executed_by_reviewer':False,'native_or_claim_started_by_reviewer':False},'required_root_before_launch_conditions':['Copy these exact release bytes into the fixed entry RELEASE_REVIEW01.json and commit/push the final public binding, review, release and later metadata. Actual RootIO preflight must authenticate every released public body against actual HEAD. Previously observed metadata readiness and archive commits do not substitute.','Actual33 returned scope covers original36 closure and old38 draft; actual34 separately covers the corrected gate/helper/admission02. Later binding/review/release references remain separately committed evidence outside both captured payloads. No recovery of changed substantive bodies may be inferred from old archive hashes.','Fresh exact preflight must require genuine recovery refs,110 extension/review,73inputs/1036source pins, corrected38 cell, unchanged selected policies/native limits, current runtime, unused namespace and no active competing claim/native unit. The sole930-byte opaque body must pass exact fd/hash/permissions/currentness without disclosure.','Fresh writable-union, RAM and disk eligibility must pass under unchanged sampled limits. Conditional preparation capacity is prospective headroom only; no hard quota, writer exclusion, measured60s performance or whole39 capacity follows.','Root alone may invoke the exact RootIO command at most once for unused38 after its genuine whole preflight passes. Preserve original FAILED/spent outer disposition, all attempted/unavailable cells, timing/journal/native/parent/cleanup outputs; freeze source through closure and do not retry a spent identity. Independent accepted/recovered component outcome is required before dependent39, with separate full capacity admission.'],'checked_actual_references':known,'evidence':evidence}
with (HERE/'RELEASE_REVIEW01.json').open('x') as out:out.write(json.dumps(result,indent=2,sort_keys=True)+'\n')
receipt={'decision':'accepted','release':pin(HERE/'RELEASE_REVIEW01.json'),'binding':pin(ENTRY/'BINDING01.json'),'evidence_count':len(evidence),'source_count':1036,'input_count':73,'reviewer_native_launch':False,'reviewer_claim':False}
with (HERE/'RELEASE_CHECK01.json').open('x') as out:out.write(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps(receipt,sort_keys=True))
