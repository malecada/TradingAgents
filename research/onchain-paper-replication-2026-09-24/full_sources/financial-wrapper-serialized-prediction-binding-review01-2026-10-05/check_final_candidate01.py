from pathlib import Path
import ast,hashlib,json,os,subprocess
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=Path(__file__).parent;C=F/'heartbeat-root-checkpoint10-2026-10-04';P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-predict-serialized-storage-root-launch-20261005-01');CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
sha=lambda b:hashlib.sha256(b).hexdigest();encode=lambda v:(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode();compact=lambda v:(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes())}
def load(p):return json.loads(p.read_bytes())
def save(n,v):
 with (D/n).open('xb') as h:h.write(compact(v))
 os.chmod(D/n,0o444);return ref(D/n)
p=P/'REQUEST_RELEASE_CANDIDATE01.json';raw=p.read_bytes();assert sha(raw)=='31473cd5079466d458292249b4f88c479377cec944f9648c18465756d8e9075f';q=json.loads(raw);pres=load(P/'REQUEST_PRESERVATION_DRAFT01.json');assert {k for k in q if q[k]!=pres[k]}=={'status','proofs'}
assert q['status']=='RELEASED_ONE_USE_FINANCIAL_PARENT' and q['final_review'] is None and q['proofs']['cumulative']==pres['proofs']['cumulative'] and q['proofs']['independent_source_input_runtime']==pres['proofs']['independent_source_input_runtime'];assert q['proofs']['full_recovery']==ref(D/'FULL_CURRENT_RECOVERY_PROOF01.json')
assert q['source']==q['design_source']=='4c66c404fd61ccdbb62c39cd91e16878df74a232' and sha((P/'parent01.py').read_bytes())==q['caller_sha256']=='e1f3687ea3c44c85efc46c948c9c745c2c1f7512e29191abd1ff9b012b8a9b97'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=CAP).decode().strip()==q['source'] and subprocess.check_output(['git','status','--short','--untracked-files=no'],cwd=CAP)==b''
contract=sha(encode({k:v for k,v in q.items() if k!='final_review'}));assert contract=='aef8c62a58150612dd527d999fca8b9721f23c5ade56cb2a8bc87f446fbea173'
proofpins={}
for k,v in q['proofs'].items():
 proofraw=Path(v['path']).read_bytes();assert sha(proofraw)==v['sha256'];doc=json.loads(proofraw);assert doc['source']==doc['design_source']==q['source'] and doc['identity']==q['identity'];proofpins[k]=v['sha256']
assert load(D/'CUMULATIVE_PROOF01.json')['spent_claims']==5 and load(D/'FULL_CURRENT_RECOVERY_PROOF01.json')['final_envelope_supplement_pending'] is True
for n,pin in q['helper_hashes'].items():assert sha((P/n).read_bytes())==pin
reg=load(CAP/q['registration']);exp=reg['experiments'][q['identity']];assert sha((CAP/q['registration']).read_bytes())==q['registration_sha256'] and exp['source_files']==q['source_files'] and {k:v['sha256'] for k,v in exp['inputs'].items()}==q['input_hashes'];assert len(exp['inputs'])==29 and len(reg['experiments'])==7
assert q['runtime_mapping']==load(CAP/exp['inputs']['runtime_mapping']['path'])
for path in [P/'REQUEST_FINAL01.json',P/'attempt',CAP/'research_runs'/q['identity'],CAP/'research_artifacts/financial_wrapper_engineering'/q['identity']]:assert not os.path.lexists(path)
review={'schema_version':1,'decision':'accepted-exact-one-use-financial-parent','contract_sha256':contract,'proof_sha256':proofpins,'identity':q['identity'],'source':q['source'],'caller_sha256':q['caller_sha256']};assert len(review)==7
reviewpath=D/'FINAL_PARENT_REVIEW01.json';reviewraw=compact(review);finalq=dict(q,final_review={'path':str(reviewpath),'sha256':sha(reviewraw)});finalraw=compact(finalq);finalpretty=encode(finalq)
# Statically enumerate every Reader path on the exact predict+trusted-reuse route.
# No helper execution, Admission, Reader or numerical import occurs.
preclaim=ast.parse((P/'preclaim01.py').read_bytes());constants={}
for n in preclaim.body:
 if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['REUSE_ANCHORS','REUSE_EXTERNAL']:constants[n.targets[0].id]=ast.literal_eval(n.value)
paths={};categories={}
def add(path,category,size=None):
 path=Path(path);assert path.is_absolute();length=path.stat().st_size if size is None else size;assert 0<=length<=4194304
 if str(path) in paths:assert paths[str(path)]==length
 paths[str(path)]=length;categories.setdefault(category,set()).add(str(path))
