"""Hand-derived linear cashflow examples; no market inputs or financial trials."""
from dataclasses import replace
import importlib

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def api():
    return importlib.import_module('tradingagents.event_accounting')


def stamp(hour):
    return pd.Timestamp('2024-01-01', tz='UTC') + pd.Timedelta(hours=hour)


def setup(api, *, weight=.5, termination=1.5, multiplier=1.):
    evidence = api.Evidence('synthetic:hand-derived', '0'*64, 'synthetic')
    rounding = api.CashRounding(None, 'unrounded')
    fee = api.FeeRule(.001, rounding, evidence)
    contract = api.Contract('venue:A:original', 'venue', 'USDT', 'linear',
        multiplier, None, stamp(-24), stamp(termination) if termination is not None else None,
        None, evidence)
    ix = pd.date_range(stamp(0), stamp(3), freq='h')
    prices = pd.DataFrame({'venue:A:original': [100., 110., np.nan, np.nan]}, index=ix)
    targets = pd.DataFrame({'venue:A:original': [weight]}, index=ix[:1])
    settlement = api.SettlementEvent('close-A', contract.identity, stamp(1.5), 1,
        80., api.FeeRule(.002, rounding, evidence), evidence)
    args = dict(prices=prices, price_evidence=evidence, targets=targets, contracts=[contract], settlements=[settlement],
        funding=None, trade_fee=fee, ordering='events_before_targets', freq='h', initial_nav=1000.)
    return args, evidence, rounding


def funding(api, args, evidence, rounding, rows, expected=None):
    identity = args['contracts'][0].identity
    events = [api.FundingEvent(f'fund-{i}', identity, stamp(t), seq, rate, mark, rounding, evidence)
              for i, (t, seq, rate, mark) in enumerate(rows)]
    calendar = api.FundingCalendar(stamp(0), stamp(3),
        {identity: [stamp(t) for t in (expected if expected is not None else [r[0] for r in rows])]}, evidence)
    return api.FundingInputs(calendar, events)


@pytest.mark.parametrize('weight,want_nav,want_pnl', [(.5, 898.7, -100.), (-.5, 1098.7, 100.)])
def test_terminal_pnl_is_signed_fixed_quantity_and_fee_is_once(api, weight, want_nav, want_pnl):
    args, _, _ = setup(api, weight=weight)
    result = api.run_event_book(**args)
    assert result.returns.index.equals(args['prices'].index[1:])
    assert result.returns.nav.tolist() == pytest.approx([1049.5 if weight > 0 else 949.5, want_nav, want_nav])
    assert result.ledger.pnl.sum() == pytest.approx(want_pnl)
    assert result.ledger.fee.sum() == pytest.approx(1.3)
    assert result.quantities.iloc[-1].eq(0).all()
    assert result.returns.net.iloc[-1] == 0.
    assert (1 + result.returns.net).prod()*1000 == pytest.approx(want_nav)


def test_multiplier_and_funding_mark_do_not_change_held_quantity_or_previous_mark(api):
    args, evidence, rounding = setup(api, multiplier=10.)
    args['funding'] = funding(api, args, evidence, rounding, [(.5, 0, .01, 120.), (2., 0, .99, 900.)])
    result = api.run_event_book(**args)
    assert result.returns.nav.tolist() == pytest.approx([1043.5, 892.7, 892.7])
    assert result.quantities.iloc[0, 0] == .5
    assert result.ledger.carry.sum() == -6.
    assert result.ledger.pnl.sum() == -100.


@pytest.mark.parametrize('fund_sequence,want_nav', [(0, 892.7), (2, 898.7)])
def test_explicit_same_time_order_decides_funding_on_terminal_quantity(api, fund_sequence, want_nav):
    args, evidence, rounding = setup(api)
    args['funding'] = funding(api, args, evidence, rounding, [(1.5, fund_sequence, .01, 120.)])
    assert api.run_event_book(**args).returns.nav.iloc[-1] == pytest.approx(want_nav)


