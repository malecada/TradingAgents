"""Invented source replies plus a disposable guarded lifecycle; no network."""
import base64
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import pytest

DIRECTORY = Path(__file__).resolve().parents[2] / "research/strategy-search-2026-09-11"
for name in ("options_metadata", "triangle_capture"):
    spec = importlib.util.spec_from_file_location(name, DIRECTORY / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
module = sys.modules["triangle_capture"]


def request_spec():
    return json.loads((DIRECTORY / "triangle-request-spec.json").read_text())


def payload(kind):
    if kind == "exchange-info":
        return {"symbols": [{"symbol": symbol, "baseAsset": pair[0], "quoteAsset": pair[1], "status": "TRADING",
                             "isSpotTradingAllowed": True, "filters": []} for symbol, pair in module.PAIRS.items()]}
    if kind == "server-time":
        return {"serverTime": 1800000000000}
    if kind == "book-ticker":
        return [{"symbol": symbol, "bidPrice": "100", "askPrice": "101", "bidQty": "2", "askQty": "3"} for symbol in module.PAIRS]
    return {"lastUpdateId": 0, "bids": [["100", "2"], ["99", "3"]], "asks": [["101", "2"], ["102", "3"]]}


def response(raw, *, status=200, complete=True, error=None):
    return {"body": raw, "http_status": status, "body_complete": complete, "headers": {}, "error": error}


def test_complete_synthetic_six_response_pipeline_is_source_only():
    frozen = request_spec()
    calls, published = [], []
    def fake(url):
        request = frozen["requests"][len(calls)]
        calls.append(url)
        return response(json.dumps(payload(request["kind"])).encode())
    raw, admission, cells = module.capture(frozen, fake, lambda name, row: published.append(name))
    assert len(calls) == len(published) == len(cells) == 6
    assert all(row["status"] == "complete" for row in cells)
    assert admission["cells"][0]["filter_interpretation"]["BTCUSDT"]["status"] == "unavailable"
    assert raw["requests"][0]["request_utc"].endswith("+00:00")


@pytest.mark.parametrize("failure", ["identity", "status", "spot_permission", "filter_schema"])
def test_exchange_metadata_guards(failure):
    data = payload("exchange-info")
    if failure == "identity":
        data["symbols"][0]["quoteAsset"] = "ETH"
    elif failure == "status":
        data["symbols"][0]["status"] = "BREAK"
    elif failure == "spot_permission":
        data["symbols"][0]["isSpotTradingAllowed"] = 1
    else:
        data["symbols"][0]["filters"] = [{}]
    with pytest.raises(ValueError):
        module.parse_response(json.dumps(data).encode(), {"kind": "exchange-info"})


@pytest.mark.parametrize("failure", ["crossed", "duplicate_price", "ordering", "zero_quantity", "too_many", "update_boolean"])
def test_depth_guards(failure):
    data = payload("depth")
    if failure == "crossed":
        data["bids"][0][0] = "102"
    elif failure == "duplicate_price":
        data["bids"][1][0] = "100"
    elif failure == "ordering":
        data["asks"].reverse()
    elif failure == "zero_quantity":
        data["asks"][0][1] = "0"
    elif failure == "too_many":
        data["bids"] *= 11
    else:
        data["lastUpdateId"] = True
    with pytest.raises(ValueError):
        module.parse_response(json.dumps(data).encode(), {"kind": "depth", "symbol": "BTCUSDT"})


@pytest.mark.parametrize("raw", [b'[]', b'{"code":-1}', b'[{"symbol":"BTCUSDT","bidPrice":NaN}]', b'[{"symbol":"BTCUSDT","symbol":"ETHUSDT"}]'])
def test_batch_ticker_rejects_bad_schema_duplicate_keys_and_nonfinite(raw):
    with pytest.raises(ValueError):
        module.parse_response(raw, {"kind": "book-ticker"})


def test_denial_and_partial_body_retain_six_cells():
    calls = []
    def denied(url):
        calls.append(url)
        return response(b"received-prefix", status=403, complete=False, error="denial/incomplete")
    raw, _, cells = module.capture(request_spec(), denied)
    assert len(calls) == 1 and len(cells) == 6
    assert all(row["status"] == "unavailable" for row in cells)
    assert base64.b64decode(raw["requests"][0]["body_base64"]) == b"received-prefix"


def test_cooperative_clock_stops_new_requests_with_less_than_twenty_seconds(monkeypatch):
    calls = iter([0] + [71] * 12)
    monkeypatch.setattr(module.time, "monotonic", lambda: next(calls))
    raw, _, cells = module.capture(request_spec(), lambda url: pytest.fail("cooperatively blocked call"))
    assert len(cells) == 6
    assert all(not row["attempted"] for row in raw["requests"])


def test_recoverable_parser_crash_follows_receipt_and_retains_denominator(monkeypatch):
    saved = []
    def fail(*args):
        assert saved
        raise RuntimeError("invented parse failure")
    monkeypatch.setattr(module, "parse_response", fail)
    _, _, cells = module.capture(request_spec(), lambda url: response(b"{}"), lambda name, row: saved.append(name))
    assert len(saved) == len(cells) == 6
    assert all(row["status"] == "unavailable" for row in cells)


@pytest.mark.parametrize("value", [True, 0, -1])
def test_server_clock_requires_positive_integer(value):
    with pytest.raises(ValueError):
        module.parse_response(json.dumps({"serverTime": value}).encode(), {"kind": "server-time"})


@pytest.mark.parametrize("failure", ["crossed", "zero_size", "duplicate_identity"])
def test_complete_batch_still_requires_valid_quotes_and_unique_identities(failure):
    data = payload("book-ticker")
    if failure == "crossed":
        data[0]["bidPrice"] = "102"
    elif failure == "zero_size":
        data[0]["askQty"] = "0"
    else:
        data[1]["symbol"] = data[0]["symbol"]
    with pytest.raises(ValueError):
        module.parse_response(json.dumps(data).encode(), {"kind": "book-ticker"})


def test_incomplete_success_response_keeps_prefix_and_other_cells():
    frozen = request_spec()
    calls = []
    def fake(url):
        request = frozen["requests"][len(calls)]
        calls.append(url)
        if len(calls) == 1:
            return response(b'{"symbols":', complete=False, error="incomplete HTTP body")
        return response(json.dumps(payload(request["kind"])).encode())
    raw, _, cells = module.capture(frozen, fake)
    assert len(calls) == len(cells) == 6
    assert sum(row["status"] == "unavailable" for row in cells) == 1
    assert base64.b64decode(raw["requests"][0]["body_base64"]) == b'{"symbols":'


def test_mutated_request_spec_cannot_call_transport():
    frozen = request_spec()
    frozen["requests"][0]["url"] += "&extra=1"
    with pytest.raises(ValueError, match="frozen definition"):
        module.capture(frozen, lambda url: pytest.fail("mutated request executed"))


DRIVER = r'''
import hashlib,json,os,subprocess
from pathlib import Path
import triangle_capture as collector
from tradingagents.research import ResearchRun,runtime_hashes
root=Path(__file__).resolve().parent
assert len(os.sched_getaffinity(0))<=2
spec=json.loads((root/'triangle-request-spec.json').read_text())
def git(*args):return subprocess.check_output(['git','-c','core.hooksPath=/dev/null',*args],cwd=root,text=True).strip()
def sha(name):return hashlib.sha256((root/name).read_bytes()).hexdigest()
git('init','-q')
(root/'charter.md').write_text('Synthetic source-only pipeline, no financial observations.')
ids=[r['id'] for r in spec['requests']]
outputs=[name+'-receipt.json' for name in ids]+['triangle-capture.json','triangle-admission.json']
registration={'schema_version':1,'program_id':'synthetic-triangle','families':{'s':{'mechanism_id':'synthetic-triangle-source','attempt_budget':1,'prior_attempts':0,'history_reference':'invented'}},'datasets':{'s':{'identity':'invented-triangle','history_reference':'invented','exposures':[{'start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','state':'spent'}]}},'experiments':{'synthetic-triangle':{'family':'s','parent':None,'charter':{'path':'charter.md','sha256':sha('charter.md')},'question':'Synthetic resource admission','stage':'development','reuse':'exploratory','windows':[{'dataset':'s','start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','availability':'existing'}],'inputs':{'request_spec':{'path':'triangle-request-spec.json','sha256':sha('triangle-request-spec.json'),'dataset':'s'}},'source_files':{n:sha(n) for n in ('driver.py','triangle_capture.py','options_metadata.py','carry_capture.py')},'runtime_hashes':runtime_hashes(),'selection':None,'cells':ids,'outputs':outputs}}}
(root/'registration.json').write_text(json.dumps(registration))
git('add','driver.py','triangle_capture.py','options_metadata.py','carry_capture.py','triangle-request-spec.json','charter.md','registration.json')
git('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','synthetic')
source=git('rev-parse','HEAD')
calls=[]
def fake(url):
    kind=spec['requests'][len(calls)]['kind'];calls.append(url)
    if kind=='exchange-info':data={'symbols':[{'symbol':s,'baseAsset':p[0],'quoteAsset':p[1],'status':'TRADING','isSpotTradingAllowed':True,'filters':[]} for s,p in collector.PAIRS.items()]}
    elif kind=='server-time':data={'serverTime':1800000000000}
    elif kind=='book-ticker':data=[{'symbol':s,'bidPrice':'100','askPrice':'101','bidQty':'2','askQty':'3'} for s in collector.PAIRS]
    else:data={'lastUpdateId':0,'bids':[['100','2']],'asks':[['101','3']]}
    raw=json.dumps(data).encode();raw+=b' '*(spec['max_response_bytes']-len(raw))
    return {'body':raw,'http_status':200,'body_complete':True,'error':None,'headers':{}}
with ResearchRun.start(root=root,registration='registration.json',experiment='synthetic-triangle',source=source) as run:
    raw,admission,cells=collector.capture(json.loads(run.read_input('request_spec')),fake,run.write_json)
    run.write_json('triangle-capture.json',raw);run.write_json('triangle-admission.json',admission);run.finish(cells)
directory=root/'research_runs/synthetic-triangle/outputs'
actual=sum((directory/n).stat().st_size for n in outputs)
assert len(calls)==len(cells)==6 and all(c['status']=='complete' for c in cells)
assert raw['total_body_bytes']==30*1024**2 and actual<=100*1024**2
(root/'synthetic-result.json').write_text(json.dumps({'output_bytes':actual,'raw_bytes':raw['total_body_bytes'],'cpu_count':len(os.sched_getaffinity(0)),'cells':len(cells)}))
'''


def test_full_synthetic_lifecycle_with_gits_under_default_resource_guard(tmp_path):
    guard_spec = importlib.util.spec_from_file_location("triangle_test_guard", DIRECTORY / "resource_guard_v2.py")
    guard = importlib.util.module_from_spec(guard_spec)
    guard_spec.loader.exec_module(guard)
    for name in ("triangle_capture.py", "options_metadata.py", "carry_capture.py", "triangle-request-spec.json"):
        shutil.copyfile(DIRECTORY / name, tmp_path / name)
    (tmp_path / "driver.py").write_text(DRIVER)
    result = guard.run_guard([sys.executable, "-B", str(tmp_path / "driver.py")])
    (tmp_path / "guard-report.json").write_text(json.dumps(result))
    assert result["child_exit_code"] == 0 and result["limit_reason"] is None, result
    saved = json.loads((tmp_path / "synthetic-result.json").read_text())
    assert saved["raw_bytes"] == 30 * 1024**2 and saved["output_bytes"] <= 100 * 1024**2
    assert saved["cells"] == 6 and saved["cpu_count"] <= 2
    assert result["rss_limit_bytes"] == 512 * 1024**2 and result["wall_limit_seconds"] == 120


def test_invalid_standalone_ticker_json_cannot_inject_wrapper_field():
    spec=request_spec()
    def transport(url):
        request=next(r for r in spec['requests'] if r['url']==url)
        raw=json.dumps(payload(request['kind'])).encode()
        if request['kind']=='book-ticker':raw+=b',"injected":true'
        return response(raw)
    _,admission,cells=module.capture(spec,transport=transport)
    assert len(cells)==6
    bad=next(row for row in cells if row['id']=='triangle-book-ticker')
    assert bad['status']=='unavailable'
    assert sum(row['status']=='complete' for row in cells)==5
