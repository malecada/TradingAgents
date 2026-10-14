"""4-week targets T6 (log return) and T7 (log realised volatility), spec §6."""
from __future__ import annotations

import math
from datetime import timedelta

from ..onchain_b2.targets import _rets


def t6(p, m):
    a, b = p.get(m), p.get(m + timedelta(days=28))
    return None if a is None or b is None else math.log(b / a)


def t7(p, m):
    r = _rets(p, m, 1, 28)
    return None if r is None else math.log(max(math.sqrt(sum(x * x for x in r)), 1e-8))