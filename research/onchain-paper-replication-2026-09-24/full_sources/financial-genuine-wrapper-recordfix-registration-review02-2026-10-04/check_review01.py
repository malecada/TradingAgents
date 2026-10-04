"""Independent draft schema/DAG/budget review; never admit/start/write gate."""
import ast,copy,hashlib,importlib,importlib.util,json,os,stat,sys
from pathlib import Path
D=Path(__file__).resolve().parent;S=D/'source';P=D.parent/'financial-genuine-wrapper-recordfix-registration-preparation02-2026-10-04';W=Path('/home/malecada/master_thesis');sys.path.insert(0,str(S));spec=importlib.util.spec_from_file_location('independent_registration',S/'generate01.py');G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G);checks=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ok(n,v,detail=None):
 if not v:raise AssertionError(n)
 checks.append({'name':n,'detail':detail})
def refuse(n,f):
 try:f()
 except (ValueError,TypeError,KeyError,OSError) as e:ok(n,True,{'error':type(e).__name__,'message':str(e)});return
 raise AssertionError('accepted '+n)
def dump(n,o):(D/n).write_text(json.dumps(o,sort_keys=True,indent=2)+'\n')
ok('actual source pin',sha(S/'generate01.py')=='062a66283351fb6712c61e5e6b6c0f6277ff2fb0a03d933e8fec45bcfd36aedb');ok('actual candidate manifest',sha(P/'MANIFEST02.json')=='08af38d682eaf9af0a79be8ed6347be4516d6d87f47ecaa8213ffba6bc4fdafb')
m=json.loads((P/'MANIFEST02.json').read_text());rows=m.get('entries',m.get('members'));ok('complete candidate membership',{p.relative_to(P).as_posix() for p in P.rglob('*') if p!=P/'MANIFEST02.json'}=={r['path'] for r in rows})
for r in rows:
 p=P/r['path'];s=p.lstat();kind=r.get('type',r.get('kind'));good=stat.S_IMODE(s.st_mode)==r['mode']
 if kind=='file':good=good and stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and sha(p)==r['sha256'] and ('nlink' not in r or s.st_nlink==r['nlink'])
 elif kind=='directory':good=good and stat.S_ISDIR(s.st_mode)
 else:good=False
 ok('manifest '+r['path'],good)
origins=json.loads((S/'ORIGINS01.json').read_text())
for n,ref in origins.items():
 actual=Path(ref['path']);actual=actual if actual.is_absolute() else W/actual;ok('actual origin '+n,sha(S/n)==ref['sha256']==sha(actual) and actual.stat().st_size==ref['bytes'])
q=json.loads((S/'ORIGINAL_REQUEST.json').read_text());original=json.loads((S/'ORIGINAL_GATE.json').read_text());historical=json.loads((S/'ORIGINAL_PHASES.json').read_text());oldorder=json.loads((S/'ORIGINAL_ORDER.json').read_text())['complete18_topological_order']
value=G.build();again=G.build();ok('actual deterministic pure build',value==again);ok('target unit remains absent',not os.path.lexists(G.TARGET.parent));ok('fresh same isolation sibling',G.TARGET.parent.parent==G.CAP.parent.parent and G.TARGET!=G.CAP and G.TARGET.resolve()==G.TARGET)
s=(S/'generate01.py').read_text()
for e in reversed(json.loads((S/'INVERSE02.json').read_text())['edits']):ok('unique inverse seam '+str(len(checks)),s.count(e['new'])==1);s=s.replace(e['new'],e['old'])
ok('full byte inverse',s==(S/'original_generate01.py').read_text());ok('full AST inverse',ast.dump(ast.parse(s))==ast.dump(ast.parse((S/'original_generate01.py').read_text())))
# Match every actual frozen output byte against fresh deterministic construction.
for key,name in [('gate','GATE_DRAFT.json'),('allocation','OPERATIONAL_AMENDMENT_DRAFT.json'),('dependent_rebindings','DEPENDENT_REBINDINGS_DRAFT.json'),('original_phases','ORIGINAL_PHASES_PRESERVED.json')]:ok('generated exact '+name,G.R.encode(value[key])==(S/'generated01'/name).read_bytes())
for rel,raw in value['bodies'].items():
 ok('generated role body '+rel,raw==(S/'generated01/bodies'/rel).read_bytes());ok('predecessor role body unchanged '+rel,raw==(S/'predecessor01/generated02/bodies'/rel).read_bytes())
