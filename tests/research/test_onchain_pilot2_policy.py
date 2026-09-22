"""Synthetic one-use policy and unavailable-coverage orchestration checks."""
import importlib.util
import copy
import json
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'research/onchain-graph-2026-09-16/pilot2'
spec=importlib.util.spec_from_file_location('pilot2_policy_test',HERE/'admission.py');policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)

def fixture():
    exp=dict(family='new',parent='eth-seven-day-pilot-20260916',cells=policy.CELLS,outputs=policy.OUTPUTS,inputs={})
    gate=dict(experiments={policy.EXPERIMENT:exp},families={'new':dict(prior_attempts=12,attempt_budget=13,mechanism_id='ethereum-seven-day-offline-numerical-continuation')})
    cert=dict(schema_version=1,target_experiment=policy.EXPERIMENT,prior_claims=12,additional_claims=1,cumulative_cap=13,network_allowed=False,prices_or_models_allowed=False,automatic_restart=False,target_contract_sha256=policy.contract(exp))
    failed={'eth-temporal-motifs-20260916','eth-seven-day-pilot-20260916'}
    history=dict(lineage=policy.LINEAGE,metadata_hashes={f'research_runs/{n}/{f}':'a'*64 for n in policy.LINEAGE for f in ['claim.json','failed.json' if n in failed else 'complete.json']})
    plan=dict(dates=policy.DATES,network_allowed=False,captures={f'2024-01-{i:02d}':{} for i in range(2,10)},limits=dict(max_requests=0,max_total_bytes=0,max_derived_bytes=8*2**30,min_free_bytes=20*2**30))
    approval=dict(decision='approve-single-offline-pilot',target_experiment=policy.EXPERIMENT)
    old=dict(families={'eth-seven-day-pilot':dict(prior_attempts=5,attempt_budget=6)})
    src=dict(families={'eth-graph-source-resume3':dict(prior_attempts=11,attempt_budget=12)})
    return copy.deepcopy([gate,cert,history,plan,approval,old,src])

def test_complete_policy():policy.validate(*fixture())

@pytest.mark.parametrize('mutation',[lambda x:x[1].update(additional_claims=2),lambda x:x[1].update(network_allowed=True),lambda x:x[2]['lineage'].pop(),lambda x:x[3]['dates'].pop(),lambda x:x[3]['limits'].update(min_free_bytes=1),lambda x:x[4].update(decision='pending'),lambda x:x[5]['families']['eth-seven-day-pilot'].update(attempt_budget=7)])
def test_policy_rejects_scope_or_lineage_changes(mutation):
    args=fixture();mutation(args)
    with pytest.raises(ValueError):policy.validate(*args)

@pytest.mark.parametrize('missing',[False,True])
def test_orchestration_relative_paths_and_missing_coverage(tmp_path,monkeypatch,missing):
    monkeypatch.setitem(sys.modules,'admission',policy)
    spec=importlib.util.spec_from_file_location('pilot2_runner_test',HERE/'run.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    here=tmp_path/'pilot2';here.mkdir();(here/'plan.json').write_text('{}')
    monkeypatch.setattr(runner,'ROOT',tmp_path);monkeypatch.setattr(runner,'HERE',here)
    monkeypatch.setattr(runner.prior,'linkage',lambda *args:{'passed':True})
    monkeypatch.setattr(runner.prior,'validate_artifacts',lambda *args:[])
    calls=[]
    def invoke(command,check):
        args=dict(zip(command[3::2],command[4::2]));calls.append(args)
        assert not Path(args['--plan']).is_absolute()
        for key in ['--current-result','--previous-result']:
            if key in args:assert not Path(args[key]).is_absolute()
        status='unavailable' if missing and args['--mode']=='source' and args['--date']==policy.DATES[0] else 'complete'
        value=dict(date=args['--date'],mode=args['--mode'],status=status,reason='synthetic missing' if status!='complete' else None,transaction_hashes=[],integrity={'rows':0})
        Path(args['--result']).write_text(json.dumps(value))
    monkeypatch.setattr(runner.subprocess,'run',invoke)
    class Run:
        def __init__(self):self.outputs={}
        def write_json(self,name,value):assert name not in self.outputs;self.outputs[name]=value
    run=Run();plan=dict(dates=policy.DATES,limits=dict(min_free_bytes=0,max_derived_bytes=8*2**30))
    cells=runner.execute(plan,run)
    assert len(cells)==17 and len(run.outputs)==20
    assert run.outputs['cross-day-integrity.json']['status']==('unavailable' if missing else 'complete')
    assert sum(c['status']=='complete' for c in cells if c['id'].startswith('motifs-'))==(0 if missing else 7)
    assert sum(a['--mode']=='count' for a in calls)==(0 if missing else 7)
