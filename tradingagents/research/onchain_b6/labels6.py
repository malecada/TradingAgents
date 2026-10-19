# tradingagents/research/onchain_b6/labels6.py
"""Label sets (spec §3): exchanges from B2 and eth-labels, classes from eth-labels and
Spellbook; frozen with source commits. LabelState applies day-after activation."""
from __future__ import annotations

import csv
import io
import json
import os
import re
from pathlib import Path

import numpy as np

from ..onchain_b2.labels import _commit
from ..onchain_b2.labels import load as load_b2
from ..onchain_b4.entities import member
from ..onchain_b4.reader import addr_keys

CLASSES = ['dex', 'bridge', 'mev', 'funds']
ADDR = re.compile(r'^0x[0-9a-f]{40}$')


def _stem(name):
    return (name or '').split(':')[0].split(' ')[0].strip().lower()


def canon(name):
    """Canonical entity: lower-case first token after '-', '.', '_' and ':' become spaces
    ('Binance 14', 'binance', 'Coinbase Prime', 'crypto.com', 'celsius-network' -> binance, coinbase, crypto, celsius)."""
    t = (name or '').lower()
    for ch in '-._:':
        t = t.replace(ch, ' ')
    return t.split()[0] if t.split() else ''


def parse_sql_addresses(text):
    return [(a.lower(), n) for a, n in re.findall(r"(0x[0-9a-fA-F]{40})\s*,\s*'([^']+)'", text)]


def classify(b2, eth_rows, spell_bridges, spell_funds, cfg):
    L = cfg['labels']
    stems = ({_stem(v.get('name')) for v in b2.values()} - {''}) | set(L['exchange_labels'])
    exchange = {a.lower(): canon(v.get('name')) or 'unknown' for a, v in b2.items()}
    cls = {c: set() for c in CLASSES}
    for r in eth_rows:
        if r.get('chainId', '1') != '1':
            continue
        a, lab, tag = r['address'].lower(), r.get('label', ''), (r.get('nameTag') or '')
        if not ADDR.match(a):
            continue
        tl = tag.lower()
        if lab in stems or lab.replace('-', ' ') in stems or lab.replace('-', '.') in stems:
            exchange.setdefault(a, canon(lab))
        elif lab == 'dex' or 'router' in tl:
            cls['dex'].add(a)
        elif lab == 'bridge' or 'bridge' in tl:
            cls['bridge'].add(a)
        elif lab in L['mev_labels']:
            cls['mev'].add(a)
        elif any(k in tl for k in L['fund_keywords']):
            cls['funds'].add(a)
    cls['bridge'] |= {a for a, _ in spell_bridges}
    cls['funds'] |= {a for a, _ in spell_funds}
    exchange.pop(cfg['issuer']['usdt_treasury'].lower(), None)        # the issuer is neither an exchange nor a class
    for c in CLASSES:
        cls[c] -= set(exchange) | {cfg['issuer']['usdt_treasury'].lower()}
    return {'exchange': dict(sorted(exchange.items())), **{c: sorted(cls[c]) for c in CLASSES},
            'issuer': {'usdt_treasury': cfg['issuer']['usdt_treasury']}}


def build(get, b2_path, cfg):
    L = cfg['labels']
    e, s = L['ethlabels'], L['spellbook']
    raw = get(f"https://raw.githubusercontent.com/{e['repo']}/{e['branch']}/{e['path']}").decode(errors='replace')
    rows = list(csv.DictReader(io.StringIO(raw)))
    sb = lambda p: get(f"https://raw.githubusercontent.com/{s['repo']}/{s['branch']}/{p}").decode()
    doc = classify(load_b2(b2_path), rows, parse_sql_addresses(sb(s['bridges'])), parse_sql_addresses(sb(s['funds'])), cfg)
    doc['sources'] = {'b2_labels': str(b2_path), 'ethlabels_commit': _commit(get, e['repo'], e['branch']),
                      'spellbook_commit': _commit(get, s['repo'], s['branch']),
                      'counts': {'exchange': len(doc['exchange']), **{c: len(doc[c]) for c in CLASSES}}}
    return doc


def save(doc, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=0, sort_keys=True))


def load(path):
    return json.loads(Path(path).read_text())


class LabelState:
    def __init__(self, doc, usdt_treasury):
        ex = doc['exchange']
        self.entity_names = sorted({v for v in ex.values()})
        addrs = np.array(sorted(ex), object)
        k = addr_keys(addrs) if len(addrs) else np.empty(0, np.uint64)
        order = np.argsort(k)
        self.ex_keys = k[order]
        self.ex_entity = np.array([self.entity_names.index(ex[a]) for a in addrs[order]], np.int32) if len(addrs) else np.empty(0, np.int32)
        self.ex_first = np.full(len(self.ex_keys), -1, np.int32)
        self.cls_keys, self.cls_first = {}, {}
        for c in CLASSES:
            kk = np.unique(addr_keys(np.array(doc[c], object))) if doc[c] else np.empty(0, np.uint64)
            self.cls_keys[c], self.cls_first[c] = kk, np.full(len(kk), -1, np.int32)
        self.treasury_key = int(addr_keys(np.array([usdt_treasury], object))[0])
        self.classes = CLASSES
        self._day = None

    def begin_day(self, day_ord):
        self._day = int(day_ord)
        self._ex_active = (self.ex_first >= 0) & (self.ex_first < self._day)
        self._cls_active = {c: (self.cls_first[c] >= 0) & (self.cls_first[c] < self._day) for c in CLASSES}

    def _lookup(self, sorted_keys, keys):
        keys = np.asarray(keys, np.uint64)
        if len(sorted_keys) == 0 or len(keys) == 0:
            return np.zeros(len(keys), bool), np.zeros(len(keys), np.int64)
        pos = np.searchsorted(sorted_keys, keys)
        pos[pos == len(sorted_keys)] = 0
        return sorted_keys[pos] == keys, pos

    @staticmethod
    def _active_hits(hit, pos, active):
        return hit & active[pos] if len(active) else hit

    def is_exchange(self, keys):
        hit, pos = self._lookup(self.ex_keys, keys)
        return self._active_hits(hit, pos, self._ex_active)

    def entity_of(self, keys):
        hit, pos = self._lookup(self.ex_keys, keys)
        out = np.full(len(hit), -1, np.int32)
        m = self._active_hits(hit, pos, self._ex_active)
        out[m] = self.ex_entity[pos[m]]
        return out

    def in_class(self, name, keys):
        hit, pos = self._lookup(self.cls_keys[name], keys)
        return self._active_hits(hit, pos, self._cls_active[name])

    def observe(self, keys, day_ord):
        keys = np.unique(np.asarray(keys, np.uint64))
        for sorted_keys, first in [(self.ex_keys, self.ex_first)] + [(self.cls_keys[c], self.cls_first[c]) for c in CLASSES]:
            if len(sorted_keys) == 0 or len(keys) == 0:
                continue
            hit = member(sorted_keys, keys)
            pos = np.searchsorted(sorted_keys, keys[hit])
            fresh = first[pos] < 0
            first[pos[fresh]] = int(day_ord)

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.stem + '.tmp.npz')
        np.savez(tmp, ex_first=self.ex_first, **{f'cls_first_{c}': self.cls_first[c] for c in CLASSES})
        os.replace(tmp, path)

    @classmethod
    def load(cls, path, doc, usdt_treasury):
        st = cls(doc, usdt_treasury)
        z = np.load(path)
        st.ex_first = z['ex_first'].copy()
        for c in CLASSES:
            st.cls_first[c] = z[f'cls_first_{c}'].copy()
        return st
