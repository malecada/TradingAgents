import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts import audit_factor_risk_policy_2026_09_10 as runner


def test_default_and_help_never_preflight(monkeypatch):
    monkeypatch.setattr(runner.registry,'preflight',lambda *a:pytest.fail('preflight called'))
    assert runner.main([])==0
    with pytest.raises(SystemExit) as exc: runner.main(['--help'])
    assert exc.value.code==0


def test_actual_gate_metadata_matches_fixed_schema_without_loading_inputs():
    gate=json.loads((runner.ROOT/'data/predlab/gates.json').read_text())[runner.KEY]
    runner.validate_gate(gate)
    for key,value in [('expected_identities',71),('variants',['primary']),('allow_holdout',True)]:
        altered=copy.deepcopy(gate); altered[key]=value
        with pytest.raises(ValueError): runner.validate_gate(altered)


def test_parquet_filter_precedes_pandas_materialization(tmp_path):
    path=tmp_path/'test.parquet'
    pd.DataFrame({'Date':pd.to_datetime(['2025-03-31','2025-04-01']),
                  'Close':[100.,99999.]}).to_parquet(path,index=False)
    got=runner.read_frame(path,'Date',pd.Timestamp('2025-03-31',tz='UTC'),pd.Timestamp('2025-03-31',tz='UTC'))
    assert got.Close.tolist()==[100.]
    with pytest.raises(ValueError):runner.read_frame(path,'Date',pd.Timestamp('2025-03-31',tz='UTC'),pd.Timestamp('2025-04-01',tz='UTC'))


def test_append_preserves_exact_prefix_and_refuses_repeat(tmp_path):
    ledger=tmp_path/'ledger'; prefix=b'{"old":1}\n'; ledger.write_bytes(prefix)
    receipt=b'{"new":1}\n'
    spec={'prefix_rows':1,'prefix_bytes':len(prefix),'prefix_sha256':hashlib.sha256(prefix).hexdigest(),'append_rows':1,'final_rows':2}
    runner.append_ledger_once(ledger,receipt,spec)
    assert ledger.read_bytes()==prefix+receipt
    with pytest.raises(ValueError):runner.append_ledger_once(ledger,receipt,spec)
    assert ledger.read_bytes()==prefix+receipt


def test_invalid_or_unserializable_ledger_rows_never_append(tmp_path):
    path=tmp_path/'receipt'
    with pytest.raises((TypeError,ValueError)):runner.write_json(path,{'x':np.nan})
    assert not path.exists()


def test_all_failure_nested_denominators_retained():
    cell={'id':'x|A11','configuration':{'name':'x'},'arm':'A11','sizing':'daily','reentry':'new_target_episode'}
    got=runner.unavailable_cell(cell,'bad input')
    assert got['metrics']['status']=='unavailable'
    assert list(got['metrics']['variants'])==list(runner.VARIANTS)
    for variant in got['metrics']['variants'].values():
        assert variant['status']=='unavailable'
        assert set(variant['sleeves'])=={'bitcoin','ethereum'}
        assert all(s['reason'] for s in variant['sleeves'].values())
        assert variant['index']['reason']
    assert got['metrics']['log_shadow']['reason']


def test_log_order_descriptor_retains_unavailable_and_detects_reversal():
    got=runner.convention_descriptor({'mean_return':-.01,'sharpe':None}, {'mean_return':.01,'sharpe':None})
    assert got['mean_return']['sign_or_order_changed'] is True
    assert got['sharpe']['sign_or_order_changed'] is None


def test_undefined_index_preserves_two_complete_sleeves(monkeypatch):
    idx=pd.date_range('2021-11-08',periods=2,tz='UTC',name='Date')
    frame=pd.DataFrame({'bitcoin':[.1,.2],'ethereum':[.3,.4]},index=idx)
    monkeypatch.setattr(runner.ev,'return_metrics',lambda *a:(_ for _ in ()).throw(ValueError('synthetic index overflow')))
    got=runner.summarize_index(frame,{'return_window':['2021-11-08','2021-11-09'],'reporting':{'periods':[]}})
    assert got['status']=='unavailable' and frame.index_return.isna().all()
    assert frame[list(runner.COINS)].notna().all().all()


