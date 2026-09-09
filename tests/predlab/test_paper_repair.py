"""Hand-derived calendar and net-accounting parity without market data."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
import predlab_s1_paper as paper
from tradingagents.predlab import opt


def panel():
    idx=pd.date_range('2026-06-20','2026-09-02',tz='UTC')
    names=[f'N{i:03}' for i in range(195)]+[f'A{i}' for i in range(5)]+[f'B{i}' for i in range(5)]
    qv=pd.DataFrame(10.,index=idx,columns=names)
    qv.loc[idx.month==7,[f'A{i}' for i in range(5)]]=20.
    qv.loc[idx.month==7,[f'B{i}' for i in range(5)]]=1.
    qv.loc[idx.month==8,[f'A{i}' for i in range(5)]]=1.
    qv.loc[idx.month==8,[f'B{i}' for i in range(5)]]=20.
    park=pd.DataFrame(np.tile(np.arange(1,206.),(len(idx),1)),index=idx,columns=names)
    close=pd.DataFrame(100.,index=idx,columns=names)
    return {'close':close,'qv':qv,'park':park,'funding':close*0}


def test_month_boundary_uses_trade_month_and_previous_calendar_month():
    p=panel(); cutoff=pd.Timestamp('2026-08-31',tz='UTC')
    _,w,_=paper.todays_book({k:v.loc[:cutoff] for k,v in p.items()},'ewma_20')
    assert set(f'B{i}' for i in range(5)) <= set(w.index)
    assert set(f'A{i}' for i in range(5)).isdisjoint(w.index)
    # Shared engine agrees; independently known B high-vol names must enter.
    d=pd.Timestamp('2026-09-01',tz='UTC')
    sig=opt.build_signal(p['park'],p['close'],'ewma_20').loc[d]
    expected=paper.pp.quintile_weights(sig.where(opt.monthly_universe(p['qv']).loc[d]),'eq')
    pd.testing.assert_series_equal(w,expected[expected!=0],check_names=False)


def test_calendar_median_does_not_admit_july_days():
    p=panel(); qv=p['qv']; qv[:]=10; qv['B4']=1
    qv.loc['2026-07-28':'2026-07-31','B4']=100
    qv.loc['2026-08-17':'2026-08-31','B4']=100
    _,w,_=paper.todays_book({k:v.loc[:'2026-09-01'] for k,v in p.items()},'ewma_20')
    assert 'B4' not in w.index


def test_partial_missing_marks_and_closes_make_measurement_incomplete():
    prev={'asof':'2026-08-31','weights':{'A':.5,'B':-.5},'mark_px':{'A':100,'B':100}}
    assert paper.realized_prev_mark_return(prev,{'A':110}) is None
    close=pd.DataFrame({'A':[100.,110.],'B':[100.,np.nan]},index=pd.date_range('2026-08-31',periods=2,tz='UTC'))
    assert paper.realized_prev_return({'close':close},prev,close.index[-1]) is None


def test_new_journal_refuses_to_mix_legacy_rows(tmp_path):
    j=tmp_path/'old.jsonl'; original=json.dumps({'asof':'2026-08-01','weights':{}})+'\n';j.write_text(original)
    with pytest.raises(ValueError,match='version|legacy'):
        paper.journal_one(j,panel(),'ewma_20','scale',.15)
    assert j.read_text()==original


def test_net_measurement_charges_initial_turnover_and_signed_funding(tmp_path):
    p=panel(); j=tmp_path/'v2.jsonl'
    cutoff=pd.Timestamp('2026-08-31',tz='UTC')
    paper.journal_one(j,{k:v.loc[:cutoff] for k,v in p.items()},'ewma_20','scale',.15)
    first=json.loads(j.read_text().splitlines()[-1]); w=first['weights']
    # All long prices +10%, all short prices -10%: gross +20%; gross notional 2.
    for s,weight in w.items():
        p['close'].loc['2026-09-01',s]=110 if weight>0 else 90
        p['funding'].loc['2026-09-01',s]=.01 if weight>0 else .02
    paper.journal_one(j,{k:v.loc[:'2026-09-01'] for k,v in p.items()},'ewma_20','scale',.15)
    r=json.loads(j.read_text().splitlines()[-1])
    assert r['journal_version']==2
    assert r['base_measurement']['gross']==pytest.approx(.2)
    assert r['base_measurement']['carry']==pytest.approx(.01)
    assert r['base_measurement']['cost']==pytest.approx(.001)
    assert r['realized_base_net_ret']==pytest.approx(.209)
    assert r['base_state']['nav']==pytest.approx(1.209)
    assert r['realized_net_ret'] is None  # overlay needs measured net-vol warmup


def test_missing_funding_is_not_reported_as_zero_net_return(tmp_path):
    p=panel();p.pop('funding');j=tmp_path/'v2.jsonl'
    for day in ['2026-08-31','2026-09-01']:
        paper.journal_one(j,{k:v.loc[:day] for k,v in p.items()},'ewma_20','scale',.15)
    r=json.loads(j.read_text().splitlines()[-1])
    assert r['realized_base_net_ret'] is None
    assert 'funding' in r['measurement_reason']
    assert r['measurement_status']=='incomplete'


def test_stale_panels_cannot_write_actionable_next_day(tmp_path):
    p={k:v.loc[:'2026-08-31'] for k,v in panel().items()};j=tmp_path/'v2.jsonl'
    result=paper.journal_one(j,p,'ewma_20','scale',.15,trade_day=pd.Timestamp('2026-09-03',tz='UTC'))
    assert result.startswith('WAIT')
    assert not j.exists()


def test_local_funding_loader_requires_all_daily_events_and_boundary(tmp_path):
    index=pd.date_range('2026-08-20','2026-08-24',freq='8h',tz='UTC')
    raw=pd.DataFrame({'fundingRate':.001},index=index)
    raw.to_parquet(tmp_path/'AAA.parquet')
    raw.drop(pd.Timestamp('2026-08-22T08:00Z')).to_parquet(tmp_path/'GAP.parquet')
    raw.iloc[:-1].to_parquet(tmp_path/'TAIL.parquet')
    days=pd.date_range('2026-08-22','2026-08-23',tz='UTC')
    daily,coverage=paper.load_observed_funding(['AAA','GAP','TAIL','MISSING'],days,tmp_path)
    assert daily.loc[days[0],'AAA']==pytest.approx(.003)
    assert pd.isna(daily.loc[days[0],'GAP'])
    assert pd.isna(daily.loc[days[1],'TAIL'])
    assert daily['MISSING'].isna().all()
    assert coverage['method']=='observed_cadence_inference'


def test_paper_net_matches_engine_with_drift_and_overlay_scale(tmp_path,monkeypatch):
    p=panel();j=tmp_path/'v2.jsonl'
    monkeypatch.setattr(paper,'vt_scale',lambda *a,**k:.5)
    for day in ['2026-08-31','2026-09-01','2026-09-02']:
        if day=='2026-09-01':
            initial=json.loads(j.read_text().splitlines()[0])
            for s,w in initial['weights'].items():
                p['close'].loc['2026-09-01':,s]=110 if w>0 else 90
                p['funding'].loc['2026-09-01',s]=.01 if w>0 else .02
        paper.journal_one(j,{k:v.loc[:day] for k,v in p.items()},'ewma_20','scale',.15)
    rows=[json.loads(l) for l in j.read_text().splitlines()]
    assert rows[1]['realized_net_ret']==pytest.approx(.1045)
    assert rows[2]['base_state']['nav']==pytest.approx(1.208791)
    assert rows[2]['base_measurement']['turnover']==pytest.approx(.418/1.209)
    engine=opt.run_ls(opt.build_signal(p['park'],p['close'],'ewma_20'),
        p['close'].pct_change(fill_method=None),opt.monthly_universe(p['qv']),p['funding'],
        opt.OptConfig(), '2026-09-01','2026-09-02')
    assert [r['realized_base_net_ret'] for r in rows[1:]]==pytest.approx(engine['rets']['net'].tolist())


def test_missing_signal_panel_does_not_write_an_intentional_exit(tmp_path):
    p=panel()
    p['park'].loc['2026-09-02']=np.nan
    j=tmp_path/'v2.jsonl'
    assert paper.journal_one(j,p,'ewma_20','scale',.15).startswith('WAIT')
    assert not j.exists()


def test_public_marks_without_exchange_timestamp_are_unavailable(monkeypatch):
    import io
    monkeypatch.setattr('urllib.request.urlopen',lambda *a,**k:io.BytesIO(
        b'[{"symbol":"AAA","price":"100","bidPrice":"99","askPrice":"101"}]'))
    assert not paper.fetch_marks()
