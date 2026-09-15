import importlib.util
from datetime import date,timedelta
from fractions import Fraction as F
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('tested_wallet_controls',Path(__file__).resolve().parents[2]/'research/defi-depth-2026-09-15/wallet_controls.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def panel():
    return [{'date':(date(2025,9,1)+timedelta(days=i)).isoformat(),
             'prices':{'ETH':F(2000 if i<10 else 2500),'USDC':F(1 if i<20 else 9,1 if i<20 else 10)}}
            for i in range(366)]


def test_padding_invariant_and_all_held_prices_preserved():
    rows=panel();original=m.padded_panel
    for policy in m.POLICIES:
        reference=m.run_book(rows,policy,'primary')
        try:
            def changed(rows):
                padded=original(rows)
                for i,row in enumerate(padded):row['prices']['WST']=F((i+1)*10**200)
                return padded
            m.padded_panel=changed
            assert m.run_book(rows,policy,'primary')==reference
        finally:m.padded_panel=original
        assert 'WST' not in reference['initial_atoms']
        assert all(set(row['prices'])=={'ETH','USDC'} and 'WST' not in row['atoms'] for row in reference['states'])
        assert reference['wrapper_exposure_verified_zero']


def test_no_wrapper_policy_or_missing_held_price_allowed():
    with pytest.raises(ValueError,match='wallet control'):m.run_book(panel(),'F2','primary')
    rows=panel();del rows[10]['prices']['ETH']
    with pytest.raises(ValueError,match='input universe'):m.run_book(rows,'wallet-ETH25','primary')
    with pytest.raises(ValueError,match='nonzero exposure'):m.no_wrapper({'WST':1})


def test_post_mutation_control_failure_retains_literal_atoms():
    progress={};original=m.W.mark
    try:
        def fail(q,p):
            if q['ETH']>m.W.RESERVE:raise ValueError('invented control mark gap')
            return original(q,p)
        m.W.mark=fail
        with pytest.raises(ValueError,match='invented'):m.run_book(panel(),'wallet-ETH25','primary',progress)
        out=m.partial_snapshot(progress)
        assert out['literal_balances_reconciled'] and not out['valued_events_cover_literal_events']
        assert out['literal_ledger_events'][0]['id']=='entry'
        assert 'WST' not in out['current_atoms']
    finally:m.W.mark=original
