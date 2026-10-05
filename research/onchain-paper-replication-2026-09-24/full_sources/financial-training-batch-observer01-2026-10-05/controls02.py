"""Source-only original calendar and exact publisher encoding joins."""
from pathlib import Path
import ast,json
from datetime import datetime,timedelta,timezone
import training_batch_observer as O
H=Path(__file__).resolve().parent;ROOT=H.parents[3];checks=[]
def extract(path,name,namespace):
 tree=ast.parse(path.read_bytes());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
 exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace);return namespace[name]
ns={'json':json};original_encode=extract(ROOT/'tradingagents/research/lifecycle.py','_encode',ns)
event={'metadata':'opaque','ids':[17,23],'unavailable':None};raw=original_encode(event)
assert raw==(json.dumps(event,sort_keys=True,indent=2,allow_nan=False)+'\n').encode();checks.append('exact original publication bytes are bounded, not compact underestimate')
helper=ast.parse((H/'training_batch_observer.py').read_bytes());observe=next(n for n in helper.body if isinstance(n,ast.FunctionDef) and n.name=='observe')
assert any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_encode' for n in ast.walk(observe));checks.append('observer uses actual writer encoder')
ns={'timedelta':timedelta,'datetime':datetime}
def utc(v):return datetime.fromisoformat(v.replace('Z','+00:00'))
ns['utc']=utc
calendar=ROOT/'tradingagents/research/onchain_replication/calendar.py'
extract(calendar,'stamp',ns);expected=extract(calendar,'expected_week',ns)
for i in range(21):
 day=(datetime(2022,1,1,tzinfo=timezone.utc)+timedelta(days=i)).date().isoformat()
 step=(utc(day+'T00:00:00Z')+timedelta(days=1)).isoformat()
 assert O.week(day)==expected(step);checks.append('original expected-week day '+day)
assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('numpy','tolist','detach','cpu','item','clone') for n in ast.walk(helper));checks.append('observer has no value/materialization tensor API')
assert 'gc' not in {n.name for x in ast.walk(helper) if isinstance(x,(ast.Import,ast.ImportFrom)) for n in x.names};checks.append('no observer heap/GC scan')
with (H/'CONTROLS02.json').open('xb') as f:f.write(O.encode({'checks':checks,'count':len(checks),'actual_native_path':False}))
print(json.dumps({'passed':len(checks),'scope':'stdlib source only'}))
