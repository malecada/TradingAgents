from fractions import Fraction
import pytest
from tradingagents.research.onchain_replication.btc import project_transaction,decode_satoshis


def tx():return {'id':'a'*64,'coinbase':False,'inputs':[{'txid':'b'*64,'vout':0},{'txid':'c'*64,'vout':1}], 'outputs':[{'address':'z','satoshis':5},{'address':'a','satoshis':2}]}


def test_exact_projection_conserves_outputs_and_separates_fees():
    result=project_transaction(tx(),{('b'*64,0):{'address':'a','satoshis':4},('c'*64,1):{'address':'b','satoshis':5}})
    assert result.fee_satoshis==2 and sum(result.edges.values())==7
    assert result.edges[('a','z')]==Fraction(20,9)
    assert result.edges[('a','a')]==Fraction(8,9) # change retained, not guessed away


def test_unknown_prevout_is_unavailable_not_excluded_or_zero():
    with pytest.raises(ValueError,match='prevout'):project_transaction(tx(),{})
    result=project_transaction(tx(),{('b'*64,0):{'address':None,'satoshis':4},('c'*64,1):{'address':'b','satoshis':5}})
    assert result.status=='excluded_nonunique_script' and not result.edges
    t=tx();t['coinbase']=True;assert project_transaction(t,{}).status=='excluded_coinbase'


def test_decimal_btc_values_must_be_exact_satoshi_grid():
    assert decode_satoshis('0.00000001')==1
    assert decode_satoshis('21000000')==2100000000000000
    with pytest.raises(ValueError):decode_satoshis(.1)
    with pytest.raises(ValueError):decode_satoshis('0.000000001')


@pytest.mark.parametrize('value',['0.00000001000000000000000000000000000001','20999999.9999999999999999999999999999'])
def test_off_grid_decimal_is_never_rounded_to_satoshi(value):
    with pytest.raises(ValueError):decode_satoshis(value)


def test_binary64_inverse_is_exact_grid_membership_not_silent_rounding():
    import math
    import random
    from fractions import Fraction
    from tradingagents.research.onchain_replication.btc import recover_binary64_satoshis
    amounts=[0,1,100000001,2100000000000000]
    amounts += [random.Random(17+i).randrange(2100000000000001) for i in range(1000)]
    for amount in amounts:
        value=float(Fraction(amount,100000000))
        assert recover_binary64_satoshis(value)==amount
        if value>0:
            with pytest.raises(ValueError,match='satoshi-grid'):recover_binary64_satoshis(math.nextafter(value,0.))
    for value in (float('nan'),float('inf'),-.1,21000001.,1):
        with pytest.raises(ValueError):recover_binary64_satoshis(value)
