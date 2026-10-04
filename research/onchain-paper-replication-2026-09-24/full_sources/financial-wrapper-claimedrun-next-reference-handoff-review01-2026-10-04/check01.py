import ast,copy,hashlib,json,os,stat,subprocess,re
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-wrapper-claimedrun-next-reference-handoff01-2026-10-04';C=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');checks=[];sha=lambda b:hashlib.sha256(b).hexdigest();enc=lambda j:(json.dumps(j,sort_keys=True,indent=2)+'\n').encode()
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
m=(A/'MANIFEST02.json').read_bytes();ok(sha(m)=='59503b5958014a83ae27d488d4c632e720f481aeae8b95fc900f2c520aaca9e3','final seal');rows=json.loads(m)['members'];ok({p.relative_to(A).as_posix() for p in A.rglob('*') if p!=A/'MANIFEST02.json'}=={x['path'] for x in rows}-{'.'},'complete actual seal membership')
for x in rows:
 p=A/x['path'];s=p.lstat();mode=int(x['mode'],8) if isinstance(x['mode'],str) else x['mode'];ok(stat.S_IMODE(s.st_mode)==mode,'author literal mode')
 if x['kind']=='file':ok(stat.S_ISREG(s.st_mode) and s.st_size==x['bytes'] and sha(p.read_bytes())==x['sha256'],'author full body')
 else:ok(stat.S_ISDIR(s.st_mode),'author directory')
D=A/'generated03';readback=json.loads((D/'SOURCE339_READBACK.json').read_bytes());records=readback['git_records'];ok(len(records)==339,'source339');env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL='',GIT_NO_REPLACE_OBJECTS='1');p=subprocess.run(['git','-C',str(C),'ls-tree','-r','-z','0a2e7639b42b9423b90743feadcda4078aa21816'],env=env,capture_output=True,timeout=10);ok(p.returncode==0 and not p.stderr,'offline current commit tree');objects={}
for entry in p.stdout.rstrip(b'\0').split(b'\0'):
 left,right=entry.split(b'\t');objects[right.decode()]=left.decode().split()
ok(set(objects)=={x['path'] for x in records},'entire339membership')
for x in records:
 p=C/x['path'];s=p.lstat();b=p.read_bytes();ok(stat.S_IMODE(s.st_mode)==x['actual_mode'] and len(b)==x['bytes'] and sha(b)==x['sha256'],'actual source body/mode');ok(objects[x['path']]==[x['git_mode'],'blob',x['oid']] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['oid'],'genuine Git join')
g=json.loads((A/'CURRENT_GATE_ORIGINAL.json').read_bytes());draft=json.loads((D/'GATE.DRAFT.json').read_bytes());ref='financial-wrapper-classification-eager-complete100-20261003-01';e=draft['experiments'][ref];inverse=copy.deepcopy(draft);inverse['experiments'][ref]=g['experiments'][ref];ok(enc(inverse)==(C/'fixture_inputs/financial_wrapper_claimedrun01/gates.json').read_bytes(),'entire gate inverse');ok(len(draft['experiments'])==12 and set(k for k in e if e[k]!=g['experiments'][ref].get(k))=={'source_files','inputs','cumulative_budget_extension'},'only exact reference three fields changed')
ok(len(e['source_files'])==338,'338 excluding gate');ok(e['source_files']=={x['path']:x['sha256'] for x in records if x['path']!='fixture_inputs/financial_wrapper_claimedrun01/gates.json'},'exact current pin closure')
for role,row in e['inputs'].items():
 b=(C/row['path']).read_bytes();ok(sha(b)==row['sha256'] and b==(D/'draft-inputs'/(role+'.json')).read_bytes(),'actual input '+role)
ok(len(e['inputs'])==8,'8 roles');cl=json.loads((D/'draft-inputs/source_closure.json').read_bytes())['installed'];ok(len(cl)==194 and sum(k.startswith('tradingagents/') for k in cl)==149,'194149 closure')
for name,pin in cl.items():ok(sha((C/name).read_bytes())==pin,'closure body')
plan=json.loads((D/'draft-inputs/wrapper_plan.json').read_bytes());ok(sha((D/'draft-inputs/wrapper_plan.json').read_bytes())=='dc5673500ff5282fe9d8769a1deca65692fc59548116fec1c7ea050419853ff5','original plan')
# Actual genuine budget pure functions, no admission or synthetic handles.
ns={'hashlib':hashlib,'json':json,'re':re};tree=ast.parse((C/'tradingagents/research/budget_extensions.py').read_bytes());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)],type_ignores=[]),'actual_budget_pure','exec'),ns)
claims=[json.loads(p.read_bytes()) for p in sorted((D/'claims').glob('*.claim.json'))];ok(len(claims)==2,'two genuine spent claims')
for p in sorted((D/'claims').glob('*.claim.json')):
 claim=json.loads(p.read_bytes());matches=[q for q in (C/'research_runs').glob('*/claim.json') if q.read_bytes()==p.read_bytes()];ok(len(matches)==1,'exact genuine claim bytes')
