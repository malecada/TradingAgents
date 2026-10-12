"""Focused new caller/producer selector check; no admission, numerical work or claim."""
import ast,copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from tradingagents.research.onchain_replication import real_pilot_import_caller as caller
P=Path('research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full39-binding-preparation01-2026-10-12/public01/pilot.json')
class Check(unittest.TestCase):
 def test_selected_plan(self):
  p=json.loads(P.read_bytes());p['weekly_graph_digest_pin']=True
  self.assertIs(caller.validate_plan(p),p)
 def test_unselected_plan(self):
  p=json.loads(P.read_bytes());self.assertIs(caller.validate_plan(p),p)
 def test_invalid_selector(self):
  for v in (1,0,None,'true',{},[]):
   p=json.loads(P.read_bytes());p['weekly_graph_digest_pin']=v
   with self.assertRaises(ValueError):caller.validate_plan(p)
 def test_false_selector(self):
  p=json.loads(P.read_bytes());p['weekly_graph_digest_pin']=False
  self.assertIs(caller.validate_plan(p),p)
 def test_compact_dispatch(self):
  s=Path('tradingagents/research/onchain_replication/compact_mcm.py').read_text();t=ast.parse(s)
  f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='produce_imported')
  self.assertIn('weekly_digest_pin',[a.arg for a in f.args.kwonlyargs])
  calls=[n for n in ast.walk(f) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Target']
  self.assertEqual(len(calls),1)
  self.assertIn('weekly_digest_pin',ast.get_source_segment(s,calls[0]))
if __name__=='__main__':unittest.main()
