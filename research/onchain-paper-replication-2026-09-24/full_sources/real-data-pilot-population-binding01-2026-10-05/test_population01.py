import ast,importlib.util,json,tempfile,hashlib,unittest
from pathlib import Path
from types import SimpleNamespace
import real_pilot_population as population
import prepare01
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('candidate_caller',HERE/'real_pilot_import_caller.py');caller=importlib.util.module_from_spec(spec);spec.loader.exec_module(caller)

class Checks(unittest.TestCase):
    def test_actual_position_derivation_and_missing_refusal(self):
        rows=[SimpleNamespace(decision_at='2022-06-06T00:00:00Z')]+[SimpleNamespace(decision_at=x) for x in population.DECISIONS]
        self.assertEqual(population.selected_positions(rows,population.DECISIONS),list(range(1,17)))
        with self.assertRaises(ValueError):population.selected_positions(rows[:-1],population.DECISIONS)
        with self.assertRaises(ValueError):population.selected_positions(rows[::-1],population.DECISIONS)

    def test_metadata_emission_and_deferred_indices(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            refs={}
            for i,w in enumerate(population.WEEKS):
                p=Path(tmp)/f'{i}.json';p.write_text(json.dumps({'graph_hash':f'{i:064x}','metadata':{'asset':'ETH','start_utc':w}}));refs[w]={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            result=prepare01.prepare(refs);p=result['pilot_plan'];plan=result['population_plan']
            self.assertIsNone(p['indices']);caller.validate_plan(p);population.validate_plan(plan,p)
            p['indices']=list(range(16))
            with self.assertRaises(ValueError):caller.validate_plan(p)
            p['indices']=None;plan['population_scope']='full_paper_fold'
            with self.assertRaises(ValueError):population.validate_plan(plan,p)
            refs.pop(population.WEEKS[-1])
            with self.assertRaises(ValueError):prepare01.prepare(refs)

    def test_subset_wrapper_rejected_by_original_financial_parser(self):
        root=next(p for p in HERE.parents if (p/'tradingagents/research/onchain_replication/job_payload.py').is_file())
        tree=ast.parse((root/'tradingagents/research/onchain_replication/job_payload.py').read_bytes())
        nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='population_from_record'];ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'original-financial-parser','exec'),ns)
        with self.assertRaisesRegex(ValueError,'population payload schema differs'):
            ns['population_from_record']({'schema_version':1,'population_scope':population.SCOPE,'resource_rows':[],'full_fold_population':False})

    def test_worker_refuses_non_authority_before_numerical_import(self):
        with self.assertRaisesRegex(ValueError,'genuine registered worker'):
            population.produce(object(),'not-an-input',{})
        import sys
        self.assertFalse(any(x in sys.modules for x in ('numpy','torch','scipy','pyarrow')))

if __name__=='__main__':unittest.main()
