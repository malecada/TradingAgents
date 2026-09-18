"""Invented source-cohort metadata; no provider or financial observations."""
import copy
from datetime import date, timedelta
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[2]/'research/onchain-graph-2026-09-16/comparison/resume2_admission.py'
SPEC = importlib.util.spec_from_file_location('resume2_policy_test', PATH)
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)


def fixture():
    dates = [(date(2000, 1, 1)+timedelta(days=n)).isoformat() for n in range(507)]
    missing, completed = dates[:446], dates[446:]
    cohort = dict(dates=missing, prior_complete_dates=sorted(completed + ['old-'+str(n) for n in range(577)]), parent_complete_dates=completed, prefixes={},
                  raw_baseline_bytes=62*1024**3, prior_metadata_baseline_bytes=1024*1024**2,
                  lifecycle_reserve_bytes=128*1024**2,
                  max_attempts_per_request=4, retry_delays_seconds=[5,15,45], monitor_authorized=True, automatic_restart=False)
    cells = [dict(id='graph-'+d, status='unavailable' if d in missing else 'complete') for d in dates]
    summary = dict(cells=cells+[dict(id='index', status='complete')])
    baseline = dict(experiments={policy.PARENT:dict(family='old')},
                    families={'old':dict(prior_attempts=9, attempt_budget=10)}, _parent_cohort=dict(prior_complete_dates=['old-'+str(n) for n in range(577)]))
    exp = dict(family='resume2', inputs={}, cells=['graph-'+d for d in missing]+['index'])
    exp['outputs'] = [c+'.json' for c in exp['cells']]+['summary.json']
    gate = dict(experiments={policy.EXPERIMENT:exp}, families={'resume2':dict(
        prior_attempts=10, attempt_budget=11, mechanism_id='ethereum-bounded-transport-source-resume2')})
    certificate = dict(schema_version=1, amendment_id='eth-raw-resume2-single-20260918',
        target_experiment=policy.EXPERIMENT, baseline_experiment=policy.PARENT,
        baseline_family_sha256=policy.digest(policy.canonical(baseline['families']['old'])),
        original_family_cap=10, cumulative_prior_claims=10, additional_claims=1, cumulative_cap=11,
        raw_only=True, automatic_restart=False, max_attempts_per_request=4, retry_delays_seconds=[5,15,45], monitor_authorized=True,
        target_contract_sha256=policy.target_contract(exp))
    failed = {'eth-temporal-motifs-20260916','eth-seven-day-pilot-20260916'}
    history = dict(lineage=list(policy.LINEAGE), metadata_hashes={f'research_runs/{n}/{f}':'invented'
        for n in policy.LINEAGE for f in ['claim.json','failed.json' if n in failed else 'complete.json']})
    review = dict(decision='approve-single-source-resume2', target_experiment=policy.EXPERIMENT, additional_claims=1)
    return dict(gate=gate, certificate=certificate, baseline=baseline, cohort=cohort,
                summary=summary, history=history, review=review)


def test_exact_amended_metadata_passes():
    policy.validate_policy(**fixture())


@pytest.mark.parametrize('change', ['old_budget','reset','extra_day','lineage','missing_failure','contract','approval','bool_increment', 'retries', 'completed', 'monitor'])
def test_changed_resume2_scope_fails_closed(change):
    f = copy.deepcopy(fixture())
    if change == 'old_budget': f['baseline']['families']['old']['attempt_budget'] = 11
    elif change == 'reset': f['gate']['families']['resume2']['prior_attempts'] = 0
    elif change == 'extra_day': f['cohort']['dates'].append(f['cohort']['prior_complete_dates'][0])
    elif change == 'lineage': f['history']['lineage'][0] = 'renamed'
    elif change == 'missing_failure': f['history']['metadata_hashes'].pop('research_runs/eth-temporal-motifs-20260916/failed.json')
    elif change == 'contract': f['gate']['experiments'][policy.EXPERIMENT]['question'] = 'changed'
    elif change == 'approval': f['review']['decision'] = 'pending'
    elif change == 'bool_increment': f['certificate']['additional_claims'] = True
    elif change == 'retries': f['cohort']['max_attempts_per_request'] = 5
    elif change == 'completed': f['cohort']['prior_complete_dates'].pop()
    elif change == 'monitor': f['certificate']['monitor_authorized'] = False
    with pytest.raises(ValueError): policy.validate_policy(**f)


def test_parent_accounting_must_fit_new_baseline():
    cohort = dict(raw_baseline_bytes=62*1024**3, prior_metadata_baseline_bytes=1024*1024**2)
    index = dict(days=[dict(budget=dict(total_raw_bytes=62*1024**3,
                                      total_metadata_bytes=1024*1024**2)) for _ in range(507)])
    policy.validate_baseline(cohort, index)
    index['days'][0]['budget']['total_metadata_bytes'] += 1
    with pytest.raises(ValueError):
        policy.validate_baseline(cohort, index)


def test_parent_accounting_rejects_missing_dates():
    with pytest.raises(ValueError):
        policy.validate_baseline(dict(raw_baseline_bytes=62*1024**3,
                                     prior_metadata_baseline_bytes=1024*1024**2), dict(days=[]))
