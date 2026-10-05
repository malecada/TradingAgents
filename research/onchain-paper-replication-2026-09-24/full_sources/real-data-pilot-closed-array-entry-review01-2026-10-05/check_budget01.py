from pathlib import Path
import ast,hashlib,json
D=Path(__file__).resolve().parent;M=D.parents[3];E=M/'research/onchain-paper-replication-2026-09-24/storage/closed-array-pilot-offload-2026-10-05-01';T=M/'research/onchain-paper-replication-2026-09-24/storage/raw-preservation-2026-09-28-09/transfer.py'
c=json.loads((E/'manifest.json').read_text());draft=json.loads((M/c['draft']['path']).read_text());sizes=[r['bytes'] for r in draft['files']];cap=max(sizes)
cl=next(n for n in ast.parse(T.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='Transport');f=next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='reserve');env={};exec(compile(ast.Module(body=[f],type_ignores=[]),str(T),'exec'),env)
class Counter:pass
counter=Counter();counter.remaining=cap;count=0;failure=None
# This deliberately omits metadata, providing a conservative impossible bound.
for i,size in enumerate(sizes):
 for direction,amount in [('put',size),('get',(size//32768+1)*32768)]:
  try:env['reserve'](counter,amount)
  except RuntimeError as error:failure={'row_index':i,'direction':direction,'required_next_bytes':amount,'remaining_bytes':counter.remaining,'message':str(error)};break
  count+=1
 if failure:break
assert failure is not None
minimum=sum(s+(s//32768+1)*32768 for s in sizes)
assert minimum>cap
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
print(json.dumps({'decision':'blocking-defect-confirmed','manifest_sha256':h(E/'manifest.json'),'worker_sha256':h(E/'offload.py'),'entry_sha256':h(E/'entry01.py'),'transport_base_sha256':h(T),'selected_files':len(sizes),'selected_total_bytes':sum(sizes),'maximum_single_body_bytes':cap,'minimum_network_budget_array_put_get_only':minimum,'omits_manifest_restore_completion_metadata':True,'successful_reservations_before_failure':count,'counterexample_failure':failure,'large_array_bodies_read_or_hashed':False,'credentials_read':False,'network_or_native_execution':False},sort_keys=True,indent=2))