def test_boundary_flat_target_cannot_skip_forced_settlement_or_charge_an_exit_trade(api):
    args, _, _ = setup(api, termination=1.)
    args['settlements'] = [replace(args['settlements'][0], time=stamp(1))]
    args['targets'].loc[stamp(1)] = 0.
    args['prices'].iloc[1] = np.nan
    result = api.run_event_book(**args)
    assert result.returns.nav.tolist() == pytest.approx([898.7]*3)
    assert result.ledger.loc[result.ledger.kind == 'trade', 'turnover'].sum() == 500.


def test_zero_terminal_price_preserves_real_long_loss_and_short_gain(api):
    args, _, _ = setup(api, weight=-.5)
    args['settlements'] = [replace(args['settlements'][0], price=0.)]
    assert api.run_event_book(**args).returns.nav.iloc[-1] == pytest.approx(1499.5)


def test_cash_rounding_is_explicit_for_settlement_and_signed_funding(api):
    args, evidence, _ = setup(api, weight=1.)
    args['initial_nav'] = 100.
    rounding = api.CashRounding(2, 'ROUND_HALF_UP')
    args['trade_fee'] = api.FeeRule(0., rounding, evidence)
    args['settlements'] = [replace(args['settlements'][0], fee=api.FeeRule(.0037, rounding, evidence))]
    args['funding'] = funding(api, args, evidence, rounding, [(.5, 0, .012345, 123.456)])
    result = api.run_event_book(**args)
    assert result.returns.nav.iloc[-1] == pytest.approx(78.18)
    assert result.ledger.carry.sum() == -1.52
    assert result.ledger.fee.sum() == .30


@pytest.mark.parametrize('missing', ['price', 'fee', 'evidence', 'record'])
def test_unknown_terminal_inputs_fail_only_when_terminal_quantity_is_held(api, missing):
    args, _, _ = setup(api)
    args['settlements'] = ([] if missing == 'record' else [replace(args['settlements'][0], **{missing: None})])
    with pytest.raises(ValueError, match='settlement'):
        api.run_event_book(**args)
    args['targets'].iloc[0] = 0.
    assert api.run_event_book(**args).returns.nav.eq(1000.).all()


@pytest.mark.parametrize('missing', ['rate', 'mark', 'rounding', 'evidence', 'record'])
def test_unknown_expected_funding_is_unavailable_while_held(api, missing):
    args, evidence, rounding = setup(api)
    inputs = funding(api, args, evidence, rounding, [(.5, 0, .01, 120.)])
    events = [] if missing == 'record' else [replace(inputs.events[0], **{missing: None})]
    args['funding'] = replace(inputs, events=events)
    with pytest.raises(ValueError, match='funding'):
        api.run_event_book(**args)
    args['targets'].iloc[0] = 0.
    assert api.run_event_book(**args).returns.nav.eq(1000.).all()


def test_missing_postclosure_funding_is_not_charged(api):
    args, evidence, rounding = setup(api)
    args['funding'] = funding(api, args, evidence, rounding, [], expected=[2.])
    assert api.run_event_book(**args).returns.nav.iloc[-1] == pytest.approx(898.7)


@pytest.mark.parametrize('bad_calendar', ['coverage', 'contract', 'unexpected'])
def test_funding_calendar_is_independent_complete_coverage_contract(api, bad_calendar):
    args, evidence, rounding = setup(api)
    inputs = funding(api, args, evidence, rounding, [(.5, 0, .01, 120.)])
    if bad_calendar == 'coverage':
        inputs = replace(inputs, calendar=replace(inputs.calendar, end=stamp(1)))
    elif bad_calendar == 'contract':
        inputs = replace(inputs, calendar=replace(inputs.calendar, expected={}))
    else:
        inputs = replace(inputs, calendar=replace(inputs.calendar, expected={args['contracts'][0].identity: []}))
    args['funding'] = inputs
    with pytest.raises(ValueError, match='funding'):
        api.run_event_book(**args)


