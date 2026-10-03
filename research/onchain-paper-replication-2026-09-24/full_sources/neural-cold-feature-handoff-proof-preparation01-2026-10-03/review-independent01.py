"""Independent stdlib-only reconstruction; no authority or numerical execution."""
import ast,hashlib,json,struct,sys,types
from pathlib import Path
from datetime import datetime,timedelta,timezone
P=Path(__file__).resolve().parent
R=P.parents[3]
PKG=R/'tradingagents/research/onchain_replication'
def defs(file,names,env):
 tree=ast.parse(file.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
 assert len(nodes)==len(names)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(file),'exec'),env)
def require(ok,msg):
 if not ok:raise ValueError(msg)
# Independently reconstruct graph availability using the actual calendar function.
cal={'datetime':datetime,'timedelta':timedelta}
def utc(x):return datetime.fromisoformat(x.replace('Z','+00:00'))
cal['utc']=utc
defs(PKG/'calendar.py',{'stamp','expected_week','eligible'},cal)
r=json.loads((P/'recipe01.json').read_bytes());a=utc(r['graph_start']+'T00:00:00Z')
graphs={cal['stamp'](a+timedelta(weeks=w)):cal['stamp'](a+timedelta(weeks=w+1,days=1)) for w in range(r['graph_weeks'])}
rows=[];excluded=[];day=utc(r['train_start']);end=utc(r['test_end']);train_end=utc(r['train_end']);test_start=utc(r['test_start'])
while day<end:
 dates=[day-timedelta(days=i) for i in range(28,0,-1)];reason=None
 if day<train_end and day+timedelta(days=1)>=test_start:reason='purged_training_label'
 elif day.date().isoformat()==r['missing_price'] or any(d.date().isoformat()==r['missing_price'] for d in dates):reason='warmup_or_missing_price'
 keys=[]
 if reason is None:
  for date in dates:
   step=cal['stamp'](date+timedelta(days=1));key=cal['expected_week'](step)
   if key not in graphs:reason='missing_expected_graph';break
   if not cal['eligible'](graphs[key],step):reason='late_expected_graph';break
   keys.append(key)
 if reason is None:rows.append((day,keys))
 else:excluded.append((day,reason))
 day+=timedelta(days=1)
train=[x for x in rows if x[0]<train_end];test=[x for x in rows if x[0]>=test_start]
assert len(train)==56 and len(test)==12 and len(excluded)==65
print('Calendar reconstruction:',len(train),'train,',len(test),'test,',len(excluded),'excluded,',len({h for _,hs in rows for h in hs}),'required weeks')
# Execute actual policy validators on the candidate's literal pair/stage inputs.
t=ast.parse((P/'compact_cold_proof_inputs.py').read_text());fn=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='materialize')
assigns={n.targets[0].id:n.value for n in fn.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
fields={'max_state_bytes','normalization_chunk_entries','hardening_chunk_entries','hardening_buffer_bytes','max_score_buffer_bytes','chunk_edges','max_checkpoint_bytes','max_publications','total_checkpoint_bytes'}
cp=types.SimpleNamespace(BACKEND='resident-native-compact-current-owner-v1')
e={'compact_policy':cp};e['pair']=eval(compile(ast.Expression(assigns['pair']),'<candidate pair>','eval'),e);stage=eval(compile(ast.Expression(assigns['stage']),'<candidate stage>','eval'),e)
io=types.SimpleNamespace(META_LIMIT=8192,MAX_CHUNK_BYTES=8*1024**2)
logenv={'require':require,'io':io,'RECORD_BYTES':struct.calcsize('<QB7xQdQ32s32s32s')+32};defs(PKG/'compact_pair_log.py',{'_limits'},logenv)
env={'require':require,'pair':types.SimpleNamespace(POLICY_FIELDS=fields,LIMIT=65536),'io':io,'log':types.SimpleNamespace(_limits=logenv['_limits']),'BACKEND':cp.BACKEND,'SCHEDULE_FIELDS':{'operations_per_call','calls_per_checkpoint','max_checkpoints','max_total_checkpoints','max_total_checkpoint_bytes'},'cache_key':lambda x:hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()}
defs(PKG/'compact_policy.py',{'positive','validate'},env)
for kind,count in [('dictionary',992),('mcm',128)]:
 result=env['validate'](stage,kind=kind,pairs=count);print('Actual policy validation',kind,result['logical_reservation_bytes'])
# Weakref layout changes preserve the complete actual baseline AST.
for name in ('compact_terminal','compact_publication','compact_closure'):
 before=ast.parse((P/(name+'.py.baseline')).read_bytes());after=ast.parse((P/(name+'.py')).read_bytes())
 changed=0
 for node in ast.walk(after):
  if isinstance(node,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='__slots__' for v in node.targets):
   values=[v for v in node.value.elts if not isinstance(v,ast.Constant) or v.value!='__weakref__'];changed+=len(node.value.elts)-len(values);node.value.elts=values
 assert changed==1 and ast.dump(before)==ast.dump(after)
 print(name,'one weakref slot only')
assert not any(x in sys.modules for x in ('numpy','torch','pandas','pyarrow'))
print('No numerical modules imported; no arrays, lifecycle, guard, claim or fit executed.')
