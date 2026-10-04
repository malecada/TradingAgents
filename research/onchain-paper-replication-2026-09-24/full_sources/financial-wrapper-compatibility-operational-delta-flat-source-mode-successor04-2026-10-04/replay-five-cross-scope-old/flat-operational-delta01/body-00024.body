from pathlib import Path
import json,hashlib,datetime,ast
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'financial-wrapper-compatibility-root-policy01-2026-10-04';D.mkdir()
S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');P=F/'financial-wrapper-operational-provenance-compatibility-preparation02-2026-10-04';I=F/'financial-wrapper-compatibility-root-integration01-2026-10-04'
def h(b):return hashlib.sha256(b).hexdigest()
def J(p):return json.loads(p.read_bytes())
def put(n,o):
 with (D/n).open('x') as f:json.dump(o,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
q=J(P/'POLICY_DRAFT01.json');old=J(I/'OLD_IMPLEMENTATION194.json');target=J(I/'TARGET_IMPLEMENTATION195.json');id=q['historical']['identity'];rd=S/'research_runs'/id;c=J(rd/'claim.json');cp=next((S/'research_artifacts/onchain_fit_cells').glob('*/'+id+'/checkpoints/*/manifest.json'));m=J(cp)
assert h(cp.read_bytes())==q['historical']['checkpoint_sha256'];assert m['provenance']['source_commit']==q['historical']['source']
assert m['provenance']['source_hashes']==sorted(set(old.values()))
for p,pin in target.items():assert h((S/p).read_bytes())==pin
q['historical']['provenance']=m['provenance'];aliases={'closure_input':'historical_source_closure','claim_input':'historical_claim','failed_input':'historical_failed','checkpoint_input':'historical_checkpoint','plan_input':'historical_plan','job_input':'historical_execution_job'};q['historical'].update(aliases);q['target']['closure_input']='source_closure'
q['consumers']={'complete100':{'experiment':'financial-wrapper-classification-eager-complete100-compatibility-20261004-01','cell_id':'financial-wrapper-classification-eager-reference-compatibility-20261004-01'},'continue100':{'experiment':'financial-wrapper-classification-eager-continue100-compatibility-20261004-01','cell_id':m['provenance']['cell_id']},'predict':{'experiment':'financial-wrapper-classification-eager-predict-compatibility-20261004-01','cell_id':m['provenance']['cell_id']}}
for v in q['consumers'].values():assert not (S/'research_runs'/v['experiment']).exists()
assert q['historical']['installed']==old and q['target']['installed']==target
put('POLICY01.json',q)
closure=J(S/c['inputs']['source_closure']['path']);assert closure['installed']==old;closure['installed']=target;put('SOURCE_CLOSURE01.json',closure)
roles={aliases['claim_input']:rd/'claim.json',aliases['failed_input']:rd/'failed.json',aliases['checkpoint_input']:cp,aliases['closure_input']:S/c['inputs']['source_closure']['path'],aliases['plan_input']:S/c['inputs']['wrapper_plan']['path'],aliases['job_input']:S/c['inputs']['execution_job']['path']}
# Independent literal historical source bodies remain at their original paths.
rows={role:{'dataset':'synthetic','path':path.relative_to(S).as_posix(),'sha256':h(path.read_bytes()),'bytes':path.stat().st_size} for role,path in roles.items()}
for name,member in m['members'].items() if isinstance(m['members'],dict) else []:print(name,member)
put('HISTORICAL_ROLE_MAP01.json',rows)
put('SOURCE_POLICY_BINDING01.json',{'schema_version':1,'status':'CONCRETE_POLICY_NOT_INSTALLED_NOT_NUMERICALLY_RELEASED','timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'genuine_root':str(S),'actual_source_design':'7b056a574e3e7b3c7ba209a39ee6a615e649d60c','historical_source':q['historical']['source'],'policy_sha256':h((D/'POLICY01.json').read_bytes()),'helper_sha256':target['tradingagents/research/onchain_replication/operational_source_compatibility.py'],'old_map_sha256':h(json.dumps(old,sort_keys=True,separators=(',',':')).encode()),'target_map_sha256':h(json.dumps(target,sort_keys=True,separators=(',',':')).encode()),'closure_sha256':h((D/'SOURCE_CLOSURE01.json').read_bytes()),'consumers':q['consumers'],'actual_review_proof':None,'actual_recovery_proof':None,'gate':None,'source_adoption_review_pending':True,'budget20_adoption':None,'numerical_release':None,'qualifications':['Historical opaque checkpoint bytes, original absolute paths and FAILED Run identity remain unchanged.','Explicit source map edge is only operational metadata; numerical/scientific code and100epochs/seed11/batch16/recipe/tolerances unchanged.','All three future consumer identities are distinct and unused; continuation retains original cell for checkpoint provenance.','Proof labels cannot replace independently authenticated review and actual recovery; all proof fields are currently absent.']})
print(h((D/'POLICY01.json').read_bytes()))
