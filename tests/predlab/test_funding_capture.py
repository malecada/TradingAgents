"""Public capture evidence and pagination; no exchange or account calls."""
import hashlib
import http.client
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import urllib.error

import pandas as pd
import pytest

from tradingagents.predlab import funding_capture as capture


DAY = 86_400_000
NOW = 20_000 * DAY + 12 * 3_600_000


@pytest.fixture(autouse=True)
def fixed_local_clock(monkeypatch):
    monkeypatch.setattr(capture,'utc_now',lambda:pd.Timestamp(NOW,unit='ms',tz='UTC').isoformat())


def contract(symbol='BTCUSDT', **updates):
    return dict(symbol=symbol, contractType='PERPETUAL', quoteAsset='USDT',
                marginAsset='USDT', status='TRADING', underlyingType='COIN',
                onboardDate=NOW-100*DAY, **updates)


def event(ts, symbol='BTCUSDT', **updates):
    return dict(symbol=symbol, fundingTime=ts, fundingRate='0.001',
                markPrice='100.0', rateType='Regular', **updates)


class PublicFixture:
    def __init__(self, rows=None, contracts=None):
        self.rows = rows if rows is not None else [event(NOW-DAY), event(NOW)]
        self.contracts = contracts or [contract()]
        self.calls = []
        self.history_failure = None

    def __call__(self, endpoint, params):
        self.calls.append((endpoint, dict(params)))
        if endpoint.endswith('/time'): data = {'serverTime': NOW}
        elif endpoint.endswith('/exchangeInfo'): data = {'symbols': self.contracts}
        elif endpoint.endswith('/fundingInfo'): data = []
        elif endpoint.endswith('/premiumIndex'): data = [{'symbol':r['symbol'], 'time':NOW, 'nextFundingTime':NOW+DAY} for r in self.contracts]
        else:
            assert endpoint == '/fapi/v1/fundingRate'
            if self.history_failure: return self.history_failure
            data = [r for r in self.rows if params['startTime'] <= r['fundingTime'] <= params['endTime']][:params['limit']]
        return 200, {'content-type':'application/json'}, json.dumps(data).encode()


def test_capture_preserves_raw_and_projects_rates_without_calling_accounts(tmp_path):
    fixture = PublicFixture()
    run = tmp_path/'run'
    result = capture.capture_run(run, transport=fixture, pace_seconds=0, page_limit=1)
    entry = result['instruments']['BTCUSDT']
    assert entry['status'] == 'captured' and entry['query_complete'] is True
    frame = pd.read_parquet(run/entry['file'])
    assert list(frame.fundingRate) == [.001, .001]
    assert list(frame.markPrice) == [100.,100.]
    assert frame.index.is_unique and str(frame.index.tz) == 'UTC'
    assert set(frame.rateType) == {'Regular'}
    assert entry['sha256'] == hashlib.sha256((run/entry['file']).read_bytes()).hexdigest()
    for receipt in result['requests']:
        assert hashlib.sha256((run/receipt['body_file']).read_bytes()).hexdigest() == receipt['body_sha256']
        assert receipt['received_utc']
    pages = [p for e,p in fixture.calls if e.endswith('/fundingRate') and p['startTime']!=p['endTime']]
    assert pages[1]['startTime'] == NOW-DAY+1
    assert all(p['endTime']==NOW for p in pages)
    assert not any('account' in e or 'order' in e for e,_ in fixture.calls)
    assert json.loads((run/'manifest.json').read_text()) == result


def test_existing_run_is_never_overwritten(tmp_path):
    run=tmp_path/'run'; fixture=PublicFixture()
    capture.capture_run(run,transport=fixture,pace_seconds=0)
    original=(run/'manifest.json').read_bytes(); calls=len(fixture.calls)
    with pytest.raises(FileExistsError): capture.capture_run(run,transport=fixture,pace_seconds=0)
    assert (run/'manifest.json').read_bytes()==original and len(fixture.calls)==calls


