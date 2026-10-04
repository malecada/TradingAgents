from pathlib import Path
import ast,difflib,hashlib,json,os,stat
H=Path(__file__).resolve().parent
SRC=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,x):(H/n).write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
old=(H/'original_workflow_storage.py').read_text();new=(H/'workflow_storage.py').read_text()
ops=[]
for tag,a,b,c,d in difflib.SequenceMatcher(a=old,b=new,autojunk=False).get_opcodes():
 if tag!='equal':ops.append({'old_start':a,'old_end':b,'new_start':c,'new_end':d,'old_literal':old[a:b],'new_literal':new[c:d]})
r=new
for row in reversed(ops):
 assert r[row['new_start']:row['new_end']]==row['new_literal'];r=r[:row['new_start']]+row['old_literal']+r[row['new_end']:]
assert r==old
x=ast.parse(old);y=ast.parse(new)
for tree in (x,y):
 tree.body=[n for n in tree.body if getattr(n,'name',None) not in ('_cleanup','StorageMutationObservation','_signature')]
 watch=next(n for n in tree.body if getattr(n,'name',None)=='StorageWatch')
 watch.body=[n for n in watch.body if getattr(n,'name',None) not in ('_check','_scan')]
assert ast.dump(x,include_attributes=False)==ast.dump(y,include_attributes=False)
put('FINAL_INVERSE08.json',{'old_sha256':sha(old.encode()),'new_sha256':sha(new.encode()),'operations':ops,'full_literal_reconstruction':True,'all_undeclared_ast_equal':True,'changed_original_definitions':['_cleanup','StorageWatch._check','StorageWatch._scan'],'added_definitions':['StorageMutationObservation','_signature']})
(H/'FINAL_SOURCE_DELTA08.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original_workflow_storage.py',tofile='workflow_storage.py')))
# Preserve reconstructable initial pre-refinement body matching original inverse01.
s=(H/'DRAFT02_interleaved_rejoin.py').read_text().replace("            result['aggregate_entry_visit_bound']=6*self.limits['max_entries']\n", "            result['aggregate_entry_visit_bound']=6*self.limits['max_entries']\n            result['aggregate_metadata_stat_bound']=6*(self.limits['max_entries']+1)\n").replace('first=dict(observed);observed={key:0 for key in observed};rejoin_entries=0','first=dict(observed);observed={key:0 for key in observed}').replace("                            listed.append(entry.name);rejoin_entries+=1\n                            if rejoin_entries>limits['max_entries']:raise StorageLimit('entries',{**observed,'entries':rejoin_entries})", "                            listed.append(entry.name)\n                            if len(listed)>limits['max_entries']:raise StorageLimit('entries',observed)")
assert sha(s.encode())==json.loads((H/'SOURCE_INVERSE01.json').read_text())['candidate_sha256']
(H/'DRAFT01_initial.py').write_text(s)
closure_path=SRC/'fixture_inputs/financial_wrapper_claimedrun01/source_closure.json';raw=closure_path.read_bytes();closure=json.loads(raw);(H/'ORIGINAL_SOURCE_CLOSURE01.json').write_bytes(raw)
rows=[]
for name,pin in sorted(closure['installed'].items()):
 p=SRC/name;st=p.lstat();assert p.resolve()==p and stat.S_ISREG(st.st_mode) and st.st_size<=4194304
 b=p.read_bytes();assert sha(b)==pin;rows.append({'path':name,'bytes':len(b),'sha256':pin,'mode':stat.S_IMODE(st.st_mode)})
