from __future__ import annotations
import numpy as np
import pandas as pd
import pytest
from scripts.audit_correction_2026_09_09 import read_development, infer_saved_enet_failures


def test_reader_excludes_holdout_at_parquet_boundary(tmp_path):
    index=pd.date_range('2025-03-30',periods=4,tz='UTC',name='ts')
    p=tmp_path/'sample.parquet'
    pd.DataFrame({'y':[1,2,999,999]},index=index).to_parquet(p)
    hashes={}; out=read_development(p,hashes)
    assert out.y.tolist()==[1,2] and len(hashes[str(p)])==64


def test_failure_reconstruction_preserves_real_zero_prediction():
    index=pd.date_range('2021-01-01',periods=100,tz='UTC')
    series=pd.DataFrame({'y':np.ones(100),'x':np.ones(100)},index=index)
    series.loc[index[91],'x']=np.nan
    saved=pd.DataFrame({'y_true':1.,'pred':0.},index=index[90:])
    failures=infer_saved_enet_failures(series,saved,21,'T1_ret')
    assert failures.sum()==1 and failures.loc[index[91]]
    saved.loc[index[91],'pred']=.1
    with pytest.raises(ValueError,match='sentinel'):
        infer_saved_enet_failures(series,saved,21,'T1_ret')


def test_no_fit_availability_is_held_until_the_next_refit():
    index=pd.date_range('2021-01-01',periods=100,tz='UTC')
    series=pd.DataFrame({'y':np.ones(100),'x':np.ones(100)},index=index)
    series.loc[index[:40],'x']=np.nan
    saved=pd.DataFrame({'y_true':1.,'pred':.02},index=index[90:])
    assert infer_saved_enet_failures(series,saved,21,'T2_dir').all()


def test_strategy_clock_rejects_truncated_endpoint():
    from scripts.audit_correction_2026_09_09 import require_strategy_clock
    full=pd.date_range('2021-01-01','2025-03-31',tz='UTC')
    require_strategy_clock(pd.Series(1.,index=full),'D','fixture')
    with pytest.raises(ValueError,match='clock'):
        require_strategy_clock(pd.Series(1.,index=full[:-1]),'D','fixture')


def test_missing_saved_source_reports_all_registered_forecast_cells(tmp_path):
    from scripts.audit_correction_2026_09_09 import saved_enet
    gate={'protocol':{},'cells':[{'cell':f'{s}|{h}|{t}','symbol':s,'horizon':h,'target':t,'strong_baseline':'base'}
        for s in ('BTCUSDT','ETHUSDT') for h in ('1h','24h') for t in ('T1_ret','T2_dir','T3_rv','T4_vol')]}
    rows=saved_enet(tmp_path,tmp_path,{},gate)
    assert len(rows)==16
    assert all(r['status']=='stopped_missing_or_inconsistent_provenance' for r in rows)