@pytest.mark.parametrize('problem',['conflict','special','wrong_symbol','nonfinite','bad_time','unsorted'])
def test_ambiguous_or_invalid_history_is_quarantined(tmp_path,problem):
    rows=[event(NOW-DAY),event(NOW)]
    if problem=='conflict': rows.insert(1,dict(rows[0],fundingRate='0.002'))
    elif problem=='special': rows[-1]['rateType']='Special'
    elif problem=='wrong_symbol': rows[-1]['symbol']='ETHUSDT'
    elif problem=='nonfinite': rows[-1]['fundingRate']='NaN'
    elif problem=='bad_time': rows[-1]['fundingTime']=True
    else: rows.reverse()
    fixture=PublicFixture(rows)
    # Return the bad page verbatim, including invalid/out-of-query values.
    base=fixture.__call__
    def transport(e,p):
        return (200,{},json.dumps(rows).encode()) if e.endswith('/fundingRate') else base(e,p)
    result=capture.capture_run(tmp_path/'run',transport=transport,pace_seconds=0)
    assert result['instruments']['BTCUSDT']['status']=='quarantined'
    assert result['instruments']['BTCUSDT']['query_complete'] is False
    assert not list((tmp_path/'run'/'events').glob('*.parquet'))


def test_exact_duplicate_can_be_deduplicated_without_losing_raw_evidence(tmp_path):
    rows=[event(NOW-DAY),event(NOW-DAY),event(NOW)]
    result=capture.capture_run(tmp_path/'run',transport=PublicFixture(rows),pace_seconds=0)
    entry=result['instruments']['BTCUSDT']
    assert entry['row_count']==2 and entry['exact_duplicates']==1
    receipt=[r for r in result['requests'] if r['endpoint'].endswith('/fundingRate')][0]
    assert len(json.loads((tmp_path/'run'/receipt['body_file']).read_text()))==3


def test_rate_limit_retains_all_requested_names_and_stops_requests(tmp_path):
    fixture=PublicFixture(contracts=[contract(),contract('ETHUSDT')])
    fixture.history_failure=(429,{'retry-after':'60'},b'{"code":-1003}')
    result=capture.capture_run(tmp_path/'run',transport=fixture,pace_seconds=0)
    assert result['requested_symbols']==['BTCUSDT','ETHUSDT']
    assert all(e['status']=='unavailable' for e in result['instruments'].values())
    assert sum(e.endswith('/fundingRate') for e,_ in fixture.calls)==1
    assert result['requests'][-1]['status']==429
    assert result['status']=='partial'


def test_unknown_requested_symbol_is_not_dropped_or_relabelled(tmp_path):
    result=capture.capture_run(tmp_path/'run',symbols=['BTCUSDT','GONEUSDT'],transport=PublicFixture(),pace_seconds=0)
    assert result['requested_symbols']==['BTCUSDT','GONEUSDT']
    assert result['instruments']['GONEUSDT']['status']=='unavailable'


@pytest.mark.parametrize('symbol',['币安人生USDT','我踏马来了USDT','龙虾USDT','牛来USDT','哈基米USDT'])
def test_provider_unicode_identity_is_preserved_in_current_universe(tmp_path,symbol):
    fixture=PublicFixture(rows=[event(NOW,symbol=symbol)],contracts=[contract(symbol)])
    result=capture.capture_run(tmp_path/'run',transport=fixture,pace_seconds=0)
    assert result['requested_symbols']==[symbol]
    assert result['instruments'][symbol]['status']=='captured'
    assert (tmp_path/'run'/f'events/{symbol}.parquet').is_file()
    assert [p['symbol'] for e,p in fixture.calls if e.endswith('/fundingRate')]==[symbol]


@pytest.mark.parametrize('symbol',['../BTCUSDT','BTC/USDT','BTC USDT','BTCUSDT\n'])
def test_unsafe_symbol_is_rejected_before_capture(tmp_path,symbol):
    with pytest.raises(ValueError):
        capture.capture_run(tmp_path/'run',symbols=[symbol],transport=PublicFixture(),pace_seconds=0)
    assert not (tmp_path/'run').exists()


