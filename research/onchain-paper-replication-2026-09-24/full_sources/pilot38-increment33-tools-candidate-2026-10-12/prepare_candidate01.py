"""Write finite helper copies only. Never execute any preservation helper."""
import ast,difflib,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3]
H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';OLD=H/'full36increment32';DEP=H/'full38increment33'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=OLD/'FRESH_GIT_RECOVERY32.json';review=F/'pilot36-increment32-return-release-review-2026-10-11/RETURN_REVIEW01.json'
main=['tradingagents/research/admission.py']+['tradingagents/research/onchain_replication/'+x+'.py' for x in ('compact_mcm','imported_authority_lease','imported_mcm_identity','job','streamed_gat')]+['tests/research/onchain_replication/test_compact_mcm.py','tests/research/test_streamed_gat_lifetime_candidate.py']
pins={x:sha(R/x) for x in main}
owned=['pilot38-target-boundary-coalescing-2026-10-12','pilot38-integration-cumulative-review-2026-10-12','real-data-pilot-full38-cumulative-preparation01-2026-10-12','real-data-pilot-full38-binding-preparation01-2026-10-12','pilot-efficiency-integration-2026-10-12','pilot38-entry-capacity-investigation-2026-10-12','pilot38-observer-ledger-correction-2026-10-12','pilot37-optimization-checks-2026-10-12','pilot38-admission-coalescing-2026-10-12','pilot36-outcome-review-2026-10-12','pilot38-public-binding-review-2026-10-12','pilot38-entry-policy-correction-2026-10-12','real-data-pilot-full38-entry-preparation01-2026-10-12','real-data-pilot-full36-entry-preparation01-2026-10-11','pilot36-increment32-return-release-review-2026-10-11','pilot36-increment32-tools-review-2026-10-11',P.name,'pilot38-increment33-tools-review-2026-10-12','pilot38-entry-registration-review-2026-10-12']
name36='eth-paper-real-data-end-to-end-resource-20261011-36'
closed=['research_runs/'+name36,'research_artifacts/onchain-paper-replication-2026-09-24/runs/'+name36,'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent/'+name36,'research_artifacts/onchain_representations/4c1d07a983d266df70164d623a20d61a71499c9fec9e9d6a64a1f7ba6b1583e6/'+name36]
post=[p.name for p in OLD.iterdir() if p.name.endswith(('.json','.stdout','.stderr')) and p.name not in ('TOOL_SCOPE01.json','HELPERS_MANIFEST01.json')]
# Deliberately retain exact named postcapture receipts; old archive stdout is excluded below as in32.
post=sorted(post)
originals={name:(OLD/(name+'32.py')).read_text() for name in ('select','capture','recover')}
products={}; aliases={}
for name in ('capture','recover'):
 s=originals[name];mapping=[('full36increment32','full38increment33'),('pilot36-preparation-increment32','pilot38-preparation-increment33'),('preparation36-20261011-32.git','preparation38-20261012-33.git'),('SELECTION32','SELECTION33'),('CAPTURE32','CAPTURE33'),('FRESH_GIT_RECOVERY32','FRESH_GIT_RECOVERY33'),('GIT_OPERATIONS32','GIT_OPERATIONS33')]
 for old,new in mapping:s=s.replace(old,new)
 inverse=s
 for old,new in reversed(mapping):inverse=inverse.replace(new,old)
 assert inverse==originals[name]
 # Only string constants change in accepted capture/recovery algorithms.
 def shape(body):
  tree=ast.parse(body)
  for node in ast.walk(tree):
   if isinstance(node,ast.Constant) and isinstance(node.value,str):node.value='<string>'
  return ast.dump(tree)
 assert shape(s)==shape(originals[name]);products[name]=s;aliases[name]=mapping
s=originals['select']
# Protect baseline aliases from the new-product32->33 aliases.
s=s.replace('full35outcome31','BASELINE_DIRECTORY').replace('failed35-outcome-increment31.tar','BASELINE_ARCHIVE').replace('fresh-git-recovered-full35outcome31.tar','BASELINE_RETURN')
s=s.replace('full36increment32','full38increment33').replace('32','33').replace('31','32')
s=s.replace('BASELINE_DIRECTORY','full36increment32').replace('BASELINE_ARCHIVE','pilot36-preparation-increment32.tar').replace('BASELINE_RETURN','fresh-git-recovered-full36increment32.tar')
# Rebuild source pin literals below; all other original digit-bearing pins must be exact baseline values.
s=s.replace("assert sha(prior)=="+repr('527f22e70b79a040928a56dea2d7dbccb127ef1d9cc615fe042a67780a889083'.replace('32','33').replace('31','32')),"assert sha(prior)=="+repr(sha(prior)))
start=s.index("review=F/");end=s.index("base =",start)
s=s[:start]+"review=F/"+repr(str(review.relative_to(F)))+"\nassert sha(review)=="+repr(sha(review))+", 'accepted32 return review changed'\n"+s[end:]
def assignment(text,name,value):
 tree=ast.parse(text);node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
 return text.replace(ast.get_source_segment(text,node),name+'='+repr(value),1)