@pytest.mark.parametrize('bad', ['duplicate_id', 'duplicate_sequence', 'missing_sequence', 'outside', 'wrong_identity', 'wrong_time'])
def test_ambiguous_or_mismatched_event_records_cannot_silently_run(api, bad):
    args, evidence, rounding = setup(api)
    s = args['settlements'][0]
    if bad == 'duplicate_id':
        args['settlements'] = [s, s]
    elif bad == 'duplicate_sequence':
        args['funding'] = funding(api, args, evidence, rounding, [(1.5, 1, .01, 120.)])
    else:
        changes = {'missing_sequence': {'sequence': None}, 'outside': {'time': stamp(4)},
                   'wrong_identity': {'contract': 'successor'}, 'wrong_time': {'time': stamp(1.25)}}
        args['settlements'] = [replace(s, **changes[bad])]
    with pytest.raises(ValueError):
        api.run_event_book(**args)


def test_missing_held_boundary_mark_cannot_be_hidden_by_flat_target(api):
    args, _, _ = setup(api)
    args['prices'].iloc[1] = np.nan
    args['targets'].loc[stamp(1)] = 0.
    with pytest.raises(ValueError, match='held.*price'):
        api.run_event_book(**args)


@pytest.mark.parametrize('bad', ['clock_gap', 'naive_clock', 'final_target', 'off_clock_target', 'ordering'])
def test_complete_clock_and_boundary_policy_are_enforced(api, bad):
    args, _, _ = setup(api)
    if bad == 'clock_gap':
        args['prices'] = args['prices'].drop(stamp(1))
    elif bad == 'naive_clock':
        args['prices'].index = args['prices'].index.tz_localize(None)
    elif bad in ('final_target', 'off_clock_target'):
        args['targets'].loc[stamp(3 if bad == 'final_target' else .5)] = 0.
    else:
        args['ordering'] = 'unknown'
    with pytest.raises(ValueError):
        api.run_event_book(**args)


def test_funding_and_settlement_at_final_boundary_are_in_last_period(api):
    args, evidence, rounding = setup(api, termination=3.)
    args['prices'].iloc[2] = 120.
    args['settlements'] = [replace(args['settlements'][0], time=stamp(3))]
    args['funding'] = funding(api, args, evidence, rounding, [(3., 0, .01, 120.)])
    result = api.run_event_book(**args)
    assert result.returns.nav.iloc[-1] == pytest.approx(892.7)
    assert len(result.returns) == 3


@pytest.mark.parametrize('new_weight,allowed', [(.5, False), (.25, True), (-.25, False), (0., True)])
def test_reduce_only_uses_drifted_quantity_not_equal_weights(api, new_weight, allowed):
    args, evidence, _ = setup(api, termination=None)
    a = replace(args['contracts'][0], reduce_only_at=stamp(1))
    b = replace(a, identity='venue:B:original', reduce_only_at=None)
    args['contracts'] = [a, b]
    args['settlements'] = []
    args['prices'] = pd.DataFrame({a.identity: 100., b.identity: [100., 200., 200., 200.]}, index=args['prices'].index)
    args['targets'] = pd.DataFrame({a.identity: [.5, new_weight], b.identity: [.5, 0.]}, index=args['prices'].index[:2])
    args['trade_fee'] = replace(args['trade_fee'], rate=0.)
    if allowed:
        result = api.run_event_book(**args)
        assert result.returns.nav.iloc[-1] == 1500.
        assert result.quantities.iloc[1, 0] == new_weight * 15.
    else:
        with pytest.raises(ValueError, match='reduce.only'):
            api.run_event_book(**args)


def test_successor_has_separate_quantity_and_cannot_reopen_original(api):
    args, _, _ = setup(api, termination=1.)
    old = args['contracts'][0]
    new = replace(old, identity='venue:A:successor', listed_at=stamp(1), settles_at=None)
    args['contracts'].append(new)
    args['prices'][new.identity] = [np.nan, 20., 22., 22.]
    args['settlements'] = [replace(args['settlements'][0], time=stamp(1))]
    args['targets'].loc[stamp(1)] = 0.
    args['targets'][new.identity] = [0., 1.]
    result = api.run_event_book(**args)
    assert result.quantities.loc[stamp(1), old.identity] == 0.
    assert result.quantities.loc[stamp(1), new.identity] == pytest.approx(44.935)
    args['targets'].loc[stamp(2), old.identity] = .1
    with pytest.raises(ValueError, match='terminated'):
        api.run_event_book(**args)


