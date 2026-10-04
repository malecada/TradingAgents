import ast,copy,importlib,json,sys
from pathlib import Path
import generate01 as G
O=Path(__file__).resolve().parent;checks=[]
def check(n,v):assert v,n;checks.append(n)
def refuse(n,f):
 try:f()
 except (ValueError,TypeError,KeyError):checks.append(n)
 else:raise AssertionError(n)
a=G.build();b=G.build();check('deterministic',a==b);family=a['gate']['families'][a['initial_experiment']['family']];check('original family18 prior0 unchanged',family['attempt_budget']==18 and family['prior_attempts']==0 and a['gate']['families']==json.loads(G.read('ORIGINAL_GATE.json'))['families']);check('no extension dependency','cumulative_budget_extension' not in a['initial_experiment'] and 'extension' not in a and a['requires_budget_extension'] is False)
old=json.loads(G.read('ORIGINAL_GATE.json'));check('original10 gate definitions preserved',all(a['gate']['experiments'][n]==v for n,v in old['experiments'].items()));check('original18 definitions preserved',a['original_phases']==json.loads(G.read('ORIGINAL_PHASES.json')));op=a['allocation'];check('19 definitions18 numericalphases',len(set(op['preserved_identity_definitions']))==19 and len(set(op['prospective_numerical_order']))==18 and G.OLD not in op['prospective_numerical_order'] and op['prospective_numerical_order'][0]==G.NEW);check('exact remaining17 order unchanged',op['prospective_numerical_order'][1:]==[x for x in op['original_order']if x!=G.OLD]);check('old outer unclaimed reserved preserved',op['permanently_reserved_original_outer']==G.OLD and not op['old_outer_is_numerical_claim'] and not op['spent_numerical_attempt_refund'] and not op['spent_numerical_attempt_transfer']);check('authority null',all(op[x]is None for x in ('actual_adoption','independent_amendment_review','original_failed_scope_acceptance','original_failed_scope_full_recovery')))
for path,raw in a['bodies'].items():check('eight predecessor body unchanged '+path,raw==(O/'predecessor01/generated02/bodies'/path).read_bytes())
plan=json.loads(a['bodies'][G.PREFIX+'/wrapper_plan.json']);job=json.loads(a['bodies'][G.PREFIX+'/execution_job.json'])
for role in G.ROLE_NAMES:
 e=copy.deepcopy(a['initial_experiment']);e['inputs'].pop(role);refuse('missing role '+role,lambda:G.schema_check(plan,e,job))
 for k,v in [('path','../bad'),('path','/tmp/bad'),('sha256',None),('sha256','wrong'),('dataset','other')]:
  e=copy.deepcopy(a['initial_experiment']);e['inputs'][role][k]=v;refuse('malformed role '+role+'/'+k+str(v),lambda:G.schema_check(plan,e,job))
# Actual original budget helper, metadata branch only: forbidden reader proves no
# extension body or closed-claim snapshot is consulted under unchanged base18.
api=importlib.import_module('tradingagents.research.budget_extensions');path=Path(api.__file__).resolve();q=json.loads(G.read('ORIGINAL_REQUEST.json'));rel=str(path.relative_to(G.CAP));check('genuine budget helper body pinned',G.R.digest(G.R.read(G.CAP,rel))==q['source_files'][rel])
def forbidden_read(ref):raise AssertionError('extension reader must not be called')
check('actual unchanged API returns18 without extension',api.effective_budget(G.CAP,a['gate']['program_id'],G.NEW,a['initial_experiment'],family,[],forbidden_read)==18)
# Exact genuine admission saturation guard on scalar population cardinalities.
source=G.R.read(G.CAP,'tradingagents/research/admission.py');tree=ast.parse(source);fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='admit');guard=next(x for x in fn.body if isinstance(x,ast.If)and any(isinstance(n,ast.Constant)and n.value=='cumulative family attempt budget exhausted'for n in ast.walk(x)));code=compile(ast.Module(body=[guard],type_ignores=[]),'<original finite budget guard>','exec')
for n in range(20):
 ns={'family':family,'relevant':[None]*n,'ceiling':18,'used':n}
 if n>=18:refuse('original18 limit refuses count'+str(n),lambda:exec(code,ns))
 else:exec(code,ns);check('original18 cardinality permits count'+str(n),True)
refuse('release refuses',G.release);check('target absent',not G.os.path.lexists(G.TARGET.parent));check('dependent pins null',len(a['dependent_rebindings'])==2 and all(x['registration']is None and x['actual_claim_pin']is None and x['actual_checkpoint_members']is None for x in a['dependent_rebindings']));check('continuation parent genuine FAILED',a['dependent_rebindings'][0]['expected_checkpoint_parent_disposition'].startswith('genuine accepted FAILED'))
s=(O/'generate01.py').read_text()
for edit in reversed(json.loads((O/'INVERSE02.json').read_bytes())['edits']):check('unique inverse '+str(len(checks)),s.count(edit['new'])==1);s=s.replace(edit['new'],edit['old'])
check('full byte inverse',s==(O/'original_generate01.py').read_text());check('full AST inverse',ast.dump(ast.parse(s),include_attributes=False)==ast.dump(ast.parse((O/'original_generate01.py').read_text()),include_attributes=False));check('no numerical import',not any(x in sys.modules for x in ('numpy','torch','pandas','scipy')));(O/'CHECKS02.json').write_bytes(G.R.encode({'count':len(checks),'checks':checks,'actual_admit_start_calls':0,'scope':'source and scalar cardinality controls; no actual claim creation'}));print(len(checks))
