from __future__ import annotations
import json
import subprocess
import numpy as np
import pandas as pd
import pytest
from statsmodels.api import OLS
from statsmodels.stats.sandwich_covariance import cov_hac
from statsmodels.tsa.stattools import coint
from tradingagents.predlab import registry, dm, rollup


def test_trial_identity_uses_whole_evaluated_cell():
    a = dict(experiment='e', cell='c', model='m', config={'a': 1}, window=['2021', '2022'])
    assert registry.trial_identity(a) == registry.trial_identity(dict(a))
    for key, value in [('experiment','f'), ('cell','d'), ('model','n'), ('window',['2020','2022']), ('config',{'a':2})]:
        assert registry.trial_identity(a) != registry.trial_identity(dict(a, **{key:value}))


def test_failed_tests_remain_in_family_denominator():
    assert rollup.bh_fdr({'valid': .075, 'failed': np.nan}) == {'valid': False, 'failed': False}


def test_selected_winner_accounts_for_all_contenders():
    card={'strong_baseline':'base','per_model':{'base':{'loss_mean':1}, 'a':{'loss_mean':.8,'dm_p':.04}, 'b':{'loss_mean':.9,'dm_p':.5}, 'failed':{'loss_mean':np.nan,'dm_p':np.nan}}}
    ch = rollup.champion(card)
    assert ch['raw_dm_p'] == .04
    assert ch['dm_p'] == pytest.approx(.12)
    assert ch['n_contenders'] == 3


def test_h1_hac_matches_independent_statsmodels():
    rng=np.random.default_rng(415)
    d=np.zeros(400)
    for i in range(1,400): d[i]=.9*d[i-1]+rng.normal()+.04
    fit=OLS(d,np.ones((len(d),1))).fit()
    lag=int(np.floor(4*(len(d)/100)**(2/9)))
    expected=fit.params[0]/np.sqrt(cov_hac(fit,nlags=lag,use_correction=False)[0,0])
    assert dm.dm_test(d,np.zeros_like(d)).stat == pytest.approx(expected)
    assert dm.gw_test(d,np.zeros_like(d)).stat == pytest.approx(expected)


def test_engle_granger_uses_cointegration_null():
    from scripts.predlab_xfam_lib import eg_fit
    rng=np.random.default_rng(9)
    a=pd.Series(rng.normal(size=300).cumsum())
    b=pd.Series(rng.normal(size=300).cumsum())
    _,p,resid=eg_fit(a,b)
    assert p == pytest.approx(coint(a,b,trend='c',maxlag=10,autolag='AIC')[1])
    assert abs(resid.mean()) < 1e-9


def _git(path,*args):
    return subprocess.run(['git',*args],cwd=path,text=True,capture_output=True,check=True).stdout


@pytest.fixture
def registered_repo(tmp_path,monkeypatch):
    root=tmp_path/'repo'; root.mkdir()
    _git(root,'init'); _git(root,'config','user.email','fixture@example.invalid'); _git(root,'config','user.name','Fixture')
    data=root/'data'/'predlab'; data.mkdir(parents=True)
    (data/'gates.json').write_text(json.dumps({'new': {'status':'registered_not_run','development_window':['2021-01-01','2022-01-01']}}))
    (root/'engine.py').write_text('x = 1\n')
    _git(root,'add','.'); _git(root,'commit','-m','preregister')
    monkeypatch.setattr(registry,'PROJECT_ROOT',root)
    monkeypatch.setenv('TRADINGAGENTS_DATA_ROOT',str(root/'data'))
    return root


def test_preflight_pins_committed_gate_and_rejects_dirty_code(registered_repo):
    p=registry.preflight('new',('2021-01-01','2022-01-01'))
    assert len(p['git_commit'])==40 and len(p['gate_sha256'])==64
    (registered_repo/'engine.py').write_text('x = 2\n')
    with pytest.raises(RuntimeError,match='uncommitted'):
        registry.preflight('new',('2021-01-01','2022-01-01'))


def test_preflight_rejects_uncommitted_gate_and_bad_window(registered_repo):
    with pytest.raises(RuntimeError,match='window'):
        registry.preflight('new',('2020-01-01','2022-01-01'))
    p=registered_repo/'data/predlab/gates.json'
    p.write_text(p.read_text().replace('registered_not_run','changed'))
    with pytest.raises(RuntimeError,match='gate'):
        registry.preflight('new',('2021-01-01','2022-01-01'))


def test_correction_history_is_append_only_and_resolves(tmp_path):
    from tradingagents.predlab.evidence import append_correction, resolve
    p=tmp_path/'corrections.jsonl'
    row={'id':'first','claim':'champion','status':'invalidated','reason':'log pnl'}
    append_correction(row,p)
    with pytest.raises(ValueError): append_correction(row,p)
    append_correction({'id':'second','claim':'champion','status':'superseded','reason':'arithmetic correction','supersedes':'first'},p)
    assert resolve('champion',p)['id']=='second'
    assert len(p.read_text().splitlines())==2


def test_oflow_reversal_meets_the_preregistered_absolute_gate():
    from scripts.predlab_oflow_p0 import floor_pass
    assert floor_pass('XS_24h_IC', {'mean_ic':-.03,'nw_t':-4.,'n_sub_right_sign':3})
    assert not floor_pass('XS_24h_IC', {'mean_ic':-.03,'nw_t':-2.,'n_sub_right_sign':3})


def test_fixed_oracle_weighting_is_not_a_dominance_bound():
    from scripts.predlab_opt_o6 import oracle_scope
    scope=oracle_scope(-1.,1.)
    assert scope['tested_oracle_weights_below_floor']
    assert not scope['axis_dominance_closed']
    assert not scope['objective_upper_bound']


def test_uncommitted_policy_change_cannot_authorize_old_experiment(registered_repo):
    policy=registered_repo/'docs/audit/corrections.jsonl'
    policy.parent.mkdir(parents=True)
    policy.write_text(json.dumps({'id':'old','claim':'new','status':'invalid','reason':'audit','rerun_requires_new_registration':True})+'\n')
    _git(registered_repo,'add','.');_git(registered_repo,'commit','-m','freeze correction policy')
    policy.write_text('')
    with pytest.raises(RuntimeError,match='uncommitted'):
        registry.preflight('new',('2021-01-01','2022-01-01'))


def test_unavailable_nested_loss_inference_cannot_be_called_no_skill_or_candidate():
    card={'loss':'qlike','strong_baseline':'base','per_model':{'base':{'loss_mean':1.},
        'harq':{'loss_mean':.5,'dm_p':.001,'nested':True,'inference_eligible':False,
                'primary_test':'unavailable_nested_loss_test'}}}
    selected=rollup.champion(card)
    assert np.isnan(selected['selection_p']) and not selected['inference_eligible']
    assert rollup.verdict(True,True,True,False,None,inference_eligible=False).startswith('DEGENERATE')
