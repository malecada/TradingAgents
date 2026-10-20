# tests/research/onchain_b6/test_tron.py
import json

import pandas as pd
import pytest

from tradingagents.research.onchain_b6 import config, tron

CFG = config.load()
L = ['TXFBqBbqJommqZf7BV8NNYzePh97UmJodJ']            # a Tron base58 address


def test_b58_to_hex_and_topics():
    h = tron.b58_to_hex(L[0])
    assert len(h) == 40 and tron.topics(L)[0] == '0' * 24 + h


def _block(num, ts, logs):
    return json.dumps({'header': {'number': num, 'timestamp': ts}, 'logs': logs}).encode()


def _log(frm, to, usd):
    pad = lambda h: '0' * 24 + h
    return {'topics': ['dd', pad(frm), pad(to)], 'data': hex(int(usd * 1e6))[2:].rjust(64, '0')}


def test_aggregate_in_out_and_big():
    lab = tron.b58_to_hex(L[0])
    other, third = 'a' * 40, 'b' * 40
    ts = int(pd.Timestamp('2023-06-01 10:30', tz='UTC').timestamp() * 1000)
    blocks = [{'header': {'number': 1, 'timestamp': ts}, 'logs': [_log(other, lab, 2e6), _log(lab, third, 5.0), _log(lab, lab, 9e6)]}]
    agg = tron.aggregate(blocks, {lab}, 1e6)
    row = agg[pd.Timestamp('2023-06-01 10:00')]
    assert row == {'tron_in_val': 2e6, 'tron_out_val': 5.0, 'tron_in_cnt': 1, 'tron_out_cnt': 1, 'tron_big_in': 1}


def test_stream_continues_partial_and_backs_off(tmp_path):
    lab = tron.b58_to_hex(L[0])
    calls, slept = [], []
    t0 = int(pd.Timestamp('2020-05-23', tz='UTC').timestamp() * 1000)

    def post(body):
        calls.append(body)
        if len(calls) == 2:
            raise tron.Overloaded(529)
        frm, to = body['fromBlock'], body['toBlock']
        last = min(to, frm + 1)                                     # the server returns only two blocks per call
        lines = [_block(n, t0 + (n - 20000000) * 3000, [_log('a' * 40, lab, 1.0)] if 'topic2' in body['logs'][0] else []) for n in range(frm, last + 1)]
        return b'\n'.join(lines)
    cfg = json.loads(json.dumps(CFG))
    cfg['tron'].update({'start_block': 20000000, 'chunk_blocks': 4, 'backoff': [1, 2], 'pause': 0})
    tron.run(post, [lab], tmp_path / 'bundle.npz', tmp_path / 'hourly.parquet', cfg, sleep=slept.append, stop_block=20000007)
    out = pd.read_parquet(tmp_path / 'hourly.parquet')
    assert out['tron_in_cnt'].sum() == 8 and slept[0] == 1
    assert all(len(b['logs']) == 2 and 'topic2' in b['logs'][0] and 'topic1' in b['logs'][1] for b in calls)   # one combined request
    import numpy as np
    assert int(np.load(tmp_path / 'bundle.npz')['next_block']) == 20000008 and not (tmp_path / 'state.json').exists()


def test_bundle_is_single_file_and_empty_responses_stop(tmp_path):
    lab = tron.b58_to_hex(L[0])
    calls = []

    def post(body):
        calls.append(body)
        return b''                                                 # nothing returned at all
    cfg = json.loads(json.dumps(CFG))
    cfg['tron'].update({'start_block': 20000000, 'chunk_blocks': 4, 'backoff': [1], 'pause': 0})
    with pytest.raises(SystemExit, match='no blocks'):
        tron.run(post, [lab], tmp_path / 'bundle.npz', tmp_path / 'hourly.parquet', cfg, sleep=lambda s: None)
    assert len(calls) == 3


def test_backoff_keeps_waiting_at_the_last_value():
    slept = []
    b = tron.Backoff([1, 2], slept.append)
    for _ in range(5):
        b.wait()
    assert slept == [1, 2, 2, 2, 2]
