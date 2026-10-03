"""Actual outer post-tail join with explicit synthetic storage response."""
import ast,hashlib,json,pathlib,sys,tempfile,unittest
D=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(D));import test_reader03 as reader;import refusal_inventory03 as inv
class Tests(unittest.TestCase):
 def test_actual_posttail_joins_inventory_and_terminal_raw_hash(self):
  tree=ast.parse((D/'refusal_outer01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='authenticate_post_tail');ns={'authenticate_native_post_tail':lambda *a:{'qualified':'synthetic storage response, no guard'},'body':reader.raw.body,'json':json,'hashlib':hashlib,'require':inv.require,'inventory_tools':inv,'Path':pathlib.Path};exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual outer post-tail','exec'),ns)
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);outer=root/'fixture_outer'/'synthetic-case';outer.mkdir(parents=True);(root/'tiny').write_text('synthetic')
   def save(n,v):(outer/n).write_bytes(inv.encode(v))
   reference=inv.publish(root,outer,reader.env['inventory'](root),'synthetic-case',save);proof={'inventory':reference};save('authenticated-refusal.json',proof);save('terminal.json',{'status':'passed','identity':'synthetic-case','proof_sha256':hashlib.sha256((outer/'authenticated-refusal.json').read_bytes()).hexdigest()})
   actual=ns['authenticate_post_tail'](root,'synthetic-case',{});self.assertEqual(actual['complete_inventory'],reference)
   value=json.loads((outer/'terminal.json').read_bytes());value['proof_sha256']='0'*64;save('terminal.json',value)
   with self.assertRaises(ValueError):ns['authenticate_post_tail'](root,'synthetic-case',{})
 def test_worker_oracle_and_preclaim_unchanged_native_bounds_retained(self):
  old=D.parent/'original-import-native-refusal-worker-preparation02-2026-10-03'
  for n in ('resource_refusal.py','refusal_preclaim01.py','refusal_native01.py','refusal_oracle_evidence01.py'):self.assertEqual((D/n).read_bytes(),(old/n).read_bytes())
  source=(D/'refusal_outer01.py').read_text();self.assertIn('time.monotonic()-started<1840',source);self.assertIn("p['wall_seconds']==1800",source);self.assertIn("'closure_seconds':None",source);self.assertNotIn("'closure_seconds':60",source);self.assertIn("release['inventory_policy']==inventory_tools.POLICY",source)
if __name__=='__main__':unittest.main(verbosity=2)
