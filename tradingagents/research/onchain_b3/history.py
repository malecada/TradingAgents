"""Cross-week address history (spec §4.7): 64-bit address keys, a Bloom filter of every
earlier week, and exact last-week / last-four-weeks membership."""
from __future__ import annotations

import numpy as np

_C = (0x9E3779B97F4A7C15, 0xC2B2AE3D27D4EB4F, 0x165667B19E3779F9, 0xD6E8FEB86659FD93,
      0xFF51AFD7ED558CCD, 0xC4CEB9FE1A85EC53, 0x94D049BB133111EB)
_LUT = np.zeros(256, np.uint64)
for _i, _c in enumerate(b'0123456789abcdef'):
    _LUT[_c] = _i
for _i, _c in enumerate(b'ABCDEF'):
    _LUT[_c] = 10 + _i


def keys_from_addresses(addresses):
    raw = np.asarray(addresses).astype('S42').view(np.uint8).reshape(-1, 42)[:, 2:18]
    nib = _LUT[raw]
    shifts = np.arange(60, -1, -4, dtype=np.uint64)
    return np.unique(np.bitwise_or.reduce(nib << shifts, axis=1))


class Bloom:
    def __init__(self, log2_bits, hashes):
        self.log2, self.k = log2_bits, hashes
        self.bits = np.zeros(1 << (log2_bits - 3), np.uint8)

    def _positions(self, keys):
        keys = np.asarray(keys, np.uint64)
        return [(keys * np.uint64(_C[j])) >> np.uint64(64 - self.log2) for j in range(self.k)]

    def add(self, keys):
        for p in self._positions(keys):
            np.bitwise_or.at(self.bits, (p >> np.uint64(3)).astype(np.int64),
                             np.left_shift(np.uint8(1), (p & np.uint64(7)).astype(np.uint8)))

    def contains(self, keys):
        ok = np.ones(len(keys), bool)
        for p in self._positions(keys):
            byte = self.bits[(p >> np.uint64(3)).astype(np.int64)]
            ok &= ((byte >> (p & np.uint64(7)).astype(np.uint8)) & 1).astype(bool)
        return ok


def history_pass(weeks, load_keys, log2_bits, hashes):
    bloom = Bloom(log2_bits, hashes)
    prev, out = [], {}
    nan = float('nan')
    for w in weeks:
        keys = load_keys(w)
        if keys is None:
            out[w] = None
            prev = (prev + [None])[-4:]
            continue
        known = bloom.contains(keys)
        last = prev[-1] if prev else np.empty(0, np.uint64)
        incomplete = any(x is None for x in prev[-4:])
        window = [x for x in prev[-4:] if x is not None]
        union = np.unique(np.concatenate(window)) if window else np.empty(0, np.uint64)
        in4 = np.isin(keys, union, assume_unique=True)
        out[w] = {'f4_new_share': float((~known).mean()),
                  'f4_prev1_share': nan if last is None else float(np.isin(keys, last, assume_unique=True).mean()),
                  'f4_prev4_share': nan if incomplete else float(in4.mean()),
                  'f4_return_share': nan if incomplete else float((known & ~in4).mean())}
        bloom.add(keys)
        prev = (prev + [keys])[-4:]
    return out