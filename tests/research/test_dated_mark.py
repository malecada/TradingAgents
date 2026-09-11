"""Invented daily mark sources only; no historical bodies or market requests."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import pytest
DIRECTORY = Path(__file__).resolve().parents[2] / 'research/strategy-search-2026-09-11'
sys.path.insert(0, str(DIRECTORY))
import dated_mark as source


def rows():
    return [[1777593600000 + i * 86400000, '10.5', '12', '9', '11', '0',
             1777593600000 + (i + 1) * 86400000 - 1, '0', 0, '0', '0', '0']
            for i in range(56)]


def response(data=None):
    return {'body': json.dumps(rows() if data is None else data).encode(),
            'http_status': 200, 'headers': {}, 'body_complete': True, 'error': None}


def run(transport):
    outputs = {}
    result = source.run(source.default_spec(), lambda name, value: outputs.__setitem__(name, value), transport)
    return result, outputs


def test_complete_source_ignores_zero_activity_fields():
    (capture, admitted, cells), outputs = run(lambda _: response())
    assert cells == [{'id': 'btc-dated-mark', 'status': 'complete'},
                     {'id': 'eth-dated-mark', 'status': 'complete'}]
    assert len(outputs) == 4 and admitted['planned_subslots'] == 112
    assert all(cell['complete_slots'] == 56 for cell in admitted['cells'])
    assert len(capture['receipts']) == 2 and admitted['graduation'] is False
    assert all('body_base64' not in ref for ref in capture['receipts'])


def test_all_raw_receipts_persist_before_any_admission(monkeypatch):
    stored = {}; calls = []; original = source.admit
    def admit(receipt):
        assert len(calls) == 2
        assert all(name + '-receipt.json' in stored for name in ('btc-dated-mark', 'eth-dated-mark'))
        return original(receipt)
    def transport(url):
        calls.append(url)
        return response()
    monkeypatch.setattr(source, 'admit', admit)
    source.run(source.default_spec(), lambda name, value: stored.__setitem__(name, value), transport)


def test_partial_extra_duplicate_and_reordered_days():
    values = rows()
    result = source.schema(json.dumps(values[:-1]).encode())
    assert result['status'] == 'unavailable' and result['complete_slots'] == 55
    assert result['slots'][-1]['reason'] == 'missing'
    result = source.schema(json.dumps(values + [values[-1]]).encode())
    assert result['status'] == 'unavailable' and result['complete_slots'] == 55
    assert result['slots'][-1]['reason'] == 'duplicate_timestamp'
    outside = copy.deepcopy(values[-1]); outside[0] += 86400000; outside[6] += 86400000
    result = source.schema(json.dumps(values + [outside]).encode())
    assert result['status'] == 'unavailable' and result['complete_slots'] == 56
    assert result['issues']['unexpected_timestamp'] == 1
    values[0], values[1] = values[1], values[0]
    result = source.schema(json.dumps(values).encode())
    assert result['status'] == 'unavailable' and result['complete_slots'] == 56
    assert result['issues']['nonascending_timestamp'] == 1


@pytest.mark.parametrize('position,value', [(0, True), (0, 1777593600001), (6, 1777679999998),
    (1, 'NaN'), (1, 'Infinity'), (1, '0'), (1, '-1'), (1, '1e33'),
    (1, '1' * 65), (1, 10), (2, '10'), (3, '11'), (4, '13')])
def test_invalid_daily_row_is_retained(position, value):
    values = rows(); values[0][position] = value
    admitted = source.schema(json.dumps(values).encode())
    assert admitted['status'] == 'unavailable' and len(admitted['slots']) == 56
    assert admitted['slots'][0]['status'] == 'unavailable'
    assert admitted['complete_slots'] == 55


@pytest.mark.parametrize('raw', [b'{}', b'{"a":1,"a":2}', b'[NaN]',
                               b'[' * 12000 + b'0' + b']' * 12000, b'\xff'])
def test_bad_payload_preserves_two_cells_and_all_slots(raw):
    def transport(_):
        value = response(); value['body'] = raw
        return value
    (_, admission, cells), outputs = run(transport)
    assert len(outputs) == 4 and len(cells) == 2
    assert all(cell['status'] == 'unavailable' for cell in cells)
    assert sum(len(cell['slots']) for cell in admission['cells']) == 112


def test_denial_stops_second_request_but_keeps_output():
    calls = []
    def denied(url):
        calls.append(url)
        return {'body': b'denied', 'http_status': 451, 'headers': {}, 'body_complete': True, 'error': 'HTTP451'}
    (_, admission, cells), outputs = run(denied)
    assert len(calls) == 1 and len(outputs) == 4
    assert outputs['btc-dated-mark-receipt.json']['attempted'] is True
    assert outputs['eth-dated-mark-receipt.json']['attempted'] is False
    assert all(cell['unavailable_slots'] == 56 for cell in admission['cells'])


def test_oversized_body_keeps_prefix_not_complete_source():
    body = b'x' * (256 * 1024 + 1)
    def oversized(_):
        return {'body': body, 'http_status': 200, 'headers': {}, 'body_complete': True, 'error': None}
    (_, admission, _), outputs = run(oversized)
    assert outputs['btc-dated-mark-receipt.json']['body_bytes'] == 256 * 1024
    assert outputs['btc-dated-mark-receipt.json']['body_complete'] is False
    assert all(cell['status'] == 'unavailable' for cell in admission['cells'])
    assert sum(len(source.encoded(value)) for value in outputs.values()) < 4 * 1024**2


@pytest.mark.parametrize('overflow', [False, True])
def test_transport_retains_actual_http_partial_prefix(monkeypatch, overflow):
    import io
    transport = source.dated_mark_transport
    body = b'x' * (transport.MAX_BYTES + 1) if overflow else b'[]'
    declared = len(body) if overflow else 100
    class Socket:
        def makefile(self, *args):
            return io.BytesIO(f'HTTP/1.1 200 OK\r\nContent-Length: {declared}\r\n\r\n'.encode() + body)
    http = transport.http.client.HTTPResponse(Socket()); http.begin()
    class Opener:
        def open(self, *args, **kwargs):
            return http
    monkeypatch.setattr(transport.urllib.request, 'build_opener', lambda *args: Opener())
    result = transport.public_get('https://fapi.binance.com/fapi/v1/markPriceKlines')
    assert result['body'] == body[:transport.MAX_BYTES] and result['body_complete'] is False
    assert ('256KiB' if overflow else 'Content-Length EOF') in result['error']


def test_request_scope_cannot_change():
    spec = source.default_spec(); spec['requests'][0]['parameters']['symbol'] = 'DIFFERENT'
    with pytest.raises(ValueError, match='specification differs'):
        source.run(spec, lambda *_: None, lambda _: pytest.fail('network'))


GUARDED_DRIVER = r'''
import hashlib,importlib.util,json,os,sys
from pathlib import Path
root=Path(__file__).resolve().parent
source_dir=root/'research/strategy-search-2026-09-11'
sys.path.insert(0,str(source_dir))
import dated_mark as runner
loader=importlib.util.spec_from_file_location('extension_fixture',root/'extension_fixture.py')
fixture=importlib.util.module_from_spec(loader);loader.loader.exec_module(fixture)
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
specfile=source_dir/'dated-mark-spec.json';specfile.write_bytes(runner.encoded(runner.default_spec()))
sourcefiles=[source_dir/'dated_mark.py',source_dir/'dated_mark_transport.py',root/'resource_guard_v2.py',root/'driver.py',root/'extension_fixture.py']
updates={'inputs':{'request_spec':{'path':str(specfile.relative_to(root)),'sha256':sha(specfile),'dataset':'sample'}},
         'source_files':{str(path.relative_to(root)):sha(path) for path in sourcefiles},
         'cells':['btc-dated-mark','eth-dated-mark'],
         'outputs':['btc-dated-mark-receipt.json','eth-dated-mark-receipt.json','capture.json','admission.json']}
root,spec,certificate,source=fixture.build_extension(root,target_updates=updates)
(source_dir/'gates-dated-mark.json').write_bytes((root/'extension-registration.json').read_bytes())
source=fixture.commit(root)
mode=sys.argv[1];calls=[]
def fake(url):
    calls.append(url)
    if mode=='denial':return {'body':b'x'*(256*1024),'http_status':451,'headers':{},'body_complete':True,'error':'HTTP451'}
    rows=[[1777593600000+i*86400000,'10.5','12','9','11','x'*4000,1777593600000+(i+1)*86400000-1,0,0,0,0,0]for i in range(56)]
    if mode=='malformed':rows=[0]*100000
    body=json.dumps(rows,separators=(',',':')).encode()
    assert len(body)<=256*1024
    return {'body':body+b' '*(256*1024-len(body)),'http_status':200,'headers':{},'body_complete':True,'error':None}
runner.dated_mark_transport.public_get=fake
sys.argv=['dated_mark.py','--source',source]
runner.main()
folder=root/'research_runs/dated-mark-20260911'
verified=fixture.verify_run(folder)
output=folder/'outputs';admitted=json.loads((output/'admission.json').read_text())
assert len(list(output.iterdir()))==4 and verified['cell_count']==2
assert sum(len(cell['slots'])for cell in admitted['cells'])==112
assert all(cell['status']==('complete' if mode=='full' else 'unavailable')for cell in admitted['cells'])
assert len(calls)==(1 if mode=='denial' else 2)
actual=sum(path.stat().st_size for path in output.iterdir())
assert actual<=4*1024**2 and len(os.sched_getaffinity(0))<=2
(root/'synthetic-result.json').write_text(json.dumps({'mode':mode,'verified':verified,'top_cells':2,'subslots':112,
 'output_count':4,'output_bytes':actual,'requests':len(calls),'cpu_count':len(os.sched_getaffinity(0)),
 'source_sha256':{str(path.relative_to(root)):sha(path)for path in sourcefiles},'runtime_hashes':fixture.runtime_hashes()}))
'''


@pytest.mark.parametrize('mode', ['full', 'denial', 'malformed'])
def test_actual_guarded_dated_mark_lifecycle(tmp_path, mode):
    import shutil
    import subprocess
    nested = tmp_path / 'research/strategy-search-2026-09-11'; nested.mkdir(parents=True)
    for name in ('dated_mark.py', 'dated_mark_transport.py'):
        shutil.copyfile(DIRECTORY / name, nested / name)
    shutil.copyfile(DIRECTORY / 'resource_guard_v2.py', tmp_path / 'resource_guard_v2.py')
    shutil.copyfile(Path(__file__).with_name('test_extended_lifecycle.py'), tmp_path / 'extension_fixture.py')
    (tmp_path / 'driver.py').write_text(GUARDED_DRIVER)
    result = subprocess.run([sys.executable, '-B', str(tmp_path / 'resource_guard_v2.py'),
                             '--report', str(tmp_path / 'guard-report.json'), '--',
                             sys.executable, '-B', str(tmp_path / 'driver.py'), mode],
                            capture_output=True, text=True, timeout=150)
    (tmp_path / 'guard-stdout.txt').write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((tmp_path / 'guard-report.json').read_text())
    assert report['limit_reason'] is None and report['wall_limit_seconds'] == 120
    assert report['rss_limit_bytes'] == 512 * 1024**2