for name,value in [('owned',owned),('prior_generated_names',post),('main_source_names',main),('main_source_pins',pins)]:s=assignment(s,name,value)
s=s.replace('pilot-transport-20261011-36-01','pilot-transport-20261012-38-01')
insert="closed_scopes=[ROOT/path for path in "+repr(closed)+"]\nfor root in closed_scopes:\n    assert root.is_dir() and not root.is_symlink(), 'required closed36 owned root absent: '+str(root)\n    scope_directories.add(root)\n    for path in root.rglob('*'):\n        if path.is_file() or path.is_symlink():names.add(str(path.relative_to(ROOT)))\n        elif path.is_dir():scope_directories.add(path)\n"
s=s.replace('# Exact generated32 receipts/raw operations only. Never traverse historical H.\n',insert+'# Exact generated32 receipts/raw operations only. Never traverse historical H.\n')
s=s.replace('allowed_roots=[F/name for name in owned]','allowed_roots=[F/name for name in owned]+closed_scopes')
s=s.replace("or relative==private_relative, relative", "or relative==private_relative or any(path.is_relative_to(root) for root in closed_scopes), relative")
opaque=json.loads((F/'real-data-pilot-full38-binding-preparation01-2026-10-12/BINDING_CHECK01.json').read_bytes())['actual_opaque_input']['archive_transport']
s=s.replace("assert private.is_file() and not private.is_symlink()", "assert private.is_file() and not private.is_symlink()\nassert private.stat().st_size=="+repr(opaque['bytes'])+" and sha(private)=="+repr(opaque['sha256'])+", 'exact bound38 opaque bytes changed'")

s=s.replace("'actual_scope_states': [{'path':str(scopes[0].relative_to(ROOT)), 'exists':True,'qualification':'One new bound opaque envelope only; no connection reference target, credential body or historical store is read.'}],","'actual_scope_states': [{'path':str(path.relative_to(ROOT)), 'exists':True,'qualification':'Exact closed36 owned root or sole new38 opaque envelope parent; no sibling historical store or referenced connection target.'} for path in closed_scopes+scopes],")
s=s.replace('Finite new efficiency and36 preparation bodies','Finite new12Oct efficiency, closed36 outcome and38 preparation bodies')
s=s.replace('# No historical raw scopes are traversed; only the new bound opaque envelope.','# Exact closed36 owned roots above; only the new bound opaque envelope below.')
s=s.replace('# Already returned failed35 archive/blob stdout stay immutable at original','# Already returned preparation36 archive/blob stdout stay immutable at original')
# Deployment at the accepted H layout is required; the candidate directory is never an execution destination.
s=s.replace('F = HERE.parent.parent\n','F = HERE.parent.parent\nassert HERE == ROOT/'+repr(str(DEP.relative_to(R)))+", 'deploy reviewed copies to exact H/full38increment33 before Root execution'\n")
assert "sha(prior)=='"+sha(prior)+"'" in s
ast.parse(s);products['select']=s
forward=[];reverse=[]
for name,body in products.items():
 (P/(name+'33.py')).write_text(body)
 forward.extend(difflib.unified_diff(originals[name].splitlines(True),body.splitlines(True),fromfile=str((OLD/(name+'32.py')).relative_to(R)),tofile=str((DEP/(name+'33.py')).relative_to(R))))
 reverse.extend(difflib.unified_diff(body.splitlines(True),originals[name].splitlines(True),fromfile=str((DEP/(name+'33.py')).relative_to(R)),tofile=str((OLD/(name+'32.py')).relative_to(R))))
(P/'LITERAL_PATCH01.diff').write_text(''.join(forward));(P/'LITERAL_INVERSE01.diff').write_text(''.join(reverse))
ref=lambda p:{'path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size}
review36=F/'pilot36-outcome-review-2026-10-12/OUTCOME_REVIEW01.json';evidence=json.loads(review36.read_bytes())['evidence']
owner_pins={k:v for k,v in evidence.items() if k.startswith(closed[3]+'/')}
scope={'status':'UNEXECUTED_TOOLS_CANDIDATE_ROOT_ONLY','deployment_directory':str(DEP.relative_to(R)),'baseline_actual32_return':ref(prior),'baseline_actual32_review':ref(review),'main_source_pins':pins,'mandatory_public_roots':owned,'closed36_owned_roots':closed,'closed36_owner_receipt_pins_from_original_review':owner_pins,'closed36_outcome_review':ref(review36),'prior32_exact_postcapture_names':post,'opaque38':json.loads((F/'real-data-pilot-full38-binding-preparation01-2026-10-12/BINDING_CHECK01.json').read_bytes())['actual_opaque_input']['archive_transport'],'opaque_semantics':'Raw body preservation accepted by Root; only mode/size/hash inspection. No JSON/connection decode or referenced target access.','capture_recover_string_aliases':aliases,'capture_recover_ast_nonstring_parity':True,'operations_executed':False,'limitations':['Final38 binding/release are postcapture increments, not claimed by this archive.','No historical H/store traversal or old tar/blob copy; exact prior32 archives/stdout are excluded.','Candidate is not actual selection/capture/external recovery, remote availability, deletion authority or empirical release.']}
(P/'TOOL_SCOPE01.json').write_text(json.dumps(scope,indent=2)+'\n')
files=['select33.py','capture33.py','recover33.py','TOOL_SCOPE01.json','LITERAL_PATCH01.diff','LITERAL_INVERSE01.diff']
(P/'HELPERS_MANIFEST01.json').write_text(json.dumps({str((DEP/name).relative_to(R)):sha(P/name) for name in files},indent=2)+'\n')
print(json.dumps({'public_roots':len(owned),'closed_roots':len(closed),'main_pins':len(pins),'prior32_postcapture_names':len(post),'owner_receipt_pins':len(owner_pins),'baseline_return_sha256':sha(prior),'baseline_review_sha256':sha(review),'helpers_executed':False}))
