import ast,hashlib,importlib.util,json,pathlib,tempfile,unittest
P=pathlib.Path(__file__).parent;s=importlib.util.spec_from_file_location('l',P/'launcher02.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_actual_tiny_recovery_bytes_membership(self):
  with tempfile.TemporaryDirectory() as d:
   parent=pathlib.Path(d);a=parent/'original';b=parent/'recovered';a.mkdir();b.mkdir()
   for root in (a,b):(root/'a').write_bytes(b'exact')
   index={'schema_version':1,'source':'b'*40,'original_root':str(a),'recovered_root':str(b),'members':[{'path':'a','kind':'file','bytes':5,'sha256':hashlib.sha256(b'exact').hexdigest()}]};p=parent/'index.json';p.write_text(json.dumps(index));q={'source':'b'*40,'recovery':{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}}
   self.assertEqual(m.recovery(q,a)['members'],1)
   (b/'a').write_bytes(b'wrong')
   with self.assertRaisesRegex(ValueError,'actual recovered'):m.recovery(q,a)
   (b/'a').write_bytes(b'exact');(b/'extra').write_bytes(b'x')
   with self.assertRaisesRegex(ValueError,'membership'):m.recovery(q,a)
 def test_full_request_shape_no_missing_role_or_bool_pid(self):
  ref={'path':'/root-provided/exact','sha256':'a'*64};q={'schema_version':1,'phase':'materialize','capsule':'/root-provided/capsule','source':'b'*40,'release':ref,'inventory':ref,'reviews':{k:ref for k in m.REVIEWS},'recovery':ref,'identity_baseline':ref,'old_roots':[{'root':'/root-provided/old','source':'c'*40,'withdrawal':ref,'baseline':ref}],'output_parent':'/root-provided/output','known_processes':[]}
  m.request_shape(q)
  for k in q:
   bad=dict(q);del bad[k]
   with self.subTest(missing=k),self.assertRaises(ValueError):m.request_shape(bad)
  bad=dict(q,known_processes=[True])
  with self.assertRaises(ValueError):m.request_shape(bad)
 def test_supervisor_only_and_genuine_postauth_source(self):
  tree=ast.parse((P/'launcher02.py').read_bytes());execute=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute');command=next(n.value for n in execute.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='command' for t in n.targets));self.assertIn('proof_supervise01.py',ast.unparse(command));self.assertNotIn('proof_outer01.py',ast.unparse(command))
  calls={ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)}
  for required in ['api.check_release','runtime.check','resources._native_owned_env','raw.authenticate','raw.closure','outer.stop_native']:self.assertIn(required,calls)
  for forbidden in ['ResearchRun.start','run.start','admit','fit']:self.assertNotIn(forbidden,calls)
 def test_fatal_selected_diagnostic_failure(self):
  f=MemoryError('first');self.assertIs(m.select(f,SystemExit()),f);later=KeyboardInterrupt();self.assertIs(m.select(m.CleanupFailure(),later),later)
if __name__=='__main__':unittest.main(verbosity=2)
