from pathlib import Path
import ast,hashlib,json,os,subprocess
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';C=F/'heartbeat-root-checkpoint10-2026-10-04';D=Path(__file__).parent;OLD=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-serialized-storage-root-launch-20261005-01');P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-predict-serialized-storage-root-launch-20261005-01');CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');SOURCE='4c66c404fd61ccdbb62c39cd91e16878df74a232'
sha=lambda b:hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes())}
def load(p):return json.loads(p.read_bytes())
def save(n,v):
 with (D/n).open('x') as h:h.write(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n')
 return ref(D/n)
def git(*args):return subprocess.check_output(['git',*args],cwd=CAP)
record=load(C/'SERIALIZED_PREDICTION_SOURCE_GATE_ADOPTION01.json');q=load(P/'REQUEST_SOURCE_BOUND_DRAFT01.json');oldq=load(OLD/'REQUEST_FINAL01.json');draft=load(C/'SERIALIZED_PREDICTION_BOUND_PARENT_DRAFT01.json');identity=draft['identity'];assert q['source']==q['design_source']==record['source']==SOURCE and git('rev-parse','HEAD').decode().strip()==SOURCE
assert git('status','--short','--untracked-files=no')==b'' and load(C/'SERIALIZED_PREDICTION_ADOPT_ROOT_EXIT01.json')['actual_exit']==0
regraw=(CAP/q['registration']).read_bytes();assert sha(regraw)==q['registration_sha256']==record['registration_sha256'];gate=json.loads(regraw);exp=gate['experiments'][identity];expected=draft['gate_literal_insert'][identity]
for role,name in [('prediction_source_successor_review','SOURCE_REVIEW_PROOF01.json'),('prediction_source_successor_recovery','SOURCE_RECOVERY_PROOF01.json')]:
 pin=sha((D/name).read_bytes());expected['inputs'][role]['sha256']=pin;expected['source_files'][expected['inputs'][role]['path']]=pin
assert exp==expected and exp['source_files']==q['source_files'] and {k:v['sha256'] for k,v in exp['inputs'].items()}==q['input_hashes']
oldgate=git('show','6b07c0f841e7d38102814aabb335751fd71fb7f7:'+q['registration']);assert sha(oldgate)==draft['gate_base']['sha256'];text=regraw.decode();start=text.index(json.dumps(identity)+':');_,end=json.JSONDecoder().raw_decode(text,start+len(json.dumps(identity))+1);assert (text[:start-1]+text[end:]).encode()==oldgate
paths=git('ls-tree','-r','--name-only','HEAD').decode().splitlines();assert len(paths)==382 and set(paths)==set(q['source_files'])|{q['registration']}
expected_paths={q['registration']}|{x['path'] for x in draft['source_adoption']['allowed_delta']}|set(draft['new_input_bodies']);changed=set(git('diff','--name-only','6b07c0f841e7d38102814aabb335751fd71fb7f7','HEAD').decode().splitlines());assert changed==expected_paths
for path in changed:
 if path==q['registration']:continue
 assert sha((CAP/path).read_bytes())==q['source_files'][path]
assert len(q['source_files'])==381 and len(q['input_hashes'])==29 and sha((json.dumps(q['source_files'],sort_keys=True,indent=2)+'\n').encode())==record['source_map_sha256']
caller=(P/'parent01.py').read_text();binding=next(ast.literal_eval(n.value) for n in ast.parse(caller).body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='SOURCE_BINDING');assert binding=={k:record[k] for k in ['source','registration_sha256','source_map_sha256','source_count','tracked_count']};assert caller.replace('SOURCE_BINDING='+repr(binding),'SOURCE_BINDING=None').encode()==(F/'financial-wrapper-serialized-prediction-parent-preparation01-2026-10-05/parent01.py').read_bytes();assert sha(caller.encode())==q['caller_sha256']==record['caller_sha256']
for name in ['supervisor01.py','descendants01.py','recovery04.py','owned_io.py','bounded_git01.py','PROTOCOL_PINS01.json']:
 assert (P/name).read_bytes()==(OLD/name).read_bytes() and sha((P/name).read_bytes())==oldq['helper_hashes'][name]==q['helper_hashes'][name]
assert sha((P/'preclaim01.py').read_bytes())=='5f7ae415804cc482dbc5b3538160688d8f4e4fe494abb4696ca047da90a994c3'
reuse=load(P/'proof_reuse_contract01.json');oldreuse=load(OLD/'proof_reuse_contract01.json');oldreuse.update(consumer=identity,current_source=SOURCE);assert reuse==oldreuse
assert q['status']=='DRAFT_NOT_RELEASED' and q['final_review'] is None and all(v is None for v in q['proofs'].values()) and q['expected_phase']=='predict'
assert q['runtime_mapping']==oldq['runtime_mapping'] and q['input_hashes']['runtime_mapping']==oldq['input_hashes']['runtime_mapping']
prior=load(F/'financial-wrapper-serialized-storage-binding-review01-2026-10-05/CUMULATIVE_PROOF01.json');outcome=load(F/'financial-wrapper-serialized-continuation-outcome-review01-2026-10-05/FULL_OUTCOME_RECOVERY_PROOF01.json');claims=prior['claims']+[{'identity':outcome['identity'],'claim_sha256':outcome['claim_sha256'],'terminal_sha256':outcome['terminal_sha256'],'effective_attempt_budget':20,'status':'complete'}]
assert set(p.name for p in (CAP/'research_runs').iterdir())=={x['identity'] for x in claims}|{'.lock'}
for row in claims:
 directory=CAP/'research_runs'/row['identity'];assert (directory/'claim.json').is_file() and (directory/(row['status']+'.json')).is_file() and not (directory/('failed.json' if row['status']=='complete' else 'complete.json')).exists()
assert not os.path.lexists(CAP/'research_runs'/identity) and not os.path.lexists(CAP/'research_artifacts/financial_wrapper_engineering'/identity) and not os.path.lexists(P/'attempt')
check={'schema_version':1,'decision':'accepted-actual-current-source-gate-caller-draft','source':SOURCE,'identity':identity,'registration':q['registration'],'registration_sha256':q['registration_sha256'],'source_map_sha256':record['source_map_sha256'],'tracked':382,'source_pins':381,'installed':195,'inputs':29,'actual_changed_paths':sorted(changed),'all_six_old_gate_definitions_and_bytes_preserved':True,'source_bound_caller_inverse_exact':True,'helper_and_reuse_contract_joins':True,'runtime_mapping_unchanged':True,'claims':claims,'reserved_no_claim':prior['reserved_no_claim'],'accounting':outcome['accounting'],'request':ref(P/'REQUEST_SOURCE_BOUND_DRAFT01.json'),'adoption_record':ref(C/'SERIALIZED_PREDICTION_SOURCE_GATE_ADOPTION01.json'),'adoption_exit':ref(C/'SERIALIZED_PREDICTION_ADOPT_ROOT_EXIT01.json'),'current_recovery':None,'final_preclaim':None,'numerical_authority':False,'qualification':'Changed source/input bytes and complete Git/source-map metadata checked; old192 installed bodies and original runtime251 reused without rescan. Old claims authenticated by accepted cumulative/full outcome basis; actual namespace/status paths rejoined.'}
print(json.dumps(save('CURRENT_GATE_CHECK01.json',check)))
