# tests/execution/live/test_hybrid_compose.py
import math
from tradingagents.execution.live.hybrid_compose import compose_final

def test_multiplier_one_is_identity():
    assert compose_final(base=0.8, multiplier=1.0, effective_weight=0.7) == 0.8

def test_effective_weight_zero_is_identity():
    assert compose_final(base=0.8, multiplier=1.5, effective_weight=0.0) == 0.8

def test_full_formula():
    # base * (1 + eff_w*(mult-1)) = 0.8*(1+0.5*(1.4-1)) = 0.8*1.2 = 0.96
    assert math.isclose(compose_final(base=0.8, multiplier=1.4, effective_weight=0.5), 0.96)

def test_negative_base_preserves_sign():
    # short base, mult>1 levers the short further
    assert math.isclose(compose_final(base=-0.5, multiplier=1.2, effective_weight=1.0), -0.6)
