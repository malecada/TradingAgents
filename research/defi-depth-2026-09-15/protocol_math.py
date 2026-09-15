"""Pure protocol bookkeeping primitives; no source reads or financial runner.

Integer quantities are token base units. LP inputs must describe the exact v3
range and protocol state; these functions do not establish source admission,
historical deployment, executable liquidation or counterfactual capacity.
Equations are documented in PROTOCOL-ACCOUNTING.md. No float arithmetic.
"""
from fractions import Fraction
from decimal import DecimalException, Inexact, localcontext
from functools import wraps
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parents[1] / 'broader-allocation-2026-09-15/spot_book.py'
_loader = importlib.util.spec_from_file_location('preserved_protocol_spot_book', _path)
_spot = importlib.util.module_from_spec(_loader)
_loader.loader.exec_module(_spot)

Q96 = 1 << 96
Q128 = 1 << 128
U256 = 1 << 256


def uint(value, bits=256):
    if type(value) is not int or not 0 <= value < 1 << bits:
        raise ValueError('canonical unsigned integer required')
    return value


def rounded_ratio(numerator, denominator, *, up=False):
    if type(numerator) is not int or type(denominator) is not int or numerator < 0 or denominator <= 0:
        raise ValueError('nonnegative integer numerator and positive denominator required')
    if type(up) is not bool:
        raise ValueError('explicit boolean rounding required')
    return (numerator + denominator - 1) // denominator if up else numerator // denominator


def _bounds(lower, upper):
    uint(lower, 160)
    uint(upper, 160)
    if not 0 < lower < upper:
        raise ValueError('positive ordered sqrt bounds required')


def lp_amounts(liquidity, sqrt_price, lower, upper, *, mint):
    """Token0/token1 needed for mint (ceil), or received on burn (floor).

    Limits the implementation to a nonnegative signed-int128 position change.
    At the lower boundary all inventory is token0; at the upper all is token1.
    Prices are Q64.96 square roots of the raw token1/token0 unit ratio.
    """
    uint(liquidity, 127)
    uint(sqrt_price, 160)
    _bounds(lower, upper)
    if sqrt_price <= 0 or type(mint) is not bool:
        raise ValueError('positive sqrt price and explicit mint/burn flag required')
    middle = min(max(sqrt_price, lower), upper)
    token0 = rounded_ratio(liquidity * Q96 * (upper - middle), upper * middle, up=mint)
    token1 = rounded_ratio(liquidity * (middle - lower), Q96, up=mint)
    uint(token0)
    uint(token1)
    return token0, token1


