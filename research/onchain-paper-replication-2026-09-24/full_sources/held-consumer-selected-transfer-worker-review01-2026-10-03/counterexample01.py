"""Metadata-only actual preflight seams; no genuine Context/Owner claimed."""
import ast,builtins,hashlib,json,pathlib,types
P=pathlib.Path(__file__).parent;C=P.parent/'held-consumer-selected-transfer-worker-preparation01-2026-10-03'
def actual(path,names,ns):
 t=ast.parse(path.read_text());exec(compile(ast.Module([n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names],[]),str(path),'exec'),ns)
engine={};actual(P.parent/'batch-output-selected-transfer-preparation01-2026-10-03/selected_non_tail_transport.py',{'require','charge'},{}) if False else None
engine={'BLOCK':32768};actual(P.parent/'batch-output-selected-transfer-preparation01-2026-10-03/selected_non_tail_transport.py',{'require','charge'},engine)
pkg=types.SimpleNamespace(selected_non_tail_transport=types.SimpleNamespace(**engine))
def imp(name,*args,**kwargs):return pkg if name=='' else builtins.__import__(name,*args,**kwargs)
ns={'Path':pathlib.Path,'json':json,'KIND':'original-import-held-score-readback-v1','TRANSFER_KIND':'original-import-held-score-selected-transfer-v2','__builtins__':{**vars(builtins),'__import__':imp}}
actual(C/'held_score_consumer.py',{'require','_policy','_transfer_budget'},ns)
graphs=['a'*64,'b'*64];nodes=dict(zip(graphs,[2,3]));chunk=64
pop=dict(slots=[dict(graph=h,role='score-batches',max_members=16,max_bytes=100000) for h in graphs],max_parts=64,max_commands=64,max_rounded_bytes=2**25,deadline_seconds=1000,max_control_bytes=4*1024**2)
tx=dict(part_bytes=8192,stderr_bytes=1024,max_parts=64,max_commands=64,max_rounded_bytes=2**25,max_channel_bytes=2**25,command_seconds=1,cleanup_seconds=1,max_local_bytes=2**28,max_files=32768)
resources=dict(wall_seconds=1800,storage_budget=dict(limits=dict(max_logical_bytes=2**30,max_allocated_bytes=2**30)))
results=[]
for changed,value in [('max_read_bytes',1),('max_members',1)]:
 policy=dict(schema_version=2,kind=ns['TRANSFER_KIND'],targets={h:{'output':f'read{i}.json'} for i,h in enumerate(graphs)},part_bytes=8192,max_read_bytes=10000,max_members=32,population_input='population',network_release_input='release',source_closure_input='closure');policy[changed]=value
 ns['_policy'](policy,graphs,['read0.json','read1.json']);totals=ns['_transfer_budget'](policy,pop,tx,nodes,chunk,resources)
 # Exact original target preflight size predicate, evaluated on already registered metadata.
 late=[graph for graph,n in nodes.items() if not (8*32*n<=policy['max_read_bytes'] and (32*n+chunk-1)//chunk<=policy['max_members'])]
 assert late
 results.append({'mutation':changed,'value':value,'new_before_context_policy_and_budget':'accepted','original_target_bound_would_refuse':late,'registered_nodes':nodes,'chunk':chunk,'transfer_totals':totals})
(P/'COUNTEREXAMPLE01.json').write_text(json.dumps({'status':'reproduced-source-bound-gap','qualification':'actual extracted policy/budget, exact later predicate; no ResearchRun, Context or Owner invoked','cases':results},sort_keys=True,indent=2)+'\n');print(json.dumps(results,sort_keys=True))
