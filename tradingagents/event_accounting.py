"""Explicit USDT-linear event accounting; independent of the frozen bar engine.

Inputs are admitted prices/rules, not an inference of historical venue rules.
Funding=None explicitly excludes funding. Otherwise a separately evidenced
calendar is mandatory: missing expected records are unknown, never zero.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

EVENT_ACCOUNTING_VERSION = 'linear-events-v1'
SIZING_REL_TOL = 8 * np.finfo(float).eps


@dataclass(frozen=True)
class Evidence:
    reference: str
    sha256: str
    kind: str  # synthetic, observed, or registered_model


@dataclass(frozen=True)
class CashRounding:
    places: int | None
    mode: str  # unrounded, ROUND_DOWN (toward zero), ROUND_HALF_UP, ROUND_HALF_EVEN


@dataclass(frozen=True)
class FeeRule:
    rate: float
    rounding: CashRounding
    evidence: Evidence
    basis: str = 'absolute_notional'


@dataclass(frozen=True)
class Contract:
    identity: str
    venue: str
    collateral: str
    payoff: str
    multiplier: float  # base units per contract
    quantity_step: float | None  # None explicitly models continuous sizing
    listed_at: pd.Timestamp
    settles_at: pd.Timestamp | None
    reduce_only_at: pd.Timestamp | None
    evidence: Evidence


@dataclass(frozen=True)
class SettlementEvent:
    event_id: str
    contract: str
    time: pd.Timestamp
    sequence: int
    price: float | None
    fee: FeeRule | None
    evidence: Evidence | None


@dataclass(frozen=True)
class FundingEvent:
    event_id: str
    contract: str
    time: pd.Timestamp
    sequence: int
    rate: float | None
    mark: float | None
    rounding: CashRounding | None
    evidence: Evidence | None


@dataclass(frozen=True)
class FundingCalendar:
    start: pd.Timestamp
    end: pd.Timestamp
    expected: Mapping[str, Sequence[pd.Timestamp]]
    evidence: Evidence


@dataclass(frozen=True)
class FundingInputs:
    calendar: FundingCalendar
    events: Sequence[FundingEvent]


@dataclass
class EventBookResult:
    returns: pd.DataFrame  # full end-boundary clock, returns relative to opening NAV
    quantities: pd.DataFrame  # full boundary clock, after any target trades
    ledger: pd.DataFrame  # dollar cashflows and units; no implied venue fill record
    metadata: dict


def _utc(value):
    t = pd.Timestamp(value)
    if pd.isna(t) or t.tz is None:
        raise ValueError('event clock requires explicit timezone')
    return t.tz_convert('UTC')


def _number(value, context, *, minimum=None):
    if value is None or not np.isfinite(value) or (minimum is not None and value < minimum):
        raise ValueError(f'unavailable or invalid {context}')
    return float(value)


def _evidence(value, context):
    if (not isinstance(value, Evidence) or not value.reference.strip() or
            value.kind not in {'synthetic', 'observed', 'registered_model'} or
            len(value.sha256) != 64 or any(c not in '0123456789abcdef' for c in value.sha256)):
        raise ValueError(f'unavailable {context} evidence')


def _round(value: Decimal, rule: CashRounding, context):
    if not isinstance(rule, CashRounding):
        raise ValueError(f'unavailable {context} rounding')
    if rule.places is None and rule.mode == 'unrounded':
        return float(value)
    modes = {'ROUND_DOWN': ROUND_DOWN, 'ROUND_HALF_UP': ROUND_HALF_UP, 'ROUND_HALF_EVEN': ROUND_HALF_EVEN}
    if type(rule.places) is not int or not 0 <= rule.places <= 18 or rule.mode not in modes:
        raise ValueError(f'unsupported {context} rounding')
    return float(value.quantize(Decimal(1).scaleb(-rule.places), rounding=modes[rule.mode]))


def _product(*values):
    result = Decimal(1)
    for value in values:
        result *= Decimal(str(value))
    return result


def _fee(quantity, multiplier, price, rule, context):
    if not isinstance(rule, FeeRule) or rule.basis != 'absolute_notional':
        raise ValueError(f'unavailable or unsupported {context} fee')
    _evidence(rule.evidence, context + ' fee')
    rate = _number(rule.rate, context + ' fee rate', minimum=0.)
    return _round(_product(abs(quantity), multiplier, price, rate), rule.rounding, context + ' fee')


def run_event_book(*, prices: pd.DataFrame, price_evidence: Evidence, targets: pd.DataFrame,
                   contracts: Sequence[Contract], settlements: Sequence[SettlementEvent],
                   funding: FundingInputs | None, trade_fee: FeeRule,
                   ordering: str, freq: str, initial_nav: float = 1.) -> EventBookResult:
    """Execute boundary targets with funding/settlement at actual timestamps.

    Only ``events_before_targets`` is supported and must be declared. Sequence
    explicitly orders simultaneous external events. Boundary marks then value
    all incoming units, followed by reporting and (except at the end) trading.
    Thus entry/maintenance fees belong to the interval being opened. Funding
    marks are charge bases only. No endpoint target or synthetic close is used.

    This models a linear cashflow book, not exchange margin or liquidation.
    Positivity is checked at fully valued boundaries and after target fees;
    an intrabar partially marked ledger balance is not a margin observation.
    """
    if ordering != 'events_before_targets':
        raise ValueError('unsupported boundary ordering')
    initial_nav = _number(initial_nav, 'initial NAV', minimum=0.)
    if initial_nav == 0:
        raise ValueError('nonpositive NAV')
    ix = prices.index
    if (not isinstance(ix, pd.DatetimeIndex) or ix.tz is None or len(ix) < 2 or
            not ix.is_unique or not ix.is_monotonic_increasing):
        raise ValueError('prices require a complete timezone-aware boundary clock')
    ix = ix.tz_convert('UTC')
    try:
        step = pd.tseries.frequencies.to_offset(freq).nanos
    except (ValueError, AttributeError) as error:
        raise ValueError('clock frequency must be fixed') from error
    if step <= 0 or not ix.equals(pd.date_range(ix[0], ix[-1], freq=freq)):
        raise ValueError('prices require a complete boundary clock')
    if not prices.columns.is_unique or not targets.columns.is_unique:
        raise ValueError('duplicate price/target contract identity')
    if (not isinstance(targets.index, pd.DatetimeIndex) or targets.index.tz is None or
            not targets.index.is_unique or not targets.index.is_monotonic_increasing):
        raise ValueError('targets require unique ordered timezone-aware boundaries')
    target_ix = targets.index.tz_convert('UTC')
    if not target_ix.isin(ix[:-1]).all():
        raise ValueError('targets must occur at boundary starts, excluding final boundary')

    specs = {}
    lifetimes = {}
    _evidence(price_evidence, 'boundary price')
    evidence = [price_evidence]
    for c in contracts:
        if not c.identity or c.identity in specs or not c.venue:
            raise ValueError('duplicate or missing original contract identity')
        if c.collateral != 'USDT' or c.payoff != 'linear':
            raise ValueError('unsupported collateral or payoff')
        if _number(c.multiplier, 'contract multiplier', minimum=0.) == 0:
            raise ValueError('invalid contract multiplier')
        if c.quantity_step is not None and _number(c.quantity_step, 'quantity step', minimum=0.) == 0:
            raise ValueError('invalid quantity step')
        _evidence(c.evidence, 'contract')
        listed = _utc(c.listed_at)
        end = None if c.settles_at is None else _utc(c.settles_at)
        restriction = None if c.reduce_only_at is None else _utc(c.reduce_only_at)
        if (end is not None and end <= listed) or (restriction is not None and
                (restriction < listed or (end is not None and restriction > end))):
            raise ValueError('invalid contract lifetime/restriction')
        specs[c.identity] = c
        lifetimes[c.identity] = (listed, end, restriction)
        evidence.append(c.evidence)
    if not specs or set(prices.columns) != set(specs) or not set(targets.columns) <= set(specs):
        raise ValueError('price/target identities must match original contract specifications')
    columns = list(specs)
    prices = prices.set_axis(ix).reindex(columns=columns)
    targets = targets.set_axis(target_ix).reindex(columns=columns)
    _fee(0., 1., 1., trade_fee, 'trade')
    evidence.append(trade_fee.evidence)

    # Validate structural coverage separately from values needed only while held.
    expected = {}
    if funding is not None:
        if not isinstance(funding, FundingInputs):
            raise ValueError('funding requires individual events and a complete calendar')
        cal = funding.calendar
        _evidence(cal.evidence, 'funding calendar')
        if (_utc(cal.start) > ix[0] or _utc(cal.end) < ix[-1] or set(cal.expected) != set(specs)):
            raise ValueError('funding calendar must cover full window and every contract')
        evidence.append(cal.evidence)
        for identity, stamps in cal.expected.items():
            times = [_utc(t) for t in stamps]
            if len(times) != len(set(times)) or times != sorted(times):
                raise ValueError('duplicate or unordered expected funding times')
            if any(t < ix[0] or t > ix[-1] for t in times):
                raise ValueError('expected funding outside requested window')
            for t in times:
                expected.setdefault(t, set()).add(identity)

    event_by_time = {}
    event_ids, slots, funding_keys, settlement_keys = set(), set(), set(), set()
    all_events = list(settlements) + ([] if funding is None else list(funding.events))
    for event in all_events:
        if not isinstance(event, (SettlementEvent, FundingEvent)):
            raise ValueError('unsupported event type')
        t = _utc(event.time)
        if event.contract not in specs or not ix[0] <= t <= ix[-1]:
            raise ValueError('event identity/time outside requested contract window')
        if not event.event_id or event.event_id in event_ids:
            raise ValueError('duplicate or missing event id')
        if type(event.sequence) is not int or (t, event.sequence) in slots:
            raise ValueError('unknown or ambiguous event sequence')
        event_ids.add(event.event_id)
        slots.add((t, event.sequence))
        key = (t, event.contract)
        if isinstance(event, SettlementEvent):
            if lifetimes[event.contract][1] != t or key in settlement_keys:
                raise ValueError('settlement does not match original contract termination')
            settlement_keys.add(key)
        else:
            if event.contract not in expected.get(t, ()) or key in funding_keys:
                raise ValueError('unexpected or duplicate funding event')
            funding_keys.add(key)
        event_by_time.setdefault(t, []).append(event)

    closures = {}
    for identity, (_, end, _) in lifetimes.items():
        if end is not None and ix[0] <= end <= ix[-1]:
            closures.setdefault(end, set()).add(identity)
    timeline = sorted(set(ix) | set(event_by_time) | set(expected) | set(closures))
    q = dict.fromkeys(columns, 0.)
    previous_price = dict.fromkeys(columns, np.nan)
    nav, opening_nav = initial_nav, initial_nav
    ledger, rows, quantities = [], [], []
    totals = dict(pnl=0., carry=0., fee=0., turnover=0.)

    def book(t, identity, kind, *, pnl=0., carry=0., fee=0., turnover=0.,
             event_id=None, sequence=None, quantity_before=None, price=None):
        nonlocal nav
        nav += pnl + carry - fee
        if not np.isfinite(nav):
            raise ValueError(f'nonfinite NAV at {t}')
        for key, amount in dict(pnl=pnl, carry=carry, fee=fee, turnover=turnover).items():
            totals[key] += amount
        ledger.append(dict(time=t, contract=identity, kind=kind, event_id=event_id,
            sequence=sequence, quantity_before=q[identity] if quantity_before is None else quantity_before,
            quantity=q[identity], price=price, multiplier=specs[identity].multiplier,
            pnl=pnl, carry=carry, fee=fee,
            turnover=turnover, book_nav=nav))

    for t in timeline:
        # Unknown ordering/record cannot be guessed from a same-time flat target.
        for identity in closures.get(t, ()):
            if q[identity] != 0. and (t, identity) not in settlement_keys:
                raise ValueError(f'unavailable settlement record: {identity} at {t}')
        for identity in expected.get(t, ()):
            if q[identity] != 0. and (t, identity) not in funding_keys:
                raise ValueError(f'unavailable funding record: {identity} at {t}')
        for event in sorted(event_by_time.get(t, ()), key=lambda x: x.sequence):
            identity = event.contract
            c = specs[identity]
            held = q[identity] != 0.
            if isinstance(event, SettlementEvent):
                quantity_before = q[identity]
                price = None
                pnl = fee = 0.
                if held:
                    _evidence(event.evidence, 'settlement')
                    price = _number(event.price, 'settlement price', minimum=0.)
                    fee = _fee(q[identity], c.multiplier, price, event.fee, 'settlement')
                    pnl = q[identity] * c.multiplier * (price - previous_price[identity])
                    evidence.extend([event.evidence, event.fee.evidence])
                q[identity] = 0.
                previous_price[identity] = np.nan
                book(t, identity, 'settlement', pnl=pnl, fee=fee,
                     event_id=event.event_id, sequence=event.sequence,
                     quantity_before=quantity_before, price=price)
            else:
                carry = 0.
                mark = None
                if held:
                    _evidence(event.evidence, 'funding')
                    mark = _number(event.mark, 'funding mark', minimum=0.)
                    rate = _number(event.rate, 'funding rate')
                    carry = _round(_product(-q[identity], c.multiplier, mark, rate), event.rounding, 'funding')
                    evidence.append(event.evidence)
                book(t, identity, 'funding', carry=carry, event_id=event.event_id,
                     sequence=event.sequence, price=mark)
        if t not in ix:
            continue
        marks = prices.loc[t]
        for identity in columns:
            if q[identity] != 0.:
                price = _number(marks[identity], f'held boundary price: {identity} at {t}', minimum=0.)
                pnl = q[identity] * specs[identity].multiplier * (price - previous_price[identity])
                previous_price[identity] = price
                book(t, identity, 'mark', pnl=pnl, price=price)
        if nav <= 0.:
            raise ValueError(f'nonpositive NAV at {t}')
        if t != ix[0]:
            rows.append(dict(gross=totals['pnl']/opening_nav, carry=totals['carry']/opening_nav,
                cost=totals['fee']/opening_nav, turnover=totals['turnover']/opening_nav,
                net=(nav-opening_nav)/opening_nav, nav=nav))
            opening_nav = nav
            totals = dict.fromkeys(totals, 0.)
        if t in targets.index and not targets.loc[t].isna().all():
            weights = targets.loc[t].fillna(0.)
            if not np.isfinite(weights).all():
                raise ValueError(f'nonfinite target at {t}')
            pretrade_nav = nav
            for identity in columns:
                c = specs[identity]
                weight = weights[identity]
                listed, end, restriction = lifetimes[identity]
                if weight != 0. and (t < listed or (end is not None and t >= end)):
                    raise ValueError(f'unlisted or terminated original contract: {identity} at {t}')
                desired = 0.
                if weight != 0.:
                    price = _number(marks[identity], f'target price: {identity}', minimum=0.)
                    if price == 0.:
                        raise ValueError('zero price cannot size a nonzero target')
                    desired_decimal = _product(weight, pretrade_nav) / _product(price, c.multiplier)
                    desired = float(desired_decimal)
                    if c.quantity_step is not None:
                        ratio = abs(desired_decimal) / Decimal(str(c.quantity_step))
                        nearest = ratio.to_integral_value(rounding=ROUND_HALF_EVEN)
                        # The preceding NAV is floating point. Snap only within
                        # its numerical resolution, then apply the lot floor.
                        tolerance = Decimal(str(SIZING_REL_TOL)) * max(Decimal(1), abs(ratio))
                        if abs(ratio-nearest) <= tolerance:
                            ratio = nearest
                        lots = ratio.to_integral_value(rounding=ROUND_DOWN)
                        desired = float(lots * Decimal(str(c.quantity_step))) * np.sign(desired)
                if restriction is not None and t >= restriction and desired != 0.:
                    # Continuous targets can differ solely through binary NAV
                    # arithmetic. No absolute tolerance: tiny real positions
                    # receive the same strict relative test as large ones.
                    if (c.quantity_step is None and desired*q[identity] > 0. and
                            abs(desired-q[identity]) <= SIZING_REL_TOL*max(abs(desired), abs(q[identity]))):
                        desired = q[identity]
                    if desired*q[identity] <= 0. or abs(desired) > abs(q[identity]):
                        raise ValueError(f'reduce-only quantity increase: {identity} at {t}')
                delta = desired - q[identity]
                if delta != 0.:
                    quantity_before = q[identity]
                    price = _number(marks[identity], f'trade price: {identity}', minimum=0.)
                    fee = _fee(delta, c.multiplier, price, trade_fee, 'trade')
                    turnover = abs(delta) * c.multiplier * price
                    q[identity] = desired
                    previous_price[identity] = price if desired != 0. else np.nan
                    book(t, identity, 'trade', fee=fee, turnover=turnover,
                         quantity_before=quantity_before, price=price)
            if nav <= 0.:
                raise ValueError(f'nonpositive postfee NAV at {t}')
        quantities.append(q.copy())
    returns = pd.DataFrame(rows, index=ix[1:])
    refs = sorted({(e.reference, e.sha256, e.kind) for e in evidence})
    metadata = dict(accounting_version=EVENT_ACCOUNTING_VERSION, ordering=ordering,
        funding_policy='excluded' if funding is None else 'event_calendar',
        evidence_references=refs, evidence_kinds=sorted({e.kind for e in evidence}),
        admission='caller-supplied; provenance references are not source authentication',
        margin_model='excluded', sizing_relative_tolerance=SIZING_REL_TOL)
    returns.attrs.update(metadata)
    return EventBookResult(returns, pd.DataFrame(quantities, index=ix, columns=columns),
        pd.DataFrame(ledger, columns=['time', 'contract', 'kind', 'event_id', 'sequence',
                                    'quantity_before', 'quantity', 'price', 'multiplier',
                                    'pnl', 'carry', 'fee', 'turnover', 'book_nav']), metadata)
