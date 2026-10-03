"""Independent source checks; no builder stage/capsule/Git subprocess invoked."""
import ast,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent;ROOT=BASE.parents[2];A=BASE/'neural-cold-feature-handoff-root-capsule-builder-preparation01-2026-10-03'
def load(p,name):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=load(A/'builder01.py','review_builder01')
class Review(unittest.TestCase):
 def test_all_manifest_dependencies_bodies(self):
  own=json.loads((A/'MANIFEST01.json').read_text())
  for row in own['files']:
   b=(A/row['path']).read_bytes();self.assertEqual(len(b),row['bytes']);self.assertEqual(m.digest(b),row['sha256'])
  for name,h in m.PINS.items():
   p=ROOT/name;b=p.read_bytes();self.assertEqual(m.digest(b),h);doc=json.loads(b);self.assertEqual(len(doc['files']),doc['file_count'])
   for row in doc['files']:
    raw=(p.parent/row['path']).read_bytes();self.assertEqual(len(raw),row['bytes']);self.assertEqual(m.digest(raw),row['sha256'])
  raw=(ROOT/m.CSC/'source_inventory03.json').read_bytes();self.assertEqual(m.digest(raw),m.INV)
  inv=json.loads(raw);self.assertEqual(len(m.ordered_rows(inv['source_inventory'])),195);self.assertEqual(inv['package_count'],147)
  self.assertEqual(sum(r['target'].startswith('tradingagents/') for r in inv['source_inventory']),147)
 def test_actual_verify_preparation_with_explicit_Git_double(self):
  inv=json.loads((ROOT/m.CSC/'source_inventory03.json').read_text());historical={r['git_commit']+':'+r['git_path']:(ROOT/m.CSC/'source-bodies'/r['target']).read_bytes() for r in inv['source_inventory'] if r.get('git_commit') is not None}
  calls=[];commit='abcdef0123'*4;original=m.git
  def fake(root,*args):
   calls.append(args)
   if args[0]=='rev-parse':return (commit+'\n').encode()
   self.assertEqual(args[0],'show');key=args[1]
   if key in historical:return historical[key]
   self.assertTrue(key.startswith(commit+':'));return (ROOT/key[41:]).read_bytes()
  m.git=fake
  try:observed,gen,metadata=m.verify_preparation(ROOT,commit)
  finally:m.git=original
  self.assertEqual(observed,inv);self.assertEqual(gen.INV if hasattr(gen,'INV') else gen.PINNED_INVENTORY,m.INV);self.assertTrue(callable(metadata.build));self.assertGreater(len(calls),400)
  # This checks joins/ordering only; the fake Git data authenticates no commit.
 def test_exclusive_tiny_put_ref_and_symlink_refusal(self):
  gen=m.load(ROOT/m.GEN/'generate03.py','review_source_generator')
  with tempfile.TemporaryDirectory(prefix='review-builder-tiny-') as name:
   root=Path(name).resolve();r=m.put(gen,root,'draft/body.json',b'{}\n');self.assertEqual(m.ref(root,r),b'{}\n')
   with self.assertRaises(ValueError):m.put(gen,root,'draft/body.json',b'changed')
   (root/'link').symlink_to(root/'draft',target_is_directory=True)
   with self.assertRaises(ValueError):m.put(gen,root,'link/new.json',b'{}')
   with self.assertRaises(ValueError):m.ref(root,dict(r,sha256='a'*64))
 def test_input_boundaries_and_actual_stage_call_order(self):
  tree=ast.parse((A/'builder01.py').read_text());execute=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute');text=ast.unparse(execute)
  self.assertLess(text.index('verify_preparation('),text.index('root.mkdir('));self.assertLess(text.index('git_installed('),text.index('checker.check('));self.assertLess(text.index('checker.check('),text.index('metadata.build('));self.assertIn('gen.render(',text);self.assertIn('gen.prepare_compare(',text)
  self.assertIn("len(inputs) == 9",text);self.assertIn("'native_environment': envref",text)
  self.assertIn("'environment': {k: inputs['environment'][k]",text)
  self.assertIn("request['output'] not in value['files']",text)
  # Only read-only local Git command forms are present.
  gitcalls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='git']
  self.assertEqual({n.args[1].value for n in gitcalls if isinstance(n.args[1],ast.Constant)},{'rev-parse','show','merge-base'})
 def test_bound_refusals_and_runtime_shape(self):
  for name in ('../x','/x','keys/a','apis/x','.env','x//y'):
   with self.assertRaises(ValueError):m.relative(name)
  rows=[{'name':str(i),'record':'/fixture/'+str(i),'record_sha256':'ab'*32} for i in range(251)];m.runtime_shape({'distribution_records':rows})
  for values in (rows[:-1],rows[:-1]+[rows[0]]):
   with self.assertRaises(ValueError):m.runtime_shape({'distribution_records':values})
 def test_no_numerics(self):self.assertFalse(any(k.split('.')[0] in {'numpy','torch','scipy','tradingagents','pandas','pyarrow'} for k in sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