def lp_liquidity(amount0, amount1, sqrt_price, lower, upper):
    """Periphery sizing with its intermediate integer truncation preserved.

    Returned L is rechecked against exact core mint debits. Unused input amounts
    remain wallet inventory; they are not silently contributed or discarded.
    """
    uint(amount0)
    uint(amount1)
    uint(sqrt_price, 160)
    _bounds(lower, upper)
    if sqrt_price <= 0:
        raise ValueError('positive sqrt price required')

    def from0(a, b):
        return amount0 * (a * b // Q96) // (b - a)

    def from1(a, b):
        return amount1 * Q96 // (b - a)

    if sqrt_price <= lower:
        result = from0(lower, upper)
    elif sqrt_price >= upper:
        result = from1(lower, upper)
    else:
        result = min(from0(sqrt_price, upper), from1(lower, sqrt_price))
    uint(result, 127)
    used0, used1 = lp_amounts(result, sqrt_price, lower, upper, mint=True)
    if used0 > amount0 or used1 > amount1:
        raise ValueError('sized liquidity exceeds funded token amounts')
    return result


def fee_inside(global_growth, lower_outside, upper_outside, tick, lower_tick, upper_tick,
               *, boundaries_qualified):
    """One token's v3 inside growth, modulo uint256.

    Caller must qualify initialization/clearing/crossing history for the held
    range. A false flag refuses the calculation; a true flag is not evidence.
    """
    for value in (global_growth, lower_outside, upper_outside):
        uint(value)
    if any(type(value) is not int or not -(1 << 23) <= value < (1 << 23)
           for value in (tick, lower_tick, upper_tick)) or lower_tick >= upper_tick:
        raise ValueError('ordered int24 ticks required')
    if boundaries_qualified is not True:
        raise ValueError('unqualified position boundary history')
    below = lower_outside if tick >= lower_tick else (global_growth - lower_outside) % U256
    above = upper_outside if tick < upper_tick else (global_growth - upper_outside) % U256
    return (global_growth - below - above) % U256


def lp_fees(liquidity, inside_start, inside_end, *, already_owed=0):
    """Single position update with no intervening liquidity change or poke.

    Fee counters wrap uint256. Values whose owed balance exceeds uint128 are
    rejected instead of pretending a wrapped token debt is usable cash.
    Missing/reset/misidentified counters must be excluded before this call.
    """
    uint(liquidity, 127)
    uint(inside_start)
    uint(inside_end)
    uint(already_owed, 128)
    accrued = liquidity * ((inside_end - inside_start) % U256) // Q128
    return uint(already_owed + accrued, 128)


def converted_units(quantity, numerator, denominator, *, round_up=False):
    """Admitted rational conversion only; no default protocol rounding model."""
    for value in (quantity, numerator, denominator):
        uint(value)
    return uint(rounded_ratio(quantity * numerator, denominator, up=round_up))


def token_value(quantity, decimals, usd_per_token):
    """Exact rational value from an explicitly supplied USD unit mark."""
    uint(quantity)
    if type(decimals) is not int or not 0 <= decimals <= 36:
        raise ValueError('explicit supported token decimals required')
    if not isinstance(usd_per_token, (Fraction, int)) or isinstance(usd_per_token, bool) or usd_per_token < 0:
        raise ValueError('explicit nonnegative exact rational mark required')
    return Fraction(quantity, 10 ** decimals) * usd_per_token


def exact_decimal(method):
    """Bound decimal operations and reject lost digits before ledger mutation."""
    @wraps(method)
    def call(*args, **kwargs):
        with localcontext() as context:
            context.prec = 256
            context.traps[Inexact] = True
            try:
                return method(*args, **kwargs)
            except DecimalException as exc:
                raise ValueError('ledger operation exceeds exact decimal domain') from exc
    return call


class ProtocolBook(_spot.SpotBook):
    """Reuse funded inventory ledger for explicit multi-asset conversions.

    Receipt assets need their own chain/contract/position or queue identity and
    liquidation mark. No conversion rate, receipt price or redemption delay is
    inferred. Gas is debited from pre-existing inventory atomically on success.
    A reverted transaction uses inherited charge() to retain gas without mint.
    Every exposed arithmetic operation uses256decimal digits and traps any
    inexact result; unsupported values fail before the ledger is mutated.
    """

    _post = exact_decimal(_spot.SpotBook._post)
    trade = exact_decimal(_spot.SpotBook.trade)
    charge = exact_decimal(_spot.SpotBook.charge)
    begin_transfer = exact_decimal(_spot.SpotBook.begin_transfer)
    settle_transfer = exact_decimal(_spot.SpotBook.settle_transfer)
    write_off = exact_decimal(_spot.SpotBook.write_off)
    liquidation_nav = exact_decimal(_spot.SpotBook.liquidation_nav)

    @exact_decimal
    def convert(self, event_id, debits, credits, *, fee_key, fee, evidence):
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError('conversion evidence reference required')
        incoming = {_spot.key(k): _spot.amount(v) for k, v in credits.items()}
        outgoing = {_spot.key(k): _spot.amount(v) for k, v in debits.items()}
        if not incoming or not outgoing or incoming.keys() & outgoing.keys():
            raise ValueError('distinct nonempty input and receipt identities required')
        if any(v <= 0 for v in (*incoming.values(), *outgoing.values())):
            raise ValueError('positive explicit conversion quantities required')
        fee_key, fee = _spot.key(fee_key), _spot.amount(fee)
        if fee < 0:
            raise ValueError('nonnegative gas/fee debit required')
        gross = dict(outgoing)
        gross[fee_key] = gross.get(fee_key, _spot.ZERO) + fee
        if any(self.balances.get(k, _spot.ZERO) < value for k, value in gross.items()):
            raise ValueError('conversion and gas require prefunded gross inputs')
        deltas = {k: -v for k, v in outgoing.items()}
        deltas.update(incoming)
        self._fee(deltas, fee_key, fee)
        self._post(event_id, 'protocol_conversion', deltas)
        self.events[-1]['evidence'] = evidence
