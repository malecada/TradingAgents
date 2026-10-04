"""Additional deterministic metadata checks; no project imports or admission."""
import ast,copy,hashlib,json,os,re,stat
from pathlib import Path
H=Path(__file__).resolve().parent;D=H/'generated03';B=H.parent
C=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
sha=lambda b:hashlib.sha256(b).hexdigest()
def raw(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<=4194304 and p.resolve()==p
 b=p.read_bytes();t=p.lstat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mode,s.st_mtime_ns,s.st_ctime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mode,t.st_mtime_ns,t.st_ctime_ns)
 return b
def put(n,v):(H/n).write_text(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n')
def enc(v):return (json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
checks=[]
def ck(v,n):assert v,n;checks.append(n)
gatepath='fixture_inputs/financial_wrapper_claimedrun01/gates.json';original=raw(C/gatepath);g=json.loads(original);draft=json.loads(raw(D/'GATE.DRAFT.json'));ref='financial-wrapper-classification-eager-complete100-20261003-01';ex=draft['experiments'][ref]
(H/'CURRENT_GATE_ORIGINAL.json').write_bytes(original)
inverse=copy.deepcopy(draft);inverse['experiments'][ref]=g['experiments'][ref];ck(enc(inverse)==original,'complete literal gate inverse restored original bytes')
ck(set(draft)==set(g) and len(draft['experiments'])==12,'gate exact schema/cardinality')
for k in g:
 if k!='experiments':ck(draft[k]==g[k],'unchanged gate '+k)
for k,v in g['experiments'].items():
 if k!=ref:ck(draft['experiments'][k]==v,'unchanged historical gate entry '+k)
ck(set(k for k in ex if ex[k]!=g['experiments'][ref].get(k))=={'source_files','inputs','cumulative_budget_extension'},'exact three changed experiment fields')
ck(ex['runtime_hashes']==g['experiments'][ref]['runtime_hashes'],'runtime admission pins unchanged')
run=json.loads(raw(D/'draft-inputs/runtime_mapping.json'));ck(len(run['distribution_records'])==251,'all251 original runtime RECORD declarations retained')
ck(len({r['name'] for r in run['distribution_records']})==251,'251 distinct distribution names')
# These are declared metadata, not a runtime environment reinspection.
put('RUNTIME_REQUIREMENTS01.json',{'actual_declared_metadata':run,'record_count':251,'actual_runtime_reverification_required':True,'no_distribution_imports':True,'new_interpreter_adoption':None})
ns={'hashlib':hashlib,'json':json,'re':re};tree=ast.parse(raw(C/'tradingagents/research/budget_extensions.py'));exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'actual_budget','exec'),ns)
claims=[json.loads(raw(p)) for p in sorted((D/'claims').glob('*.claim.json'))]
def bound(v):
 ck(type(v)is dict and set(v)=={'path','sha256'},'budget reference exactshape')
 b=raw(C/v['path']);
 if sha(b)!=v['sha256']:raise ValueError('actual body pin differs')
 return b
family=g['families']['synthetic-financial-wrapper'];ck(family['attempt_budget']==18 and family['prior_attempts']==0,'original base18/prior0')
for part in ('extension','review'):
 body=bound(ex['cumulative_budget_extension'][part]);(H/(part.upper()+'19_ORIGINAL.json')).write_bytes(body)
ext=json.loads((H/'EXTENSION19_ORIGINAL.json').read_bytes());(H/'ALLOCATION19_ORIGINAL.json').write_bytes(bound(ext['allocation']));ck(ext['consumed_before']==1 and len(ext['claims'])==1,'original adopted snapshot remains1 not rewritten2')
refusals=[]
mutations=[('missing',lambda v:v.pop('cumulative_budget_extension')),('empty',lambda v:v.update(cumulative_budget_extension={})),('extra',lambda v:v['cumulative_budget_extension'].update(extra=True)),('wrong-extension-pin',lambda v:v['cumulative_budget_extension']['extension'].update(sha256='0'*64)),('wrong-review-pin',lambda v:v['cumulative_budget_extension']['review'].update(sha256='0'*64))]
for name,mut in mutations:
 v=copy.deepcopy(ex);mut(v)
 try:ns['effective_budget'](C,g['program_id'],ref,v,family,claims,bound)
 except ValueError as err:refusals.append({'case':name,'type':type(err).__name__,'reason':str(err)})
 else:raise AssertionError('missing refusal '+name)
ck(len(refusals)==5,'five actual original budget refusals')
ck(ns['effective_budget'](C,g['program_id'],ref,ex,family,claims,bound)==19,'actual2 claim original extension carryforward returns19')
# Full DAG numerator/denominator retained independently from descriptive output.
charter=json.loads(raw(D/'ORIGINAL_CHARTER02.json'));phases=charter['phases'];ck(len(phases)==18,'all18 original phases')
ck(sum(p['training_fit_cell_calls'] for p in phases)==12,'12 original fit invocations')
ck(sum(p['expected_lifecycle_status']=='COMPLETE' for p in phases)==14,'14 prospective completes')
ck(sum(p['expected_lifecycle_status']=='FAILED' for p in phases)==4,'4 planned failure slots')
ck(sum(p['optimizer_updates_if_successful'] for p in phases)==804,'800 training plus4 agreement updates')
ck(sum(p['phase'] in ('complete100','continue100') for p in phases)==8,'8 full100 completed fits')
ck(len(set(p['proposed_cell'] for p in phases))==10,'10 exact original cells')
ck(phases[1]['proposed_identity']==ref and phases[1]['proposed_dependencies']==[],'original slot2 independent reference')
ck(phases[2]['dependencies']==['classification/eager/interrupt1','classification/eager/complete100'],'continuation requires both genuine outcomes')
# Authenticate existing different-author opaque outcome evidence, never rerun it.
o=B/'financial-wrapper-claimedrun-native-outcome-review01-2026-10-04';ev=[]
for name in ('MANIFEST01.json','MACHINE01.json','REPORT01.md'):
 b=raw(o/name);(H/('OUTCOME_'+name)).write_bytes(b);ev.append({'path':str(o/name),'bytes':len(b),'sha256':sha(b)})
ck(ev[0]['sha256']=='0f27670fa421d15fea717ef3326e92fce6f2cd37c29430686c4d399057bffa9e','exact actual outcome review seal')
put('CHECKS04.json',{'checks':len(checks),'names':checks,'budget_refusals':refusals,'actual_outcome_evidence':ev,'no_runtime_import_or_claim':True})
print(json.dumps({'checks':len(checks),'refusals':len(refusals),'runtime_records':len(run['distribution_records']),'inverse':'literal complete gate bytes'}))
