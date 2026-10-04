import ast,copy,json,sys
from pathlib import Path
import generate01 as G
checks=[];O=Path(__file__).resolve().parent

def check(n,v):assert v,n;checks.append(n)
def refuse(n,f):
 try:f()
 except (ValueError,TypeError,KeyError) as e:checks.append(n)
 else:raise AssertionError(n)
a=G.build();b=G.build();check('deterministic metadata and eight body bytes',a==b);check('old10 definitions unchanged',all(a['gate']['experiments'][n]==v for n,v in json.loads(G.read('ORIGINAL_GATE.json'))['experiments'].items()));check('old18 slot definitions unchanged',a['original_phases']==json.loads(G.read('ORIGINAL_PHASES.json')));check('11gate19slots298sourcepins',len(a['gate']['experiments'])==11 and a['total_preserved_plus_new_slots']==19 and len(a['initial_experiment']['source_files'])==298)
for role in ('environment','model','runtime_mapping','synthetic_recipe','training'):check('unchanged '+role,a['bodies'][G.PREFIX+'/'+role+'.json']==G.read('original_'+role+'.json'))
plan=json.loads(a['bodies'][G.PREFIX+'/wrapper_plan.json']);job=json.loads(a['bodies'][G.PREFIX+'/execution_job.json']);oldplan=json.loads(G.read('original_wrapper_plan.json'));p=dict(plan);p.update(experiment=G.OLD,namespace=G.OLD);check('plan exact two-field inverse',p==oldplan);j=copy.deepcopy(job);j['resources']['disk_paths']=[str(G.CAP)];j['resources']['storage_budget']['root']=str(G.CAP);check('job exact two-path inverse',j==json.loads(G.read('original_execution_job.json')));c=json.loads(a['bodies'][G.PREFIX+'/source_closure.json']);oldc=json.loads(G.read('original_source_closure.json'));c['installed'][G.SOURCE_PATH]=oldc['installed'][G.SOURCE_PATH];check('source closure exact one-body inverse',c==oldc)
for role in G.ROLE_NAMES:
 e=copy.deepcopy(a['initial_experiment']);e['inputs'].pop(role);refuse('missing role '+role,lambda:G.schema_check(plan,e,job))
 for field,value in [('path','/tmp/wrong'),('path','../wrong'),('sha256',None),('sha256','g'*64),('dataset','other')]:
  e=copy.deepcopy(a['initial_experiment']);e['inputs'][role][field]=value;refuse('role field '+role+'/'+field+'/'+str(value),lambda:G.schema_check(plan,e,job))
for key,value in [('phase','continue100'),('prior_input','invented'),('namespace','../bad')]:
 p=copy.deepcopy(plan);p[key]=value;refuse('invalid initial plan '+key,lambda:G.schema_check(p,a['initial_experiment'],job))
refuse('release no authority',G.release)
# Exact original empty-snapshot guard, no accepted review or claim fabricated.
source=G.R.read(G.CAP,'tradingagents/research/budget_extensions.py');tree=ast.parse(source);fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='effective_budget');node=next(x for x in fn.body if isinstance(x,ast.If)and any(isinstance(v,ast.Constant)and v.value=='budget extension closed claim snapshot required'for v in ast.walk(x)));code=compile(ast.Module(body=[node],type_ignores=[]),'<actual empty-claim extension guard>','exec');refuse('actual19extension refuses genuine-zero-snapshot',lambda:exec(code,{'snapshot':a['extension']['claims']}));check('proposed19 base18 prior0 preserved',a['extension']['cumulative_ceiling']==19 and a['extension']['consumed_before']==0 and a['extension']['base_family']['attempt_budget']==18 and a['extension']['claims']==[])
check('dependent actual pins remain unknown',len(a['dependent_rebindings'])==2 and all(x['registration']is None and x['actual_checkpoint_members']is None and x['actual_claim_pin']is None for x in a['dependent_rebindings']));check('target remains absent',not G.os.path.lexists(G.TARGET.parent));check('no numerical imports',not any(n in sys.modules for n in ('numpy','torch','pandas','scipy')))
G.write(O/'generated02');(O/'CHECKS01.json').write_bytes(G.R.encode({'count':len(checks),'names':checks,'exact_budget_source_sha256':G.R.digest(source),'no_real_admission_or_claim':True}));print(len(checks))
