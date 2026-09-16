"""Synthetic-only source audit checks. No network or financial inputs."""
import importlib.util
import io
from pathlib import Path
import struct
import subprocess
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('onchain_source_probe', ROOT / 'research/onchain-graph-2026-09-16/source_probe.py')
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def config():
    import json
    return json.loads((ROOT / 'research/onchain-graph-2026-09-16/request-spec.json').read_text())


def xml(prefix, *, truncated='false', key=None):
    key = key or prefix + 'part-0.parquet'
    return (f'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
            f'<Prefix>{prefix}</Prefix><IsTruncated>{truncated}</IsTruncated>'
            f'<Contents><Key>{key}</Key><Size>100</Size><ETag>"abc"</ETag></Contents>'
            '</ListBucketResult>').encode()


def test_listing_preserves_truncation_and_binds_prefix():
    p = 'v1.0/eth/blocks/date=2024-01-01/'
    assert probe.listing(xml(p, truncated='true'), p)['truncated']
    with pytest.raises(ValueError, match='prefix'):
        probe.listing(xml(p), 'another/')
    with pytest.raises(ValueError, match='identity'):
        probe.listing(xml(p, key='another/x.parquet'), p)
    with pytest.raises(ValueError, match='truncation'):
        probe.listing(xml(p, truncated='maybe'), p)


def test_footer_reads_real_parquet_metadata_without_rows():
    sink = io.BytesIO()
    pq.write_table(pa.table({'value': [1.5, 2.5], 'receipt_status': [1, 0]}), sink)
    body = sink.getvalue()
    tail = body[-8:]
    length = struct.unpack('<I', tail[:4])[0]
    result = probe.footer_metadata(tail, body[-length-8:], len(body))
    assert result['rows'] == 2
    assert result['schema']['value'] == 'double'
    with pytest.raises(ValueError, match='match'):
        probe.footer_metadata(tail, body[-length-9:], len(body))


def test_range_requires_206_etag_total_and_length():
    obj = {'size': 100, 'etag': '"abc"'}
    valid = {'status': 206, 'response_headers': {'content-range': 'bytes 92-99/100', 'etag': '"abc"'}}
    probe.validate_range(valid, b'x' * 8, 92, 99, obj)
    for altered in ({**valid, 'status': 200},
                    {**valid, 'response_headers': {**valid['response_headers'], 'etag': 'other'}},
                    {**valid, 'response_headers': {**valid['response_headers'], 'content-range': 'bytes 92-99/101'}}):
        with pytest.raises(ValueError):
            probe.validate_range(altered, b'x' * 8, 92, 99, obj)


class Response(io.BytesIO):
    def __init__(self, body, status=200, headers=None):
        super().__init__(body)
        self.status = status
        self.headers = headers or {'Content-Length': str(len(body))}


def test_denial_retains_body_and_prevents_more_calls():
    records = {}
    cap = probe.Capture(config(), records.__setitem__)
    with patch.object(cap.opener, 'open', return_value=Response(b'denied', 403)) as call:
        assert cap.get(config()['base_url'])[0] is None
        assert cap.get(config()['base_url'])[0] is None
        assert call.call_count == 1
    assert records['request-01.json']['bytes'] == 6
    assert records['request-01.json']['sha256'] == probe.sha(b'denied')


def test_oversize_partial_body_is_retained_and_rejected():
    spec = {**config(), 'max_response_bytes': 3}
    records = {}
    cap = probe.Capture(spec, records.__setitem__)
    with patch.object(cap.opener, 'open', return_value=Response(b'123456')):
        body, receipt = cap.get(spec['base_url'])
    assert body is None and receipt['bytes'] == 4
    assert 'byte limit' in receipt['error']


