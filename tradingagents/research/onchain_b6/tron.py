# tradingagents/research/onchain_b6/tron.py
"""Tron USDT exchange flows (spec §7) from the SQD portal: server-side topic filters on the
labelled exchange addresses, hourly aggregation on the fly, resumable by block."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

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
        if self.i >= len(self.waits):
            raise SystemExit('tron stream: back-off exhausted')
        self.sleep(self.waits[self.i])
        self.i += 1

    def reset(self):
        self.i = 0


def _body(cfg, frm, to, key, tops):
    t = cfg['tron']
    return {'type': 'tron', 'fromBlock': frm, 'toBlock': to,
            'logs': [{'address': [t['usdt']], 'topic0': [t['topic0']], key: tops}],
            'fields': {'block': {'number': True, 'timestamp': True}, 'log': {'topics': True, 'data': True}}}


def run(post, labels_hex, state_path, out_path, cfg, sleep=time.sleep, stop_block=None):
    t = cfg['tron']
    tops = ['0' * 24 + h for h in labels_hex]
    label_set = set(labels_hex)
    end_ms = int(pd.Timestamp(t['end'], tz='UTC').timestamp() * 1000)
    state_path, out_path = Path(state_path), Path(out_path)
    state = json.loads(state_path.read_text()) if state_path.exists() else {'next_block': t['start_block']}
    rows = pd.read_parquet(out_path).to_dict('index') if out_path.exists() else {}
    rows = {pd.Timestamp(k): v for k, v in rows.items()}
    back = Backoff(t['backoff'], sleep)
    nxt = state['next_block']
    done = False
    while not done:
        frm, to = nxt, nxt + t['chunk_blocks'] - 1
        if stop_block is not None:
            to = min(to, stop_block)
        for key in ('topic2', 'topic1'):
            cur = frm
            while cur <= to:
                try:
                    blocks = parse_lines(post(_body(cfg, cur, to, key, tops)))
                except Overloaded:
                    back.wait()
                    continue
                back.reset()
                if not blocks:
                    cur = to + 1
                    break
                for hour, agg in aggregate(blocks, label_set, t['big_usd']).items():
                    r = rows.setdefault(hour, {c: 0.0 for c in COLS})
                    if key == 'topic2':
                        for c in ('tron_in_val', 'tron_in_cnt', 'tron_big_in'):
                            r[c] += agg[c]
                    else:
                        for c in ('tron_out_val', 'tron_out_cnt'):
                            r[c] += agg[c]
                last = blocks[-1]['header']
                if int(last['timestamp']) >= end_ms:
                    done = True
                cur = int(last['number']) + 1
        nxt = to + 1
        if stop_block is not None and nxt > stop_block:
            done = True
        df = pd.DataFrame.from_dict(rows, orient='index').sort_index()[COLS] if rows else pd.DataFrame(columns=COLS)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = out_path.with_name('.' + out_path.name + '.tmp')
        df.to_parquet(tmp)
        os.replace(tmp, out_path)
        state_path.write_text(json.dumps({'next_block': nxt}))
