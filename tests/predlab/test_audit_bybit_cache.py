from __future__ import annotations
import json
import pandas as pd
import pytest
from scripts import predlab_bybit_fetch as fetch


def test_existing_files_do_not_skip_requested_tail_and_metadata_is_preserved(tmp_path, monkeypatch):
    store=tmp_path/'bybit'
    for folder in ('klines','funding'): (store/folder).mkdir(parents=True)
    oldidx=pd.date_range('2024-01-01',periods=2,tz='UTC')
    pd.DataFrame({'close':[1.,2.]},index=oldidx).to_parquet(store/'klines/A.parquet')
    pd.DataFrame({'fundingRate':[0.,0.]},index=oldidx).to_parquet(store/'funding/A.parquet')
    (store/'manifest.json').write_text(json.dumps({'symbols':{'A':{'note':'original'},'B':{'kline_days':100}}}))
    monkeypatch.setattr(fetch,'STORE',store);monkeypatch.setattr(fetch,'DATA_ROOT',tmp_path)
    monkeypatch.setattr(fetch,'enumerate_symbols',lambda:[{'symbol':'A','status':'Trading','fundingInterval':480}])
    monkeypatch.setattr(fetch.sys,'argv',['fetch','--end','2024-01-03'])
    calls=[]
    def klines(*args):
        calls.append('kline')
        return pd.DataFrame({'close':[3.]},index=pd.DatetimeIndex(['2024-01-03'],tz='UTC'))
    monkeypatch.setattr(fetch,'fetch_klines',klines)
    monkeypatch.setattr(fetch,'fetch_funding',lambda *args:pd.DataFrame({'fundingRate':[.001]},index=pd.DatetimeIndex(['2024-01-03'],tz='UTC')))
    fetch.main()
    assert calls==['kline']
    m=json.loads((store/'manifest.json').read_text())
    assert m['symbols']['A']['note']=='original' and m['symbols']['B']['kline_days']==100
    assert m['symbols']['A']['kline_days']==3
    assert m['symbols']['A']['kline_end']=='2024-01-03'
    assert len(pd.read_parquet(store/'klines/A.parquet'))==3
    assert list((store/'snapshots').rglob('*.parquet'))


def test_cache_requires_explicit_complete_end(tmp_path):
    kp=tmp_path/'k.parquet';fp=tmp_path/'f.parquet'
    idx=pd.date_range('2024-01-01',periods=3,freq='D',tz='UTC')
    pd.DataFrame({'close':[1.,2.,3.]},index=idx).to_parquet(kp)
    pd.DataFrame({'fundingRate':[0.]},index=idx[:1]).to_parquet(fp)
    end=int(idx[-1].timestamp()*1000)
    assert not fetch.cache_current(kp,fp,end,480)
    pd.DataFrame({'fundingRate':0.},index=pd.date_range('2024-01-01',periods=9,freq='8h',tz='UTC')).to_parquet(fp)
    assert fetch.cache_current(kp,fp,end,480)
