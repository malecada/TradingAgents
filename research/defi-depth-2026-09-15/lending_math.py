"""Pure Aave V3 source-model integer checks, not historical deployment proof.

Equations follow Aave WadRayMath/ValidationLogic (BUSL-1.1 upstream). No source
reads, acquisition, user account calls or empirical calculation entry point.
"""
import importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('lending_protocol_uint',Path(__file__).with_name('protocol_math.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
RAY=10**27;MAX=(1<<256)-1
class SourceModelUnavailable(ValueError):pass

def ray_mul(a,b):
    m.uint(a);m.uint(b)
    if a*b>MAX-RAY//2:raise ValueError('source-model ray multiplication overflow')
    return (a*b+RAY//2)//RAY

def ray_div(a,b):
    m.uint(a);m.uint(b)
    if b==0 or a>(MAX-b//2)//RAY:raise ValueError('source-model ray division zero/overflow')
    return (a*RAY+b//2)//b

def configuration(word):
    m.uint(word)
    return {'decimals':(word>>48)&255,'active':bool((word>>56)&1),'frozen':bool((word>>57)&1),
            'paused':bool((word>>60)&1),'supply_cap_whole_tokens':(word>>116)&((1<<36)-1)}

def index(value):
    m.uint(value,128)
    if value<RAY:raise SourceModelUnavailable('normalized income below initial source-model index')
    return value

def deposit_preview(amount,income,config_word,scaled_supply,accrued_treasury):
    m.uint(amount);index(income);m.uint(scaled_supply);m.uint(accrued_treasury,128)
    cfg=configuration(config_word)
    if amount==0 or cfg['decimals']!=6 or not cfg['active'] or cfg['frozen'] or cfg['paused']:
        raise SourceModelUnavailable('deposit amount, native-USDC decimals or reserve flags unavailable')
    supply_plus_treasury=m.uint(scaled_supply+accrued_treasury)
    before=ray_mul(supply_plus_treasury,income)
    cap=cfg['supply_cap_whole_tokens']*10**6
    if cap and before+amount>cap:raise SourceModelUnavailable('source-model supply cap exceeded including treasury accrual')
    scaled=m.uint(ray_div(amount,income),128)
    if scaled==0:raise SourceModelUnavailable('minted scaled amount rounds to zero')
    return {'scaled_atoms':scaled,'underlying_debit_atoms':amount,'initial_display_atoms':ray_mul(scaled,income),
            'supply_with_treasury_before_atoms':before,'supply_cap_atoms':cap,'scope':'conditional source model only'}

def withdrawal_preview(scaled,income,config_word,contract_cash):
    m.uint(scaled,128);index(income);m.uint(contract_cash)
    cfg=configuration(config_word)
    if scaled==0 or cfg['decimals']!=6 or not cfg['active'] or cfg['paused']:
        raise SourceModelUnavailable('withdrawal position/decimals/active/paused qualification unavailable')
    # A frozen reserve can still permit withdrawal in this source model.
    amount=ray_mul(scaled,income)
    burned=ray_div(amount,income)
    if burned!=scaled:raise SourceModelUnavailable('full-withdrawal scaled round trip differs')
    if contract_cash<amount:raise SourceModelUnavailable('insufficient observed contract cash, no invented withdrawal')
    return {'underlying_credit_atoms':amount,'scaled_burn_atoms':burned,'remaining_scaled_atoms':0,
            'scope':'observed contract cash is not a solvency or future-priority guarantee'}


def supply_cap_sufficient_bound(amount,income,config_word,scaled_supply,stored_treasury,
                                current_debt_upper_bound,*,debt_bound_qualified):
    """Sufficient cap test under independently qualified debt-accrual assumptions.

    False means inconclusive, not cap failure. The zero-cap branch deliberately
    does not infer or require unknown treasury/debt values. See independent review.
    Does not replace mint units, flags, execution or implementation qualification.
    """
    m.uint(amount);cfg=configuration(config_word)
    if amount==0 or cfg['decimals']!=6:raise SourceModelUnavailable('native USDC amount/decimals required')
    if cfg['supply_cap_whole_tokens']==0:
        return {'sufficient_cap_pass':True,'cap_disabled':True,'scope':'source-model cap branch only'}
    if debt_bound_qualified is not True:raise SourceModelUnavailable('same-block debt/treasury bound assumptions unqualified')
    index(income);m.uint(scaled_supply);m.uint(stored_treasury,128);m.uint(current_debt_upper_bound)
    reserve_factor=(config_word>>64)&65535
    if reserve_factor>10000:raise SourceModelUnavailable('reserve factor exceeds 100 percent')
    delta_scaled=ray_div(current_debt_upper_bound,income)
    upper_scaled=m.uint(scaled_supply+stored_treasury+delta_scaled)
    upper_underlying=ray_mul(upper_scaled,income)
    total=m.uint(upper_underlying+amount)
    cap=cfg['supply_cap_whole_tokens']*10**6
    return {'sufficient_cap_pass':total<=cap,'cap_disabled':False,'upper_supply_plus_deposit_atoms':total,
            'cap_atoms':cap,'inconclusive_if_false':True,'scope':'qualified conservative source-model bound; no exact cap-failure claim'}
