"""Source/generator checks only; no gate publication, admission or authority."""
import ast,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;FULL=HERE.parent
SOURCE=HERE/'generate_inputs01.py'
if len(sys.argv)>1 and sys.argv[1]=='--source':SOURCE=Path(sys.argv.pop(2));sys.argv.pop(1)
CAP=FULL/'original-import-native-release-2026-10-03/capsule01'
def read(path):return json.loads(path.read_bytes())
def rendered():
    spec=importlib.util.spec_from_file_location('actual_successor_generator',SOURCE);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    old=read(CAP/'fixture-registration.json');release=read(FULL/'original-import-native-release-2026-10-03/release01.json')
    original=read(FULL/'original-import-fixture-native-preparation-2026-10-03/original_inputs01.json')
    evidence=read(FULL/'original-dictionary-bridge-investigation-2026-10-02/evidence01.json');matching=read(FULL.parent/'config/matching-stable.json')
    environment=read(CAP/'fixture_inputs/success/environment.json')
    package={name:pin for name,pin in release['source_files'].items() if name.startswith('tradingagents/')}
    inputs={case:module.inputs(case=case,capsule=str(HERE/'capsule02'),source_anchor=release['source_anchor'],source_files=package,original_index=original,evidence=evidence,matching=matching,environment=environment) for case in ['success','second_target_publication_failure']}
    reference={'extension':{'path':'fixture_budget/cumulative-extension01.json','sha256':hashlib.sha256((HERE/'cumulative-extension01.json').read_bytes()).hexdigest()},'review':{'path':'fixture_budget/cumulative-extension-review01.json','sha256':hashlib.sha256((HERE/'cumulative-extension-review01.json').read_bytes()).hexdigest()}}
    gate,charters=module.registration(rendered=inputs,source_files=release['source_files'],runtime_hashes=old['experiments']['original-import-native-success-20261003-01']['runtime_hashes'],historical_gate=old,budget_reference=reference)
    return old,gate,charters
class Successor(unittest.TestCase):
    def test_case_charters_match_the_accepted_denominators(self):
        old,gate,charters=rendered();allocation=read(HERE/'successor-allocation01.json')
        success=gate['experiments']['original-import-native-success-20261003-02'];failure=gate['experiments']['original-import-native-publication-failure-20261003-02']
        self.assertEqual(allocation['case_denominators']['success']['scalar_reference_comparisons'],160)
        self.assertEqual(allocation['case_denominators']['second_target_publication_failure']['first_target_scalar_reference_comparisons'],64)
        self.assertEqual(allocation['case_denominators']['second_target_publication_failure']['second_target_numerical_cells'],96)
        success_text=charters[success['charter']['path']].decode()
        self.assertIn('all160',success_text)
        self.assertTrue('scalar-reference comparisons' in success_text or 'scalar reference' in success_text)
        text=charters[failure['charter']['path']].decode()
        self.assertIn('complete64 scalar-reference comparisons',text);self.assertIn('96 numerical cells',text);self.assertIn('remain unavailable',text)
        self.assertNotIn('complete all160',text)
    def test_new_charter_paths_preserve_every_historical_charter(self):
        old,gate,charters=rendered();historical={e['charter']['path'] for e in old['experiments'].values()}
        self.assertFalse(historical&set(charters))
        for name,entry in old['experiments'].items():self.assertEqual(entry,gate['experiments'][name])
        self.assertEqual(old['families'],gate['families']);self.assertEqual(old['datasets'],gate['datasets'])
    def test_only_fresh_fixed_identities_and_closed_parent_are_added(self):
        old,gate,charters=rendered();names=set(gate['experiments'])-set(old['experiments'])
        self.assertEqual(names,{'original-import-native-success-20261003-02','original-import-native-publication-failure-20261003-02'})
        for name in names:
            self.assertEqual(gate['experiments'][name]['parent'],'original-import-native-success-20261003-01')
            self.assertEqual(gate['experiments'][name]['cumulative_budget_extension']['extension']['sha256'],hashlib.sha256((HERE/'cumulative-extension01.json').read_bytes()).hexdigest())
    def test_graph_inputs_arrays_and_numerical_generator_functions_unchanged(self):
        before=ast.parse((HERE/'generate_inputs.baseline.py').read_bytes());after=ast.parse(SOURCE.read_bytes())
        def strip(tree):return ast.dump(ast.Module(body=[n for n in tree.body if not isinstance(n,ast.FunctionDef) or n.name!='registration'],type_ignores=[]))
        changed=[]
        for node in ast.walk(after):
            if isinstance(node,ast.Dict):
                for key,value in zip(node.keys,node.values):
                    if isinstance(key,ast.Constant) and key.value=='edge_chunk' and isinstance(value,ast.Constant) and value.value==4096:
                        changed.append(value);value.value=65536
        self.assertEqual(len(changed),1)
        self.assertEqual(strip(before),strip(after))
if __name__=='__main__':unittest.main(verbosity=2)
