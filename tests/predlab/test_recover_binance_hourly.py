"""Offline evidence checks for the bounded 360-hour recovery."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/recover_binance_hourly_2026_09_10.py"


def module():
    assert SCRIPT.exists(), "bounded hourly recovery transform is missing"
    spec = importlib.util.spec_from_file_location("hourly_recovery", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rows(start="2022-02-26", n=24):
    return [[int(t.timestamp()*1000), "10.0", "12.0", "9.0", "11.0", "100.0",
             int(t.timestamp()*1000)+3599999, "1100.0", 20, "50.0", "550.0", "0"]
            for t in pd.date_range(start, periods=n, freq="1h", tz="UTC")]


def zip_bytes(values, header=False):
    buf = io.BytesIO()
    text = pd.DataFrame(values).to_csv(index=False, header=header)
    with zipfile.ZipFile(buf, "w") as z: z.writestr("bars.csv", text)
    return buf.getvalue()


def test_valid_checksum_and_strict_observed_bar_schema():
    mod = module()
    raw = zip_bytes(rows())
    checksum = (hashlib.sha256(raw).hexdigest()+"  sample.zip\n").encode()
    mod.verify_checksum(raw, checksum, "sample.zip")
    frame = mod.parse_zip(raw)
    assert len(frame) == 24 and frame.index[0] == pd.Timestamp("2022-02-26",tz="UTC")
    assert frame.close_time.iloc[0] == 1645837199999
    with pytest.raises(mod.RecoveryError, match="checksum"):
        mod.verify_checksum(raw+b"corrupt", checksum, "sample.zip")
    with pytest.raises(mod.RecoveryError, match="filename"):
        mod.verify_checksum(raw, checksum, "different.zip")


@pytest.mark.parametrize("change", ["duplicate", "nan", "ohlc", "negative_volume", "close_clock", "microseconds", "unsorted"])
def test_malformed_bar_or_duplicate_rejected(change):
    mod = module(); values = rows()
    if change == "duplicate": values.append(values[0].copy())
    elif change == "nan": values[0][4] = "NaN"
    elif change == "ohlc": values[0][2] = "8"
    elif change == "negative_volume": values[0][5] = "-1"
    elif change == "close_clock": values[0][6] += 1
    elif change == "microseconds": values[0][0] *= 1000
    elif change == "unsorted": values[0],values[1] = values[1],values[0]
    with pytest.raises(mod.RecoveryError): mod.parse_rows(values)


def test_immutable_insertion_preserves_every_old_value_and_rejects_conflicts():
    mod = module(); genuine = mod.parse_rows(rows(n=5))
    old = genuine.loc[genuine.index[[0,4]], mod.OLD_COLUMNS].copy()
    recovered = genuine.loc[genuine.index[1:4]]
    out, info = mod.insert_verified(old, recovered, recovered.index)
    pd.testing.assert_frame_equal(out.loc[old.index], old, check_freq=False)
    assert len(out) == 5 and info["inserted_rows"] == 3
    wrong = genuine.copy(); wrong.loc[old.index[0], "close"] += .5
    with pytest.raises(mod.RecoveryError, match="overlap conflict"):
        mod.compare_overlap(old, wrong, "original", "provider")
    with pytest.raises(mod.RecoveryError, match="target coverage"):
        mod.insert_verified(old, recovered.iloc[:-1], recovered.index)


def test_existing_target_or_unregistered_extra_bar_cannot_be_overwritten():
    mod=module(); bars=mod.parse_rows(rows(n=5)); target=bars.index[1:4]
    old=bars.loc[bars.index[[0,1,4]],mod.OLD_COLUMNS]
    with pytest.raises(mod.RecoveryError,match="already present"):
        mod.insert_verified(old,bars.loc[target],target)
    with pytest.raises(mod.RecoveryError,match="unexpected"):
        mod.insert_verified(old.iloc[[0,2]],bars.loc[bars.index[1:]],target)


def test_plan_is_bounded_and_all_target_and_overlap_sources_fixed():
    mod=module(); plan=mod.request_plan()
    assert len(plan)==72  # 33 zips +33 checksums +6 public API windows
    assert sum(x["kind"]=="monthly_zip" for x in plan)==6
    assert sum(x["kind"]=="daily_zip" for x in plan)==27
    assert sum(x["kind"]=="api" for x in plan)==6
    assert sum(len(mod.target_clock(s)) for s in mod.SYMBOLS)==360
    for req in plan:
        assert req["symbol"] in mod.SYMBOLS
        assert req["url"].startswith(("https://data.binance.vision/", "https://fapi.binance.com/fapi/v1/klines?"))


def test_receipt_store_refuses_overwrite_and_enforces_download_budget(tmp_path):
    mod=module(); store=mod.ReceiptStore(tmp_path/"raw", budget=3)
    receipt=store.save("one", "https://data.binance.vision/test", b"abc",200,{})
    assert receipt["sha256"]==hashlib.sha256(b"abc").hexdigest()
    assert (tmp_path/"raw/one.bin").read_bytes()==b"abc"
    with pytest.raises(FileExistsError): store.save("one","url",b"",200,{})
    with pytest.raises(mod.RecoveryError,match="budget"):store.save("two","url",b"x",200,{})


@pytest.mark.parametrize('symbol', ['BNXUSDT','ICPUSDT'])
def test_identity_quarantined_requests_excluded_until_contract_alias_registration(symbol):
    mod=module()
    assert mod.request_plan([{"symbol":symbol,"ranges":[{"start":"2022-04-17","end_exclusive":"2022-04-18"}]}]) == []


@pytest.mark.parametrize("name,body", [("empty.csv", b""), ("bad.json", b"{}")])
def test_empty_or_non_csv_archive_is_explicitly_invalid(name, body):
    mod=module(); buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w") as archive: archive.writestr(name,body)
    with pytest.raises(mod.RecoveryError,match="archive/CSV"):
        mod.parse_zip(buf.getvalue())


def fixture_recovery(mod):
    ranges=[{"start":"2022-02-26","end_exclusive":"2022-02-27"},
            {"start":"2022-04-01","end_exclusive":"2022-04-02"}]
    item={"symbol":"TRXUSDT","ranges":ranges}; plan=mod.request_plan([item]); frames={}
    for req in plan:
        if req["kind"] == "checksum": continue
        n=int((mod.utc(req["end_exclusive"])-mod.utc(req["start"]))/mod.HOUR)
        values=rows(start=req["start"], n=n)
        frames[req["id"]]=mod.parse_rows(values)
    old=mod.join_consistent([f for reqid,f in frames.items() if next(p for p in plan if p['id']==reqid)['kind']=='monthly_zip'],"fixture")
    old=old.drop(mod.target_clock(item["symbol"],ranges))[mod.OLD_COLUMNS]
    return item,old,plan,frames


def test_caller_recovers_exact_observed_sources_and_retains_good_second_interval_after_conflict():
    mod=module(); item,old,plan,frames=fixture_recovery(mod)
    merged,outcomes,comparisons,added=mod.recover_symbol(item,old,plan,frames,{})
    assert [r["status"] for r in outcomes] == ["verified","verified"]
    assert len(added)==48 and len(comparisons)==12
    pd.testing.assert_frame_equal(merged.loc[old.index],old,check_freq=False)
    first_api=next(p for p in plan if p['kind']=='api')
    frames[first_api['id']]=frames[first_api['id']].copy()
    frames[first_api['id']].iloc[0,frames[first_api['id']].columns.get_loc('close')]=10.5
    merged,outcomes,_,added=mod.recover_symbol(item,old,plan,frames,{})
    assert [r["status"] for r in outcomes] == ["unavailable","verified"]
    assert 'overlap conflict' in outcomes[0]['reason'] and len(added)==24
    assert len(merged)==len(old)+24


@pytest.mark.parametrize('symbol', ['BNXUSDT','ICPUSDT'])
def test_identity_quarantine_even_if_price_frames_exist(symbol):
    mod=module(); item,old,plan,frames=fixture_recovery(mod); item['symbol']=symbol
    _,outcomes,_,added=mod.recover_symbol(item,old,plan,frames,{})
    assert added is None
    assert all('identity_quarantine' in r['reason'] for r in outcomes)


def test_truncated_response_retains_partial_bytes_and_budget(tmp_path,monkeypatch):
    mod=module(); store=mod.ReceiptStore(tmp_path/'raw',budget=100)
    class Response(io.BytesIO):
        status=200
        headers={'Content-Length':'10'}
    monkeypatch.setattr(mod.urllib.request,'urlopen',lambda *a,**k:Response(b'abc'))
    receipt=mod.fetch_receipt({'id':'r','url':'https://example.test'},store,
        {'max_attempts_per_request':1,'timeout_seconds':45})
    assert receipt['error'] and 'truncated' in receipt['error']
    assert receipt['bytes']==3 and store.used==3
    assert (store.root/receipt['body_file']).read_bytes()==b'abc'


def test_retry_after_case_insensitive_and_no_early_retry(tmp_path,monkeypatch):
    mod=module(); calls=[]; store=mod.ReceiptStore(tmp_path/'raw')
    class Response(io.BytesIO):
        status=429
        headers={'Content-Length':'0','retry-after':'120'}
    def request(*a,**k): calls.append(1); return Response()
    monkeypatch.setattr(mod.urllib.request,'urlopen',request)
    monkeypatch.setattr(mod.time,'sleep',lambda n:pytest.fail('premature retry'))
    receipt=mod.fetch_receipt({'id':'r','url':'https://example.test'},store,
        {'max_attempts_per_request':3,'timeout_seconds':45})
    assert receipt['status']==429 and len(calls)==1


def test_development_only_read_and_source_hash_required_before_write(tmp_path):
    mod=module(); path=tmp_path/'old.parquet'
    old=mod.parse_rows(rows('2025-03-31',n=25))[mod.OLD_COLUMNS]
    old.to_parquet(path); digest=mod.sha256(path)
    bounded=mod.read_original(path,digest)
    assert len(bounded)==24 and bounded.index.max() < mod.utc('2025-04-01')
    path.write_bytes(b'changed')
    with pytest.raises(mod.RecoveryError,match='checksum'):
        mod.write_symbol_artifacts(tmp_path,'TRXUSDT',path,digest,bounded,bounded,old.iloc[:0])
    assert not (tmp_path/'TRXUSDT.parquet').exists()


def test_snapshot_read_retains_registered_2020_warmup(tmp_path):
    mod=module(); path=tmp_path/'old.parquet'
    warmup=mod.parse_rows(rows('2020-06-01',n=1))[mod.OLD_COLUMNS]
    warmup.to_parquet(path)
    assert mod.read_original(path,mod.sha256(path)).equals(warmup)


def test_family_run_finishes_readiness_and_good_snapshot_when_another_original_is_unavailable(tmp_path,monkeypatch):
    from tradingagents.predlab import registry
    mod=module(); item,old,plan,frames=fixture_recovery(mod)
    source=tmp_path/'source.parquet'; old.to_parquet(source)
    item.update(source_path=str(source),source_sha256=mod.sha256(source))
    bad={**item,'symbol':'FILUSDT','source_path':str(tmp_path/'absent.parquet')}
    scope_path=tmp_path/'scope.json'; scope_path.write_text(json.dumps({'scope':[item,bad]}))
    gate={'timestamp_inventory_scope_addendum':{'path':'scope.json','sha256':mod.sha256(scope_path)},
          'output_root':'recovery','source_roots':[str(tmp_path)],
          'fetch_limits':{'max_download_bytes':250000000,'max_parallel_requests':3,
                          'max_attempts_per_request':3,'timeout_seconds':45}}
    monkeypatch.setattr(mod,'ROOT',tmp_path)
    monkeypatch.setattr(registry,'get_experiment',lambda key:gate)
    monkeypatch.setattr(registry,'preflight',lambda *a:{'git_commit':'synthetic'})
    monkeypatch.setattr(mod,'request_plan',lambda *a:plan)
    monkeypatch.setattr(mod,'fetch_receipt',lambda *a:{})
    monkeypatch.setattr(mod,'load_sources',lambda *a:(frames,{}))
    result=json.loads(mod.run('primary').read_text())
    assert result['inserted_hours']==48 and not result['all_ranges_verified']
    assert len(result['symbols'])==2 and result['symbols'][1]['inserted_hours']==0
    assert 'TRXUSDT.parquet' in result['output_sha256']
    assert result['snapshot_window'][1]=='2025-04-01T00:00:00Z'
    assert result['documentary_budget_reserved'] >= 5000000
    assert mod.sha256(source)==item['source_sha256']
