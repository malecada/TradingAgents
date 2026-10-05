"""Owned finite actual-root and opaque Reader checks; no fake Admission/Run/Owner."""
from pathlib import Path
import importlib.util,json,hashlib,ast,copy
H=Path(__file__).resolve().parent;B=H.parent;CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');sha=lambda b:hashlib.sha256(b).hexdigest()
s=importlib.util.spec_from_file_location('_proof_reuse_candidate',H/'preclaim_reuse01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
original=(H/'original_preclaim01.py').read_text();candidate=(H/'preclaim_reuse01.py').read_text();inverse=json.loads((H/'INVERSE01.json').read_text());reverted=candidate.replace(inverse['remove_exact_added_block'],'',1).replace(inverse['replace']['new'],inverse['replace']['old'],1);assert reverted==original
oldnodes={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(original).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};newnodes={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(candidate).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};assert all(v==newnodes[k] for k,v in oldnodes.items() if k!='_proof_bundle');assert ast.dump(ast.parse(reverted),include_attributes=False)==ast.dump(ast.parse(original),include_attributes=False)
checks=['complete literal and AST inverse','Reader/_physical/finish/Inputs/current-source/prior/reference/public validator identical']
g=json.loads((CAP/'fixture_inputs/financial_wrapper_compatibility01/gates.json').read_text());e=g['experiments'][m.REUSE_REFERENCE];r=m.Reader();i=m.Inputs(CAP,e['inputs'],r);policy=i.json(m.ROLE);refs=copy.deepcopy(m.REUSE_EXTERNAL);known=m._reuse_known_roots(refs,i,policy,r);assert known['outcome']['epochs']==100;first=r.total;r.finish();assert r.total==2*first;checks.append('actual fixed accepted ancestry roots, registered proofs and final reread')
for k in refs:
 bad=copy.deepcopy(refs);bad[k]['sha256']='0'*64
 try:m._reuse_known_roots(bad,i,policy,m.Reader())
 except m.Unavailable:checks.append('fixed root substitution refused '+k)
 else:raise AssertionError(k)
bad=copy.deepcopy(refs);bad['recovery_proof']['path']=bad['recovery_proof']['path']+'/foreign'
try:m._reuse_known_roots(bad,i,policy,m.Reader())
except m.Unavailable:checks.append('foreign proof path refused')
else:raise AssertionError('foreign path')
for side in ('historical','target'):
 bad=copy.deepcopy(policy);key=next(iter(bad[side]['installed']));bad[side]['installed'][key]='0'*64
 try:m._reuse_known_roots(refs,i,bad,m.Reader())
 except m.Unavailable:checks.append('wrong full path-map refused '+side)
 else:raise AssertionError(side)
# Pure predicate refusals only: no synthetic accepted recovery or public success.
draft=json.loads((H/'PROOF_REUSE_CONTRACT_DRAFT01.json').read_text());q=json.loads((CAP.parent.parent/'genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01/REQUEST_FINAL01.json').read_text());metadata=known['source_runtime']
for label,value in [('unbound draft',draft),('wrong consumer',dict(draft,consumer='foreign')),('stale original source',dict(draft,current_source=m.REUSE_SOURCE))]:
 try:m._reuse_contract(value,q,metadata,m.Reader())
 except m.Unavailable:checks.append('prospective contract refusal '+label)
 else:raise AssertionError(label)
# Actual checkpoint hashes are mandatory in Inputs and unchanged _checkpoint.
handoff=json.loads((B/'financial-wrapper-compatible-next-phases-investigation01-2026-10-05/NEXT_INPUT_HANDOFF01.json').read_text());v=handoff['actual_reference_roles']['reference_state'];rr=m.Reader();raw=rr.read(CAP/v['path']);assert len(raw)==v['bytes'] and sha(raw)==v['sha256'];rr.finish();checks.append('actual reference opaque body/hash/final reread')
try:m.Reader().reference({'path':str(CAP/v['path']),'sha256':'0'*64})
except m.Unavailable:checks.append('actual reference checkpoint wrong hash refused')
else:raise AssertionError('bad state hash')
for k in ('Reader','Inputs','_checkpoint','_historical','_complete','validate_preclaim','_parent_release'):assert oldnodes[k]==newnodes[k]
checks.append('all current-source/provenance/checkpoint/one-use/fresh-final-Parent checks unchanged')
result={'schema_version':1,'checks':checks,'count':len(checks),'actual_known_proof_component_bytes_including_finish':r.total,'public_full_success':False,'actual_completed100_recovery_proof':None,'all_original_bounds':[m.TOTAL,m.FILE,m.SECONDS],'numerical_imports':False,'inverse_sha256':sha(reverted.encode())};(H/'CONTROLS01.json').write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps(result))