def test_quantity_step_is_explicit_and_small_targets_do_not_invent_units(api):
    args, _, _ = setup(api)
    args['contracts'] = [replace(args['contracts'][0], multiplier=10., quantity_step=.3)]
    result = api.run_event_book(**args)
    assert result.quantities.iloc[0, 0] == .3
    assert result.returns.nav.iloc[-1] == pytest.approx(939.22)


def test_initial_fee_and_drift_fee_belong_to_the_opened_period(api):
    args, _, _ = setup(api, weight=1., termination=None)
    args['initial_nav'] = 100.
    args['settlements'] = []
    args['prices'] = args['prices'].iloc[:3].copy()
    args['prices'].iloc[2] = 110.
    args['targets'].loc[stamp(1)] = 1.
    args['trade_fee'] = replace(args['trade_fee'], rate=.01)
    result = api.run_event_book(**args)
    assert result.returns.nav.tolist() == pytest.approx([109., 108.99])
    assert result.returns.net.tolist() == pytest.approx([.09, -.01/109.])
    assert result.returns.cost.tolist() == pytest.approx([.01, .01/109.])


def test_rounding_quantity_at_exact_lot_boundary_does_not_drop_a_lot(api):
    args, _, _ = setup(api, weight=.29)
    args['initial_nav'] = 100.
    args['prices'].iloc[0] = 10.
    args['contracts'] = [replace(args['contracts'][0], quantity_step=.1)]
    result = api.run_event_book(**args)
    assert result.quantities.iloc[0, 0] == 2.9


def test_event_ledger_exposes_incoming_settlement_units_and_cash_basis(api):
    args, _, _ = setup(api)
    result = api.run_event_book(**args)
    settlement = result.ledger[result.ledger.kind == 'settlement'].iloc[0]
    assert settlement.quantity_before == 5.
    assert settlement.quantity == 0.
    assert settlement.price == 80.
    assert settlement.multiplier == 1.


def test_boundary_price_provenance_is_required_and_retained(api):
    args, evidence, _ = setup(api)
    args['price_evidence'] = None
    with pytest.raises(ValueError, match='price.*evidence'):
        api.run_event_book(**args)
    price_evidence = replace(evidence, reference='synthetic:boundary-price-fixture')
    args['price_evidence'] = price_evidence
    result = api.run_event_book(**args)
    assert (price_evidence.reference, price_evidence.sha256, price_evidence.kind) in result.metadata['evidence_references']


@pytest.mark.parametrize('weight,rate,expected', [(.5, -.01, 6.), (-.5, .01, 6.), (-.5, -.01, -6.)])
def test_signed_funding_uses_event_units_and_rate(api, weight, rate, expected):
    args, evidence, rounding = setup(api, weight=weight)
    args['funding'] = funding(api, args, evidence, rounding, [(.5, 0, rate, 120.)])
    assert api.run_event_book(**args).ledger.carry.sum() == expected


def test_zero_intermediate_mark_does_not_erase_short_contract_quantity(api):
    args, _, _ = setup(api, weight=-.5)
    args['prices'].iloc[1] = 0.
    result = api.run_event_book(**args)
    assert result.quantities.loc[stamp(1)].iloc[0] == -5.
    assert result.returns.nav.tolist() == pytest.approx([1499.5, 1098.7, 1098.7])


def test_input_event_list_order_cannot_override_declared_sequence(api):
    args, evidence, rounding = setup(api)
    args['funding'] = funding(api, args, evidence, rounding, [(.5, 0, .01, 120.), (1.5, 2, .2, 120.)])
    first = api.run_event_book(**args)
    args['funding'] = replace(args['funding'], events=list(reversed(args['funding'].events)))
    pd.testing.assert_frame_equal(first.returns, api.run_event_book(**args).returns)


