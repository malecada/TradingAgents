"""Exact late binding/release construction; no Git, admission or launch."""
import ast,copy,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];E=F/'real-data-pilot-full36-entry-preparation01-2026-10-11';NAME='eth-paper-real-data-end-to-end-resource-20261011-36'
sha=lambda b:hashlib.sha256(b).hexdigest();js=lambda p:json.loads(p.read_bytes())
def ref(p):
    b=p.read_bytes();return {'path':str(p.relative_to(R)),'sha256':sha(b),'bytes':len(b)}
binding=js(E/'BINDING01.json');request=js(E/'BINDING_REQUEST02.json');br=ref(P/'BINDING_REVIEW01.json');review=js(P/'BINDING_REVIEW01.json')
assert ref(E/'BINDING01.json')=={'path':str((E/'BINDING01.json').relative_to(R)),'sha256':'1a2e789707e0e2ed17587e75e33fa8ae95d7685c0f040f04c1d45e48c8907844','bytes':24253}
expected=copy.deepcopy(request);expected['binding_review']=br;expected['status']='FIXED_BINDING_PENDING_EXACT_FINAL_RELEASE';assert binding==expected
assert br['sha256']=='99f04625df4caa6b97eb02062e3736b957f706d7bee328cd24920d245fabffcd' and review['decision']=='accepted' and review['identity']==NAME
gate=js(E/'gate01.json');experiment=gate['experiments'][NAME];actual={role:{k:v[k] for k in ('path','sha256')} for role,v in experiment['inputs'].items()}
assert actual==binding['input_refs']==review['input_refs'] and len(actual)==73 and len(experiment['source_files'])==909
assert binding['budget_review']==experiment['cumulative_budget_extension']['review']
evidence=dict(review['evidence']);checked={}
def add(r):
    p=R/r['path'];assert p.resolve()==p and p.is_file() and not p.is_symlink() and p.stat().st_nlink==1
    b=p.read_bytes();assert sha(b)==r['sha256'] and len(b)<=4*1024**2
    if 'bytes' in r:assert len(b)==r['bytes']
    if r['path'] in evidence:assert evidence[r['path']]==r['sha256']
    evidence[r['path']]=r['sha256'];checked[r['path']]={'bytes':len(b),'sha256':r['sha256']}
add(ref(E/'BINDING01.json'));add(br)
for role,r in binding.items():
    if isinstance(r,dict) and {'path','sha256'}<=set(r):
        assert r['path'] in evidence and evidence[r['path']]==r['sha256']
        # Prior unchanged source/input/evidence authentication is reused.
        if role in ('complete_increment_recovery','new_increment_recovery_review','binding_review','gate'):add(r)