def bound(row):
 if type(row)is not dict or set(row)!={'path','sha256'}:raise ValueError('invalid pin')
 p=C/row['path'];b=p.read_bytes()
 if sha(b)!=row['sha256']:raise ValueError('pin mismatch')
 return b
family=g['families']['synthetic-financial-wrapper'];ok(family['attempt_budget']==18 and family['prior_attempts']==0,'base18prior0');ok(ns['effective_budget'](C,g['program_id'],ref,e,family,claims,bound)==19,'exact current allowance19');refusals=[]
for name in ['missing','empty','extra','wrong-extension','wrong-review','stale-original']:
 v=copy.deepcopy(e)
 if name=='missing':v.pop('cumulative_budget_extension')
 elif name=='empty':v['cumulative_budget_extension']={}
 elif name=='extra':v['cumulative_budget_extension']['extra']=True
 elif name=='stale-original':v=g['experiments'][ref]
 else:v['cumulative_budget_extension']['extension' if name=='wrong-extension' else 'review']['sha256']='0'*64
 try:ns['effective_budget'](C,g['program_id'],ref,v,family,claims,bound)
 except ValueError as err:refusals.append({'case':name,'reason':str(err)})
 else:raise AssertionError(name)
ok(len(refusals)==6 and 19-len(claims)==17,'all budget refusals; no refund')
phases=json.loads((D/'ORIGINAL_CHARTER02.json').read_bytes())['phases'];ok(len(phases)==18 and phases[1]['proposed_identity']==ref and phases[1]['proposed_dependencies']==[],'original independent next phase');ok(sum(x['expected_lifecycle_status']=='COMPLETE' for x in phases)==14 and sum(x['expected_lifecycle_status']=='FAILED' for x in phases)==4,'original14/4');ok(sum(x['training_fit_cell_calls'] for x in phases)==12 and sum(x['optimizer_updates_if_successful'] for x in phases)==804,'12 fits804 updates');ok(len({x['proposed_cell'] for x in phases})==10,'10cells')
caller=json.loads((D/'CALLER.DRAFT.json').read_bytes());ok(caller['status']=='DRAFT_NOT_RELEASED','caller draft');
for k in ['source','design_source','new_external_parent_root','new_request_sha256','native_readiness','numerical_release','failed_outcome_actual_external_and_flat_recovery','new_source_and_full_caller_external_and_flat_recovery']:ok(caller[k] is None,'mandatory unresolved '+k)
for name,path in caller['derived_namespaces'].items():ok(not os.path.lexists(path),'unused namespace '+name)
errata=json.loads((A/'ERRATA01.json').read_bytes());wrapper=(C/'tradingagents/research/onchain_replication/financial_wrapper_fixture.py').read_bytes();defs={x.name:x for x in ast.parse(wrapper).body if isinstance(x,(ast.FunctionDef,ast.ClassDef))};ok(sha(wrapper)==errata['actual_source_sha256'],'errata exactsource');
for name,line in errata['actual_lines'].items():ok(defs[name].lineno==line,'actual AST line '+name)
ok(sha((A/'MANIFEST01.json').read_bytes())==errata['original_seal'],'original seal preserved')
api=json.loads((D/'SOURCE_API_JOINS.json').read_bytes());
for row in api:
 p=C/row['path'];b=p.read_bytes();ok(sha(b)==row['sha256'] and len(b)==row['bytes'],'actual API body');nodes={n.name:n for n in ast.parse(b).body if isinstance(n,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef))}
 for definition in row['definitions']:
  n=nodes[definition['name']];ok(n.lineno==definition['line'] and sha(ast.dump(n,include_attributes=False).encode())==definition['ast_sha256'],'actual API AST')
(H/'READBACK01.json').write_text(json.dumps({'checks':len(checks),'names':checks,'budget_refusals':refusals,'current_claims':2,'ceiling':19,'remaining':17,'future_source':None,'actual_admission':False,'flat_recovery_prerequisite_discharged':False},indent=2)+'\n');print(json.dumps({'checks':len(checks),'refusals':len(refusals)}))
