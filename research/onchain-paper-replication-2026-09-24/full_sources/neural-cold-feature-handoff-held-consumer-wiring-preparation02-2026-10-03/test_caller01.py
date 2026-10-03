"""Actual extracted caller/consumer bodies; authority stand-ins explicitly synthetic."""
import ast,hashlib,json,os,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class Checks(unittest.TestCase):
 def test_inverse_bytes_and_math(self):
  b=(P/'compact_mcm.baseline01.py').read_text();c=(P/'compact_mcm.py').read_text()
  c=c.replace("        held_consumer = None\n        if _imported(dictionary):\n            from . import held_score_consumer\n            held_consumer = held_score_consumer.preflight(dictionary)\n",'')
  c=c.replace("            stream_terminal = stream.finish()['terminal_sha256']\n            if held_consumer is not None:\n                held_score_consumer.consume(dictionary,stage,held,stream)\n            return actual,stream_terminal,numeric_pin","            return actual,stream.finish()['terminal_sha256'],numeric_pin")
  self.assertEqual(c,b);self.assertEqual(ast.dump(ast.parse(c)),ast.dump(ast.parse(b)))
 def test_extracted_compute_tail_order(self):
  tree=ast.parse((P/'compact_mcm.py').read_text());compute=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='compute')
  body=compute.body[-3:]
  fun=ast.FunctionDef(name='tail',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=body,decorator_list=[])
  for selected,fail in [(None,False),('input',False),('input',True)]:
   events=[]
   class Stream:
    def finish(self):
     events.append('finish')
     if fail:raise ValueError('finish failed')
     return {'terminal_sha256':'terminal'}
   ns={'stream':Stream(),'held_consumer':selected,'held_score_consumer':types.SimpleNamespace(consume=lambda *x:events.append('consume')),'dictionary':object(),'stage':object(),'held':object(),'actual':object(),'numeric_pin':'pin'}
   exec(compile(ast.fix_missing_locations(ast.Module(body=[fun],type_ignores=[])),'actual tail','exec'),ns)
   if fail:
    with self.assertRaises(ValueError):ns['tail']()
    self.assertEqual(events,['finish'])
   else:
    result=ns['tail']();self.assertIs(result[0],ns['actual']);self.assertEqual(result[1:],('terminal','pin'));self.assertEqual(events,['finish']+(['consume'] if selected else []))
 def test_consumer_closes_before_output_and_no_output_on_close_failure(self):
  tree=ast.parse((P/'held_score_consumer.py').read_text());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='consume');f.body=[n for n in f.body if not isinstance(n,ast.ImportFrom)]
  for failure in (None,MemoryError('close')):
   events=[]
   class Held:
    def check(self,o):events.append('held')
   class Stage:pass
   class Stream:pass
   stage=Stage();owner=types.SimpleNamespace(identity='owner',active=stage);stage.owner=owner;stage.closed=False;stage.name='mcm-target'
   target=types.SimpleNamespace(key='a'*64,owner=owner,check=lambda:events.append('target'))
   stream=Stream();stream.cells=1;stream.batches=types.SimpleNamespace(chunk_cells=1)
   class Run:
    directory=Path('/nonexistent/synthetic-held-review');_published_outputs={}
    def write_json(self,n,v):events.append('output');self.value=v
   run=Run();policy={'targets':{target.key:{'output':'read.json'}},'part_bytes':8,'max_read_bytes':8,'max_members':1}
   class CM:
    def __enter__(self):events.append('open');return object()
    def __exit__(self,*args):
     events.append('close')
     if failure:raise failure
   ns={'compact_owner':types.SimpleNamespace(Stage=Stage,_HeldTransition=Held,verify_current=lambda x:events.append('verify')),'mcm_score_stream':types.SimpleNamespace(MCMScoreStream=Stream),'_route':lambda x:(run,'policy',b'{}',policy),'require':lambda v,m:self.assertTrue(v,m),'os':os,'_api':lambda x:types.SimpleNamespace(open_held=lambda *a:CM()),'_read_all':lambda *a:{'bytes':8},'hashlib':hashlib,'json':json,'KIND':'synthetic'}
   exec(compile(ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[])),'actual consume','exec'),ns)
   if failure:
    with self.assertRaises(MemoryError) as e:ns['consume'](target,stage,Held(),stream)
    self.assertIs(e.exception,failure);self.assertNotIn('output',events)
   else:
    ns['consume'](target,stage,Held(),stream);self.assertLess(events.index('close'),events.index('output'));self.assertFalse(run.value['scientific_publication']);self.assertEqual(run.value['local_bytes_retired'],0)
if __name__=='__main__':unittest.main(verbosity=2)