def test_full_nonadvancing_page_cannot_claim_exhaustion(tmp_path):
    fixture=PublicFixture(); base=fixture.__call__
    def transport(e,p):
        return (200,{},json.dumps([event(NOW-DAY)]).encode()) if e.endswith('/fundingRate') else base(e,p)
    result=capture.capture_run(tmp_path/'run',transport=transport,pace_seconds=0,page_limit=1)
    assert result['instruments']['BTCUSDT']['status']=='quarantined'


def test_missing_rate_type_is_only_admitted_for_explicit_crypto_perpetual(tmp_path):
    row=event(NOW);row.pop('rateType')
    result=capture.capture_run(tmp_path/'run',transport=PublicFixture([row]),pace_seconds=0)
    assert result['instruments']['BTCUSDT']['status']=='captured'
    frame=pd.read_parquet(tmp_path/'run'/result['instruments']['BTCUSDT']['file'])
    assert frame.rateType.iloc[0]=='unspecified_crypto'


def test_initial_metadata_failure_is_preserved_not_a_successful_empty_universe(tmp_path):
    result=capture.capture_run(tmp_path/'run',transport=lambda e,p:(503,{},b'Unavailable'),pace_seconds=0)
    assert result['status']=='failed' and result['requests'][0]['status']==503
    assert (tmp_path/'run'/'manifest.json').exists()


def test_partial_http_body_and_request_survive_transport_exception(tmp_path):
    def transport(e,p): raise http.client.IncompleteRead(b'{"serverTime":',3)
    result=capture.capture_run(tmp_path/'run',transport=transport,pace_seconds=0)
    assert result['status']=='failed'
    assert 'IncompleteRead' in result['requests'][0]['error']
    assert (tmp_path/'run'/result['requests'][0]['body_file']).read_bytes()==b'{"serverTime":'


def test_interrupted_rate_limit_body_preserves_status_and_stops(tmp_path,monkeypatch):
    class BrokenBody:
        closed = False
        def read(self): raise http.client.IncompleteRead(b'{"code":',10)
        def close(self): pass
    class Opener:
        def open(self,request,timeout):
            raise urllib.error.HTTPError(request.full_url,429,'rate limited',{'Retry-After':'60'},BrokenBody())
    monkeypatch.setattr(capture.urllib.request,'build_opener',lambda *args:Opener())
    fixture=PublicFixture(contracts=[contract(),contract('ETHUSDT'),contract('SOLUSDT')])
    calls=[]
    def transport(e,p):
        if e.endswith('/fundingRate'):
            calls.append(p)
            return capture.public_get(e,p)
        return fixture(e,p)
    result=capture.capture_run(tmp_path/'run',transport=transport,pace_seconds=0)
    assert len(calls)==1
    receipt=result['requests'][-1]
    assert receipt['status']==429 and receipt['headers']['retry-after']=='60'
    assert 'IncompleteRead' in receipt['error']
    assert (tmp_path/'run'/receipt['body_file']).read_bytes()==b'{"code":'


def test_conflict_split_across_full_page_boundary_is_quarantined(tmp_path):
    rows=[event(NOW-DAY),dict(event(NOW-DAY),fundingRate='.002'),event(NOW)]
    result=capture.capture_run(tmp_path/'run',transport=PublicFixture(rows),pace_seconds=0,page_limit=1)
    assert result['instruments']['BTCUSDT']['status']=='quarantined'
    assert result['instruments']['BTCUSDT']['query_complete'] is False


@pytest.mark.parametrize('endpoint,bad', [('/fapi/v1/premiumIndex',[{'bogus':True}]),
    ('/fapi/v1/fundingInfo',[{'symbol':'BTCUSDT','fundingIntervalHours':'hourly'}]),
    ('/fapi/v1/time',{'serverTime':NOW-DAY})])
