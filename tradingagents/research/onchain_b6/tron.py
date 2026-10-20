# tradingagents/research/onchain_b6/tron.py
"""Tron USDT exchange flows (spec §7) from the SQD portal: server-side topic filters on the
labelled exchange addresses, hourly aggregation on the fly, resumable by block."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
COLS = ['tron_in_val', 'tron_out_val', 'tron_in_cnt', 'tron_out_cnt', 'tron_big_in']


class Overloaded(RuntimeError):
    def __init__(self, status):
        super().__init__(f'HTTP {status}')
        self.status = status


def b58_to_hex(addr):
    n = 0
    for ch in addr:
        n = n * 58 + ALPHABET.index(ch)
    return n.to_bytes(25, 'big')[1:21].hex()


def topics(addrs):
    return ['0' * 24 + b58_to_hex(a) for a in addrs]


def parse_lines(raw):
    return [json.loads(x) for x in raw.splitlines() if x.strip()]


def aggregate(blocks, label_set, big_usd):
    out = {}
    for b in blocks:
        hour = pd.Timestamp(int(b['header']['timestamp']), unit='ms').floor('h')
        row = out.setdefault(hour, {c: 0.0 for c in COLS})
        for lg in b.get('logs', []):
            t = lg['topics']
            if len(t) < 3:
                continue
            frm, to = t[1][-40:], t[2][-40:]
            usd = int(lg['data'], 16) / 1e6 if lg.get('data') else 0.0
            fi, ti = frm in label_set, to in label_set
            if ti and not fi:
                row['tron_in_val'] += usd
                row['tron_in_cnt'] += 1
                row['tron_big_in'] += usd >= big_usd
            elif fi and not ti:
                row['tron_out_val'] += usd
                row['tron_out_cnt'] += 1
    return out


class Backoff:
    def __init__(self, waits, sleep):
        self.waits, self.sleep, self.i = list(waits), sleep, 0

    def wait(self):
        # a persistently throttled portal is waited out at the longest interval, never abandoned
        self.sleep(self.waits[min(self.i, len(self.waits) - 1)])
        self.i += 1

    def reset(self):
        self.i = 0


def _body(cfg, frm, to, tops):
    """One request per range: transfers to (topic2) or from (topic1) a labelled address."""
    t = cfg['tron']
    base = {'address': [t['usdt']], 'topic0': [t['topic0']]}
    return {'type': 'tron', 'fromBlock': frm, 'toBlock': to,
            'logs': [{**base, 'topic2': tops}, {**base, 'topic1': tops}],
            'fields': {'block': {'number': True, 'timestamp': True}, 'log': {'topics': True, 'data': True}}}


def load_bundle(path):
    z = np.load(path)
    hours = pd.to_datetime(z['hours'])
    rows = {h: {c: float(v) for c, v in zip(COLS, vals)} for h, vals in zip(hours, z['values'])}
    return rows, int(z['next_block'])


def save_bundle(path, rows, next_block, out_path):
    """The npz bundle (hours, values, next_block) is the truth and is replaced atomically; the
    parquet is a derived view written afterwards."""
    hours = sorted(rows)
    values = np.array([[rows[h][c] for c in COLS] for h in hours], float).reshape(len(hours), len(COLS))
    tmp = path.with_name('.' + path.name + '.tmp.npz')
    np.savez(tmp, hours=np.array(hours, dtype='datetime64[ns]'), values=values, next_block=np.array(next_block))
    os.replace(tmp, path)
    df = pd.DataFrame(values, index=pd.DatetimeIndex(hours), columns=COLS)
    tmp2 = out_path.with_name('.' + out_path.name + '.tmp')
    df.to_parquet(tmp2)
    os.replace(tmp2, out_path)


def run(post, labels_hex, bundle_path, out_path, cfg, sleep=time.sleep, stop_block=None, log=None):
    t = cfg['tron']
    tops = ['0' * 24 + h for h in labels_hex]
    label_set = set(labels_hex)
    end_ms = int(pd.Timestamp(t['end'], tz='UTC').timestamp() * 1000)
    bundle_path, out_path = Path(bundle_path), Path(out_path)
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    rows, nxt = load_bundle(bundle_path) if bundle_path.exists() else ({}, t['start_block'])
    back = Backoff(t['backoff'], sleep)
    empties = 0
    done = False
    while not done:
        frm, to = nxt, nxt + t['chunk_blocks'] - 1
        if stop_block is not None:
            to = min(to, stop_block)
        cur = frm
        while cur <= to:
            if t.get('pause', 0) > 0:
                sleep(t['pause'])                                  # the keyless portal throttles bursts
            t0 = time.time()
            try:
                blocks = parse_lines(post(_body(cfg, cur, to, tops)))
            except Overloaded as e:
                if log:
                    log(event='overloaded', status=e.status, block=cur, wait=back.waits[min(back.i, len(back.waits) - 1)])
                back.wait()
                continue
            back.reset()
            if log:
                log(event='request', frm=cur, to=to, blocks=len(blocks), seconds=round(time.time() - t0, 1))
            if not blocks:
                empties += 1
                if empties >= 3:
                    raise SystemExit(f'tron stream: no blocks returned three times from block {cur}; head reached or portal empty')
                cur = to + 1
                break
            empties = 0
            for hour, agg in aggregate(blocks, label_set, t['big_usd']).items():
                r = rows.setdefault(hour, {c: 0.0 for c in COLS})
                for c in COLS:
                    r[c] += agg[c]
            last = blocks[-1]['header']
            if int(last['timestamp']) >= end_ms:
                done = True
            cur = int(last['number']) + 1
        nxt = to + 1
        if stop_block is not None and nxt > stop_block:
            done = True
        save_bundle(bundle_path, rows, nxt, out_path)
