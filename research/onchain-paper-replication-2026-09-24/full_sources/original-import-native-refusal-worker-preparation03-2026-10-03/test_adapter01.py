"""Exact source and bounded refusal metadata tests; no real authority objects."""
import ast,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;ROOT=D.parents[3]
inv=json.loads((F/'original-import-native-refusal-candidate05-2026-10-03/source_inventory05.json').read_text());rows={x['target']:x for x in inv['source_inventory']}
# Only stdlib helper sources, not the tradingagents package, are imported.
for target in ('fixture_tools/raw_receipts01.py','fixture_tools/refusal_cases.py','fixture_tools/original_semantics.py','fixture_tools/refusal_evidence.py','fixture_tools/refusal_stage.py','fixture_tools/refusal_pair_identity.py','fixture_tools/resource_policy05.py','fixture_tools/mutation_inputs.py'):
 row=rows[target];path=ROOT/row['origin'];sys.path.insert(0,str(path.parent))
for path in (F/'original-import-native-refusal-candidate04-2026-10-03',F/'original-import-native-refusal-candidate05-2026-10-03',D):sys.path.insert(0,str(path))
import refusal_oracle_evidence01 as oracle
import refusal_cases as cases
class Tests(unittest.TestCase):
 def test_mathematical_callbacks_and_mutations_unchanged(self):
  old=ast.parse((F/'original-import-native-refusal-candidate02-2026-10-03/resource_refusal.py').read_text());new=ast.parse((D/'resource_refusal.py').read_text())
  for name in ('active_case','score_callback','compute_callback','returned','observe','forbidden_compute'):
   get=lambda t:next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name);self.assertEqual(ast.dump(get(old)),ast.dump(get(new)))
 def test_no_owner_requires_absent_oracle(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);name=cases.identity('job-input');p=root/'research_runs'/name/'outputs';p.mkdir(parents=True);(p/'resource-summary.json').write_text(json.dumps({'oracle_observation':None}));claim=json.dumps({'experiment_id':name}).encode()
   self.assertIsNone(oracle.authenticate_oracle(root,'job-input',claim));(p.parent/'refusal-oracle.json').write_text('{}')
   with self.assertRaises(ValueError):oracle.authenticate_oracle(root,'job-input',claim)
 def test_owner_requires_durable_oracle_not_summary_label(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);name=cases.identity('wrong-ack');p=root/'research_runs'/name/'outputs';p.mkdir(parents=True);(p/'resource-summary.json').write_text(json.dumps({'oracle_observation':{'claimed':True}}));claim=json.dumps({'experiment_id':name}).encode()
   with self.assertRaises(FileNotFoundError):oracle.authenticate_oracle(root,'wrong-ack',claim)
   (p.parent/'refusal-oracle.json').write_text('{}')
   with self.assertRaises(ValueError):oracle.authenticate_oracle(root,'wrong-ack',claim)
 def test_actual_worker_chain_not_reimplemented(self):
  worker=ast.parse((D/'resource_refusal.py').read_text());text=ast.unparse(worker);self.assertIn('resource_binding.open_first',text);self.assertIn('original_import_stage.attach',text);self.assertIn('Target(execution, graph, key)',text)
  outer=(D/'refusal_outer01.py').read_text();self.assertIn('job._command(',outer);self.assertIn("outer.mkdir(exist_ok=False)",outer);self.assertIn("process.returncode==1",outer)
  pre=(D/'refusal_preclaim01.py').read_text();self.assertIn('resources.assert_guarded_worker',pre);self.assertIn('observation=preclaim(',pre);self.assertNotIn('ResearchRun.start(',pre)
 def test_finite_counts_and_no_numeric_top_level_imports(self):
  self.assertEqual((len(cases.NAMES),len(cases.GROUPS),len(cases.PRECLAIM),sum(x not in cases.PRECLAIM for x in cases.NAMES),sum(x not in cases.NO_OWNER for x in cases.NAMES),sum(x not in cases.NO_JOURNAL for x in cases.NAMES)),(27,16,4,23,17,19))
  for p in D.glob('*.py'):
   t=ast.parse(p.read_text());compile(t,str(p),'exec')
   for n in t.body:
    if isinstance(n,ast.Import):self.assertFalse(any(x.name.split('.')[0] in ('numpy','torch','scipy') for x in n.names))
 def test_exact_all27_template_draft(self):
  path=F/'original-import-native-refusal-candidate05-2026-10-03/test_inputs05.py';spec=importlib.util.spec_from_file_location('qualified_inputs05',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);base,_,sources,sourceinv=mod.render()
  primary,_=mod.generator.registration(rendered={'success':base,'second_target_publication_failure':base},source_files=sources,runtime_hashes={'qualified_only':'a'*64})
  import templates01
  row=next(r for r in sourceinv['source_inventory'] if r['target']=='tradingagents/research/onchain_replication/imported_mcm_identity.py')
  value=templates01.prepare(base,primary,source_files=sources,runtime_hashes={'qualified_only':'a'*64},imported_identity_source=(ROOT/row['origin']).read_bytes(),runtime={'qualified_only':True},native_environment={'qualified_only':True},capsule='/qualified-unregistered-synthetic',source_commit='a'*40)
  self.assertEqual(value['release']['status'],'draft-not-released');self.assertTrue(value['release']['remaining']);self.assertEqual(value['protocol']['max_oracle_pairs'],1088);self.assertEqual(len(value['registration']['experiments']),27)
if __name__=='__main__':
 result=unittest.main(exit=False);assert not any(n.split('.')[0] in ('numpy','scipy','torch','tradingagents') for n in sys.modules);sys.exit(not result.result.wasSuccessful())