metadata={k:v for k,v in value.items() if k not in ('bodies','gate','allocation','dependent_rebindings','original_phases')};metadata['role_body_pins']={p:G.R.digest(raw) for p,raw in sorted(value['bodies'].items())};ok('generated preparation exact',G.R.encode(metadata)==(S/'generated01/PREPARATION01.json').read_bytes())
# Independently reconstruct exact permitted role deltas from actual originals.
roles={role:json.loads(value['bodies'][G.PREFIX+'/'+role+'.json']) for role in G.ROLE_NAMES}
for role in ('environment','model','runtime_mapping','synthetic_recipe','training'):ok('original immutable role '+role,value['bodies'][G.PREFIX+'/'+role+'.json']==(S/('original_'+role+'.json')).read_bytes())
plan0=json.loads((S/'original_wrapper_plan.json').read_text());expectedplan={**plan0,'experiment':G.NEW,'namespace':G.NEW};ok('only plan identity namespace changed',roles['wrapper_plan']==expectedplan)
job0=json.loads((S/'original_execution_job.json').read_text());expectedjob=copy.deepcopy(job0);expectedjob['resources']['disk_paths']=[str(G.TARGET)];expectedjob['resources']['storage_budget']['root']=str(G.TARGET);ok('only owned job paths changed',roles['execution_job']==expectedjob)
closure0=json.loads((S/'original_source_closure.json').read_text());expectedclosure=copy.deepcopy(closure0);expectedclosure['installed'][G.SOURCE_PATH]=G.CORRECTION;ok('only corrected runtime body closure pin',roles['source_closure']==expectedclosure and len(expectedclosure['installed'])==194 and sum(x.startswith('tradingagents/') for x in expectedclosure['installed'])==149)
priorreview=D.parent/'financial-genuine-wrapper-runtime-record-review01-2026-10-04';ok('independent runtime correction accepted source pin',json.loads((priorreview/'REVIEW01.json').read_text())['candidate_source_sha256']==G.CORRECTION and sha(priorreview/'MANIFEST01.json')=='0f831ce02ebd367337a1d33078b6b781cc70379641494416906388c8fd2f93a7')
expectedsource={**q['source_files'],q['registration']:q['registration_sha256'],G.SOURCE_PATH:G.CORRECTION,**{p:G.R.digest(raw) for p,raw in value['bodies'].items()}};exp=value['initial_experiment'];ok('exact298 finite source role map',exp['source_files']==expectedsource and len(expectedsource)==298);ok('old gate hash preserved inside source map',expectedsource[q['registration']]==sha(S/'ORIGINAL_GATE.json'))
# No new gate or charter hash self-cycle is present; authority additions pending.
ok('closure no metadata self hash cycle',G.PREFIX+'/source_closure.json' not in roles['source_closure']['installed']);ok('no new gate self hash',not any('recordfix01' in path and path.endswith('gates.json') for path in expectedsource));ok('charter unresolved',exp['charter']=={'path':G.PREFIX+'/CHARTER_PENDING.json','sha256':None} and exp['charter']['path'] not in expectedsource)
newgate=value['gate'];ok('exact original ten definitions preserved',len(original['experiments'])==10 and all(newgate['experiments'][k]==v for k,v in original['experiments'].items()) and set(newgate['experiments'])==set(original['experiments'])|{G.NEW});ok('all other original gate fields unchanged',{k:v for k,v in newgate.items() if k!='experiments'}=={k:v for k,v in original.items() if k!='experiments'});ok('old18 slots preserved',value['original_phases']==historical)
family=newgate['families'][exp['family']];op=value['allocation'];ok('numerical18/prior0 unchanged',family==original['families'][exp['family']] and family['attempt_budget']==18 and family['prior_attempts']==0 and value['numerical_claims_before']==0);ok('19 definitions distinct from18 prospective',len(op['preserved_identity_definitions'])==len(set(op['preserved_identity_definitions']))==19 and len(op['prospective_numerical_order'])==len(set(op['prospective_numerical_order']))==18);ok('precise one unclaimed operational substitution',op['preserved_identity_definitions']==oldorder+[G.NEW] and op['prospective_numerical_order']==[G.NEW]+[x for x in oldorder if x!=G.OLD]);ok('no numerical refund/transfer',op['old_outer_is_numerical_claim'] is False and op['spent_numerical_attempt_refund'] is False and op['spent_numerical_attempt_transfer'] is False)
# Reconstruct the full18-node prospective DAG including withheld dependencies.
order=op['prospective_numerical_order'];position={name:i for i,name in enumerate(order)};dag=[]
for slot in historical['slots']:
 oldid=slot['proposed_plan']['experiment'];ident=G.NEW if oldid==G.OLD else oldid;deps=[G.NEW if x==G.OLD else x for x in slot['dependencies']];ok('topological phase '+ident,all(x in position and position[x]<position[ident] for x in deps));dag.append({'identity':ident,'phase':slot['proposed_plan']['phase'],'dependencies':deps,'expected_status':slot['expected_disposition_if_contract_met']})
