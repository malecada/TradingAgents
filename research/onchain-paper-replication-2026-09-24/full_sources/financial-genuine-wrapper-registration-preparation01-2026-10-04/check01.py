import copy,json
from pathlib import Path
import generate03 as G
H=Path(__file__).resolve().parent;refs=G.references();pins=G.authenticate(refs);ad,lc,fw=G.actual_api(pins);checks=[]
def ok(n,v):assert v,n;checks.append(n)
def bad(n,fn):
 try:fn()
 except ValueError:checks.append(n);return
 raise AssertionError(n+' accepted')
r=json.loads((H/'generated03/INITIAL_REGISTRATION_DRAFT01.json').read_bytes());p=json.loads((H/'generated03/PREPARATION01.json').read_bytes());ph=json.loads((H/'generated03/PHASES01.json').read_bytes())
ok('10 initial8dependent18unreserved',len(r['experiments'])==10 and len(ph['withheld_dependent_registrations'])==8 and ph['all18_unreserved'])
ok('conditional14complete4failed10cells',ph['conditional_dispositions']=={'COMPLETE':14,'FAILED':4} and ph['ten_proposed_cells']==10)
ok('family budget and history unresolved',all(r['families'][refs['charter']['family']][k] is None for k in ('attempt_budget','prior_attempts','history_reference')))
for name,exp in r['experiments'].items():
 raw=(H/'generated03/bodies'/exp['inputs']['wrapper_plan']['path']).read_bytes();plan=json.loads(raw);G.validate_initial(exp,plan,ad,fw);ok('actual API accepts initial shape '+name,True)
 for role,ref in exp['inputs'].items():ok(name+'/'+role+' portable exact pin',ref['path'].startswith('fixture_inputs/financial_wrapper_registered01/') and G.R.digest((H/'generated03/bodies'/ref['path']).read_bytes())==ref['sha256'])
 exp=copy.deepcopy(exp);exp['inputs']['model']['dataset']='other';bad('wrongdataset '+name,lambda:G.validate_initial(exp,plan,ad,fw))
name=next(iter(r['experiments']));exp=r['experiments'][name];plan=json.loads((H/'generated03/bodies'/exp['inputs']['wrapper_plan']['path']).read_bytes())
for field,value in [('experiment',None),('namespace','../bad'),('phase','fit_forever'),('task','unregistered')]:
 altered=copy.deepcopy(plan);altered[field]=value;bad('malformed plan '+field,lambda:fw.validate_plan(altered))
for field,value in [('path','../secret'),('sha256','xyz')]:
 altered=copy.deepcopy(exp);altered['inputs']['model'][field]=value;bad('malformedinput '+field,lambda:G.validate_initial(altered,plan,ad,fw))
bad('release refuses full generated draft',lambda:G.release(r))
ok('current243 vs prospective269 distinguished',p['current_tracked']==243 and p['prospective_source_files_before_charter_gate']==269 and p['implementation']==194 and p['package']==149)
ok('no fictitious schema class',p['DatasetSchema_class_exists'] is False)
ok('genuine ResearchRun untouched',p['admit_or_start_called'] is False and callable(lc.ResearchRun.start))
(H/'CHECKS01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'status':'passed'},indent=2)+'\n');print(len(checks),'checks passed')
