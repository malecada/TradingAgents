"""Bounded AST/hash source tests, no package/array imports or authority."""
import ast,hashlib,json,os,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;ROOT=P.parents[3]
import prepare_metadata_composed01 as prep
class Tests(unittest.TestCase):
 def setUp(self):self.inv=json.loads((P/'source_inventory01.json').read_bytes());self.rows={r['target']:r for r in self.inv['source_inventory']}
 def test_complete_materialization_source_map(self):
  root=P/'source-bodies'
  if os.environ.get('PREDECESSOR'):
   path=F/'neural-cold-feature-handoff-proof-preparation01-2026-10-03/prepare_metadata01.py';fn=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='build');i=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='source');env={'root':root,'digest':prep.digest};exec(compile(ast.Module(body=fn.body[i:i+3],type_ignores=[]),str(path),'exec'),env);value=env['source']
  else:value=prep.source_mapping(root,self.inv)
  self.assertEqual(value,{k:v['sha256'] for k,v in self.rows.items()})
 def test_exact_science_outer_bodies(self):
  for rel,name,key in [('neural-cold-feature-handoff-proof-preparation01-2026-10-03','install-map01.json','source'),('neural-cold-feature-handoff-proof-outer-preparation02-2026-10-03','install-map02.json','origin')]:
   for row in json.loads((F/rel/name).read_bytes())['files']:self.assertEqual((ROOT/row[key]).read_bytes(),(P/'source-bodies'/row['target']).read_bytes())
 def test_base_numerics_and_metadata_cleanup_preserved(self):
  base=json.loads((F/'original-import-native-successor-preparation03-2026-10-03/source_inventory01.json').read_bytes());changed={Path(n).name for n in ('compact_native_producer.py','job_payload.py','compact_terminal.py','compact_publication.py','compact_closure.py','job.py')}
  for row in base['source_inventory']:
   if Path(row['target']).name not in changed:self.assertEqual(row['sha256'],self.rows[row['target']]['sha256'])
  self.assertEqual(self.rows['tradingagents/research/onchain_replication/compact_mcm.py']['sha256'],'08150fb38943717d7f173c30b6dda12c494d8663654670c6b8cd865df1dd3caf')
 def test_typed_archive_separate_and_no_replay(self):
  for n in ('archive_owner_seal.py','archive_consume.py','archive_chunks.py','compact_stage.py'):
   self.assertIn('tradingagents/research/onchain_replication/'+n,self.rows)
  text=(P/'source-bodies/tradingagents/research/onchain_replication/compact_cold_features.py').read_text();self.assertIn('archive_owner_seal.check_content',text);self.assertIn('actual compact terminal required; resource-only receipts refused',text)
 def test_weakref_slots_only(self):
  science=F/'neural-cold-feature-handoff-proof-preparation01-2026-10-03'
  for n in ('compact_terminal.py','compact_publication.py','compact_closure.py'):
   a=ast.parse((science/(n+'.baseline')).read_text());b=ast.parse((science/n).read_text())
   class Remove(ast.NodeTransformer):
    def visit_Tuple(self,node):node=self.generic_visit(node);node.elts=[v for v in node.elts if not isinstance(v,ast.Constant) or v.value!='__weakref__'];return node
   self.assertEqual(ast.dump(Remove().visit(a)),ast.dump(Remove().visit(b)))
 def test_source_compile_only(self):
  for target in self.rows:
   if target.endswith('.py'):compile((P/'source-bodies'/target).read_bytes(),target,'exec')
  self.assertFalse(any(n.split('.')[0] in {'numpy','torch','scipy','pandas','tradingagents'} for n in sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
