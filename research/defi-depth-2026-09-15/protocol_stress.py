"""Invented-input protocol stress primitives; no source or financial runner."""
from fractions import Fraction
from math import isqrt
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('stress_accounting_math',HERE/'protocol_math.py')
accounting=importlib.util.module_from_spec(s);s.loader.exec_module(accounting)
MIN_SQRT=4295128739
MAX_SQRT=1461446703485210103287273052203988822378723970342


def positive_factor(value):
    if isinstance(value,bool) or not isinstance(value,(int,Fraction)) or value<=0:
        raise ValueError('explicit positive rational shock factor required')
    return Fraction(value)


def shocked_sqrt_price(sqrt_price,token0_usd_factor,token1_usd_factor,*,operating_arbitrage_path):
    """Scale raw token1/token0 square-root price by sqrt(factor0/factor1).

    Existing token ordering and decimals remain unchanged. This assumes an
    operating arbitraged pool and unchanged initial pool/mark basis; a caller
    flag states the chosen scenario, not evidence it actually occurred. Prices
    outside protocol domain are unavailable, never silently clamped. Zero-value
    token/catastrophic outcomes require their separate claim/recovery scenario.
    """
    accounting.uint(sqrt_price,160)
    if not MIN_SQRT<=sqrt_price<MAX_SQRT or operating_arbitrage_path is not True:
        raise ValueError('qualified in-domain operating pool scenario required')
    ratio=positive_factor(token0_usd_factor)/positive_factor(token1_usd_factor)
    numerator=sqrt_price*sqrt_price*ratio.numerator
    result=isqrt(numerator//ratio.denominator)
    if not MIN_SQRT<=result<MAX_SQRT:
        raise ValueError('shocked pool price outside protocol domain')
    return result


def lp_stress_inventory(liquidity,sqrt_price,lower,upper,token0_usd_factor,token1_usd_factor,*,operating_arbitrage_path):
    """Burn inventories after the stated pool shock; no added fees or IL debit."""
    shocked=shocked_sqrt_price(sqrt_price,token0_usd_factor,token1_usd_factor,operating_arbitrage_path=operating_arbitrage_path)
    token0,token1=accounting.lp_amounts(liquidity,shocked,lower,upper,mint=False)
    return {'sqrt_price':shocked,'token0_base_units':token0,'token1_base_units':token1,
            'incremental_shock_fees':0,'scope':'inventory scenario only; cash exit, arbitrage and gas remain to be qualified'}


def fixed_flow_participation_bounds(virtual_liquidity,historical_liquidity_floor):
    """Ideal proportional fixed-flow factor relative to infinitesimal attribution.

    Positive historical active-liquidity floor must hold on EVERY fee-producing
    step, not just daily samples. Actual fees, integer rounding, flow changes,
    prices, flash activity and zero-liquidity periods are outside this theorem.
    This is a dimensionless identity, not a realized fee or profitability bound.
    """
    virtual=positive_factor(virtual_liquidity);floor=positive_factor(historical_liquidity_floor)
    return floor/(floor+virtual),Fraction(1)
