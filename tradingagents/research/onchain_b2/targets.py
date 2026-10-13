"""Targets T1–T5 and price/volume features F0 (spec §5.1, §6). Decision at the close of
day d (or Monday m); every input is a close or volume at or before d."""
from __future__ import annotations

import math
from datetime import timedelta


def _c(p, d, k=0):
    return p.get(d + timedelta(days=k))


def _rets(p, d, start, n):
    """Daily log returns for days d+start … d+start+n-1 (each relative to the previous day)."""
    out = []
    for k in range(start, start + n):
        a, b = _c(p, d, k - 1), _c(p, d, k)
        if a is None or b is None:
            return None
        out.append(math.log(b / a))
    return out


def t1(p, d):
    a, b = _c(p, d), _c(p, d, 1)
    return None if a is None or b is None else int(b > a)


def t2(p, m):
    a, b = _c(p, m), _c(p, m, 7)
    return None if a is None or b is None else int(b > a)


def t3(p, m):
    a, b = _c(p, m), _c(p, m, 7)
    return None if a is None or b is None else math.log(b / a)


def t4(p, m):
    r = _rets(p, m, 1, 7)
    return None if r is None else math.log(max(math.sqrt(sum(x * x for x in r)), 1e-8))


def t5(v, m):
    xs = [v.get(m + timedelta(days=k)) for k in range(1, 8)]
    return None if any(x is None for x in xs) or sum(xs) <= 0 else math.log(sum(xs))


def f0(p, v, d):
    r = _rets(p, d, -27, 28)            # returns ending at d: days d-27 … d
    c, c1, c7, c28 = _c(p, d), _c(p, d, -1), _c(p, d, -7), _c(p, d, -28)
    vols = [v.get(d - timedelta(days=k)) for k in range(28)]
    if r is None or None in (c, c1, c7, c28) or any(x is None for x in vols) or sum(vols[:7]) <= 0:
        return None
    v7, v28 = sum(vols[:7]), sum(vols)
    return {'f0_r1': math.log(c / c1), 'f0_r7': math.log(c / c7), 'f0_r28': math.log(c / c28),
            'f0_rv7': math.sqrt(sum(x * x for x in r[-7:])), 'f0_rv28': math.sqrt(sum(x * x for x in r)),
            'f0_lvol7': math.log(v7), 'f0_volratio': math.log(v7 / (v28 * 7 / 28))}