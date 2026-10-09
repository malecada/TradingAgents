import ast,copy,hashlib,json,os,resource,types
from pathlib import Path
OUT=Path(__file__).resolve().parent;H=OUT.parent/'mcm-batched-grouped-driver01-2026-10-09';ROOT=H.parents[3];BASE=ROOT/'tradingagents/research/onchain_replication'
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);os.nice(10)
s=(H/'compact_mcm_batched.py').read_text();old=(BASE/'compact_mcm_batched.py').read_text();tree=ast.parse(s);base=ast.parse(old)
def require(v,m):
 if not v:raise ValueError(m)
ns={'require':require,'FORMAT':'ordered-mcm-batch-closure-v2'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('selected','validate')],type_ignores=[]),'<actual policy AST>','exec'),ns)
p={'schema_version':5,'max_entries':64,'max_workflow_metadata_bytes':100000,'numeric':{},'batched':{'format':ns['FORMAT'],'authority_boundaries':'entry-batch-checkpoint-final','batch_cells':32,'max_journal_bytes':100000,'max_body_bytes':1024,'max_closure_token_bytes':10000,'max_checkpoint_bytes':10000,'retention':'local-v2','max_spool_bytes':10000,'max_offload_metadata_bytes':10000,'max_offload_entries':10000,'max_offload_anchor_bytes':10000,'execution':{'route':'immutable-input-session+exact-byte-reuse-v1','max_entries':4096,'max_retained_bytes':64*1024**2,'max_key_bytes':8*1024**2,'max_origin_bytes':10000,'max_summary_bytes':10000}}}
ns['validate'](p,64);g=copy.deepcopy(p);g['schema_version']=6;g['batched'].update(group_batches=16,retention='typed-grouped-recover-before-retire-v1');ns['validate'](g,64)
refusals=0
for version,retention,group in [(5,'typed-grouped-recover-before-retire-v1',16),(6,'local-v2',16),(6,'typed-grouped-recover-before-retire-v1',True),(6,'typed-grouped-recover-before-retire-v1',15)]:
 q=copy.deepcopy(g);q['schema_version']=version;q['batched'].update(retention=retention,group_batches=group)
 try:ns['validate'](q,64)
 except ValueError:refusals+=1
 else:raise AssertionError('policy silently accepted')
# Literal AST inverse for entire original _compute after deleting the one new elif.
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_compute');orig=next(n for n in base.body if isinstance(n,ast.FunctionDef) and n.name=='_compute')
branch=next(n for n in ast.walk(fn) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and ast.unparse(n.test)=="b['retention'] == 'typed-grouped-recover-before-retire-v1'")
funcs=[n for n in branch.body if isinstance(n,ast.FunctionDef)]
for n in ast.walk(fn):
 if isinstance(n,ast.If) and n.orelse==[branch]:n.orelse=[]
assert ast.dump(fn)==ast.dump(orig)
# Actual callback AST, synthetic callback routing only. No Owner/transport construction.
wrapper=ast.parse('def make():\n pass').body[0]
wrapper.args=ast.parse('def make(boundary,require,modules,grouped_offload,target,stage,work,hashlib,json,os,_checkpoint_inventory,b,spool_fd,batch_total):\n pass').body[0].args
wrapper.body=ast.parse('group_total=(batch_total+15)//16\nanchors=bytearray(group_total*32)\npending=[]\ngroups=0\nnext_batch=0\nexternal=None').body+funcs+ast.parse('return post_batch,final_batches,lambda:(groups,len(pending),external)').body
exec(compile(ast.fix_missing_locations(ast.Module(body=[wrapper],type_ignores=[])),'<actual callback AST>','exec'),globals())
class Journal:pass
for count in (1,15,16,17,32,33):
 records={};calls=[]
 def preserve(owner,stage,**kw):
  items=kw['items'];assert all(len(t)==168 for _,t in items);calls.append(tuple(i for i,_ in items));r={'batch_count':len(items)};records[kw['work']/'offload.json']=json.dumps(r).encode();return r
 off=types.SimpleNamespace(preserve_and_retire=preserve,typed=types.SimpleNamespace(_read=lambda p:records[p]),finalize=lambda *a,**kw:{'groups':kw['group_count'],'batches':kw['batch_count'],'records':len(list(kw['records']))})
 post,final,state=make(lambda:None,require,{'journal':types.SimpleNamespace(BatchJournal=Journal)},off,types.SimpleNamespace(owner=None),None,Path('/synthetic'),hashlib,json,types.SimpleNamespace(fsync=lambda fd:None),lambda *a,**k:{'bytes':1}, {'max_offload_entries':1000,'max_offload_metadata_bytes':1000},-1,count)
 j=Journal()
 for i in range(count):post(j,i,bytes([i%256])*168,None)
 assert state()[0]==count//16 and state()[1]==count%16
 final(j,None,count,None);assert calls==[tuple(range(i,min(i+16,count))) for i in range(0,count,16)] and state()[1]==0
 assert state()[2]['coverage']['records']==(count+15)//16
result={'status':'PASS','schema_refusals':refusals,'original_compute_AST_inverse':True,'callback_batch_counts':[1,15,16,17,32,33],'genuine_owner_transport':'UNEXECUTED','affinity':sorted(os.sched_getaffinity(0))}
(OUT/'ROUTING02.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
