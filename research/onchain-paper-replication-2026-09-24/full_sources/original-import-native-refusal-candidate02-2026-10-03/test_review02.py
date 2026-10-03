"""Actual source extraction and fake raw files only; no authority/numerical imports."""
import ast,hashlib,importlib.util,inspect,json,os,tempfile,types,unittest
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent
S=Path(os.environ.get('REFUSAL_SOURCE_DIR',D))
def load(name,file):
 spec=importlib.util.spec_from_file_location(name,file);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
cases=load('selected_cases',S/'refusal_cases.py');mutate=load('selected_mutate',S/'mutation_inputs.py')
inv=json.loads((F/'original-import-fixture-native-preparation03-2026-10-03/source_inventory03.json').read_bytes());ROOT=F.parents[2];by_target={r['target']:r for r in inv['source_inventory']}
# ROOT is checkout for relative source inventory paths.
ROOT=next(p for p in D.parents if (p/'pyproject.toml').is_file())
class Review(unittest.TestCase):
 def test_first_actual_owner_lease_message_matches_registered_fragment(self):
  row=by_target['tradingagents/research/onchain_replication/compact_owner.py'];raw=(ROOT/row['origin']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256']);tree=ast.parse(raw);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Owner');method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='lease')
  def require(v,m):
   if not v:raise ValueError(m)
  ns={'require':require,'Path':Path,'cache_key':lambda v:'pin','present':lambda p:p.exists()};exec(compile(ast.Module(body=[method],type_ignores=[]),'actual Owner.lease extracted','exec'),ns)
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp);(path/'failed.json').write_text('{}');record={'journal_directory':tmp}
   value=types.SimpleNamespace(poisoned=False,closed=False,check_binding=lambda:None,configuration=lambda:{},configuration_sha256='pin',reserved=1,_reserved=1,bound=types.SimpleNamespace(record=record))
   with self.assertRaises(ValueError) as caught:ns['lease'](value)
   self.assertEqual(str(caught.exception),cases.FRAGMENTS['lease-terminal'])
 def test_gate_mutates_actual_selected_kernel(self):
  rows={r['target']:r['sha256'] for r in inv['source_inventory']};identity_row=by_target['tradingagents/research/onchain_replication/imported_mcm_identity.py'];raw=(ROOT/identity_row['origin']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),identity_row['sha256'])
  constants={n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse(raw).body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('KERNEL','HELPER')}
  template={'family':'x','inputs':{},'source_files':rows,'charter':{},'runtime_hashes':{}};gate={'experiments':{'template':template},'families':{}};rendered={n:{'inputs':{}} for n in cases.NAMES};kwargs={}
  if 'imported_identity_source' in inspect.signature(mutate.draft_gate).parameters:kwargs['imported_identity_source']=raw
  result,_=mutate.draft_gate(gate,rendered,rows,{},**kwargs)
  actual=result['experiments'][cases.identity('kernel')]['source_files'];self.assertEqual(actual[constants['KERNEL']],'0'*64)
  missing=dict(rows);missing.pop(constants['KERNEL'])
  with self.assertRaises(ValueError):mutate.draft_gate(gate,rendered,missing,{},**kwargs)
if __name__=='__main__':unittest.main()
