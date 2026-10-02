import ast,json,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent

def schema():
 p=HERE/'resource_fixture.py'
 if not p.exists():raise AssertionError('explicit genuine worker adapter absent')
 t=ast.parse(p.read_text());nodes=[n for n in t.body if isinstance(n,ast.Assign) or isinstance(n,ast.FunctionDef) and n.name in ('require','selection','schema')]
 ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),ns);return ns

def job():
 hashes=['a'*64,'b'*64];fixture={'schema_version':1,'case':'success','data_kind':'synthetic-targets-original-dictionary','target_nodes':dict(zip(hashes,[2,3])),'target_provenance_input':'synthetic_targets'}
 selected={key:key for key in ('plan_input','producer','pair_checkpoint_input','original_dictionary_input','compact_policy_input','native_backend','original_dictionary_stage_input','compact_mcm_input','compact_mcm_output_input')};selected.update(operation='produce',descriptor={'arm':'proposed','dictionary_origin':'imported-original-v1','required_graphs':hashes,'resource_graph_inputs':dict(zip(hashes,['g1','g2'])),'resource_fixture':fixture})
 return {'schema_version':1,'kind':'compact_resource','resources':{'wall_seconds':1800,'memory_max_bytes':3*1024**3,'storage_budget':{'root':'/isolated','limits':{'max_logical_bytes':1024**3,'max_allocated_bytes':1024**3,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}}},'environment_input':'environment','payload':{'representation_jobs':{'r':selected}}}

class Contract(unittest.TestCase):
 def test_exact_finite_selection_and_refusals(self):
  ns=schema();value=job();ns['schema'](value)
  for mutate in (lambda x:x.update(kind='fit'),lambda x:x.update(schema_version=True),lambda x:x['payload']['representation_jobs'].update(second={}),lambda x:x['payload']['representation_jobs']['r']['descriptor']['resource_fixture'].update(case='arbitrary_callback'),lambda x:x['payload']['representation_jobs']['r']['descriptor']['resource_fixture']['target_nodes'].update({'a'*64:True})):
   x=job();mutate(x)
   with self.assertRaises(ValueError):ns['schema'](x)
 def test_actual_worker_route_and_completion_contract(self):
  text=(HERE/'job.py').read_text();self.assertIn("include_torch=job['kind'] in ('fit','neural_resource','compact_resource')",text);self.assertIn('resource_fixture.execute',text);self.assertIn('resource_fixture.worker_limits',text)
  text=(HERE/'resource_fixture.py').read_text()
  for value in ('resource_binding.open_first','original_import_preparation.prepare','original_import_stage.attach','ImportedExecution','produce_imported','mcm_features','owner._finish','resource_complete') :self.assertIn(value,text)
  journal=(HERE/'feature_journal.py').read_text();self.assertIn('def resource_complete(',journal);self.assertIn('not a scientific representation',journal)
 def test_full_source_join(self):
  source=(HERE/'imported_mcm_identity.py').read_text();self.assertIn('original-import-fixture-bridge-candidate-2026-10-02/imported_kernel.py',source)
  text=(HERE/'resource_fixture.py').read_text();self.assertIn('original_source_blobs',text);self.assertIn('run.admission.root',text);self.assertIn('StorageWatch',text)

if __name__=='__main__':unittest.main()