def test_invalid_schedule_or_stale_current_clock_cannot_claim_capture(tmp_path,endpoint,bad):
    fixture=PublicFixture()
    def transport(e,p): return (200,{},json.dumps(bad).encode()) if e==endpoint else fixture(e,p)
    result=capture.capture_run(tmp_path/'run',transport=transport,pace_seconds=0)
    assert result['status']=='failed' and result.get('error')


def isolated_collector(root, monkeypatch):
    """Load the actual collector from a synthetic source tree without .git."""
    module_path = root/'tradingagents'/'predlab'/'funding_capture.py'
    module_path.parent.mkdir(parents=True)
    module_path.write_bytes(Path(capture.__file__).read_bytes())
    spec = importlib.util.spec_from_file_location('isolated_funding_capture', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'utc_now', lambda: pd.Timestamp(NOW, unit='ms', tz='UTC').isoformat())
    return module


def initialize_local_git(root):
    root.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1')
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], env=env, stderr=subprocess.DEVNULL)
    git('init')
    (root/'seed.txt').write_text('synthetic source identity fixture\n')
    git('add', '.')
    git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
        '-c', 'commit.gpgsign=false', 'commit', '-m', 'synthetic source')
    return git('rev-parse', 'HEAD').decode().strip()


@pytest.mark.parametrize('enclosing_git', [False, True])
def test_release_source_commit_is_used_without_own_git_checkout(tmp_path, monkeypatch, enclosing_git):
    outer = tmp_path/'outer'
    if enclosing_git:
        initialize_local_git(outer)
    root = outer/'release'
    module = isolated_collector(root, monkeypatch)
    commit = '1234567890abcdef1234567890abcdef12345678'
    (root/'SOURCE_COMMIT').write_text(commit+'\n')
    result = module.capture_run(tmp_path/'run', transport=PublicFixture(), pace_seconds=0)
    assert result['status'] == 'captured'
    assert result['source']['git_commit'] == commit
    assert result['source']['source_identity_method'] == 'release_marker'
    assert result['source']['collector_sha256'] == hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()


@pytest.mark.parametrize('enclosing_git', [False, True])
def test_missing_module_source_identity_stops_before_requests(tmp_path, monkeypatch, enclosing_git):
    outer = tmp_path/'outer'
    if enclosing_git:
        initialize_local_git(outer)
    module = isolated_collector(outer/'release', monkeypatch)
    fixture = PublicFixture()
    result = module.capture_run(tmp_path/'run', symbols=['BTCUSDT'], transport=fixture, pace_seconds=0)
    assert result['status'] == 'failed' and 'source identity' in result['error']
    assert result['requests'] == [] and fixture.calls == []
    assert result['requested_symbols'] == ['BTCUSDT']
    assert json.loads((tmp_path/'run'/'manifest.json').read_text()) == result


@pytest.mark.parametrize('marker', [b'', b'g'*40+b'\n', b'a'*39+b'\n', b'a'*40, b'a'*40+b'\nextra\n'])
def test_invalid_release_marker_fails_before_any_request(tmp_path, monkeypatch, marker):
    root = tmp_path/'release'
    module = isolated_collector(root, monkeypatch)
    (root/'SOURCE_COMMIT').write_bytes(marker)
    fixture = PublicFixture()
    result = module.capture_run(tmp_path/'run', transport=fixture, pace_seconds=0)
    assert result['status'] == 'failed' and 'SOURCE_COMMIT' in result['error']
    assert not fixture.calls and result['requests'] == []
    assert (root/'SOURCE_COMMIT').read_bytes() == marker
    assert json.loads((tmp_path/'run'/'manifest.json').read_text()) == result


def test_own_module_checkout_identifies_its_git_commit(tmp_path, monkeypatch):
    root = tmp_path/'checkout'
    module = isolated_collector(root, monkeypatch)
    commit = initialize_local_git(root)
    result = module.capture_run(tmp_path/'run', transport=PublicFixture(), pace_seconds=0)
    assert result['status'] == 'captured'
    assert result['source']['git_commit'] == commit
    assert result['source']['source_identity_method'] == 'git_checkout'
