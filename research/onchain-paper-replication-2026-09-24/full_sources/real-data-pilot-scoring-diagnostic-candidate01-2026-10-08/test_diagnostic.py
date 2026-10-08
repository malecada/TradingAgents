import importlib.util,json,sys,copy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from tests.research.onchain_replication import test_compact_matcher as tiny
from tradingagents.research.onchain_replication.compact_pair_log import PairLog
from tradingagents.research.onchain_replication.matching_identity import graph_identity
ROOT=Path(__file__).resolve().parent
PREFIX='tradingagents.research.onchain_replication.'
def module(name,file):
 spec=importlib.util.spec_from_file_location(PREFIX+name,ROOT/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
telemetry=module('_diagnostic','real_pilot_partial_progress.py')
matcher=module('_diag_matcher','compact_matcher.py')
caller=module('_diag_caller','real_pilot_import_caller.py')
selection={'schema_version':1,'max_completed_pairs':2,'checkpoint_every_pairs':1,'checkpoint_relative':'scoring-diagnostic/progress.json'}
def make(root,diagnostic):
 a=tiny.graph([[0.],[.3]],[(0,1,.1)]);b=tiny.graph([[.2],[.7]],[(1,0,.4)]);c=tiny.config()|{'beta_final':1.}
 scope=matcher.scope(c,tiny.CONTEXT,tiny.POLICY,'f'*64,tiny.SCHEDULE)
 log=PairLog(root/'log',owner='d'*64,scope=scope,limits={'chunk_events':16,'max_events':100,'max_pairs':10,'max_logical_bytes':40000},max_iterations=c['max_iterations'],lease=lambda:None)
 with patch.dict(sys.modules,{PREFIX+'real_pilot_partial_progress':telemetry}):
  m=matcher.CompactMatcher(log,config=c,context=tiny.CONTEXT,policy=tiny.POLICY,workload_sha256='f'*64,schedule=tiny.SCHEDULE,lease=lambda:None,diagnostic=diagnostic)
 if diagnostic:diagnostic.begin('1'*64,log)
 purpose={'schema_version':1,'kind':'mcm','workload_sha256':'f'*64,'typed_graphs':[graph_identity(a),graph_identity(b)],'center_index':0,'motif_index':0}
 return m,log,a,b,c,purpose

def test_real_tiny_engine_stops_after_acknowledged_limit(tmp_path):
 d=telemetry.ScoringDiagnostic(selection,tmp_path,claim_sha256='a'*64,source='b'*40)
 m,log,a,b,c,p=make(tmp_path,d)
 try:
  first=m(p,a,b);assert first['score']==tiny.match_reference(a,b,c).score
  with pytest.raises(telemetry.PlannedScoringStop):m(p|{'motif_index':1},a,b)
  assert log.state['completed_pairs']==2 and log.state['pending'] is None and log.events==4
  assert m.poisoned and d.completed==2 and d.stopped
  with pytest.raises(ValueError):m(p|{'motif_index':2},a,b)
  assert log.events==4
  stream=SimpleNamespace(cells=1,batches=SimpleNamespace(cells=0),active=None)
  d.observe_tail(log,stream)
  raw=(tmp_path/'scoring-diagnostic/progress.json').read_bytes();row=json.loads(raw)
  assert len(raw)<=8192 and row['tail_observation']['acknowledged_tail_cells']==1
  assert row['completed_scalar_pairs']==2 and row['full_mcm_complete'] is False and row['paper_financial_fits']==0
  assert row['phase_timings']['score_only']['calls']==2
 finally:log.fail('synthetic planned diagnostic stop');d.close()

def test_default_path_has_no_diagnostic_clock_or_files(tmp_path):
 m,log,a,b,c,p=make(tmp_path,None)
 try:
  with patch.object(telemetry,'ScoringDiagnostic',side_effect=AssertionError('unselected diagnostic')):
   assert m(p,a,b)['score']==tiny.match_reference(a,b,c).score
  assert not (tmp_path/'scoring-diagnostic').exists()
 finally:log.close()

@pytest.mark.parametrize('change',[{'max_completed_pairs':1025},{'max_completed_pairs':True},{'checkpoint_every_pairs':0},{'checkpoint_relative':'../escape'},{'alpha':2}])
def test_policy_refusals(change):
 with pytest.raises(ValueError):telemetry.diagnostic_policy(selection|change)

def test_original_failure_priority_and_policy_mutation(tmp_path):
 d=telemetry.ScoringDiagnostic(selection,tmp_path,claim_sha256='a'*64,source='b'*40)
 def fail():raise RuntimeError('original numerical error')
 try:
  with patch.object(d,'_record',side_effect=ValueError('clock failure')):
   with pytest.raises(RuntimeError,match='original numerical error') as e:d.measure('score_only',fail)
  assert 'clock failure' in e.value.__notes__[0]
  d.policy['max_completed_pairs']=3
  with pytest.raises(ValueError,match='policy changed'):d.summary()
 finally:d.close()

def plan():
 hashes=[format(i,'064x') for i in range(1,8)]
 return {'schema_version':2,'kind':caller.KIND,'asset':'ETH','seed':11,'batch_size':16,'lookback_days':28,'cell_id':'synthetic','graph_inputs':dict(zip(hashes,['g'+str(i) for i in range(7)])),'indices':list(range(16)),'decisions':[f'd{i:02d}' for i in range(16)],'graph_sequences':[hashes*4 for _ in range(16)],'population_plan_input':'population','model_input':'model','training_input':'training','model_execution':None,'max_checkpoint_bytes':1000,'resource_policy':{},'outputs':dict(summary='summary.json',ledger='ledger.json',binding='binding.json',journal='journal.json')}

def test_plan_optin_and_fifth_output():
 p=plan()
 with patch.object(caller,'_finite_resources'),patch.dict(sys.modules,{PREFIX+'real_pilot_partial_progress':telemetry}):
  caller.validate_plan(p)
  diagnostic=p|{'scoring_diagnostic':selection,'outputs':p['outputs']|{'diagnostic':'diagnostic.json'}}
  caller.validate_plan(diagnostic)
  with pytest.raises(ValueError):caller.validate_plan(p|{'scoring_diagnostic':selection})
  with pytest.raises(ValueError):caller.validate_plan(diagnostic|{'scoring_diagnostic':selection|{'max_completed_pairs':1025}})

def test_exact1024_counter_and_bounded_checkpoint(tmp_path):
 selected=selection|{'max_completed_pairs':1024,'checkpoint_every_pairs':64}
 d=telemetry.ScoringDiagnostic(selected,tmp_path,claim_sha256='a'*64,source='b'*40)
 log=SimpleNamespace(state={'completed_pairs':0,'pending':None})
 try:
  d.begin('1'*64,log)
  for i in range(1,1025):
   log.state['completed_pairs']=i
   if i==1024:
    with pytest.raises(telemetry.PlannedScoringStop):d.completed_pair(log)
   else:d.completed_pair(log)
  assert d.writes==17 and d.completed==1024
  assert (tmp_path/'scoring-diagnostic/progress.json').stat().st_size<=8192
  assert not (tmp_path/'scoring-diagnostic/progress.tmp').exists()
  with pytest.raises(ValueError):d.completed_pair(log)
 finally:d.close()
