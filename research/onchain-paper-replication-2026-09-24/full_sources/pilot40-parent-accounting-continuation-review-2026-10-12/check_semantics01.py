from pathlib import Path
import ast,json,hashlib,tarfile,io
F=Path('research/onchain-paper-replication-2026-09-24/full_sources');C=F/'pilot40-parent-accounting-continuation-candidate-2026-10-12';R=F/'pilot40-parent-accounting-continuation-review-2026-10-12';h=lambda b:hashlib.sha256(b).hexdigest()
t=ast.parse((C/'batched_continuation.py').read_text());fn=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_original39_contract');env={};exec(compile(ast.Module([fn],[]),'<literal-contract>','exec'),env);fixed=env['_original39_contract']();claimpath=Path('research_runs')/fixed['parent']/'claim.json';claimraw=claimpath.read_bytes();claim=json.loads(claimraw);assert h(claimraw)==fixed['claim_sha256']
evidence={str(claimpath):h(claimraw)}
for path,digest in fixed['sources'].items():
 p=C/'original_source'/Path(path).name;b=p.read_bytes();assert h(b)==digest==claim['experiment']['source_files'][path];evidence[str(p)]=digest
for key,pin in fixed['evidence'].items():
 b=Path(pin['path']).read_bytes();assert h(b)==pin['sha256'];evidence[pin['path']]=pin['sha256']
trace=Path(fixed['evidence']['traceback']['path']).read_text()
for text in ['batched_driver.py", line 185','compact_mcm_batched.py", line 678','compact_mcm_batched.py", line 668','typed_payload_operations.py", line 262','imported_authority_interval.py", line 35','stale interval cannot refresh']:assert text in trace,text
recovery=json.loads(Path(fixed['evidence']['recovery']['path']).read_bytes());archive=Path(recovery['returned_archive']['path']).read_bytes();assert h(archive)==recovery['returned_archive']['sha256'];evidence[recovery['returned_archive']['path']]=h(archive)
with tarfile.open(fileobj=io.BytesIO(archive),mode='r:') as a:
 names=a.getnames();origin_name=next(x for x in names if x.endswith('/stream/numeric-origins.bin'));origins=a.extractfile(origin_name).read();base=origin_name[:-len('stream/numeric-origins.bin')];last=None
 for i,expected in enumerate(fixed['batches']):
  paths=[base+f'matching/{i:08d}.'+s for s in ['pending.json','records.bin','complete.json']]+[base+f'stream/numeric-batches/{i:012d}.json',base+f'matching/{i:08d}.prefix.json'];b=[a.extractfile(p).read() for p in paths];o=origins[i*4096*9:(i+1)*4096*9]
  assert [h(b[0]),h(b[1]),h(b[2]),h(o),h(b[3]),h(b[4])]==expected
  marker=json.loads(b[4]);assert marker['batch']==i and marker['start']==i*4096 and marker['stop']==(i+1)*4096 and marker['cost_epoch_start']==0
  costs={'checkpoint_attempts':marker['checkpoint_attempts'],'checkpoint_reserved_bytes':marker['checkpoint_reserved_bytes'],**marker['operation_counters']};assert all(type(v)is int and v>=0 for v in costs.values())
  if last:assert all(costs[k]>=v for k,v in last.items())
  last=costs
assert last==fixed['costs'] and fixed['stop']==65536
# The exact old driver's publication/post_batch ordering and lack of catch/retry.
driver=ast.parse((C/'original_source/batched_driver.py').read_text());calls=[n for n in ast.walk(driver) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('commit_batch','post_batch')];assert [x.func.id for x in sorted(calls,key=lambda n:n.lineno)]==['commit_batch','post_batch']
pair=ast.parse((C/'original_source/batched_pair_executor.py').read_text());writes=[]
for n in ast.walk(pair):
 if isinstance(n,(ast.Assign,ast.AugAssign)):
  targets=n.targets if isinstance(n,ast.Assign) else [n.target]
  for x in targets:
   if isinstance(x,ast.Attribute) and x.attr in ['checkpoints','reserved_bytes','completed_operations','advance_calls','abandoned_call_operation_limit']:writes.append((n.lineno,x.attr))
print(json.dumps({'status':'PASS','source_bodies':len(fixed['sources']),'original_claim_pins':True,'trace_exact_source_frames':True,'recovered_batch_hashes':16*6,'prefix_epoch_start_zero_all16':True,'five_final_costs':last,'pair_counter_write_sites':writes,'evidence':evidence,'qualification':'No numeric computation or restored prefix capability. Original marker costs plus source-order proof; generic failures and other costs remain outside scope.'},indent=2))
