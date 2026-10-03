import ast,json,types,unittest
from pathlib import Path
P=Path(__file__).parent
def load(file,names,ns):
 t=ast.parse((P/file).read_text());exec(compile(ast.Module([n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names],[]),file,'exec'),ns);return ns
class Checks(unittest.TestCase):
 def test_raw_policy(self):
  ns=load('archive_non_tail.py',{'require','encode','validate_policy'},{'json':json,'META':8192});p=dict(schema_version=3,kind='non-tail-produced-f32-population-v1',category='non-tail-original-members',namespace='raw-proof',deadline_seconds=600,max_rounded_bytes=2**24,max_commands=32,max_parts=32,max_control_bytes=2**24,part_bytes=8192,receipt_output='context.json',terminal_output='terminal.json',slots=[dict(graph='a'*64,role='mcm-output',max_bytes=65536,max_members=2)],transport_input='transport')
  self.assertEqual(ns['validate_policy'](p),p)
  for role in ['graph-artifact','score-batches']:
   with self.assertRaises(ValueError):ns['validate_policy'](p|{'slots':[p['slots'][0]|{'role':role}]})
 def test_typed_completed_implementation(self):
  self.assertTrue((P/'completed_f32.py').exists(),'concrete typed Produced adapter absent')
if __name__=='__main__':unittest.main()
