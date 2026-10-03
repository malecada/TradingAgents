"""Pure source inverse, complete-container budget, canonical metadata tests."""
import ast,builtins,hashlib,json,os,threading,types,unittest
from pathlib import Path
P=Path(__file__).parent
CONSUMER=P/'held_score_consumer.py'
def load(names,pkg=None):
 ns=dict(Path=Path,json=json,hashlib=hashlib,os=os,threading=threading)
 if pkg:
  def imp(n,*args,**kw):
   if n=='':return pkg
   return builtins.__import__(n,*args,**kw)
  ns['__builtins__']={**vars(builtins),'__import__':imp}
 t=ast.parse(CONSUMER.read_text());exec(compile(ast.Module([n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(CONSUMER),'exec'),ns);return ns
class Checks(unittest.TestCase):
 def test_byte_inverse(self):
  for name,names,marker in [('held_score_consumer.py',{'_policy','preflight','consume'},'\n\n# No context'),('resource_fixture.py',{'selection','preflight'},'\n\ndef execute(run,payload')]:
   old=(P/(name+'.baseline04.txt')).read_text();new=(P/name).read_text().split(marker)[0]
   new=new.replace("TRANSFER_KIND='original-import-held-score-selected-transfer-v2'\n_WORKER=None\n",'').replace('def _execute_original(', 'def execute(')
   originals={n.name:ast.get_source_segment(old,n) for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)}
   lines=new.splitlines(keepends=True)
   for n in reversed(ast.parse(new).body):
    if isinstance(n,ast.FunctionDef) and n.name in names:lines[n.lineno-1:n.end_lineno]=[originals[n.name]+'\n']
   restored=''.join(lines).rstrip()+'\n';self.assertEqual(restored,old.rstrip()+'\n',name)
 def test_budget(self):
  engine=types.SimpleNamespace(charge=lambda tx,rx,d,c:((tx+32767)//32768+rx//32768+1+(d+1+32767)//32768+(c+32767)//32768)*32768)
  ns=load({'require','_transfer_budget'},types.SimpleNamespace(selected_non_tail_transport=engine))
  graphs=['a'*64,'b'*64];pop=dict(slots=[dict(graph=h,role='score-batches',max_members=16,max_bytes=100000) for h in graphs],max_parts=64,max_commands=64,max_rounded_bytes=2**25,deadline_seconds=1000,max_control_bytes=4*1024**2)
  tx=dict(part_bytes=8192,stderr_bytes=1024,max_parts=64,max_commands=64,max_rounded_bytes=2**25,max_channel_bytes=2**25,command_seconds=1,cleanup_seconds=1,max_local_bytes=2**28,max_files=32768)
  resources=dict(wall_seconds=1800,storage_budget=dict(limits=dict(max_logical_bytes=2**30,max_allocated_bytes=2**30)))
  value=ns['_transfer_budget']({'max_read_bytes':10000,'max_members':32},pop,tx,dict(zip(graphs,[2,3])),128,resources)
  self.assertEqual(value['members'],8);self.assertEqual(value['parts'],16);self.assertEqual(value['commands'],24);self.assertEqual(value['bytes'],6*8192+160*8)
  for key in ('max_parts','max_commands','max_rounded_bytes','max_channel_bytes','max_local_bytes','max_files'):
   with self.assertRaises(ValueError):ns['_transfer_budget']({'max_read_bytes':10000,'max_members':32},pop,tx|{key:1},dict(zip(graphs,[2,3])),128,resources)
  with self.assertRaises(ValueError):ns['_transfer_budget']({'max_read_bytes':10000,'max_members':32},pop,tx,dict(zip(graphs,[2,3])),1,resources)
  with self.assertRaises(ValueError):ns['_transfer_budget']({'max_read_bytes':10000,'max_members':32},pop|{'deadline_seconds':10},tx,dict(zip(graphs,[2,3])),128,resources)
 def test_canonical_registered_json(self):
  ns=load({'require','_transfer_json'});raw=b'{"a":1}\n';run=types.SimpleNamespace(admission=types.SimpleNamespace(inputs={'p':{}}),read_input=lambda n:raw)
  self.assertEqual(ns['_transfer_json'](run,'p'),(raw,{'a':1}))
  for bad in (b'{"a":1,"a":1}\n',b'{"a": 1}\n',b' '*8193):
   run.read_input=lambda n:bad
   with self.assertRaises(ValueError):ns['_transfer_json'](run,'p')
  with self.assertRaises(ValueError):ns['_transfer_json'](run,'absent')
 def test_default_output_check_nested(self):
  t=ast.parse((P/'resource_fixture.py').read_text());pre=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='preflight')
  checks=[n for n in ast.walk(pre) if isinstance(n,ast.If) and ast.unparse(n.test)=="policy['schema_version'] == 2"]
  self.assertEqual(len(checks),1);self.assertNotIn('six held',ast.unparse(ast.Module(checks[0].body,type_ignores=[])));self.assertIn('six held',ast.unparse(ast.Module(checks[0].orelse,type_ignores=[])))
if __name__=='__main__':unittest.main()
