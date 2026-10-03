"""Exact prevout-aware BTC projection; no float amount is silently treated as exact."""
from dataclasses import dataclass
from decimal import Decimal,InvalidOperation
from fractions import Fraction
from collections import defaultdict
from types import MappingProxyType
from .provenance import require_hash


@dataclass(frozen=True)
class Projection:
    transaction_id:str
    status:str
    edges:object
    input_satoshis:int|None
    output_satoshis:int|None
    fee_satoshis:int|None


def decode_satoshis(decimal_btc):
    if not isinstance(decimal_btc,str):raise ValueError('exact decimal BTC text required; floating source needs separate admission')
    try:value=Fraction(Decimal(decimal_btc))*100000000
    except (InvalidOperation,ValueError,OverflowError) as error:raise ValueError('invalid decimal BTC') from error
    if value.denominator!=1 or not 0<=value<=21000000*100000000:raise ValueError('invalid satoshi amount')
    return int(value)


def _amount(output):
    value=output['satoshis']
    if type(value) is not int or not 0<=value<=21000000*100000000:raise ValueError('exact nonnegative integer satoshis required')
    return value


def project_transaction(transaction,prevouts):
    identity=transaction['id'];require_hash(identity)
    if type(transaction['coinbase']) is not bool:raise ValueError('coinbase flag required')
    if transaction['coinbase']:return Projection(identity,'excluded_coinbase',MappingProxyType({}),None,None,None)
    inputs=transaction['inputs'];outputs=transaction['outputs']
    if not inputs or not outputs:raise ValueError('non-coinbase transaction needs inputs/outputs')
    resolved=[];used=set()
    for item in inputs:
        require_hash(item['txid'])
        if type(item['vout']) is not int or item['vout']<0:raise ValueError('invalid prevout index')
        key=(item['txid'],item['vout'])
        if key in used:raise ValueError('duplicate spent prevout')
        used.add(key)
        if key not in prevouts:raise ValueError('unavailable prevout')
        resolved.append(prevouts[key])
    total_in=sum(_amount(x) for x in resolved);total_out=sum(_amount(x) for x in outputs)
    if total_in<=0 or total_out>total_in:raise ValueError('invalid exact value conservation')
    fee=total_in-total_out
    if any(not isinstance(x.get('address'),str) or not x['address'] for x in [*resolved,*outputs]):return Projection(identity,'excluded_nonunique_script',MappingProxyType({}),total_in,total_out,fee)
    by_sender=defaultdict(int);by_recipient=defaultdict(int)
    for x in resolved:by_sender[x['address']]+=_amount(x)
    for x in outputs:by_recipient[x['address']]+=_amount(x)
    edges={(a,b):Fraction(value_a*value_b,total_in) for a,value_a in sorted(by_sender.items()) for b,value_b in sorted(by_recipient.items()) if value_a and value_b}
    if sum(edges.values())!=total_out:raise AssertionError('exact projection output conservation')
    for b,value in by_recipient.items():
        if sum(weight for (a,target),weight in edges.items() if target==b)!=value:raise AssertionError('exact recipient conservation')
    return Projection(identity,'admitted',MappingProxyType(edges),total_in,total_out,fee)


def recover_binary64_satoshis(value):
    """Unique inverse on the valid satoshi grid; requires explicit source admission.

    No arbitrary decimal rounding: reject unless correctly rounded n/1e8 maps
    back to the identical binary64 input. Below21million BTC, adjacent satoshis
    are farther apart than a binary64 ULP, so a valid inverse is unique.
    """
    import math
    if type(value) is not float or not math.isfinite(value) or not 0<=value<=21000000:raise ValueError('finite binary64 BTC amount required')
    scaled=Fraction.from_float(value)*100000000
    q,r=divmod(scaled.numerator,scaled.denominator)
    nearest=q+int(2*r>scaled.denominator)
    if 2*r==scaled.denominator:raise ValueError('ambiguous satoshi-grid midpoint')
    if float(Fraction(nearest,100000000))!=value:raise ValueError('binary64 amount is not an exact satoshi-grid image')
    return nearest
