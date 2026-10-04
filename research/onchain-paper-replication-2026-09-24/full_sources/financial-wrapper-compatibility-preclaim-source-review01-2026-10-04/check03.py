import copy,hashlib,importlib.util,json,os,sys
from pathlib import Path
P=Path(__file__).absolute().parent;B=P.parent;A=B/'financial-wrapper-compatibility-preclaim-source01-2026-10-04';S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
os.environ['GIT_NO_LAZY_FETCH']='1';os.environ['GIT_NO_REPLACE_OBJECTS']='1'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=load('preclaim_review03',P/'CANDIDATE_preclaim01.py');h=load('actual_compatibility_metadata',S/m.HELPER);f=load('actual_fixture_metadata',S/m.PREFIX/'financial_wrapper_fixture.py');v=load('actual_verify_metadata',S/'tradingagents/research/verify.py')
pol=json.loads((A/'POLICY01.json').read_bytes());roles=json.loads((A/'HISTORICAL_ROLE_MAP01.json').read_bytes());reg={k:{n:r[n] for n in ('path','sha256','dataset')} for k,r in roles.items()}
old=json.loads((S/reg['historical_claim']['path']).read_bytes());plan=json.loads((S/reg['historical_plan']['path']).read_bytes());cell=m.sha(plan['cell_id'].encode());fit=S/'research_artifacts/onchain_fit_cells'/cell/h.HISTORICAL_ID
more={'fit_claim_input':('old_fit_claim',fit/'claim.json'),'failed_fit_input':('old_failed_fit',fit/'failed.json'),'diagnostic_input':('old_diagnostic',S/'research_artifacts/financial_wrapper_engineering'/h.HISTORICAL_ID/'interrupted-checkpoint.json'),'schedule_input':('old_schedule',fit/'schedule.json')}
for key,(role,p) in more.items():reg[role]={'path':p.relative_to(S).as_posix(),'sha256':m.sha(p.read_bytes()),'dataset':'synthetic'}
cp=S/reg['historical_checkpoint']['path'];manifest=json.loads(cp.read_bytes());state=cp.parent/'state.pt';reg['old_state']={'path':state.relative_to(S).as_posix(),'sha256':manifest['members']['state.pt']['sha256'],'dataset':'synthetic'};reg['training']=old['inputs'][plan['training_input']]
prior={'parent':h.HISTORICAL_ID,'claim_input':'historical_claim','terminal_input':'historical_failed','checkpoint_input':'historical_checkpoint','completion_input':None,'provenance':manifest['provenance'],'parent_job_input':'historical_execution_job','parent_plan_input':'historical_plan',**{k:x[0] for k,x in more.items()}}
current=dict(plan,phase='continue100',experiment=m.FIXED['continue100']['experiment'],namespace=m.FIXED['continue100']['experiment'])
provenance=dict(manifest['provenance'],source_commit='7b056a574e3e7b3c7ba209a39ee6a615e649d60c',source_hashes=sorted(set(pol['target']['installed'].values())))
r=m.Reader();inputs=m.Inputs(S,reg,r);m._historical(inputs,prior,pol,current,provenance,S,h,f,v,r);r.finish()
checks=['actual-original-verify_claim-historical-allmetadata-pass']
for key,value in [('parent','unrelated'),('completion_input','invented'),('provenance',dict(manifest['provenance'],source_commit='0'*40)),('parent_plan_input','historical_execution_job')]:
 changed=dict(prior);changed[key]=value
 try:m._historical(inputs,changed,pol,current,provenance,S,h,f,v,m.Reader())
 except (ValueError,KeyError,TypeError):checks.append('refused-history-'+key)
 else:raise AssertionError(key)
for phase in ('complete100','continue100'):
 try:m._complete(inputs,prior,pol,phase,provenance,S,h,v,m.Reader())
 except (ValueError,KeyError,TypeError,FileNotFoundError):checks.append('absent-genuine-COMPLETE-refused-'+phase)
 else:raise AssertionError(phase)
assert not any(n.split('.')[0] in ('numpy','torch','scipy','pandas') for n in sys.modules)
checks.append('no-numerical-imports')
(P/'HISTORICAL_READBACK01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'genuine_Admission_Run_Owner_constructed':False,'verify_claim_actual_original_only':True,'no_checkpoint_decode':True,'own_reader_bytes':r.total,'original_verify_claim_reads_outside_reader':True,'old_claim_sha256':m.sha((S/reg['historical_claim']['path']).read_bytes()),'old_state_sha256':m.sha(state.read_bytes()),'future_COMPLETE_success_not_tested':True},indent=2)+'\n')
print(json.dumps({'checks':len(checks),'status':'actual-historical-metadata-only-pass'}))