def test_all_cells_and_outputs_remain_after_denial():
    records = {}
    with patch.object(probe.urllib.request.OpenerDirector, 'open', return_value=Response(b'no', 403)) as call:
        cells = probe.execute(config(), records.__setitem__)
    assert call.call_count == 1
    assert len(cells) == 8
    assert all(c['status'] == 'unavailable' and c['reason'] for c in cells)
    assert len(records) == 25
    assert not records['source-audit.json']['financial_evaluation_admitted']


def test_off_host_request_is_rejected_before_network():
    cap = probe.Capture(config(), lambda *args: None)
    with patch.object(cap.opener, 'open') as call, pytest.raises(ValueError):
        cap.get('https://example.org/')
    call.assert_not_called()


def test_redirect_handler_does_not_follow():
    assert probe.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.org/') is None


def test_intent_exists_before_io_and_no_ambient_proxy():
    records = {}
    with patch.dict('os.environ', {'https_proxy': 'http://secret:secret@proxy.invalid:443'}):
        cap = probe.Capture(config(), records.__setitem__)
    assert not any(isinstance(h, probe.urllib.request.ProxyHandler) and h.proxies for h in cap.opener.handlers)
    def network(*args, **kwargs):
        assert records['request-01-intent.json']['status'] == 'intent'
        raise TimeoutError('synthetic timeout')
    with patch.object(cap.opener, 'open', side_effect=network):
        cap.get(config()['base_url'])
    assert 'TimeoutError' in records['request-01.json']['error']


def launcher():
    spec = importlib.util.spec_from_file_location('onchain_source_launcher',
        ROOT / 'research/onchain-graph-2026-09-16/launch_source.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resource_monitor_does_not_kill_for_elapsed_time():
    from types import SimpleNamespace
    from unittest.mock import Mock
    launch = launcher()
    child = Mock(pid=123, poll=Mock(side_effect=[None, None, 0]), wait=Mock(return_value=0))
    guard = SimpleNamespace(_limits=lambda: None, tree_rss=lambda pid: 1000)
    with patch.object(launch.subprocess, 'Popen', return_value=child), \
         patch.object(launch.time, 'sleep'), \
         patch.object(launch.time, 'monotonic', side_effect=[0, 1000000]), \
         patch.object(launch.os, 'killpg') as kill:
        result = launch.run_without_elapsed_kill(['synthetic'], guard, ROOT)
    kill.assert_not_called()
    assert result['elapsed_seconds'] == 1000000
    assert result['elapsed_time_kill'] is False and result['limit_reason'] is None


@pytest.mark.parametrize('error', [OSError('launch failed'), subprocess.SubprocessError('preexec failed')])
def test_resource_setup_failure_is_retained(error):
    from types import SimpleNamespace
    launch = launcher()
    with patch.object(launch.subprocess, 'Popen', side_effect=error):
        result = launch.run_without_elapsed_kill(['synthetic'], SimpleNamespace(_limits=lambda: None), ROOT)
    assert result['child_exit_code'] is None and result['peak_sampled_tree_rss_bytes'] is None
    assert result['retry'] is False and result['elapsed_time_kill'] is False
    assert 'launch/setup failed' in result['limit_reason']


@pytest.mark.parametrize('monitor, reason', [
    (lambda pid: 2 * 1024**3 + 1, 'RSS limit'),
    (lambda pid: (_ for _ in ()).throw(RuntimeError('unreadable')), 'monitor failed'),
])
def test_resource_monitor_stops_for_memory_or_unknown_usage(monitor, reason):
    from types import SimpleNamespace
    from unittest.mock import Mock
    launch = launcher()
    child = Mock(pid=123, poll=Mock(return_value=None), wait=Mock(return_value=-15))
    guard = SimpleNamespace(_limits=lambda: None, tree_rss=monitor)
    with patch.object(launch.subprocess, 'Popen', return_value=child), \
         patch.object(launch.os, 'killpg') as kill:
        result = launch.run_without_elapsed_kill(['synthetic'], guard, ROOT)
    kill.assert_called_once_with(123, launch.signal.SIGTERM)
    assert reason in result['limit_reason'] and result['child_exit_code'] == -15
