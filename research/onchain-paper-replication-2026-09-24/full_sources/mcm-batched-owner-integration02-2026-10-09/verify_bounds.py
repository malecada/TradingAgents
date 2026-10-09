import ast,json,resource,os,signal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
H=Path(__file__).resolve().parent
src=ast.parse((H/'compact_mcm_batched.py').read_text());ns={'FORMAT':'ordered-mcm-batch-closure-v2'}
def require(ok,message):
 if not ok:raise ValueError(message)
ns['require']=require
for name in ('selected','validate'):
 node=next(n for n in src.body if isinstance(n,ast.FunctionDef) and n.name==name);exec(compile(ast.Module(body=[node],type_ignores=[]),'actual_adapter','exec'),ns)
p={'schema_version':4,'max_entries':64,'max_workflow_metadata_bytes':65536,'numeric':{},'batched':{'format':ns['FORMAT'],'authority_boundaries':'entry-batch-checkpoint-final','batch_cells':48,'max_journal_bytes':200000,'max_body_bytes':1024,'max_closure_token_bytes':336,'max_checkpoint_bytes':1000000,'retention':'typed-recover-before-retire-v2','max_spool_bytes':256,'max_offload_metadata_bytes':100000,'max_offload_entries':1000,'max_offload_anchor_bytes':64}}
ns['validate'](p,64);refusals=[]
for field,value in [('max_offload_anchor_bytes',63),('max_spool_bytes',255),('max_offload_anchor_bytes',True),('max_offload_entries',4000001)]:
 q=json.loads(json.dumps(p));q['batched'][field]=value
 try:ns['validate'](q,64)
 except ValueError:refusals.append(field)
 else:raise AssertionError(field)
(H/'BOUNDS_RESULT01.json').write_text(json.dumps({'refusals':refusals,'synthetic_metadata_only':True,'affinity':sorted(os.sched_getaffinity(0))},indent=2)+'\n');print('PASS explicit spool/anchor bounds; wrong types and entry ceiling refused')