@pytest.fixture
def synthetic_run(tmp_path,monkeypatch):
    """Only synthetic temporary targets/control books; never reads original values."""
    from scripts.baseline_strategy_v2 import run_coin_backtest
    config={'name':'synthetic','family':'synthetic'}
    idx=pd.date_range('2021-11-07',periods=65,tz='UTC')
    cells=[dict(id='synthetic|'+a['id'],configuration=config,arm=a['id'],sizing=a['sizing'],reentry=a['reentry']) for a in runner.ARMS]
    output=tmp_path/runner.SOURCE;output.mkdir(parents=True)
    hashes={};control_hashes={}
    def record(path):
        key=str(path.relative_to(tmp_path));digest=runner.sha(path);hashes[key]=digest
        if path.parent==output:control_hashes[path.name]=digest
    targets={}
    for number,coin in enumerate(runner.COINS):
        close=100*np.exp(.012*np.sin(np.arange(len(idx))/3+number))
        raw=np.zeros(len(idx));raw[23:42]=.2;raw[46:]=-.2
        frame=pd.DataFrame(dict(Date=idx,Open=close,High=close*1.02,Low=close*.98,Close=close,target=raw))
        frame.loc[32,'Low']*=.94
        path=output/f'synthetic-{coin}-targets.parquet';frame.to_parquet(path,index=False);record(path);targets[coin]=frame
    for variant in runner.VARIANTS:
        saved=pd.DataFrame(index=pd.DatetimeIndex(idx[1:],name='Date'))
        for coin,frame in targets.items():
            trace=[]
            equity,_=run_coin_backtest(frame.Date.to_numpy(),frame.Close.to_numpy(),frame.target.to_numpy(),10000.,
                **runner.ev.cost_variant(runner.ev.COSTS,variant),highs=frame.High.to_numpy(),lows=frame.Low.to_numpy(),price_stop_pct=.03,trace=trace)
            saved[coin]=np.asarray(equity)[1:]/np.asarray(equity)[:-1]-1
            path=output/f'synthetic-{variant}-{coin}-trace.parquet';pd.DataFrame(trace).to_parquet(path,index=False);record(path)
        saved['index_return']=saved[list(runner.COINS)].mean(axis=1)
        path=output/f'synthetic-{variant}-returns.parquet';saved.to_parquet(path);record(path)
    prior=output/'result.json';prior.write_text(json.dumps({'output_sha256':control_hashes,'git_commit':'1'*40}));record(prior)
    originals=tmp_path/'original-gates.json';originals.write_text(json.dumps({'audit_factor_floor_2026_09_10':{'cells':[config]}}));record(originals)
    ledger=tmp_path/'ledger.jsonl';prefix=b'{"old":1}\n{ "old": 2 }\n';ledger.write_bytes(prefix)
    gate=dict(cells=cells,configurations=[config],pinned_files=hashes,output_dir=runner.OUTPUT,source_result=runner.SOURCE+'/result.json',
        original_gates='original-gates.json',source_execution_commit='1'*40,development_window=[idx[0].date().isoformat(),idx[-1].date().isoformat()],
        return_window=[idx[1].date().isoformat(),idx[-1].date().isoformat()],policy=runner.ev.POLICY,costs=runner.ev.COSTS,
        reporting={'periods':[[idx[1].date().isoformat(),idx[-1].date().isoformat()]]},
        financial_ledger=dict(path='ledger.jsonl',prefix_rows=2,prefix_bytes=len(prefix),prefix_sha256=hashlib.sha256(prefix).hexdigest(),append_rows=4,final_rows=6))
    provenance={'git_commit':'a'*40,'gate_sha256':'b'*64,'correction_policy_sha256':'c'*64}
    monkeypatch.setattr(runner.registry,'preflight',lambda *a:dict(provenance))
    monkeypatch.setattr(runner.registry,'get_experiment',lambda *a:gate)
    monkeypatch.setattr(runner,'validate_gate',lambda *a:None)
    return tmp_path,gate,ledger,prefix,provenance