ok('retained conditional14complete4failed denominator',sum(r['expected_status']=='COMPLETE' for r in dag)==14 and sum(r['expected_status']=='FAILED' for r in dag)==4)
deps=value['dependent_rebindings'];ok('exact two downstream proposals',len(deps)==2)
for row in deps:
 slot=next(s for s in historical['slots'] if s['proposed_plan']['experiment']==row['identity']);ok('original downstream slot immutable '+row['identity'],row['original_unregistered_draft']==slot);ok('only predecessor substitution '+row['identity'],row['proposed_dependencies']==[G.NEW if x==G.OLD else x for x in slot['dependencies']]);ok('dependent actualauthority null '+row['identity'],all(row[k] is None for k in ('actual_prior_input','actual_reference_input','actual_claim_pin','actual_checkpoint_members','independent_outcome_acceptance','external_recovery','registration')))
cont=next(x for x in deps if x['original_unregistered_draft']['proposed_plan']['phase']=='continue100');pred=next(x for x in deps if x['original_unregistered_draft']['proposed_plan']['phase']=='predict');ok('continuation requires accepted FAILED parent plus separate100 reference',cont['proposed_dependencies'][0]==G.NEW and len(cont['proposed_dependencies'])==2 and 'complete100' in cont['proposed_dependencies'][1] and cont['expected_checkpoint_parent_disposition']=='genuine accepted FAILED planned-interruption checkpoint');ok('predict requires COMPLETE100 continuation',pred['proposed_dependencies']==[cont['identity']] and pred['expected_checkpoint_parent_disposition']=='genuine accepted COMPLETE100 continuation checkpoint')
# Actual pinned metadata-only API; no admit, start or constructed Run objects.
ad=importlib.import_module('tradingagents.research.admission');bud=importlib.import_module('tradingagents.research.budget_extensions');jobapi=importlib.import_module('tradingagents.research.onchain_replication.job')
for module in (ad,bud,jobapi):
 path=Path(module.__file__).resolve();rel=path.relative_to(G.CAP).as_posix();ok('genuine API origin '+rel,sha(path)==q['source_files'][rel])
jobapi.job_schema(roles['execution_job']);ok('original actual job_schema accepts',True)
def forbidden_read(ref):raise AssertionError('no extension lookup allowed')
ok('actual base18 no extension branch',bud.effective_budget(G.CAP,newgate['program_id'],G.NEW,exp,family,[],forbidden_read)==18);ok('no extension metadata/schema change','cumulative_budget_extension' not in exp and value['requires_budget_extension'] is False)
adfn=next(x for x in ast.parse(Path(ad.__file__).read_text()).body if isinstance(x,ast.FunctionDef) and x.name=='admit');guard=next(x for x in adfn.body if isinstance(x,ast.If) and any(isinstance(y,ast.Constant) and y.value=='cumulative family attempt budget exhausted' for y in ast.walk(x)));code=compile(ast.Module(body=[guard],type_ignores=[]),'<exact-original-ceiling-guard>','exec')
for used in (0,1,9,17,18,19,100):
 run=lambda used=used:exec(code,{'family':family,'used':used,'ceiling':18})
 if used>=18:refuse('genuine ceiling refuses '+str(used),run)
 else:run();ok('genuine scalar count permitted '+str(used),True)
for role in sorted(G.ROLE_NAMES):
 bad=copy.deepcopy(exp);bad['inputs'].pop(role);refuse('missing role '+role,lambda bad=bad:G.schema_check(roles['wrapper_plan'],bad,roles['execution_job']))
 for field,v in [('path','../escape'),('path','/absolute'),('sha256',None),('sha256','A'*64),('dataset','wrong')]:
  bad=copy.deepcopy(exp);bad['inputs'][role][field]=v;refuse('invalid role '+role+'/'+field+str(v),lambda bad=bad:G.schema_check(roles['wrapper_plan'],bad,roles['execution_job']))
refuse('release remains refused',G.release);ok('future Root source/release all withheld',value['release'] is False and value['paper_financial_credit']==0 and all(value[k] is None for k in ('future_source_commit','future_design_source','future_registration_commit','charter','operational_amendment_review','complete_original_failed_recovery','caller','native_capacity')))
ok('no actual claims manufactured',not any(n in sys.modules for n in ('numpy','torch','pandas','scipy')));ok('target still absent',not os.path.lexists(G.TARGET.parent))
dump('DAG01.json',{'prospective_order':order,'nodes':dag,'operational_identity_count':19,'numerical_ceiling':18,'observed_claim_count_qualification':'Zero numerical claims is the explicitly recorded current premise from Root failed-predispatch evidence; this source review does not replace actual closure/ledger review or reobserve it. Genuine admission must recount immediately before adoption.','authority':None});dump('CHECKS01.json',{'count':len(checks),'checks':checks,'source_sha256':sha(S/'generate01.py'),'manifest_sha256':sha(P/'MANIFEST02.json'),'status':'ACCEPTED_SOURCE_ONLY_DRAFT_OPERATIONAL_ACCOUNTING','actual_admit_or_start_calls':0,'source_adoption':False,'numerical_imports':0,'authority':None});print(json.dumps({'checks':len(checks),'verdict':'ACCEPTED_SOURCE_ONLY_DRAFT_OPERATIONAL_ACCOUNTING'}))
