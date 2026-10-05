"""Synthetic metadata/clock checks only; no graph/model or research execution."""
from pathlib import Path
import ast,hashlib,importlib.util,json,sys,types,unittest
D=Path(__file__).resolve().parent;M=D.parents[3];P=Path('tradingagents/research/onchain_replication');T=D/'candidate'/P
spec=importlib.util.spec_from_file_location('pilot_measurement_candidate',T/'real_pilot_throughput.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Clock:
 def __init__(self):self.value=100.
 def __call__(self):return self.value

def sample():
 c=Clock();nodes={f'{i:064x}':i+2 for i in range(7)};return c,nodes,m.MCMMeasurements(nodes,population_scope='resource_pilot_subset',clock=c)
def record(key,n):return {'graph_hash':key,'rows':n,'motifs':32,'cells':n*32}
class Checks(unittest.TestCase):
 def test_complete_full_denominator_and_zero_time(self):
  c,nodes,v=sample()
  for i,(key,n) in enumerate(nodes.items()):
   v.begin(key);c.value+=i;v.completed(key,record(key,n))
  result=v.summary({'status':'complete','optimizer_steps':1,'financial_fit_complete':False,'seconds':{'forward':0.,'backward':2.}})
  self.assertEqual(result['complete_graphs'],7);self.assertEqual(result['failed_graphs']+result['unavailable_graphs'],0)
  self.assertEqual(result['verified_completed_nodes'],sum(nodes.values()));self.assertEqual(result['verified_completed_motif_cells'],32*sum(nodes.values()))
  self.assertEqual(result['completed_mcm_seconds'],21.);self.assertEqual(result['completed_motif_cells_per_second'],32*sum(nodes.values())/21)
  self.assertEqual(result['one_update_phase_seconds'],{'forward':0.,'backward':2.});self.assertIsNone(result['guard_resource_evidence']);self.assertFalse(result['full_fold_fit'])
  c,nodes,v=sample()
  for k,n in nodes.items():v.begin(k);v.completed(k,record(k,n))
  self.assertIsNone(v.summary(None)['completed_motif_cells_per_second'])
 def test_partial_failure_never_credits_expected_counts(self):
  c,nodes,v=sample();keys=list(nodes)
  v.begin(keys[0]);c.value+=2;v.completed(keys[0],record(keys[0],nodes[keys[0]]))
  v.begin(keys[1]);c.value+=3
  wrong=record(keys[1],nodes[keys[1]]);wrong['cells']-=1
  with self.assertRaises(ValueError):v.completed(keys[1],wrong)
  v.failed(MemoryError('synthetic interrupted second graph'));r=v.summary(None)
  self.assertEqual((r['complete_graphs'],r['failed_graphs'],r['unavailable_graphs']),(1,1,5))
  self.assertEqual(r['verified_completed_motif_cells'],64);self.assertEqual(r['attempted_mcm_seconds'],5.)
  self.assertEqual(r['verified_motif_cells_per_attempted_second'],64/5)
  self.assertTrue(all(row['completed_motif_cells'] is None and row['completed_nodes'] is None for row in r['graphs'][1:]));self.assertIsNone(r['one_update_phase_seconds'])
  with self.assertRaises(ValueError):v.begin(keys[2])
  c,nodes,v=sample();v.failed(ValueError('before any MCM'));r=v.summary(None)
  self.assertEqual((r['complete_graphs'],r['failed_graphs'],r['unavailable_graphs']),(0,0,7));self.assertIsNone(r['verified_motif_cells_per_attempted_second'])
 def test_inverse_and_actual_failure_handler_preserves_fatal(self):
  d=json.loads((D/'SOURCE_DELTA01.json').read_text());raw=(T/'real_pilot_import_caller.py').read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),d['candidate_sha256']);lines=raw.decode().splitlines(True)
  for e in reversed(d['edits']):self.assertEqual(lines[e['new_start']:e['new_end']],e['new']);lines[e['new_start']:e['new_end']]=e['old']
  self.assertEqual(''.join(lines).encode(),(D/'caller.baseline.py').read_bytes())
  def functions(s):return {n.name:n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
  old=functions((D/'caller.baseline.py').read_text());new=functions(raw.decode())
  for n in old:
   if n!='execute':self.assertEqual(ast.dump(old[n]),ast.dump(new[n]))
  source=(M/P/'resource_fixture.py').read_text();reducer=functions(source)['_preserve_terminal'];fatal=functions((M/P/'owned_io.py').read_text())['_fatal']
  env={'CleanupFailure':type('SyntheticCleanupMarker',(BaseException,),{})};exec(compile(ast.Module(body=[fatal,reducer],type_ignores=[]),'accepted-reducer-extraction','exec'),env)
  def bad_measurement(error):raise OSError('synthetic timing publication error')
  primary=MemoryError('synthetic original fatal');env.update(error=primary,journal=None,measurements=types.SimpleNamespace(failed=bad_measurement),resource_fixture=types.SimpleNamespace(_preserve_terminal=env['_preserve_terminal']))
  handler=next(h for n in new['execute'].body if isinstance(n,ast.Try) for h in n.handlers if isinstance(h.type,ast.Name) and h.type.id=='BaseException' and h.name=='error')
  exec(compile(ast.Module(body=handler.body,type_ignores=[]),'actual-candidate-failure-handler','exec'),env)
  self.assertIs(env['primary'],primary)
  self.assertTrue(any(isinstance(n,ast.Raise) and isinstance(n.exc,ast.Name) and n.exc.id=='primary' for n in ast.walk(new['execute'])))
  self.assertFalse({'torch','numpy','scipy','networkx'}&set(sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
