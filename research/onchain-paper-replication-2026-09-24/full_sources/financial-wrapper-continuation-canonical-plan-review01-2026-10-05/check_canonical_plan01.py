"""Independent exact metadata correction review; no public preclaim/lifecycle."""
from pathlib import Path,PurePosixPath
import ast,copy,hashlib,json,os,sys
H=Path(__file__).resolve().parent;F=H.parent;A=F/'financial-wrapper-continuation-canonical-plan-preparation01-2026-10-05'
C=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-compatibility-root-launch-20261005-01')
sys.path.insert(0,str(F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05'))
from verify_capture01 import Reader,R
rd=Reader();manifest=json.loads(rd.read(A/'MANIFEST01.json','2e9eca8f6b62e19a651be677dd984f9ea45d404b4131b8a4744549c0302ac3fb'))
rows=[]
for row in manifest['members']:
 rd.need(row['kind']=='file' and Path(row['path']).name==row['path'],'finite exact author file namespace')
 raw=rd.read(A/row['path'],row['sha256']);rd.need(len(raw)==row['bytes'] and (A/row['path']).stat().st_mode&0o777==row['mode'],'author typed body/extent/mode');rows.append(row)
scan=R.scan(A);rd.need([r for r in scan['members'] if r['path']!='MANIFEST01.json']==rows and scan['root_mode']==manifest['root_mode'],'complete author typed namespace')
oldprior=rd.read(C/'fixture_inputs/financial_wrapper_continuation01/prior.json','f4a61c48432488c40106b94ae6e829007187f2b0e31ebc781395f5f820ae244e')
oldgate=rd.read(C/'fixture_inputs/financial_wrapper_continuation01/gates.json','c4f33416f952ee5e9a2177fc4455bff51662e9fe6639016a92373ca16ba1d693')
newprior=rd.read(A/'prior.json','b8b4b4f124aebdd5816c8dc0427814139feedd66682f1092bc76c6d25d50b9a9');newgate=rd.read(A/'gates.json','1f96b8efd7fdd468cb9ef87059c5bba026c4aa238f21580ed3ae6e961146e18d')
rd.need(oldprior.count(b'"historical_wrapper_plan"')==1 and newprior==oldprior.replace(b'"historical_wrapper_plan"',b'"historical_plan"'),'complete exact prior literal inverse')
rd.need(oldgate.count(b'"historical_wrapper_plan"')==1 and oldgate.count(R.digest(oldprior).encode())==3,'literal gate replacement denominator')
rd.need(newgate==oldgate.replace(b'"historical_wrapper_plan"',b'"historical_plan"').replace(R.digest(oldprior).encode(),R.digest(newprior).encode()),'complete exact gate literal inverse')
old=json.loads(oldgate);new=json.loads(newgate);prior0=json.loads(oldprior);prior1=json.loads(newprior)
continue_id='financial-wrapper-classification-eager-continue100-compatibility-20261004-01';predict_id='financial-wrapper-classification-eager-predict-compatibility-20261004-01';priorpath='fixture_inputs/financial_wrapper_continuation01/prior.json'
expected=copy.deepcopy(old);e=expected['experiments'][continue_id];planinfo=e['inputs'].pop('historical_wrapper_plan');e['inputs']['historical_plan']=planinfo
priorroles=[k for k,v in e['inputs'].items() if v['path']==priorpath];rd.need(len(priorroles)==1,'one actual registered prior descriptor');e['inputs'][priorroles[0]]['sha256']=R.digest(newprior)
for identity in (continue_id,predict_id):expected['experiments'][identity]['source_files'][priorpath]=R.digest(newprior)
rd.need(expected==new,'only exact two-file semantic correction and three dependent hashes')
rd.need(len(new['experiments'][continue_id]['inputs'])==29 and len(new['experiments'][predict_id]['inputs'])==17,'original input denominators retained')
for identity in set(old['experiments'])-{continue_id,predict_id}:rd.need(old['experiments'][identity]==new['experiments'][identity],'historical experiment definition literal semantic equality')
policyref=e['inputs']['operational_source_compatibility'];policy=json.loads(rd.read(C/policyref['path'],policyref['sha256']));hist=policy['historical']
rd.need(hist['plan_input']=='historical_plan' and prior1['parent_plan_input']==hist['plan_input'],'actual unchanged policy canonical alias')
q=json.loads(rd.read(P/'REQUEST_FINAL01.json','c00ce9b4a9410d6045baf957030431f2ef3851ac84fb43436d0e2e013c9cfe63'))
preclaim=rd.read(P/'preclaim01.py',q['helper_hashes']['preclaim01.py']);tree=ast.parse(preclaim);historical=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_historical');loop=next(n for n in historical.body if isinstance(n,ast.For))
nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name in {'require','sha','digest','relative'}) or (isinstance(n,ast.ClassDef) and n.name in {'Unavailable','Inputs'})]
ns={'Path':Path,'PurePosixPath':PurePosixPath,'hashlib':hashlib,'json':json};exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual pinned preclaim input predicates>','exec'),ns)
probe=ast.FunctionDef(name='alias_probe',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='prior'),ast.arg(arg='hist')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[copy.deepcopy(loop)],decorator_list=[])
exec(compile(ast.fix_missing_locations(ast.Module(body=[probe],type_ignores=[])),'<actual pinned historical alias loop>','exec'),ns)
controls=[]
def refusal(label,fn):
 try:fn()
 except ns['Unavailable'] as error:controls.append({'case':label,'refused':True,'message':str(error)})
 else:raise AssertionError(label+' must refuse')
