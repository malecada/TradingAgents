import ast,json,re,unittest,types
from pathlib import Path
P=Path(__file__).parent;D=P.parent/'batch-output-produced-f32-adapter-preparation02-2026-10-03'
def extract(file,names,extra):
 tree=ast.parse((D/file).read_bytes());ns={'json':json,'Path':Path,'re':re,'META':8192};ns.update(extra);exec(compile(ast.Module([n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],[]),file,'exec'),ns);return ns
class T(unittest.TestCase):
 def test_missing_real_policy_refused(self):
  pop=json.loads((P/'RAW_POPULATION_TEMPLATE01.json').read_bytes());f=extract('archive_non_tail.py',{'require','encode','validate_policy'},{});
  with self.assertRaises(ValueError):f['validate_policy'](pop)
  tx=json.loads((P/'TRANSPORT_TEMPLATE01.json').read_bytes());g=extract('selected_non_tail_transport.py',{'require','encoded','policy'},{'durable':types.SimpleNamespace(encode=f['encode'])});
  with self.assertRaises(ValueError):g['policy'](tx,pop)
 def test_synthetic_schema_only(self):
  pop=json.loads((P/'RAW_POPULATION_TEMPLATE01.json').read_bytes());pop.update(namespace='synthetic',deadline_seconds=1800,max_rounded_bytes=10000000,max_commands=108,max_parts=36,max_control_bytes=6000000)
  tx=json.loads((P/'TRANSPORT_TEMPLATE01.json').read_bytes());tx.update(connection=dict(host='invalid.example',user='synthetic',port=23,identity_file='/synthetic-only/key',known_hosts_file='/synthetic-only/hosts'),remote_namespace='synthetic',command_seconds=1,cleanup_seconds=1,stderr_bytes=1024,max_commands=108,max_parts=72,max_rounded_bytes=10000000,max_channel_bytes=1000000,max_local_bytes=10000000,max_files=1000)
  f=extract('archive_non_tail.py',{'require','encode','validate_policy'},{});self.assertEqual(f['validate_policy'](pop),pop)
  g=extract('selected_non_tail_transport.py',{'require','encoded','policy'},{'durable':types.SimpleNamespace(encode=f['encode'])});self.assertEqual(g['policy'](tx,pop),tx)
if __name__=='__main__':unittest.main()
