"""Finite deterministic input source tests; fake source/runtime pins are explicit."""
import ast,importlib.util,json,unittest
from pathlib import Path
import mutation_inputs as mutate
import refusal_cases as cases
D=Path(__file__).resolve().parent;F=D.parent
spec=importlib.util.spec_from_file_location('generator',F/'original-import-fixture-native-preparation02-2026-10-03/generate_inputs01.py');generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
class Inputs(unittest.TestCase):
 def test_all27_inputs_exact_deltas_and_source_schema(self):
  index=json.loads((F/'original-import-fixture-native-preparation-2026-10-03/original_inputs01.json').read_text());evidence=json.loads((F/'original-dictionary-bridge-investigation-2026-10-02/evidence01.json').read_text());matching=json.loads((F.parent/'config/matching-stable.json').read_text())
  source={f'qualified_fake_{i}.py':'a'*64 for i in range(142)}
  base=generator.inputs(case='success',capsule='/qualified-synthetic',source_anchor='a'*40,source_files=source,original_index=index,evidence=evidence,matching=matching,environment={'qualified_fake':True})
  complete=source|{'resource_refusal.py':'b'*64,'resource_refusal_cases.py':'c'*64};allcases={}
  tree=ast.parse((D/'resource_fixture.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('require','selection','schema') or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('GIB','FILE_MAX','KEYS') for t in n.targets)];ns={'cases':cases};exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-refusal-schema','exec'),ns)
  for variant in cases.NAMES:
   item=mutate.render(base,variant,complete);allcases[variant]=item;self.assertEqual(item,mutate.render(base,variant,complete));job=json.loads(item['files'][item['job_path']])
   if variant=='kind':
    with self.assertRaises(ValueError):ns['schema'](job)
   else:ns['schema'](job)
   descriptor=job['payload']['representation_jobs']['original32']['descriptor'];self.assertEqual(descriptor['configs']['matching'],matching);self.assertEqual(sum(x['nodes']*32 for x in item['targets']),160)
   for row in item['inputs'].values():
    if row['path'] in item['files']:self.assertEqual(mutate.sha(item['files'][row['path']]),row['sha256'])
  primary,_=generator.registration(rendered={'success':base,'second_target_publication_failure':base},source_files=source,runtime_hashes={'qualified_fake':'a'*64})
  exact=complete|{p:'a'*64 for p in ('tradingagents/research/onchain_replication/compact_mcm.py','research/onchain-paper-replication-2026-09-24/full_sources/original-dictionary-import-mcm-implementation03-2026-10-02/imported_kernel.py','research/onchain-paper-replication-2026-09-24/full_sources/pair-workload-2026-09-30/workload.py')}
  gate,files=mutate.draft_gate(primary,allcases,exact,{'qualified_fake':'a'*64});self.assertEqual(len(gate['experiments']),27);self.assertEqual(gate['families']['import-refusal-engineering']['attempt_budget'],23)
  self.assertEqual(sum('0'*64 in e['source_files'].values() for e in gate['experiments'].values()),3)
if __name__=='__main__':unittest.main()
