"""Source-only actual validators, not real admission or authority."""
import ast,json,types,unittest
from pathlib import Path
import generate_inputs01 as generate
D=Path(__file__).resolve().parent;F=D.parent
class Schemas(unittest.TestCase):
    def test_generated_job_reaches_actual_finite_schema(self):
        index=json.loads((F/'original-import-fixture-native-preparation-2026-10-03/original_inputs01.json').read_text());evidence=json.loads((F/'original-dictionary-bridge-investigation-2026-10-02/evidence01.json').read_text());matching=json.loads((F.parent/'config/matching-stable.json').read_text())
        source={f'source-{i}.py':'a'*64 for i in range(142)}
        items={case:generate.inputs(case=case,capsule='/future-capsule',source_anchor='a'*40,source_files=source,original_index=index,evidence=evidence,matching=matching,environment={'qualified_fake':True}) for case in ('success','second_target_publication_failure')}
        tree=ast.parse((F/'original-import-fixture-native-preparation-2026-10-03/resource_fixture.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('require','selection','schema') or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('GIB','FILE_MAX','KEYS') for t in n.targets)]
        ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-selected-resource-schema','exec'),ns)
        for item in items.values():
            job=json.loads(item['files'][item['job_path']]);ns['schema'](job)
            self.assertEqual(sum(t['nodes']*32 for t in item['targets']),160)
            self.assertEqual(job['payload']['representation_jobs']['original32']['descriptor']['configs']['matching'],matching)
            job['resources']['native_unit_limits']['file_size_bytes']=True
            with self.assertRaises(ValueError):ns['schema'](job)
        gate,files=generate.registration(rendered=items,source_files=source,runtime_hashes={'qualified_fake':'b'*64})
        self.assertEqual(len(gate['experiments']),2);self.assertEqual(gate['families']['import-engineering']['attempt_budget'],2)
        for exp in gate['experiments'].values():self.assertEqual({r['dataset'] for r in exp['inputs'].values()},{r['dataset'] for r in exp['windows']})
if __name__=='__main__':unittest.main()
