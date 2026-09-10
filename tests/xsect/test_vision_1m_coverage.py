import pandas as pd

from scripts import fetch_vision_1m as fetcher
from scripts.fetch_vision_1m import month_covered


def test_minute_month_requires_full_unique_aligned_clock():
    month = pd.Period('2022-02', freq='M')
    clock = pd.date_range('2022-02-01', '2022-03-01', inclusive='left', freq='min', tz='UTC')
    complete = pd.DataFrame({'close': 1.}, index=clock)
    assert month_covered(complete, month)
    assert not month_covered(complete.iloc[:1], month)
    assert not month_covered(complete.iloc[:-72*60], month)
    assert not month_covered(complete.drop(clock[100:103]), month)
    duplicate = pd.concat([complete.iloc[:-1], complete.iloc[:1]])
    assert not month_covered(duplicate, month)
    off_grid = complete.copy()
    off_grid.index = off_grid.index + pd.Timedelta(seconds=1)
    assert not month_covered(off_grid, month)


def test_minute_coverage_does_not_infer_missing_month_from_later_data():
    later = pd.DataFrame({'close': [1.]}, index=pd.to_datetime(['2022-04-01'], utc=True))
    assert not month_covered(later, pd.Period('2022-02', freq='M'))
    assert not month_covered(None, pd.Period('2022-02', freq='M'))


def test_partial_month_is_retried_despite_legacy_absent_archive_marker(tmp_path, monkeypatch):
    monkeypatch.setattr(fetcher, 'OUT_DIR', tmp_path)
    frame = pd.DataFrame({'close': [1.]}, index=pd.to_datetime(['2022-02-01'], utc=True))
    frame.to_parquet(tmp_path/'TESTUSDT.parquet')
    calls = []
    def fetch_month(sym, month):
        calls.append((sym,month))
        return month, 'failed', None
    monkeypatch.setattr(fetcher, 'fetch_month', fetch_month)
    month = pd.Period('2022-02', freq='M')
    fetcher.fetch_symbol('TESTUSDT', [month], {'2022-02'}, 1)
    assert calls == [('TESTUSDT', month)]
