"""Metadata-only actual preflight seams; no genuine Context/Owner claimed."""
import ast,builtins,hashlib,json,pathlib,types
P=pathlib.Path(__file__).parent;C=P
def actual(path,names,ns):
 t=ast.parse(path.read_text());exec(compile(ast.Module([n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names],[]),str(path),'exec'),ns)
engine={'BLOCK':32768};actual(P.parent/'batch-output-selected-transfer-preparation01-2026-10-03/selected_non_tail_transport.py',{'require','charge'},engine)
pkg=types.SimpleNamespace(selected_non_tail_transport=types.SimpleNamespace(**engine))
def imp(name,*args,**kwargs):return pkg if name=='' else builtins.__import__(name,*args,**kwargs)
ns={'Path':pathlib.Path,'json':json,'KIND':'original-import-held-score-readback-v1','TRANSFER_KIND':'original-import-held-score-selected-transfer-v2','__builtins__':{**vars(builtins),'__import__':imp}}
actual(C/'held_score_consumer.py',{'require','_policy','_transfer_budget'},ns)
graphs=['a'*64,'b'*64];nodes=dict(zip(graphs,[2,3]));chunk=64
pop=dict(slots=[dict(graph=h,role='score-batches',max_members=16,max_bytes=100000) for h in graphs],max_parts=64,max_commands=64,max_rounded_bytes=2**25,deadline_seconds=1000,max_control_bytes=4*1024**2)
tx=dict(part_bytes=8192,stderr_bytes=1024,max_parts=64,max_commands=64,max_rounded_bytes=2**25,max_channel_bytes=2**25,command_seconds=1,cleanup_seconds=1,max_local_bytes=2**28,max_files=32768)
resources=dict(wall_seconds=1800,storage_budget=dict(limits=dict(max_logical_bytes=2**30,max_allocated_bytes=2**30)))
tree=ast.parse((C/'held_score_consumer.py').read_text());pre=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='preflight')
call=next(n for n in ast.walk(pre) if isinstance(n,ast.Call) and len(n.args)==2 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='held original population exceeds read policy before birth')
late_predicate=compile(ast.Expression(call.args[0]),'actual-original-target-size-predicate','eval')

import unittest
class Bounds(unittest.TestCase):
 def policy(self):return dict(schema_version=2,kind=ns['TRANSFER_KIND'],targets={h:{'output':f'read{i}.json'} for i,h in enumerate(graphs)},part_bytes=8192,max_read_bytes=768,max_members=2,population_input='population',network_release_input='release',source_closure_input='closure')
 def test_small_bytes(self):
  p=self.policy();p['max_read_bytes']=1;ns['_policy'](p,graphs,['read0.json','read1.json'])
  self.assertTrue(any(not eval(late_predicate,{'cells':32*n,'chunk':chunk,'p':p}) for n in nodes.values()))
  with self.assertRaisesRegex(ValueError,'held original population'):ns['_transfer_budget'](p,pop,tx,nodes,chunk,resources)
 def test_small_members(self):
  p=self.policy();p['max_members']=1;ns['_policy'](p,graphs,['read0.json','read1.json'])
  self.assertTrue(any(not eval(late_predicate,{'cells':32*n,'chunk':chunk,'p':p}) for n in nodes.values()))
  with self.assertRaisesRegex(ValueError,'held original population'):ns['_transfer_budget'](p,pop,tx,nodes,chunk,resources)
 def test_exact_enough(self):
  p=self.policy();ns['_policy'](p,graphs,['read0.json','read1.json'])
  self.assertTrue(all(eval(late_predicate,{'cells':32*n,'chunk':chunk,'p':p}) for n in nodes.values()))
  result=ns['_transfer_budget'](p,pop,tx,nodes,chunk,resources)
  self.assertEqual(result['members'],10) # complete containers, distinct from payload2 maximum
  self.assertEqual(result['commands'],30)
if __name__=='__main__':unittest.main()
