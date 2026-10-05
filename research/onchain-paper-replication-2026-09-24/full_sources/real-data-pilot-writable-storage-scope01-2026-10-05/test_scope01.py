"""Offline metadata counters/routing only, no worker/authority construction."""
import ast,hashlib,importlib.util,json,os,sys,tempfile,types,unittest
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parents[3];P=Path('tradingagents/research/onchain_replication');T=D/'candidate'/P
pkg=types.ModuleType('scope_test');pkg.__path__=[str(T),str(ROOT/P)];sys.modules['scope_test']=pkg
import scope_test.real_pilot_storage as m
import scope_test.resources as r
sys.modules['tradingagents.research.onchain_replication.real_pilot_storage']=m
L={'max_allocated_bytes':1000000,'max_logical_bytes':1000000,'max_entries':1000,'max_depth':16,'max_scan_seconds':5}
def budget(root):return {'schema_version':2,'kind':m.KIND,'authority_root':str(root),'roots':[str(root/'research_artifacts'),str(root/'research_runs')],'limits':dict(L)}
def layout(root):
 for name in ('research_artifacts','research_runs'):(root/name).mkdir()
class Tests(unittest.TestCase):
 def test_aggregate_and_identity(self):
  with tempfile.TemporaryDirectory(dir=D) as t:
   root=Path(t);layout(root)
   for name in ('research_artifacts','research_runs'):(root/name/'body').write_bytes(b'123456')
   w=m.WritableUnion(budget(root),root);v=w.check();self.assertEqual(v['logical_file_bytes'],12);self.assertEqual(v['entries'],2);self.assertEqual(len(v['root_identities']),2)
   bad=budget(root);bad['limits']['max_logical_bytes']=10
   with self.assertRaises(m.StorageLimit) as e:m.WritableUnion(bad,root).check()
   self.assertEqual(e.exception.observation['logical_file_bytes'],12)
 def test_strict_link_and_scope_refusal(self):
  with tempfile.TemporaryDirectory(dir=D) as t:
   root=Path(t);layout(root);p=root/'research_artifacts/file';p.write_text('x');link=p.with_name('alias');link.symlink_to(p)
   with self.assertRaises(ValueError):m.WritableUnion(budget(root),root).check()
   link.unlink();os.link(p,link)
   with self.assertRaises(ValueError):m.WritableUnion(budget(root),root).check()
   b=budget(root);b['roots'][1]=str(root/'research_artifacts/sub')
   with self.assertRaisesRegex(ValueError,'exact disjoint'):m.WritableUnion(b,root)
 def test_environment_and_generic_policy_refusal(self):
  with tempfile.TemporaryDirectory(dir=D) as t:
   root=Path(t);layout(root);b=budget(root)
   original=r._native_owned_env(root);union=r._native_owned_env(root,b)
   self.assertEqual(original['TMPDIR'],str(root/'fixture_runtime/tmp'));self.assertEqual(r._native_owned_env(root,{'root':str(root),'limits':L}),original)
   for k in set(union)-{'PYTHONPATH','PYTHONDONTWRITEBYTECODE','PYTEST_DISABLE_PLUGIN_AUTOLOAD','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'}:self.assertTrue(Path(union[k]).is_relative_to(root/'research_artifacts'))
   self.assertEqual(union['TMP'],union['TEMP']);self.assertEqual(union['TMP'],union['TMPDIR'])
   node=next(n for n in ast.parse((T/'job.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='resource_policy')
   env={'__package__':'scope_test','resources':r,'Path':Path};exec(compile(ast.Module(body=[node],type_ignores=[]),'actual_policy','exec'),env)
   policy={'memory_max_bytes':r.GIB,'memory_high_bytes':r.GIB,'reserve_bytes':3*r.GIB,'start_reserve_bytes':4*r.GIB,'disk_floor_bytes':10*r.GIB,'disk_paths':[str(root)],'wall_seconds':10,'storage_budget':b,'native_unit_limits':{'file_size_bytes':1000}}
   with self.assertRaisesRegex(ValueError,'explicit real-pilot'):env['resource_policy'](policy,root)
   with self.assertRaises(TypeError):env['resource_policy'](policy,root,real_pilot=True)
 def test_shared_scan_deadline(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory(dir=D) as t:
   root=Path(t);layout(root);w=m.WritableUnion(budget(root),root);begins=[]
   def sample(watch,begin,history):
    begins.append(begin);return {'allocated_bytes':1,'logical_file_bytes':0,'entries':0,'regular_files':0,'directories':1}
   with patch.object(m.StorageWatch,'_check',sample):w.check()
   self.assertEqual(len(begins),2);self.assertEqual(begins[0],begins[1])
 def test_exact_inverse(self):
  delta=json.loads((D/'SOURCE_DELTA01.json').read_text())
  for name,record in delta.items():
   source=(T/name).read_text();baseline=Path(record['baseline']).read_text();self.assertEqual(hashlib.sha256(baseline.encode()).hexdigest(),record['baseline_sha256'])
   for edit in reversed(record['replacements']):self.assertEqual(source.count(edit['new']),1);source=source.replace(edit['new'],edit['old'])
   self.assertEqual(source,baseline)
   ast.parse((T/name).read_text())
  self.assertFalse({'numpy','torch','networkx','scipy'}&set(sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
