"""Synthetic mutation checks for the continuation's frozen admission boundary."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'research/onchain-graph-2026-09-16/fullpanel_resume2'
spec=importlib.util.spec_from_file_location('resume2_policy',BASE/'admission.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def fixture():
    plan=json.loads((BASE/'plan.json').read_bytes())
    history=json.loads((BASE/'history.json').read_bytes())
    e=dict(family='resume',parent=None,continuation_of=m.PRIOR,inputs={},cells=[k+'-'+d for d in plan['dates'] for k in ('source','graph')]+['global-uniqueness'],outputs=['day-'+d+'.json' for d in plan['dates']]+['hash-audit.json','panel.json','summary.json'])
    gate=dict(families={'resume':dict(prior_attempts=15,attempt_budget=16,mechanism_id='ethereum-full-history-daily-feature-extraction-resume2')},experiments={m.EXPERIMENT:e})
    amendment=dict(schema_version=1,target_experiment=m.EXPERIMENT,prior_claims=15,additional_claims=1,cumulative_cap=16,target_contract_sha256=m.contract(e),network_allowed=False,prices_or_models_allowed=False)
    return [gate,plan,amendment,history,dict(decision='approve-single-fullpanel-continuation')]

def test_contract_accepts_retained_checkpoint():
    m.validate(*fixture())

@pytest.mark.parametrize('mutation',[
    lambda v:v[0]['families']['resume'].update(prior_attempts=13),
    lambda v:v[0]['families']['resume'].update(attempt_budget=17),
    lambda v:v[1].update(seed_count=205),
    lambda v:v[1].update(remaining_dates=v[1]['dates'][205:]),
    lambda v:v[1]['memory'].update(memory_max_bytes=8*2**30),
    lambda v:v[1]['memory'].update(reserve_bytes=0),
    lambda v:v[1]['hash_roots'][1].update(day_indices=list(range(1096))),
    lambda v:v[1].update(network_allowed=True),
    lambda v:v[2].update(prices_or_models_allowed=True),
    lambda v:v[3]['lineage'].__setitem__(0,'invented-predecessor'),
    lambda v:v[3]['metadata_hashes'].__setitem__('invented-receipt','0'*64),
    lambda v:v[4].update(decision='pending'),
    lambda v:v[1]['seed_files'].__setitem__('research/onchain-graph-2026-09-16/fullpanel/artifacts/prefixes/2022-07-26/orphan.zst',{'bytes':1,'sha256':'0'*64}),
    lambda v:v[1]['seed_files'].pop(next(k for k in v[1]['seed_files'] if k.startswith('research_runs/'))),
])
def test_mutated_boundary_is_rejected(mutation):
    value=fixture();mutation(value)
    with pytest.raises(ValueError):m.validate(*value)


def test_review_admission_excludes_only_existing_own_claim(monkeypatch):
    calls=[]
    class Stop(Exception):pass
    def fake(**kwargs):calls.append(kwargs);raise Stop
    monkeypatch.setattr(m,'admit',fake)
    with pytest.raises(Stop):m.admit_resume(ROOT,'source',review=True)
    assert calls[0]['_own_claim']==m.EXPERIMENT
    with pytest.raises(Stop):m.admit_resume(ROOT,'source')
    assert calls[1]['_own_claim'] is None
