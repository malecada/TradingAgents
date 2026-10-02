import ast
import hashlib
import json
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parent

def load():
 p=HERE/'imported_mcm_identity.py'
 if not p.exists():raise AssertionError('authenticated workload source absent')
 tree=ast.parse(p.read_text());nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='workload_record']
 if len(nodes)!=1:raise AssertionError('workload derivation absent')
 ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),ns);return ns['workload_record']

class Contract(unittest.TestCase):
 def test_both_identity_families_and_order_affect_workload(self):
  f=load();args=dict(workflow='w',backend={'v':1},graph='g',node_order='n',dictionary='d',ordered_motifs=['a','b'],matching={'x':1},original_matching='o',execution_matching='e',execution_identity='i')
  baseline=f(**args)
  self.assertEqual(baseline['dictionary'],'d');self.assertEqual(baseline['original_matching'],'o')
  for field,value in [('original_matching','o2'),('execution_matching','e2'),('execution_identity','i2'),('ordered_motifs',['b','a'])]:
   with self.subTest(field=field):self.assertNotEqual(f(**(args|{field:value})),baseline)
 def test_historical_numeric_loop_ast_unchanged(self):
  old=ast.parse((HERE/'baseline/kernel.py').read_text());newfile=HERE/'imported_kernel.py'
  self.assertTrue(newfile.exists(),'typed imported kernel missing')
  new=ast.parse(newfile.read_text())
  def body(tree):
   fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='mcm')
   start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.With))
   return ast.dump(ast.Module(body=fn.body[start:start+2],type_ignores=[]),include_attributes=False)
  self.assertEqual(body(old),body(new))

if __name__=='__main__':unittest.main()