refusal('actual old prior reproduces public alias failure',lambda:ns['alias_probe'](prior0,hist));ns['alias_probe'](prior1,hist);controls.append({'case':'corrected prior exact actual policy aliases','accepted_component_only':True})
# Independent actual original claim -> job -> plan body linkage, without generic claim verifier or checkpoint decoding.
registered=new['experiments'][continue_id]['inputs'];claim=json.loads(rd.read(C/registered[hist['claim_input']]['path'],hist['claim_sha256']));jobref=claim['inputs']['execution_job'];job=json.loads(rd.read(C/jobref['path'],jobref['sha256']));actualplan=claim['inputs'][job['payload']['plan_input']]
rd.need(planinfo==actualplan and planinfo['sha256']=='15fd8a363806a15b68a6ff23b029847727b5ddbeb9e945454a1f9b5d4c4ac729','exact same original claim-selected path/hash/dataset')
body=rd.read(C/planinfo['path'],planinfo['sha256']);rd.need(len(body)==636,'original immutable plan extent')
component=ns['Inputs'](C,{'historical_plan':planinfo},rd);rd.need(component.exact('historical_plan',C/actualplan['path'])==json.loads(body),'actual pinned Inputs exact path/hash predicate passes')
refusal('old registered alias cannot supply canonical role',lambda:ns['Inputs'](C,{'historical_wrapper_plan':planinfo},rd).raw('historical_plan'))
refusal('wrong original absolute plan path',lambda:component.exact('historical_plan',C/'fixture_inputs/financial_wrapper_continuation01/continue-plan.json'))
wrong=dict(planinfo,sha256='0'*64);refusal('wrong registered original plan hash',lambda:ns['Inputs'](C,{'historical_plan':wrong},rd))
failure=F/'financial-wrapper-continuation-current-preservation-review01-2026-10-05/ACTUAL_CONTINUATION_PUBLIC_PREFLIGHT02_FAILED.json';rawfailure=rd.read(failure);rd.need(json.loads(rawfailure)['error']==controls[0]['message'],'retained actual public failure exact message')
rd.need(not os.path.lexists(C/'research_runs'/continue_id) and not os.path.lexists(P/'attempt'),'no numerical attempt exists at source check')
rd.finish()
result={'schema_version':1,'decision':'ACCEPTED_EXACT_TWO_FILE_CANONICAL_PLAN_CORRECTION_SOURCE_ONLY','author_manifest_sha256':R.digest(R.encode(manifest)) if False else '2e9eca8f6b62e19a651be677dd984f9ea45d404b4131b8a4744549c0302ac3fb','source_before':'664e2ca5fa11d6640ab79f64c5aa222aeb3a9128','candidate_pins':{'prior.json':R.digest(newprior),'gates.json':R.digest(newgate)},'old_pins':{'prior.json':R.digest(oldprior),'gates.json':R.digest(oldgate)},'literal_and_semantic_inverse':True,'unchanged_historical_definitions':2,'continue_roles':29,'predict_roles':17,'actual_original_plan':dict(planinfo,bytes=len(body)),'preclaim_source_sha256':R.digest(preclaim),'actual_public_failure':{'path':str(failure),'sha256':R.digest(rawfailure)},'controls':controls,'full_public_preflight_passed':False,'new_Parent_binding_reviewed':False,'numerical_authority':False,'checks':rd.checks,'read_bytes':rd.total}
R.put(H/'SOURCE_READBACK01.json',result);print(json.dumps(result))
