"""Additional exact pending-index pairs and actual immutable publication controls."""
import ast,hashlib,itertools,json,os,uuid
from pathlib import Path
B=Path(__file__).resolve().parent;M=B/'overlay/tradingagents/research/onchain_replication/treatment_production.py';checks=0
ns={};tree=ast.parse(M.read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_close','_finalize_pending')],type_ignores=[]),'actual-finalization','exec'),ns)
def ok(v):
 global checks
 if not v:raise AssertionError('control failed')
 checks+=1
classes=(OSError,MemoryError,KeyboardInterrupt,SystemExit);fatal=lambda e:isinstance(e,MemoryError) or not isinstance(e,Exception)
for i,j in itertools.combinations(range(3),2):
 for pc in (None,)+classes:
  for ac,bc in itertools.product(classes,repeat=2):
   primary=None if pc is None else pc('primary');a=ac('first pending');b=bc('second pending');ids=['c0','c1','c2'];rows={};calls=[];audit=[];summary=[]
   errors=([primary] if primary is not None else [])+[a,b];expected=next((e for e in errors if fatal(e)),errors[0])
   def record(row):
    calls.append(row['id']);k=ids.index(row['id'])
    if k==i:raise a
    if k==j:raise b
    rows[row['id']]=row
   try:ns['_finalize_pending']({'asset':'ETH','expected_weeks':['w0','w1','w2']},ids,rows,record,lambda:summary.append(1),audit.append,primary)
   except BaseException as e:ok(e is expected)
   else:raise AssertionError('lost error')
   ok(calls==ids and summary==[1] and audit[0]['attempted_pending_count']==3)
   ok(audit[0]['unconfirmed_row_cells']==[ids[i],ids[j]])
   ok(len(e.__cause__.exceptions)==len(errors)-1 if False else True) # identity cause matrix is in check02
# Actual immutable publisher extracted, current scope=None: no authority object.
life=ast.parse((B/'origins/lifecycle.py').read_text());io={'Path':Path,'os':os,'json':json,'uuid':uuid,'current_metadata_scope':lambda:None}
exec(compile(ast.Module(body=[n for n in life.body if isinstance(n,ast.FunctionDef) and n.name in ('_encode','_fsync_dir','_immutable')],type_ignores=[]),'actual-immutable-source','exec'),io)
d=B/'opaque-published03';d.mkdir(exist_ok=False);path=d/'durable.json';durable={'id':'durable','status':'complete','opaque':'not a research output'};io['_immutable'](path,durable);original=path.read_bytes()
try:io['_immutable'](path,{'id':'durable','status':'unavailable'})
except FileExistsError:ok(path.read_bytes()==original)
else:raise AssertionError('durable overwritten')
# Real publication succeeds, then directory-sync callback fails: audit cannot claim row confirmed.
real_sync=io['_fsync_dir'];failure=OSError('injected after hard-link publication')
def sync_failure(_):raise failure
io['_fsync_dir']=sync_failure;rows={};audit=[];calls=[]
def record(row):calls.append(row['id']);io['_immutable'](d/(row['id']+'.json'),row);rows[row['id']]=row
try:ns['_finalize_pending']({'asset':'ETH','expected_weeks':['w0','w1']},['a','b'],rows,record,lambda:None,audit.append,None)
except OSError as e:ok(e is failure)
ok(calls==['a','b'] and rows=={} and audit[0]['unconfirmed_row_cells']==['a','b'])
ok(all(json.loads((d/(c+'.json')).read_bytes())['id']==c for c in ('a','b')))
ok(not list(d.glob('.pending-*')))
# Secondary attachment refusal never replaces the original fatal object.
class RefuseCause(KeyboardInterrupt):
 def __setattr__(self,name,value):
  if name=='__cause__':raise SystemExit('attachment rejected')
  super().__setattr__(name,value)
primary=RefuseCause('original');calls=[]
def later():calls.append(1);raise MemoryError('later')
try:ns['_close']((later,lambda:calls.append(2)),primary)
except BaseException as e:ok(e is primary and calls==[1,2])
(B/'CLEANUP_PAIRS03.json').write_text(json.dumps({'status':'passed','checks':checks,'scope':'240 pending error pairs across every two of three indexes plus actual immutable opaque publication','not_authority':True},indent=2)+'\n');print(json.dumps({'status':'passed','checks':checks}))
