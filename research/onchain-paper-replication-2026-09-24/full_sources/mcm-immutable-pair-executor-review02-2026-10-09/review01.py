import ast,copy,hashlib,json,os,resource,signal,types
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
H=Path(__file__).resolve().parent;R=H.parents[3];C=H.parent/'mcm-immutable-pair-executor02-2026-10-09';O=H.parent/'mcm-immutable-pair-executor01-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
man=json.loads((C/'MANIFEST01.json').read_text());assert all(sha(C/n)==v for n,v in man.items())
pins=json.loads((C/'BASELINE01.json').read_text())['main'];assert all(sha(R/'tradingagents/research/onchain_replication'/n)==v for n,v in pins.items())
old=ast.parse((O/'pair_executor.py').read_text());new=ast.parse((C/'pair_executor.py').read_text())
def call(t):return next(x for n in t.body if isinstance(n,ast.ClassDef) and n.name=='PairExecutor' for x in n.body if isinstance(x,ast.FunctionDef) and x.name=='__call__')
a=next(n for n in call(old).body if isinstance(n,ast.Try));b=next(n for n in call(new).body if isinstance(n,ast.Try));saved=b.finalbody;b.finalbody=copy.deepcopy(a.finalbody);assert ast.dump(old)==ast.dump(new);b.finalbody=saved
checks=[]
for version,tree in [('old',old),('new',new)]:
 for case in (['primary'] if version=='old' else ['primary','success','success-close','double-close','constructor','score','engine-close']):
  calls=[];primary=RuntimeError('body');one=RuntimeError('sessionclose');two=RuntimeError('engineclose');state={'phase':'running'}
  def create(*a,**k):calls.append('create');return state
  def close(s):
   calls.append('engineclose');s['closed']=True
   if case in ('double-close','engine-close'):raise two
  def score(*a,**k):
   calls.append('score')
   if case=='score':raise primary
   return types.SimpleNamespace(score=.25,iterations=3,convergence='iteration_cap')
  class Session:
   def __init__(self,*a,**k):
    calls.append('session')
    if case=='constructor':raise primary
   def advance(self,s,**kw):
    calls.append('advance')
    if case not in ('primary','double-close'):s['phase']='done'
   def close(self):
    calls.append('sessionclose')
    if case in ('primary','success-close','double-close'):raise one
  def checkpoint(*a):calls.append('checkpoint');raise primary
  engine=types.SimpleNamespace(create=create,close=close,score_only=score)
  pair=types.SimpleNamespace(hash_string=lambda v:None,policy_check=lambda *a,**k:None,LIMIT=8192,ENGINE_FIELDS=())
  ns={'copy':copy,'engine':engine,'pair':pair,'annealing':None,'ImmutablePairSession':Session}
  nodes=[n for n in tree.body if isinstance(n,ast.ClassDef)];exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual_executor_ast','exec'),ns)
  ex=ns['PairExecutor']({},dict(max_publications=1,max_checkpoint_bytes=100,max_score_buffer_bytes=100,chunk_edges=1),dict(max_checkpoints=1,calls_per_checkpoint=1,operations_per_call=1,max_total_checkpoints=2,max_total_checkpoint_bytes=100000),checkpoint)
  caught=None
  try:result=ex(None,None,'a'*64)
  except BaseException as e:caught=e
  if version=='old':assert caught is one and 'engineclose' not in calls
  else:
   assert calls.count('engineclose')==1 and state['closed']
   assert calls.count('sessionclose')==(0 if case=='constructor' else 1)
   expected={'primary':primary,'success':None,'success-close':one,'double-close':primary,'constructor':primary,'score':primary,'engine-close':two}[case];assert caught is expected
   assert ex.poisoned==(case!='success')
   if case=='success':assert result==(.25,3,'iteration_cap')
   if case=='double-close':assert len(primary.__notes__)==2
  checks.append({'version':version,'case':case,'calls':calls,'primary_or_first_cleanup_preserved':version=='new'})
out={'decision':'accepted','scope':'finally-only cleanup source; synthetic metadata control fixtures, prior numeric proof reused','source_sha256':sha(C/'pair_executor.py'),'manifest_sha256':sha(C/'MANIFEST01.json'),'main_pins':pins,'exact_ast_inverse_except_finally':True,'checks':checks,'genuine_authority':False,'numerical_imports':False,'limitation':'No universal guarantee for asynchronous interruption/allocation failure or exceptional repr/add_note behavior during cleanup bookkeeping.'};(H/'RESULT01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