@pytest.mark.parametrize('mutate', ['inverse', 'collateral', 'multiplier', 'quantity_step', 'fee_basis', 'rounding', 'source'])
def test_unsupported_contract_or_cash_rules_are_rejected(api, mutate):
    args, _, _ = setup(api)
    c = args['contracts'][0]
    if mutate in ('inverse', 'collateral', 'multiplier', 'quantity_step'):
        changes = {'inverse': {'payoff': 'inverse'}, 'collateral': {'collateral': 'BTC'},
                   'multiplier': {'multiplier': None}, 'quantity_step': {'quantity_step': 0.}}
        args['contracts'] = [replace(c, **changes[mutate])]
    elif mutate == 'fee_basis':
        args['settlements'] = [replace(args['settlements'][0], fee=replace(args['settlements'][0].fee, basis='quarterly_delivery'))]
    elif mutate == 'rounding':
        args['trade_fee'] = replace(args['trade_fee'], rounding=api.CashRounding(2, 'unknown'))
    else:
        args['contracts'] = [replace(c, evidence=replace(c.evidence, sha256='invalid'))]
    with pytest.raises(ValueError):
        api.run_event_book(**args)


def test_nonpositive_fully_valued_nav_fails(api):
    args, _, _ = setup(api, weight=-2.)
    args['prices'].iloc[1] = 200.
    with pytest.raises(ValueError, match='nonpositive NAV'):
        api.run_event_book(**args)


def test_continuous_reduce_only_maintenance_ignores_machine_roundoff(api):
    args, _, _ = setup(api, weight=1., termination=None)
    args['initial_nav'] = 1.
    args['settlements'] = []
    args['contracts'] = [replace(args['contracts'][0], reduce_only_at=stamp(1))]
    args['prices'].iloc[:, 0] = [.3, 3., 3., 3.]
    args['targets'].loc[stamp(1)] = 1.
    args['trade_fee'] = replace(args['trade_fee'], rate=0.)
    result = api.run_event_book(**args)
    assert result.quantities.iloc[:, 0].tolist() == pytest.approx([10/3]*4)
    assert result.returns.nav.iloc[-1] == pytest.approx(10.)
    assert len(result.ledger[result.ledger.kind == 'trade']) == 1


def test_continuous_reduce_only_tolerance_cannot_allow_a_real_increase(api):
    args, _, _ = setup(api, weight=1., termination=None)
    args['initial_nav'] = 1.
    args['settlements'] = []
    args['contracts'] = [replace(args['contracts'][0], reduce_only_at=stamp(1))]
    args['prices'].iloc[:, 0] = [.3, 3., 3., 3.]
    args['targets'].loc[stamp(1)] = 1.00000001
    args['trade_fee'] = replace(args['trade_fee'], rate=0.)
    with pytest.raises(ValueError, match='reduce.only'):
        api.run_event_book(**args)


def test_lot_sizing_does_not_sell_a_contract_due_to_nav_roundoff(api):
    args, _, _ = setup(api, weight=1., termination=None)
    args['initial_nav'] = .3
    args['settlements'] = []
    args['contracts'] = [replace(args['contracts'][0], quantity_step=1., reduce_only_at=stamp(1))]
    args['prices'].iloc[:, 0] = [.1, .3, .3, .3]
    args['targets'].loc[stamp(1)] = 1.
    args['trade_fee'] = replace(args['trade_fee'], rate=0.)
    result = api.run_event_book(**args)
    assert result.quantities.iloc[:, 0].tolist() == [3.]*4
    assert len(result.ledger[result.ledger.kind == 'trade']) == 1


def test_lot_sizing_still_floors_a_real_shortfall(api):
    args, _, _ = setup(api, weight=.99999999, termination=None)
    args['initial_nav'] = .3
    args['settlements'] = []
    args['contracts'] = [replace(args['contracts'][0], quantity_step=1.)]
    args['prices'].iloc[:, 0] = .1
    args['trade_fee'] = replace(args['trade_fee'], rate=0.)
    assert api.run_event_book(**args).quantities.iloc[0, 0] == 2.
