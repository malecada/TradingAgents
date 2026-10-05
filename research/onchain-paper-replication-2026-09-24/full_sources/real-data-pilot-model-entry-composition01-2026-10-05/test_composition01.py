"""Cross-seam tests only; no genuine worker, arrays or prior test-suite replay."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys,types,unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
D=Path(__file__).resolve().parent;P=Path('tradingagents/research/onchain_replication');T=D/'candidate'/P
# Reuse immutable schema fixture constructors and stdlib loader, not its tests.
spec=importlib.util.spec_from_file_location('previous_policy_fixture',D.parent/'real-data-pilot-full-size-policy01-2026-10-05/test_policy01.py');fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
caller=fixture.load('policy_offline.composed_caller',T/'real_pilot_import_caller.py')
population=fixture.load('policy_offline.real_pilot_population',T/'real_pilot_population.py')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def pilot(job,version,subset=False):
 p=fixture.plan(job,version);p['decisions']=population.DECISIONS[:]
 if subset:p.update(population_scope=population.SCOPE,indices=None)
 return p

def branch(p):
 """Execute the actual population dispatch AST only, with metadata-return mocks."""
 tree=ast.parse((T/'real_pilot_import_caller.py').read_text());body=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute').body
 start=next(i for i,n in enumerate(body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='resource_subset' for t in n.targets))
 stop=next(i for i,n in enumerate(body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='control' for t in n.targets))
 assert any(isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='admitted' for n in body[:start])
 offset=0 if p.get('population_scope')==population.SCOPE else p['indices'][0]
 selected=[types.SimpleNamespace(decision_at=d,graph_hashes=g,input_prices=(0,)*28) for d,g in zip(p['decisions'],p['graph_sequences'],strict=True)]
 examples=types.SimpleNamespace(train=[None]*offset+selected);calls=[]
 def subset(*args):calls.append('subset');return examples,'subset-scaler',list(range(16))
 def full(*args):calls.append('full');return {'population':{},'provenance':{'source_admission':{'asset':'ETH'}}}
 def parse(*args):calls.append('financial-parser');return examples,'full-scaler'
 env={'__package__':'policy_offline','p':p,'run':None,'require':caller.require,'produce_registered_population':full,'population_from_record':parse}
 with patch.object(population,'produce',side_effect=subset):exec(compile(ast.Module(body=body[start:stop],type_ignores=[]),str(T/'real_pilot_import_caller.py'),'exec'),env)
 return calls,env['indices']

class Checks(unittest.TestCase):
 def test_01_both_inverses_helper_native_unchanged(self):
  record=json.loads((D/'COMPOSITION01.json').read_text());new=(T/'real_pilot_import_caller.py').read_text()
  for row in record['baselines']:
   lines=new.splitlines(True)
   for e in reversed(row['edits']):self.assertEqual(lines[e['new_start']:e['new_end']],e['new']);lines[e['new_start']:e['new_end']]=e['old']
   self.assertEqual(''.join(lines).encode(),Path(row['origin']).read_bytes());self.assertEqual(sha(Path(row['manifest'])),row['manifest_sha256']);self.assertEqual(sha(Path(row['origin'])),row['sha256'])
  self.assertEqual(sha(T/'real_pilot_population.py'),record['helper']['sha256']);self.assertEqual((T/'real_pilot_population.py').read_bytes(),Path(record['helper']['path']).read_bytes())
  for row in record['native_policy_reuse']:self.assertEqual(sha(Path(row['path'])),row['sha256'])
  old=fixture.ast_functions(D/'baseline/full-size-policy.py');current=fixture.ast_functions(T/'real_pilot_import_caller.py')
  for n,v in old.items():
   if n not in {'validate_plan','execute'}:self.assertEqual(v,current[n],n)
 def test_02_schema_cross_product_no_scope_fallback(self):
  j=fixture.make_job(D,True)
  for version,subset in [(1,False),(2,False),(2,True)]:
   p=pilot(j,version,subset);caller.validate_plan(p)
  invalid=[]
  for scope in [None,'fullfold','resource_pilot_subse','']:
   p=pilot(j,2,True);p['population_scope']=scope;invalid.append(p)
  p=pilot(j,1);p['population_scope']=population.SCOPE;p['indices']=None;invalid.append(p)
  p=pilot(j,2);p['indices']=None;invalid.append(p)
  p=pilot(j,2,True);p['indices']=list(range(16));invalid.append(p)
  for subset in [False,True]:
   p=pilot(j,2,subset);del p['resource_policy'];invalid.append(p)
  for p in invalid:
   with self.subTest(scope=p.get('population_scope'),version=p['schema_version']),self.assertRaises(ValueError):caller.validate_plan(p)
 def test_03_all_routes_bind_same_exact_resources(self):
  with TemporaryDirectory(dir=D) as tmp:
   root=Path(tmp);j=fixture.make_job(root,True);ad=types.SimpleNamespace(root=root)
   for subset in [False,True]:
    p=pilot(j,2,subset);caller.validate_plan(p);caller._bind_resources(ad,j,p)
    p['resource_policy']['native_unit_limits']['file_size_bytes']-=1
    with self.assertRaisesRegex(ValueError,'plan/job'):caller._bind_resources(ad,j,p)
   with self.assertRaises(ValueError):caller._bind_resources(ad,j,pilot(j,1))
 def test_04_actual_dispatch_branch_selects_scope_not_version(self):
  j=fixture.make_job(D,True)
  for version in [1,2]:
   p=pilot(j,version);p['indices']=list(range(5,21));caller.validate_plan(p)
   calls,indices=branch(p);self.assertEqual(calls,['full','financial-parser']);self.assertEqual(indices,list(range(5,21)))
  p=pilot(j,2,True);caller.validate_plan(p);calls,indices=branch(p)
  self.assertEqual(calls,['subset']);self.assertEqual(indices,list(range(16)))
 def test_05_helper_contract_matches_composed_plan(self):
  p=pilot(fixture.make_job(D,True),2,True)
  q={'schema_version':1,'population_scope':population.SCOPE,'financial_fit_complete':False,'fold':'2024','scope_input':'scope','calendar_input':'calendar','price_panel_input':'price','graphs':dict(zip(population.WEEKS,p['graph_inputs'].values(),strict=True)),'outputs':{'resource_population':'subset.json','binding':'subset-binding.json'}}
  population.validate_plan(q,p)
  with self.assertRaises((ValueError,KeyError)):population.validate_plan(q,pilot(fixture.make_job(D,True),2))
  self.assertFalse({'numpy','torch','scipy','networkx'}&set(sys.modules))

if __name__=='__main__':unittest.main(verbosity=2)