for v in exp['inputs'].values():add(CAP/v['path'],'registered_inputs')
add(CAP/q['registration'],'registration')
edge=load(CAP/exp['inputs']['prediction_source_successor']['path']);assert len(edge['installed'])==195
for n in edge['installed']:add(CAP/n,'target_195')
add(P/'REQUEST_FINAL01.json','final_contract',len(finalraw));add(reviewpath,'final_review',len(reviewraw))
for v in q['proofs'].values():add(v['path'],'three_current_proofs')
add(P/'parent01.py','Parent_source_helpers')
for n in q['helper_hashes']:add(P/n,'Parent_source_helpers')
for v in constants['REUSE_ANCHORS'].values():add(v['path'],'fixed_reuse_anchors')
for n in ['review_proof','recovery_proof','review_machine','review_report']:add(constants['REUSE_EXTERNAL'][n]['path'],'actually_consumed_original_external')
reuse=load(P/'proof_reuse_contract01.json');add(reuse['outcome_recovery']['path'],'original_complete100_recovery');oldrecovery=load(Path(reuse['outcome_recovery']['path']));add(oldrecovery['review']['path'],'original_complete100_recovery')
unique=sum(paths.values());physical=2*unique;prettyphysical=physical+2*(len(finalpretty)-len(finalraw));assert physical<8388608 and prettyphysical<8388608
budget={'schema_version':1,'decision':'accepted-static-complete-Reader-byte-denominator-not-preflight','preclaim':ref(P/'preclaim01.py'),'route':'predict with successor/prediction contexts and fixed trusted proof reuse','unique_paths':len(paths),'unique_bytes_compact_final':unique,'physical_bytes_with_complete_final_reread_compact':physical,'headroom_compact':8388608-physical,'physical_bytes_with_complete_final_reread_pretty':prettyphysical,'headroom_pretty':8388608-prettyphysical,'limit':8388608,'final_contract_compact_bytes':len(finalraw),'final_contract_pretty_bytes':len(finalpretty),'final_review_compact_bytes':len(reviewraw),'path_sizes':paths,'categories':{k:sorted(v) for k,v in categories.items()},'denominator_basis':['Inputs constructor reads all29 role paths (deduplicated only by actual Reader cache path).','Current registration and all195 target source files.','Final contract/review, allthree current proofs, actual Parent caller and everyhelper.','Allseven fixed reused anchors; two external original proof bodies and concrete review machine/report.','Bound proof-reuse contract and original complete100 recovery plus its independent review.','Claim/checkpoint/prior completion paths are registered inputs; no excluded new dependency or state body.','Reader.finish physically rereads every unique cached path once; all such bytes included.'],'exclusions':'Genuine Admission/Git verify_claim and Parent ordinary reads outside this Reader have their original separate limits; this is only the exact Reader.TOTAL8MiB denominator. No Reader/preclaim run was executed. Future path/content changes require recomputation.'}
bp=save('FINAL_METADATA_BUDGET01.json',budget)
check={'schema_version':1,'decision':'accepted-exact-final-contract-pending-envelope-and-preflight','candidate':ref(p),'contract_sha256':contract,'caller_sha256':q['caller_sha256'],'source':q['source'],'identity':q['identity'],'proof_sha256':proofpins,'only_preservation_changes':['status intendedfinal','full_recovery actual10533045 reference'],'all_source_input_runtime_and_helper_fields_unchanged':True,'current_gate_check':ref(D/'CURRENT_GATE_CHECK01.json'),'actual_current_recovery':ref(D/'FULL_CURRENT_RECOVERY_PROOF01.json'),'metadata_budget':bp,'review_schema_fields':sorted(review),'review_bytes':len(reviewraw),'final_envelope_supplement_required':True,'genuine_full_preflight_required':True,'fresh_native_resource_eligibility_required':True,'numerical_entry_release':None,'original_parent_exit':None,'native_PID_history_complete':False,'qualification':'Exact seven-field Parent review accepts this contract binding only. Root must bind the genuine review, directly preserve/recover final request/review/currentproof and all post-capture evidence, then obtain successful exact full Parent preflight and separate finite native entry. No launch before those conditions.'}
cp=save('FINAL_PARENT_CHECK01.json',check);rp=save('FINAL_PARENT_REVIEW01.json',review)
print(json.dumps({'check':cp,'review':rp,'budget':bp,'physical_compact':physical,'physical_pretty':prettyphysical,'headroom_compact':8388608-physical}))