def test_synthetic_full_runner_control_first_and_append_once(synthetic_run,monkeypatch):
    root,gate,ledger,prefix,_=synthetic_run
    seen=[];original=runner.simulate_sleeve
    def monitored(target,cell,costs,policy):
        seen.append(cell['arm']);return original(target,cell,costs,policy)
    monkeypatch.setattr(runner,'simulate_sleeve',monitored)
    result=runner.execute(root)
    assert seen[:8]==['A00']*8 and len(seen)==32
    assert len(result['cells'])==4 and all(c['metrics']['status']=='complete' for c in result['cells'])
    assert len(result['direct_contrasts'])==len(result['factorial_contrasts'])==3
    assert ledger.read_bytes().startswith(prefix) and len(ledger.read_bytes().splitlines())==6
    assert result['control_parity']['traces']==8
    for name,digest in result['output_sha256'].items():assert runner.sha(root/runner.OUTPUT/name)==digest
    with pytest.raises(FileExistsError):runner.execute(root)
    assert len(ledger.read_bytes().splitlines())==6


def test_one_alternative_sleeve_failure_keeps_other_and_null_index(synthetic_run,monkeypatch):
    root,gate,ledger,prefix,_=synthetic_run
    original=runner.simulate_sleeve;seen={'n':0}
    def broken(target,cell,costs,policy):
        if cell['arm']=='A10':
            seen['n']+=1
            if seen['n']==1:raise ValueError('synthetic unavailable first sleeve')
        return original(target,cell,costs,policy)
    monkeypatch.setattr(runner,'simulate_sleeve',broken)
    result=runner.execute(root)
    cell=result['cells'][1];v=cell['metrics']['variants']['primary']
    assert v['sleeves']['bitcoin']['status']=='unavailable'
    assert v['sleeves']['ethereum']['status']=='complete'
    assert v['index']['status']=='unavailable' and cell['metrics']['status']=='unavailable'
    frame=pd.read_parquet(root/runner.OUTPUT/'synthetic-A10-primary-returns.parquet')
    assert frame.ethereum.notna().all() and frame.index_return.isna().all()
    assert len(ledger.read_bytes().splitlines())==6


@pytest.mark.parametrize('fault',['missing','parity','ledger','postflight','receipt'])
def test_global_failure_preserves_all_identities_and_safe_append(synthetic_run,monkeypatch,fault):
    root,gate,ledger,prefix,provenance=synthetic_run
    called=[];original=runner.simulate_sleeve
    def monitored(target,cell,costs,policy):
        called.append(cell['arm']);result=original(target,cell,costs,policy)
        if fault=='postflight' and cell['arm']=='A11':provenance['gate_sha256']='d'*64
        return result
    monkeypatch.setattr(runner,'simulate_sleeve',monitored)
    if fault=='missing':next((root/runner.SOURCE).glob('*-targets.parquet')).unlink()
    if fault=='parity':monkeypatch.setattr(runner.ev,'control_trace_parity',lambda *a:(_ for _ in ()).throw(ValueError('parity mutation')))
    if fault=='ledger':ledger.write_bytes(prefix+b'bad\n')
    if fault=='receipt':
        path=root/gate['source_result'];prior=json.loads(path.read_text());prior['git_commit']='2'*40
        path.write_text(json.dumps(prior));gate['pinned_files'][gate['source_result']]=runner.sha(path)
    with pytest.raises((ValueError,FileNotFoundError)):runner.execute(root)
    output=root/runner.OUTPUT;failure=json.loads((output/'failure.json').read_text())
    assert len(failure['cells'])==4 and all(c['metrics']['status']=='unavailable' for c in failure['cells'])
    assert len((output/'prepared-failure-ledger.jsonl').read_text().splitlines())==4
    assert not (output/'result.json').exists()
    if fault in ('ledger','postflight'):
        assert failure['central_ledger_appended'] is False
        assert ledger.read_bytes()==prefix+(b'bad\n' if fault=='ledger' else b'')
    else:assert len(ledger.read_bytes().splitlines())==6
    if fault=='parity':assert set(called)=={'A00'}
    if fault in ('missing','ledger','receipt'):assert called==[]
