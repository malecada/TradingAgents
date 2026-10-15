# tradingagents/research/onchain_b4/entities.py
"""Exchange entities (spec §4.2): labelled addresses plus deposit addresses learned causally.
An address joins the candidate table on the day of its first observed send if it was never seen
sending before and its earliest block of sends that day includes a transfer to a label; it is a
deposit address from the next day while at least `share` of its outgoing transfers go to labels."""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from ..onchain_b3.history import Bloom


def member(sorted_keys, keys):
    keys = np.asarray(keys, np.uint64)
    if len(sorted_keys) == 0 or len(keys) == 0:
        return np.zeros(len(keys), bool)
    pos = np.searchsorted(sorted_keys, keys)
    pos[pos == len(sorted_keys)] = 0
    return sorted_keys[pos] == keys


class Entities:
    def __init__(self, labels, log2_bits, hashes, share):
        self.labels = np.unique(np.asarray(labels, np.uint64))
        self.bloom = Bloom(log2_bits, hashes)
        self.share = float(share)
        self.c_keys = np.empty(0, np.uint64)
        self.c_out = np.empty(0, np.uint32)
        self.c_lab = np.empty(0, np.uint32)
        self.deposits = np.empty(0, np.uint64)
        self.last_day = None

    def is_labelled(self, keys):
        return member(self.labels, keys)

    def is_exchange(self, keys):
        return member(self.labels, keys) | member(self.deposits, keys)

    def update(self, src, dst, block, day):
        src, dst, block = np.asarray(src, np.uint64), np.asarray(dst, np.uint64), np.asarray(block, np.int64)
        keep = ~member(self.labels, src)
        s, b, lab = src[keep], block[keep], member(self.labels, dst[keep])
        if len(s):
            order = np.lexsort((b, s))
            s, b, lab = s[order], b[order], lab[order]
            uniq, first, counts = np.unique(s, return_index=True, return_counts=True)
            n_lab = np.add.reduceat(lab.astype(np.uint32), first).astype(np.uint32)
            earliest = np.repeat(b[first], counts)
            first_lab = np.add.reduceat(((b == earliest) & lab).astype(np.uint32), first) > 0
            known = member(self.c_keys, uniq)
            pos = np.searchsorted(self.c_keys, uniq[known])
            self.c_out[pos] += counts[known].astype(np.uint32)
            self.c_lab[pos] += n_lab[known]
            new = ~known & first_lab & ~self.bloom.contains(uniq)
            if new.any():
                at = np.searchsorted(self.c_keys, uniq[new])
                self.c_keys = np.insert(self.c_keys, at, uniq[new])
                self.c_out = np.insert(self.c_out, at, counts[new].astype(np.uint32))
                self.c_lab = np.insert(self.c_lab, at, n_lab[new])
        if len(src):
            self.bloom.add(np.unique(src))
        ok = (self.c_lab >= 1) & (self.c_lab.astype(np.float64) >= self.share * self.c_out)
        self.deposits = self.c_keys[ok]
        self.last_day = day

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.stem + '.tmp.npz')
        np.savez(tmp, labels=self.labels, bits=self.bloom.bits, bloom=np.array([self.bloom.log2, self.bloom.k]),
                 share=np.array([self.share]), c_keys=self.c_keys, c_out=self.c_out, c_lab=self.c_lab,
                 last_day=np.array([self.last_day or '']))
        os.replace(tmp, path)

    @classmethod
    def load(cls, path):
        z = np.load(path)
        e = cls(z['labels'], int(z['bloom'][0]), int(z['bloom'][1]), float(z['share'][0]))
        e.bloom.bits = z['bits'].copy()
        e.c_keys, e.c_out, e.c_lab = z['c_keys'].copy(), z['c_out'].copy(), z['c_lab'].copy()
        ok = (e.c_lab >= 1) & (e.c_lab.astype(np.float64) >= e.share * e.c_out)
        e.deposits = e.c_keys[ok]
        e.last_day = str(z['last_day'][0]) or None
        return e
