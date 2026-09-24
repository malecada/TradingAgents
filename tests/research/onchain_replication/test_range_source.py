import json

import pytest

from tests.research.test_lifecycle import registered, start, commit
from tests.research.onchain_replication.test_parquet_ranges import fixture
from tradingagents.research.onchain_replication.provenance import file_hash
from tradingagents.research.onchain_replication.parquet_ranges import decode_projected_btc
from tradingagents.research.onchain_replication.range_source import capture_ranges, range_policy


def prepare(registered, raw, *, limits=None):
    root, spec, _ = registered
    item = {'key': 'v1.0/btc/transactions/date=2016-01-01/part.parquet',
            'date': '2016-01-01', 'bytes': len(raw), 'etag': '"synthetic-etag"'}
    catalogue = {'asset': 'BTC', 'year': 2016, 'listing_complete': True,
                 'dates': {'2016-01-01': {'objects': [item]},
                           '2016-01-02': {'objects': []}}}
    policy = range_policy('BTC', ['2016-01-01', '2016-01-02'],
                          {'2016': 'catalogue_2016'}, maximum_span_bytes=1024,
                          max_requests=500, max_received_bytes=10*1024**2,
                          max_blob_bytes=10*1024**2)
    if limits:
        policy.update(limits)
    for name, value in [('range_policy', policy), ('catalogue_2016', catalogue)]:
        path = root / (name + '.json')
        path.write_text(json.dumps(value))
        spec['experiments']['example-a']['inputs'][name] = {
            'path': path.name, 'sha256': file_hash(path), 'dataset': 'sample'}
    spec['experiments']['example-a']['cells'] = ['BTC-2016-01-01', 'BTC-2016-01-02']
    return (root, spec, commit(root, spec)), policy, item


def response(raw, calls, *, fault=None):
    def transport(url, headers, limit):
        calls.append((url, headers.copy(), limit))
        a, b = map(int, headers['Range'][6:].split('-'))
        body = raw[a:b+1]
        reply = {'Content-Range': f'bytes {a}-{b}/{len(raw)}',
                 'ETag': '"synthetic-etag"', 'Content-Length': str(len(body))}
        if fault == 'etag':
            reply['ETag'] = '"changed"'
        if fault == 'range':
            reply['Content-Range'] = f'bytes 0-{b}/{len(raw)}'
        if fault == 'oversize':
            body += b'x'
        return (403 if fault == 'denied' else 206), reply, body
    return transport


def test_registered_selected_capture_decodes_and_preserves_missing_date(registered, tmp_path):
    raw, _, _ = fixture(tmp_path)
    setup, policy, item = prepare(registered, raw)
    calls = []
    with start(setup) as run:
        rows, summary, directory = capture_ranges(run, transport=response(raw, calls))
        assert [r['status'] for r in rows] == ['complete', 'unavailable']
        assert summary['complete_dates'] == 1
        assert not summary['transaction_data_admitted']
        day = json.loads((directory / 'BTC-2016-01-01.json').read_bytes())
        member = day['members'][0]
        decoded = list(decode_projected_btc(member, scratch=tmp_path,
                       precision_policy='binary64_satoshi_grid_inverse_v1'))
        assert len(decoded) == 2
        assert summary['received_bytes'] == sum(x[2] for x in calls)
        assert all(x[1]['If-Match'] == item['etag'] for x in calls)
        projected = json.loads(open(member['path']).read())
        assert projected['column_plan']['selected_bytes'] < len(raw)
        prior = len(calls)
        with pytest.raises(FileExistsError):
            capture_ranges(run, transport=response(raw, calls))
        assert len(calls) == prior


@pytest.mark.parametrize('fault', ['etag', 'range', 'oversize', 'denied'])
def test_failed_response_is_retained_and_never_retried(registered, tmp_path, fault):
    raw, _, _ = fixture(tmp_path)
    setup, _, _ = prepare(registered, raw)
    calls = []
    with start(setup) as run:
        rows, summary, directory = capture_ranges(run, transport=response(raw, calls, fault=fault))
        assert len(calls) == 1
        assert all(r['status'] == 'unavailable' for r in rows)
        assert summary['requests'] == 1 and summary['received_bytes'] == 8 + (fault == 'oversize')
        assert len(list(directory.glob('objects/*/*-response.json'))) == 1
        assert len(list(directory.glob('objects/*/*.zst'))) == 1
        assert rows[0]['reason']


def test_request_budget_does_not_shrink_date_denominator(registered, tmp_path):
    raw, _, _ = fixture(tmp_path)
    setup, _, _ = prepare(registered, raw, limits={'max_requests': 1})
    calls = []
    with start(setup) as run:
        rows, summary, _ = capture_ranges(run, transport=response(raw, calls))
        assert len(rows) == 2 and len(calls) == 1
        assert all(r['status'] == 'unavailable' for r in rows)
        assert 'budget' in rows[0]['reason']


def test_bad_registered_cell_membership_refuses_before_network(registered, tmp_path):
    raw, _, _ = fixture(tmp_path)
    setup, _, _ = prepare(registered, raw)
    root, spec, _ = setup
    spec['experiments']['example-a']['cells'] = ['BTC-2016-01-01']
    setup = root, spec, commit(root, spec)
    with start(setup) as run, pytest.raises(ValueError, match='denominator'):
        capture_ranges(run, transport=lambda *args: pytest.fail('unadmitted request'))


@pytest.mark.parametrize('partial', [b'12345678', None])
def test_transport_failure_retains_prefix_and_conservatively_spends_budget(registered, tmp_path, partial):
    from http.client import IncompleteRead
    import zstandard
    raw, _, _ = fixture(tmp_path)
    setup, _, item = prepare(registered, raw, limits={'max_received_bytes': 9})
    root, spec, _ = setup
    path = root/'catalogue_2016.json'
    catalogue = json.loads(path.read_bytes())
    catalogue['dates']['2016-01-01']['objects'].append({**item, 'key': item['key'].replace('part.', 'second.')})
    path.write_text(json.dumps(catalogue))
    spec['experiments']['example-a']['inputs']['catalogue_2016']['sha256'] = file_hash(path)
    setup = root, spec, commit(root, spec)
    calls = []
    def transport(*args):
        calls.append(args)
        if partial is None:
            raise TimeoutError('unknown transfer prefix')
        raise IncompleteRead(partial, 1)
    with start(setup) as run:
        rows, summary, directory = capture_ranges(run, transport=transport)
        assert len(calls) == 1 and summary['charged_bytes'] == 9
        assert summary['received_bytes'] == len(partial or b'')
        assert summary['requests_with_unknown_received_bytes'] == 1
        retained = list(directory.glob('objects/*/*-partial.zst'))
        assert len(retained) == 1
        assert zstandard.ZstdDecompressor().decompress(retained[0].read_bytes()) == (partial or b'')
        assert all(x['status'] == 'unavailable' for x in rows)


def test_capture_parent_is_durable_before_first_request(registered, tmp_path, monkeypatch):
    import tradingagents.research.onchain_replication.range_source as module
    raw, _, _ = fixture(tmp_path)
    setup, _, _ = prepare(registered, raw)
    synced = []
    actual = module.sync_directory
    def sync(path):
        synced.append(path.resolve())
        actual(path)
    monkeypatch.setattr(module, 'sync_directory', sync)
    with start(setup) as run:
        directory = run.admission.root/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/run.admission.experiment_id
        def transport(*args):
            assert directory.resolve() in synced
            return 403, {}, b''
        capture_ranges(run, transport=transport)
