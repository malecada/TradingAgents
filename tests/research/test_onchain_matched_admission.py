"""Synthetic metadata contracts only; no empirical admission or data reads."""
import copy
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[2] / 'research/onchain-graph-2026-09-16/comparison/evaluation-20260924/admission.py'


def module():
    assert PATH.exists(), 'comparison admission not implemented'
    spec = importlib.util.spec_from_file_location('matched_admission_test', PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def fixture():
    m = module()
    history = {'lineage': list(m.LINEAGE), 'metadata_hashes': {}}
    for name in history['lineage']:
        history['metadata_hashes'][f'research_runs/{name}/claim.json'] = 'a'*64
        terminal = 'failed.json' if name in m.FAILED else 'complete.json'
        history['metadata_hashes'][f'research_runs/{name}/{terminal}'] = 'b'*64
    e = dict(family='eth-matched-direction', parent=None, graph_parent=m.GRAPH_EXPERIMENT, stage='development',
             reuse='exploratory', cells=m.expected_cells(), outputs=m.OUTPUTS,
             inputs={k: {'path': k, 'sha256': 'a'*64} for k in m.required_inputs()})
    e['inputs']['config']['sha256'] = m.CONFIG_SHA
    e['inputs']['protocol']['sha256'] = m.PROTOCOL_SHA
    gate = dict(experiments={m.EXPERIMENT:e},families={'eth-matched-direction':dict(
        prior_attempts=16,attempt_budget=17,mechanism_id=m.MECHANISM)})
    approval = dict(decision='approve-single-matched-comparison', review_sha256='a'*64)
    amendment = dict(additional_claims=1,prior_claims=16,cumulative_cap=17,
                     target_experiment=m.EXPERIMENT,network_allowed=False,
                     prices_or_models_allowed=True,target_contract_sha256=m.contract(e))
    return m,gate,history,approval,amendment


def test_one_additive_comparison_keeps_full_denominator():
    m,g,h,a,x = fixture()
    m.validate_metadata(g,h,a,x)
    assert len(g['experiments'][m.EXPERIMENT]['cells']) == 77


@pytest.mark.parametrize('field', ['budget','history','cells','protocol','inputs','contract','approval'])
def test_changed_scientific_or_history_contract_fails(field):
    m,g,h,a,x=fixture()
    if field=='budget':g['families']['eth-matched-direction']['prior_attempts']=0
    elif field=='history':h['lineage']=h['lineage'][1:]
    elif field=='cells':g['experiments'][m.EXPERIMENT]['cells'].pop()
    elif field=='protocol':g['experiments'][m.EXPERIMENT]['inputs']['protocol']['sha256']='b'*64
    elif field=='inputs':del g['experiments'][m.EXPERIMENT]['inputs']['spot_2024-12_checksum']
    elif field=='contract':x['target_contract_sha256']='c'*64
    else:a['decision']='approve-failure-evidence-only'
    with pytest.raises(ValueError):m.validate_metadata(g,h,a,x)


def test_upstream_failed_motif_attempt_is_preserved():
    m,g,h,a,x=fixture()
    assert 'research_runs/eth-temporal-motifs-20260916/failed.json' in h['metadata_hashes']
    assert len(m.FAILED)==4


def test_cross_family_graph_ancestry_is_explicit_not_lifecycle_parent():
    m,g,h,a,x=fixture()
    e=g['experiments'][m.EXPERIMENT]
    e['parent']=m.GRAPH_EXPERIMENT
    with pytest.raises(ValueError):m.validate_metadata(g,h,a,x)
    e['parent']=None;e['graph_parent']='wrong'
    with pytest.raises(ValueError):m.validate_metadata(g,h,a,x)


@pytest.mark.parametrize('bad', ['receipt','interpreter'])
def test_runtime_preflight_rejects_unpinned_environment(monkeypatch,bad):
    m=module()
    class FakeRuntime:
        @staticmethod
        def receipt(root):return {'ok':bad!='receipt','problems':['wrong numpy'] if bad=='receipt' else []}
    monkeypatch.setattr(m,'runtime_module',lambda root:FakeRuntime)
    root=Path('/invented/repo')
    monkeypatch.setattr(m.sys,'executable',str(root/'.venv/bin/python') if bad!='interpreter' else '/usr/bin/python')
    with pytest.raises(ValueError):m.assert_runtime(root)


def test_runtime_preflight_admits_pinned_receipt(monkeypatch):
    m=module()
    class FakeRuntime:
        @staticmethod
        def receipt(root):return {'ok':True,'problems':[]}
    monkeypatch.setattr(m,'runtime_module',lambda root:FakeRuntime)
    root=Path('/invented/repo');monkeypatch.setattr(m.sys,'executable',str(root/'.venv/bin/python'))
    assert m.assert_runtime(root)['ok']
