"""Two-asset controls using the unchanged, tested funded F2 wallet engine.

The engine's required third price is computational padding for identically zero
WST units, never observed data. Strictly excludes F2/WST-bearing policies and
removes that unused asset from source/position reports. All held prices are real
inputs; no missing held asset is filled. See independent review.
"""
import importlib.util
from pathlib import Path
from fractions import Fraction as F
HERE=Path(__file__).resolve().parent

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result

W=module('controls_frozen_wallet_engine','wrapper_book.py')
R=module('controls_literal_receipts','literal_receipts.py')
POLICIES=('wallet-cash','wallet-ETH25')
FinancialUnavailable=W.FinancialUnavailable


def padded_panel(panel):
    result=[]
    for row in panel:
        if set(row['prices'])!={'ETH','USDC'}:raise ValueError('exactly held-market ETH/USDC input universe required')
        result.append({'date':row['date'],'prices':{**row['prices'],'WST':F(1)}})
    return result


def no_wrapper(q):
    if q.get('WST',0)!=0:raise ValueError('unused wrapper sentinel cannot value nonzero exposure')


def check_progress(progress):
    for key in ('initial_atoms','current_atoms','terminal_atoms'):
        if key in progress:no_wrapper(progress[key])
    for row in progress.get('states',[]):no_wrapper(row['atoms'])
    for row in progress.get('events',[]):
        for key in ('before_atoms','after_atoms','debits_atoms','credits_atoms'):no_wrapper(row[key])
    if 'book' in progress:
        no_wrapper(W.amounts(progress['book']))
        for event in progress['book'].events:
            if event['deltas'].get(W.ASSETS['WST'],0)!=0:raise ValueError('wrapper delta under unheld sentinel')


def strip_padding(result):
    from copy import deepcopy
    out=deepcopy(result)
    for key in ('initial_atoms','current_atoms','terminal_atoms','literal_replay_atoms'):
        if key in out:out[key].pop('WST',None)
    for row in out.get('states',[]):
        row['atoms'].pop('WST',None);row['prices'].pop('WST',None)
    for row in out.get('events',[]):
        for key in ('before_atoms','after_atoms','debits_atoms','credits_atoms'):row[key].pop('WST',None)
    if 'current_prices' in out:out['current_prices'].pop('WST',None)
    if 'literal_balance_rows' in out:
        out['literal_balance_rows']=[row for row in out['literal_balance_rows'] if row['symbol']!='WST']
    out.get('stress',{}).pop('total-wrapper-position-loss',None)
    out['wrapper_exposure_verified_zero']=True
    out['unused_asset_padding_is_not_observed_data']=True
    out['scope']='Conditional two-asset oracle ETH/USDC wallet control; prefunded gas and authored execution/route costs'
    return out


def run_book(panel,policy,scenario,progress=None):
    if policy not in POLICIES:raise ValueError('zero-wrapper wallet control policy only')
    state={} if progress is None else progress
    try:
        result=W.run_book(padded_panel(panel),policy,scenario,state)
    finally:
        check_progress(state)
    no_wrapper(result['terminal_atoms']);no_wrapper(result['initial_atoms'])
    return strip_padding(result)


def partial_snapshot(progress):
    check_progress(progress)
    out={k:v for k,v in progress.items() if k not in ('book','formation_loss','market','event_loss')}
    for key in ('formation_loss','market','event_loss'):
        if key in progress:out[key]=W.fraction_record(progress[key])
    if 'book' in progress:
        out.update(R.snapshot(progress['book'],progress['initial_atoms'],W.ASSETS))
        out['valued_events_cover_literal_events']=len(progress['events'])==len(progress['book'].events)
    return strip_padding(R.json_safe(out))
