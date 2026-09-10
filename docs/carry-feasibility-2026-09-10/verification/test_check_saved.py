"""Fabricated book and saved-record corruption tests; never calls a market API."""
import copy
import importlib.util
import hashlib
import json
from pathlib import Path

import pytest


@pytest.fixture
def checker():
    path = Path(__file__).with_name('check_saved.py')
    assert path.exists(), 'independent saved checker absent'
    spec = importlib.util.spec_from_file_location('independent_carry_checker', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def example():
    from scripts.carry_feasibility_math_2026_09_10 import size_hedge, terminal_case
    pair = dict(books=dict(
        spot={'asks': [['100', '100']], 'bids': [['99', '100']]},
        future={'bids': [['110', '100']], 'asks': [['111', '100']]}),
        instrument=dict(future_multiplier='1',
            spot_rules={'step_size': '.001', 'min_qty': '.001', 'max_qty': '100', 'min_notional': '1'},
            future_rules={'step_size': '.1', 'min_qty': '.1', 'max_qty': '100', 'min_notional': '1'}))
    gate=dict(spot_fee='.001',future_entry_fee='.0005',future_expiry_fee='.0005',
              cash_benchmark_annual=['0','.03','.05'])
    identity=dict(capital='210.255',reserve='1',fee_multiplier='1')
    e=size_hedge(spot_book=pair['books']['spot'],future_book=pair['books']['future'],
        spot_rules=pair['instrument']['spot_rules'],future_rules=pair['instrument']['future_rules'],
        capital=identity['capital'],reserve_fraction='1',fee_multiplier='1')
    r=terminal_case(e,terminal_index_ratio='1',adverse_exit_bps='0',seconds_to_expiry='31536000')
    return pair,gate,identity,e,r


def test_valid_hand_derived_book_and_terminal_record(checker,example):
    pair,gate,identity,entry,result=example
    assert result['net_cash_profit']=='9.6947002'
    checker.check_entry(entry,pair,identity,gate)
    checker.check_terminal(result,entry,'1','0','31536000',gate)


@pytest.mark.parametrize('field', ['spot_net_quantity','residual_base_quantity','spot_entry_cost',
    'future_entry_notional','future_entry_cash_fee','reserve_committed','uncommitted_cash',
    'future_entry_principal_cashflow','future_lots'])
def test_independent_entry_rejects_each_cash_or_quantity_corruption(checker,example,field):
    pair,gate,identity,entry,_=example
    entry[field]=entry[field]+1 if isinstance(entry[field],int) else '999'
    with pytest.raises(AssertionError):checker.check_entry(entry,pair,identity,gate)


@pytest.mark.parametrize('field', ['net_cash_profit','terminal_nav','net_return_on_capital',
    'annualized_simple_return','terminal_futures_reserve','terminal_residual_spot_value'])
def test_independent_terminal_rejects_each_total_corruption(checker,example,field):
    _,gate,_,entry,result=example;result[field]='999'
    with pytest.raises(AssertionError):checker.check_terminal(result,entry,'1','0','31536000',gate)


@pytest.mark.parametrize('field', ['future_entry_principal','spot_sale_gross','spot_exit_fee',
    'future_settlement_pnl','future_expiry_fee','reserve_released','paid_financing'])
def test_terminal_leg_cannot_be_hidden_by_correct_total(checker,example,field):
    _,gate,_,entry,result=example;result['cash_components'][field]='999'
    with pytest.raises(AssertionError):checker.check_terminal(result,entry,'1','0','31536000',gate)


def test_margin_flag_and_benchmark_are_independently_checked(checker,example):
    _,gate,_,entry,result=example
    altered=copy.deepcopy(result);altered['terminal_reserve_insufficient']=True
    with pytest.raises(AssertionError):checker.check_terminal(altered,entry,'1','0','31536000',gate)
    result['benchmarks']['0.03']['cash_profit']='0'
    with pytest.raises(AssertionError):checker.check_terminal(result,entry,'1','0','31536000',gate)


def test_exact_maximum_lot_and_rational_reserve(checker,example):
    from scripts.carry_feasibility_math_2026_09_10 import size_hedge,terminal_case
    pair,gate,identity,_,_=example
    identity.update(capital='410.165',reserve='1/3');gate['spot_fee']='0'
    entry=size_hedge(spot_book=pair['books']['spot'],future_book=pair['books']['future'],
        spot_rules=pair['instrument']['spot_rules'],future_rules=pair['instrument']['future_rules'],
        capital='410.165',reserve_fraction='1/3',fee_multiplier='1',spot_fee='0')
    assert entry['future_base_quantity']=='3' and entry['reserve_committed']=='110'
    checker.check_entry(entry,pair,identity,gate)
    result=terminal_case(entry,terminal_index_ratio='2',adverse_exit_bps='50',seconds_to_expiry='86400.5')
    checker.check_terminal(result,entry,'2','50','86400.5',gate)
    # Internally valid smaller sizing must still be rejected against the full budget.
    smaller=size_hedge(spot_book=pair['books']['spot'],future_book=pair['books']['future'],
        spot_rules=pair['instrument']['spot_rules'],future_rules=pair['instrument']['future_rules'],
        capital='200',reserve_fraction='1/3',fee_multiplier='1',spot_fee='0')
    with pytest.raises(AssertionError):checker.check_entry(smaller,pair,identity,gate)


def test_unavailable_is_not_zero_profit_or_a_missing_identity(checker,example):
    pair,gate,identity,_,_=example;identity['capital']='1'
    checker.check_entry({'status':'unavailable','reason':'no lot fits'},pair,identity,gate)
    with pytest.raises(AssertionError):checker.check_entry({'status':'unavailable'},pair,identity,gate)


def test_reject_missing_or_duplicate_registered_identity(checker):
    gate=dict(assets=['BTC','ETH'],capital=['1000','10000'],reserve_fractions=['1','1/3'],
        fee_multipliers=['1','2'],terminal_index_ratios=['0.5','1','2'],adverse_exit_bps=['0','10','50'],snapshots=3)
    entries,rows=checker.expected_ids(gate)
    assert len(entries)==48 and len(rows)==432
    checker.check_ids(entries,rows,gate)
    with pytest.raises(AssertionError):checker.check_ids(entries[:-1],rows,gate)
    with pytest.raises(AssertionError):checker.check_ids(entries,rows[:-1]+[rows[0]],gate)


@pytest.fixture
def raw_receipt(checker,tmp_path):
    directory=tmp_path/checker.CAPTURE/'raw';directory.mkdir(parents=True)
    key='000_spot_depth';body=b'{"asks":[["100","1"]],"bids":[["99","1"]]}'
    raw=directory/(key+'.bin');raw.write_bytes(body)
    receipt=dict(id=key,market='spot',endpoint='depth',url='https://api.binance.com/api/v3/depth?symbol=BTCUSDT',
        raw_path=str(raw.relative_to(tmp_path)),bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),
        start_ns=1000000000,end_ns=1100000000,elapsed_ns=100000000,http_status=200,error=None)
    path=directory/(key+'.json');path.write_text(json.dumps(receipt))
    manifest=dict(requests=[receipt],files={str(p.relative_to(tmp_path)):checker.sha(p) for p in directory.iterdir()})
    checker.check_receipts(tmp_path,manifest)
    return tmp_path,raw,path,manifest


@pytest.mark.parametrize('mode',['raw_bytes','receipt_body','unlisted_file','duplicate_request'])
def test_raw_receipt_integrity_cannot_be_hidden_by_normalized_records(checker,raw_receipt,mode):
    root,raw,path,manifest=raw_receipt
    if mode=='raw_bytes':raw.write_bytes(b'{}')
    elif mode=='receipt_body':
        row=json.loads(path.read_text());row['url']='https://unregistered.example/depth';path.write_text(json.dumps(row))
        manifest['files'][str(path.relative_to(root))]=checker.sha(path)
    elif mode=='unlisted_file':path.with_name('unlisted.bin').write_bytes(b'{}')
    else:manifest['requests'].append(manifest['requests'][0])
    with pytest.raises(AssertionError):checker.check_receipts(root,manifest)
