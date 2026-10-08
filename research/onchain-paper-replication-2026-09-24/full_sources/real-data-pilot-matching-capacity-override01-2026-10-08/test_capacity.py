import copy,importlib.util,json
from pathlib import Path
from unittest.mock import patch
import pytest
from tests.research.onchain_replication import test_compact_matcher as tiny
from tests.research.onchain_replication import test_restart_retention_integration as retained
from tests.research.onchain_replication.test_compact_policy import candidate
from tradingagents.research.onchain_replication import compact_matcher as original
from tradingagents.research.onchain_replication import compact_policy as oldpolicy
from tradingagents.research.onchain_replication.cache import cache_key
ROOT=Path(__file__).resolve().parent

def module(name,file):
 spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication.'+name,ROOT/file)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
policy=module('_capacity_policy','compact_policy.py')
matcher=module('_capacity_matcher','compact_matcher.py');matcher.compact_policy=policy

def test_default_bytes_and_scope():
 c=tiny.config();p=candidate()
 assert policy.validate(p,kind='mcm',pairs=4)==oldpolicy.validate(p,kind='mcm',pairs=4)
 assert matcher.scope(c,tiny.CONTEXT,tiny.POLICY,'f'*64,tiny.SCHEDULE)==original.scope(c,tiny.CONTEXT,tiny.POLICY,'f'*64,tiny.SCHEDULE)
 assert policy.effective_matching(c,tiny.POLICY)==c
 assert policy.effective_matching(c,tiny.POLICY) is not c

@pytest.mark.parametrize('value',[0,-1,True,1.5,2**63,{'max_pair_entries':6},'6'])
def test_invalid(value):
 with pytest.raises(ValueError):policy.effective_matching(tiny.config()|{'max_pair_entries':4},tiny.POLICY|{'max_pair_entries_override':value})

def test_semantic_and_lower_refusals():
 c=tiny.config()|{'max_pair_entries':4}
 for p in (tiny.POLICY|{'max_pair_entries_override':3},tiny.POLICY|{'alpha':2},tiny.POLICY|{'max_pair_entries_override':6,'beta0':9}):
  with pytest.raises(ValueError):matcher.scope(c,tiny.CONTEXT,p,'f'*64,tiny.SCHEDULE)

def setup_retained(tmp_path):
 c=tiny.config()|{'max_pair_entries':1};p=tiny.POLICY|{'max_pair_entries_override':4}
 with patch.object(retained,'matcher_module',matcher),patch.object(tiny,'POLICY',p),patch.object(tiny,'config',return_value=c):
  result=retained.fixture(tmp_path,progress=True)
 return result,c,p

def test_effective_pair_checkpoint_retention_identity(tmp_path):
 (m,log,a,b,c,purpose,transport),original_c,p=setup_retained(tmp_path)
 try:
  assert original_c['max_pair_entries']==1 and c['max_pair_entries']==1
  assert m.config['max_pair_entries']==4 and m.original_config==c
  assert {k:v for k,v in m.config.items() if k!='max_pair_entries'}=={k:v for k,v in c.items() if k!='max_pair_entries'}
  assert log.start['scope']['config']==cache_key(c)
  assert log.start['scope']['policy']==cache_key({'pair':p,'schedule':m.schedule})
  assert m.pair_identity(a,b)['ordered_pair']==matcher.engine.ann.identity(a,b,m.config)
  assert m.retention.claim['config']==m.config and m.retention.claim['pair_policy']==p
  with pytest.raises(ValueError,match='capacity exceeded'):matcher.engine.create(a,b,c,**{k:p[k] for k in matcher.pair.ENGINE_FIELDS})
  with pytest.raises(matcher.CheckpointStop):m(purpose,a,b)
  assert m.retention.spent['generations']==3
  anneal=list((tmp_path/'checkpoints/stores').glob('*/generation-*/state/annealing/manifest.json'))
  assert len(anneal)==3
  for f in anneal:assert json.loads(f.read_bytes())['identity']['configuration']==matcher.engine.ann.identity(a,b,m.config)['configuration']
 finally:log.fail('synthetic capacity checkpoint stop')

@pytest.mark.parametrize('which',['effective','original','policy'])
def test_mutation_refuses(tmp_path,which):
 (m,log,*_),_,_=setup_retained(tmp_path)
 try:
  if which=='effective':m.config['alpha']+=1
  elif which=='original':m.original_config['alpha']+=1
  else:m.policy['max_pair_entries_override']+=1
  with pytest.raises(ValueError,match='resource policy changed'):m._check()
 finally:log.close()

def test_completed_score_with_explicit_capacity(tmp_path):
 c=tiny.config()|{'max_pair_entries':1};p=tiny.POLICY|{'max_pair_entries_override':4}
 with patch.object(retained,'matcher_module',matcher),patch.object(tiny,'POLICY',p),patch.object(tiny,'config',return_value=c):
  m,log,a,b,original_c,purpose,transport=retained.fixture(tmp_path,progress=False)
 try:
  actual=m(purpose,a,b)
  expected=retained.match_reference(a,b,m.config)
  assert actual['score'].hex()==expected.score.hex()
  assert m.retention.claim['config']['max_pair_entries']==4
  assert original_c['max_pair_entries']==1 and c['max_pair_entries']==1
  assert log.state['completed_pairs']==1
  assert m.retention.finish_stage()
 finally:log.close()
