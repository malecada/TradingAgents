import ast,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent

def functions():
 tree=ast.parse((HERE/'resource_fixture.py').read_text())
 names={'require','failure_rows','validate_records','retained_actions'}
 nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
 ns={'CELLS':['import-target-01','import-target-02']};exec(compile(ast.Module(body=nodes,type_ignores=[]),'candidate','exec'),ns);return ns

class Boundaries(unittest.TestCase):
 def test_limit_applies_in_actual_worker_before_claim(self):
  tree=ast.parse((HERE/'job.py').read_text());worker=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='worker')
  calls=[(n.lineno,ast.unparse(n.func)) for n in ast.walk(worker) if isinstance(n,ast.Call)]
  limits=[line for line,name in calls if name=='resource_fixture.worker_limits']
  claims=[line for line,name in calls if name=='ResearchRun.start']
  self.assertEqual(len(limits),1);self.assertLess(limits[0],claims[0])
 def test_exact_missing_denominator(self):
  f=functions()['failure_rows'];out=f([],ValueError('stop'))
  self.assertEqual([v['status'] for v in out],['failed','unavailable'])
  first={'id':'import-target-01','status':'complete'};self.assertEqual(f([first],ValueError('stop'))[0]['id'],'import-target-02')
  self.assertEqual(first,{'id':'import-target-01','status':'complete'})
 def test_duplicate_or_reordered_complete_refused(self):
  f=functions()['validate_records'];keys=['a','b'];counts={'a':2,'b':3}
  rows=[{'graph_hash':k,'rows':counts[k],'motifs':32,'cells':32*counts[k]} for k in keys]
  f(rows,keys,counts)
  for bad in ([rows[0],rows[0]],rows[::-1],[rows[0],dict(rows[1],cells=95)]):
   with self.assertRaises(ValueError):f(bad,keys,counts)
 def test_retained_actions_first_fatal_and_all_callbacks(self):
  tree=ast.parse((HERE/'import_metadata.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='close_actions')
  class CleanupFailure(BaseException):pass
  class IO:pass
  IO.CleanupFailure=CleanupFailure
  ns={'io':IO};exec(compile(ast.Module(body=[node],type_ignores=[]),'accepted-reducer','exec'),ns)
  f=functions()['retained_actions'];seen=[];fatal=MemoryError('body')
  def bad():seen.append('bad');raise OSError('tail')
  def last():seen.append('last')
  with self.assertRaises(MemoryError) as caught:f(fatal,[bad,last],ns['close_actions'])
  self.assertIs(caught.exception,fatal);self.assertEqual(seen,['bad','last'])
  later=SystemExit(17);seen.clear()
  def terminate():seen.append('fatal');raise later
  with self.assertRaises(SystemExit) as caught:f(ValueError('ordinary'),[bad,terminate,last],ns['close_actions'])
  self.assertIs(caught.exception,later);self.assertEqual(seen,['bad','fatal','last']);self.assertIsNotNone(later.__cause__)
 def test_ordinary_body_only_retains_return(self):
  f=functions()['retained_actions'];seen=[]
  f(ValueError('ordinary'),[lambda:seen.append(1)],lambda actions:[a() for a in actions])
  self.assertEqual(seen,[1])

if __name__=='__main__':unittest.main()