for n in ('preflight36_01.py','root_io36_01.py','ADMISSION01.json','ROOT_ADMISSION_OPERATIONS01.json'):add(ref(E/n))
for n in ('BINDING_REQUEST01.json','BINDING_REQUEST02.json'):add(ref(E/n))
for n in ('RETURN_REPORT01.md','REPORT01.md','RETURN_CHECK01.txt','RETURN_CHECK02.txt','BINDING_CHECK01.txt','BINDING_CHECK02.txt','BINDING_CHECK02.json','check_return32.py','check_return32b.py','check_binding01.py','check_binding02.py','make_release01.py'):add(ref(P/n))
assert all(evidence.get(p)==h for p,h in experiment['source_files'].items()) and all(evidence.get(r['path'])==r['sha256'] for r in actual.values())
assert evidence[str((E/'preflight36_01.py').relative_to(R))]=='b00449135a348f5393afef09acadda02bab0cc2c60cf00f5abaa75f92ae72138'
assert evidence[str((E/'gate01.json').relative_to(R))]=='20f769eea62240230e8353cf35988d2b58cbcbf25a91bdfcf32a59a4e4e6e228'
return_review=js(P/'RETURN_REVIEW01.json');assert return_review['decision']=='accepted' and binding['new_increment_recovery_review']['sha256']==ref(P/'RETURN_REVIEW01.json')['sha256']
# Actual fixed helper proves there is exactly one opaque body exception.
tree=ast.parse((E/'preflight36_01.py').read_bytes());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('need','reference','committed_refs')]
ns={'Path':Path,'ROOT':R};exec(compile(ast.Module(body=nodes,type_ignores=[]),'fixed_committed_reference_scope','exec'),ns)
public=ns['committed_refs'](evidence,binding);assert set(evidence)-set(public)=={binding['transport']['path']}
assert not (E/'RELEASE_REVIEW01.json').exists() and not (R/'research_runs'/NAME).exists()
job=js(R/actual['execution_job']['path'])
out={'schema_version':1,'decision':'accepted','reviewer':'Independent pilot36 increment return, concrete binding and source/entry reviewer','identity':NAME,'scope':'Conditional exact fixed36 preparation-only source/entry release after authentic increment32 return and machine binding acceptance. Fresh actual whole preflight and Root-only one-use launch remain mandatory. Whole37/scientific/paper-fit authority excluded.','binding':ref(E/'BINDING01.json'),'binding_review':br,'gate':ref(E/'gate01.json'),'admission':ref(E/'ADMISSION01.json'),'source_count':909,'input_count':73,'output_count':9,'evidence':evidence,'checked_actual_references':checked,'command_cwd':str(R),'exact_read_only_preflight_command':['.venv/bin/python','-B',str((E/'preflight36_01.py').relative_to(R))],'exact_root_command':['.venv/bin/python','-B',str((E/'root_io36_01.py').relative_to(R))],'limits':job['resources'],'checks':{'actual_increment32_return_accepted':True,'final_binding_exact_request02_plus_review_status':True,'budget_reference_exact_gate_equality':True,'source_input_binding_evidence_closure':True,'sole_opaque_dispatch_exception':True,'fixed_preflight_recovery_guards':True,'genuine_preflight_executed_by_reviewer':False,'native_or_claim_started_by_reviewer':False},'required_root_before_launch_conditions':['Copy these exact release bytes to the fixed entry RELEASE_REVIEW01.json. Commit and push the final public source/binding/release and late reference/operation/admission/review metadata. The actual RootIO preflight must authenticate every public released body against actual HEAD; the earlier metadata admission and archive source are not substitutes.','Archive32 actual return covers its declared frozen289bodies and explicit31 lineage. Later reference-only binding/recovery/admission/release/review records are separately authenticated committed bodies, never represented as archive32 payload. Any substantive source/input change requires renewed exact review.','The fixed preflight must freshly require the complete increment recovery and independent return review, exact108 extension/review, all73inputs/909source pins, current runtime inventory, unchanged kernel/native/resource limits, unused36 namespace and absence of active program claims/native units. Exactly one private dispatch body is excepted from public Git and must pass its original hash/permission/currentness checks without disclosure.','Fresh actual writable-union, RAM and disk eligibility must pass. Accepted capacity is prospective headroom only for the exact36 pre-MCM endpoint; no hard quota, writer exclusion, measured memory peak or full37 capacity is inferred.','Root alone may invoke the exact RootIO command for at most one unused36 attempt after its single genuine whole preflight passes. Preserve original FAILED/spent disposition and all original attempted/unavailable failure/journal/timing/native/parent/cleanup outputs. Freeze source until closure; no retry or spent-identity reuse. Independent component outcome/recovery is required before dependent37, which must omit the stop and obtain separate complete capacity admission.']}
with (P/'RELEASE_REVIEW01.json').open('x') as h:json.dump(out,h,sort_keys=True,indent=2);h.write('\n')
print(json.dumps({'decision':'accepted','release':ref(P/'RELEASE_REVIEW01.json'),'evidence_count':len(evidence),'public_commit_references':len(public),'native_or_claim':False}))
