"""Metadata and source-order controls only; no authority object construction."""
import ast,copy,hashlib,importlib,json,sys,types,unittest
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parents[3];P=Path('tradingagents/research/onchain_replication');C=D/'candidate'/P
pkg=types.ModuleType('preimport_probe');pkg.__path__=[str(C),str(ROOT/P)];sys.modules[pkg.__name__]=pkg
caller=importlib.import_module('preimport_probe.real_pilot_import_caller')
def resources():
 g=1024**3
 return {'memory_max_bytes':g,'memory_high_bytes':g,'reserve_bytes':3*g,'start_reserve_bytes':4*g,'disk_floor_bytes':10*g,'disk_paths':['/synthetic'],'wall_seconds':100,'native_unit_limits':{'file_size_bytes':1024},'storage_budget':{'root':'/synthetic','limits':{'max_allocated_bytes':g,'max_logical_bytes':g,'max_entries':100,'max_depth':8,'max_scan_seconds':5}}}
def plan():
 hashes=[str(i)*64 for i in range(7)]
 return {'schema_version':2,'kind':caller.KIND,'asset':'ETH','seed':11,'batch_size':16,'lookback_days':28,'cell_id':'synthetic-metadata-only','graph_inputs':{h:'g'+str(i) for i,h in enumerate(hashes)},'indices':list(range(16)),'decisions':[f'2022-06-{i:02d}' for i in range(7,23)],'graph_sequences':[hashes*4 for _ in range(16)],'population_plan_input':'population','model_input':'model','training_input':'training','model_execution':None,'max_checkpoint_bytes':1024,'outputs':{k:k+'.json' for k in ['summary','ledger','binding','journal']},'resource_policy':resources(),'archive_inputs':{'policy_input':'archive','transport_input':'transport'}}
def job():
 s={k:k for k in caller.KEYS};s.update(operation='produce',descriptor={'arm':'proposed','dictionary_origin':'imported-original-v1'},compact_archive_input='archive',compact_archive_transport_input='transport')
 return {'schema_version':1,'kind':'compact_resource','environment_input':'env','resources':resources(),'payload':{'representation_jobs':{'original':s}}}
class Checks(unittest.TestCase):
 def test_explicit_registered_pair_metadata_refusals(self):
  caller.validate_plan(plan());caller.schema(job())
  for change in [lambda p:p.update(schema_version=1),lambda p:p.update(archive_inputs=None),lambda p:p['archive_inputs'].update(transport_input='archive'),lambda p:p['archive_inputs'].update(unknown='x')]:
   p=plan();change(p)
   with self.assertRaises(ValueError):caller.validate_plan(p)
  for key in ['compact_archive_input','compact_archive_transport_input']:
   j=job();del j['payload']['representation_jobs']['original'][key]
   with self.assertRaises(ValueError):caller.schema(j)
 def test_legacy_plan_and_selection(self):
  p=plan();p.pop('archive_inputs');p.pop('resource_policy');p['schema_version']=1;caller.validate_plan(p)
  j=job();s=j['payload']['representation_jobs']['original'];s.pop('compact_archive_input');s.pop('compact_archive_transport_input');caller.schema(j)
 def test_actual_source_order_and_typed_run_join(self):
  source=(C/'original_import_stage.py').read_text();tree=ast.parse(source);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='attach')
  calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call)]
  owner=next(n for n in calls if ast.unparse(n.func)=='owners.Owner');attach=next(n for n in calls if ast.unparse(n.func)=='archive_owner_operations.attach')
  self.assertLess(owner.lineno,attach.lineno)
  completions=[n for n in calls if ast.unparse(n.func)=='complete_import'];self.assertTrue(any(n.lineno>attach.lineno for n in completions));self.assertIn('archive_owner_policy.select',ast.unparse(attach))
  for text in ['type(archive_transport) is archive_dispatch.View','type(archive_transport._context) is archive_dispatch.Context','context._run is run','context._outer();prepared._check()','owner.poisoned=True','io._close_after_failure(ledger.close,primary)']:self.assertIn(text,source)
  dispatch=(C/'archive_dispatch.py').read_text();self.assertIn("compact_routes=={name:True}",dispatch);self.assertIn("type(run) is ResearchRun",dispatch)
  self.assertIn('archive_context.close(primary)',(C/'real_pilot_import_caller.py').read_text())
 def test_exact_inverse_and_no_numeric_imports(self):
  for name,row in json.loads((D/'SOURCE_DELTA01.json').read_text()).items():
   s=(C/name).read_text();ast.parse(s)
   for e in reversed(row['edits']):self.assertEqual(s.count(e['new']),1);s=s.replace(e['new'],e['old'])
   self.assertEqual(s,Path(row['baseline']).read_text());self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),row['baseline_sha256'])
  self.assertFalse({'numpy','torch','scipy','networkx'}&set(sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
