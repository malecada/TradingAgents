"""Invented source-cohort metadata; no provider or financial observations."""
import copy
from datetime import date, timedelta
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[2]/'research/onchain-graph-2026-09-16/comparison/recovery_admission.py'
SPEC = importlib.util.spec_from_file_location('recovery_policy_test', PATH)
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)


def fixture():
    dates = [(date(2000, 1, 1)+timedelta(days=n)).isoformat() for n in range(1084)]
    missing, completed = dates[:521], dates[521:]
    cohort = dict(dates=missing, prior_complete_dates=completed, prefixes={},
                  raw_baseline_bytes=54*1024**3, prior_metadata_baseline_bytes=512*1024**2,
                  lifecycle_reserve_bytes=128*1024**2,
                  stop_on_first_transport_failure=True, automatic_restart=False)
    cells = [dict(id='graph-'+d, status='unavailable' if d in missing else 'complete') for d in dates]
    summary = dict(cells=cells+[dict(id='index', status='complete')])
    baseline = dict(experiments={policy.PARENT:dict(family='old')},
                    families={'old':dict(prior_attempts=7, attempt_budget=8)})
    exp = dict(family='recovery', inputs={}, cells=['graph-'+d for d in missing]+['index'])
    exp['outputs'] = [c+'.json' for c in exp['cells']]+['summary.json']
    gate = dict(experiments={policy.EXPERIMENT:exp}, families={'recovery':dict(
        prior_attempts=8, attempt_budget=9, mechanism_id='ethereum-missing-source-response-recovery')})
    certificate = dict(schema_version=1, amendment_id='eth-raw-recovery-single-20260917',
        target_experiment=policy.EXPERIMENT, baseline_experiment=policy.PARENT,
        baseline_family_sha256=policy.digest(policy.canonical(baseline['families']['old'])),
        original_family_cap=8, cumulative_prior_claims=8, additional_claims=1, cumulative_cap=9,
        raw_only=True, automatic_restart=False, stop_on_first_transport_failure=True,
        target_contract_sha256=policy.target_contract(exp))
    failed = {'eth-temporal-motifs-20260916','eth-seven-day-pilot-20260916'}
    history = dict(lineage=list(policy.LINEAGE), metadata_hashes={f'research_runs/{n}/{f}':'invented'
        for n in policy.LINEAGE for f in ['claim.json','failed.json' if n in failed else 'complete.json']})
    review = dict(decision='approve-single-source-recovery', target_experiment=policy.EXPERIMENT, additional_claims=1)
    return dict(gate=gate, certificate=certificate, baseline=baseline, cohort=cohort,
                summary=summary, history=history, review=review)


def test_exact_amended_metadata_passes():
    policy.validate_policy(**fixture())


@pytest.mark.parametrize('change', ['old_budget','reset','extra_day','lineage','missing_failure','contract','approval','bool_increment'])
def test_changed_recovery_scope_fails_closed(change):
    f = copy.deepcopy(fixture())
    if change == 'old_budget': f['baseline']['families']['old']['attempt_budget'] = 9
    elif change == 'reset': f['gate']['families']['recovery']['prior_attempts'] = 0
    elif change == 'extra_day': f['cohort']['dates'].append(f['cohort']['prior_complete_dates'][0])
    elif change == 'lineage': f['history']['lineage'][0] = 'renamed'
    elif change == 'missing_failure': f['history']['metadata_hashes'].pop('research_runs/eth-temporal-motifs-20260916/failed.json')
    elif change == 'contract': f['gate']['experiments'][policy.EXPERIMENT]['question'] = 'changed'
    elif change == 'approval': f['review']['decision'] = 'pending'
    elif change == 'bool_increment': f['certificate']['additional_claims'] = True
    with pytest.raises(ValueError): policy.validate_policy(**f)