assert len(rows)==194
watchpath='tradingagents/research/onchain_replication/workflow_storage.py';assert closure['installed'][watchpath]==sha(old.encode())
actual=set(closure['installed'].values());future=set({**closure['installed'],watchpath:sha(new.encode())}.values());assert actual!=future
put('SOURCE194_READBACK01.json',{'original_closure_path':str(closure_path),'original_closure_sha256':sha(raw),'source_current_historical':'9dc5c79f738920b52947b4e63fed0397f1b5b207','bodies':rows,'candidate_only_change':watchpath,'unchanged_other_bodies':193,'original_provenance_hash_set_sha256':sha(json.dumps(sorted(actual)).encode()),'prospective_provenance_hash_set_sha256':sha(json.dumps(sorted(future)).encode()),'old_checkpoint_source_hash_equality_under_unchanged_API':False})
claims=[]
for name in ('financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01','financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01','financial-wrapper-classification-eager-complete100-20261003-01'):
 entry={'identity':name}
 for kind in ('claim','failed'):
  p=SRC/'research_runs'/name/(kind+'.json');b=p.read_bytes();assert len(b)<=4194304
  entry[kind]={'path':str(p),'sha256':sha(b),'bytes':len(b)}
  (H/(name+'-'+kind+'.json')).write_bytes(b)
 entry['complete_present']=(SRC/'research_runs'/name/'complete.json').exists();assert not entry['complete_present'];claims.append(entry)
put('ACTUAL_FAILED_METADATA01.json',{'claims':claims,'observed_failed_claims':3,'old_identity_reopen_allowed':False,'raw_guard_outcome_semantics_independently_reviewed_here':False})
for filename,p in [('ACTUAL_PARENT_TERMINAL_ORIGINAL01.json',Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-root-launch-20261004-01/attempt/parent-terminal.json')),('ACTUAL_GUARD_FINAL_ORIGINAL01.json',SRC/'research_artifacts/onchain-paper-replication-2026-09-24/runs/financial-wrapper-classification-eager-complete100-20261003-01/guard/final.json')]:
 b=p.read_bytes();assert len(b)<=4194304;(H/filename).write_bytes(b)
put('MIGRATION_REQUIREMENTS01.json',{'status':'DRAFT_SOURCE_ONLY_NO_ADOPTION','candidate_source_sha256':sha(new.encode()),'actual_future_source':None,'actual_future_gate':None,'actual_future_identity':None,'actual_future_budget_extension':None,'actual_future_caller':None,'actual_external_recovery':None,'effective_allowance_observed':19,'spent_failed_claims':3,'remaining_allowances_arithmetic':16,'original_phases_remaining_as_root_task_scope':17,'cumulative20_is_necessary_arithmetic_not_admitted_or_sufficient':True,'continuation_blocker':{'path':'tradingagents/research/onchain_replication/financial_wrapper_fixture.py','authorize_return_line':177,'provenance_line':231,'prior_comparison_line':277,'reference_comparison_line':353,'reason':'Entire installed194 hash set enters checkpoint provenance. Guard-only workflow_storage change changes that set. Old one-update checkpoint and future corrected-reference hashes cannot compare equal under unchanged original API. No implicit exception or provenance rewriting is supplied.'},'required':['Preserve permanent failed complete100 claim2e3 and prior failed claims plus raw entire outcome; independently review and externally/freshly recover complete failure scope before future release.','Obtain different-author source review of this candidate and all original/preliminary/control failures.','Resolve original checkpoint provenance compatibility explicitly before promising dependent continuation; preserve all original claims/checkpoints, no relabeling or fake ancestry.','Root must prospectively commit an exact same-family cumulative amendment and independent genuine budget review if authorized; this preparation does not amend19 or decide whether20 is sufficient after provenance resolution.','Use a new genuinely registered unused identity and fresh source/caller namespaces; no relaunch/retry/refund/transfer/reset of complete100 original or any other spent identity.','Adopt only reviewed workflow_storage successor, keep193 other installed implementation bodies byte-identical and model/training/recipe/seeds/tolerances/runtime/native/floor limits unchanged. Update the one closure digest and every actual source/gate/role/caller/review mapping; recompute actual counts rather than reuse339/338.','Genuine metadata admission and exact source/runtime/input/native policy review, complete new source/caller external and fresh recovery and final release remain separate Root prerequisites.','Root alone performs any future native eligibility measurement or ONE newly released attempt; no ordinary stdlib controls establish100epoch or whole-population capacity.']})
print(json.dumps({'full_literal_inverse':True,'all_other_ast_equal':True,'source194_hashes_verified':len(rows),'failed_claim_metadata':len(claims),'candidate_sha256':sha(new.encode()),'old_checkpoint_provenance_migration_blocker':True},indent=2))
