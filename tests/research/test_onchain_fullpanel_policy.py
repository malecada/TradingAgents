"""Full-calendar registration contract without any empirical inputs."""
import copy
from datetime import date,timedelta
import importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('fullpanel_policy_test',ROOT/'research/onchain-graph-2026-09-16/fullpanel/admission.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
def fixture():
 dates=[str(date(2022,1,1)+timedelta(days=i)) for i in range(1096)]
 exp=dict(family='full',parent=None,continuation_of=p.LINEAGE[-1],cells=[c+'-'+d for d in dates for c in ['source','graph']]+['global-uniqueness'],outputs=['day-'+d+'.json' for d in dates]+['hash-audit.json','panel.json','summary.json'],inputs={})
 gate=dict(experiments={p.EXPERIMENT:exp},families={'full':dict(prior_attempts=13,attempt_budget=14,mechanism_id='ethereum-full-history-daily-feature-extraction')})
 amendment=dict(schema_version=1,target_experiment=p.EXPERIMENT,prior_claims=13,additional_claims=1,cumulative_cap=14,target_contract_sha256=p.contract(exp),network_allowed=False,prices_or_models_allowed=False)
 q,r=divmod(1221389903,len(dates));rows={d:q+(i<r) for i,d in enumerate(dates)}
 plan=dict(dates=dates,expected_rows=rows,expected_hash_bytes=39084476896,network_allowed=False,limits=dict(max_requests=0,max_total_bytes=0,max_derived_bytes=2*2**30,max_scratch_bytes=2*2**30,max_hash_bytes=40*2**30,min_free_bytes=20*2**30))
 failed={'eth-temporal-motifs-20260916','eth-seven-day-pilot-20260916'}
 history=dict(lineage=p.LINEAGE,metadata_hashes={f'research_runs/{n}/{f}':'a'*64 for n in p.LINEAGE for f in ['claim.json','failed.json' if n in failed else 'complete.json']})
 return copy.deepcopy([gate,amendment,plan,history,dict(decision='approve-single-fullpanel-extraction')])
def test_full_calendar_denominator():p.validate(*fixture())
@pytest.mark.parametrize('mutation',[lambda x:x[1].update(additional_claims=2),lambda x:x[2]['dates'].pop(),lambda x:x[2]['expected_rows'].pop('2022-01-01'),lambda x:x[2].update(network_allowed=True),lambda x:x[2]['limits'].update(max_hash_bytes=48*2**30),lambda x:x[3]['lineage'].pop(),lambda x:x[4].update(decision='pending')])
def test_scope_population_or_budget_change_rejected(mutation):
 args=fixture();mutation(args)
 with pytest.raises(ValueError):p.validate(*args)
