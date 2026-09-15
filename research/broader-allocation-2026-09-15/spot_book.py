"""Pure funded inventory ledger; no data acquisition, execution or strategy rules.

Keys identify (location, asset). A token asset must include chain+contract when
applicable. Decimal inputs only; no borrowed balances or external top-ups.
Prices and costs are supplied evidence, never inferred from a token symbol.
"""
from decimal import Decimal

ZERO = Decimal('0')


def amount(value):
    if not isinstance(value, (str, Decimal, int)) or isinstance(value, bool):
        raise ValueError('exact decimal string, Decimal or integer required')
    value = Decimal(value)
    if not value.is_finite():
        raise ValueError('finite value required')
    return value


def key(value):
    if not isinstance(value, tuple) or len(value) != 2 or any(not isinstance(x, str) or not x for x in value):
        raise ValueError('nonempty (location, asset) identity required')
    return value


class MissingValuation(ValueError):
    pass


class SpotBook:
    def __init__(self, initial_balances):
        self.balances = {key(k): amount(v) for k, v in initial_balances.items()}
        if any(v < 0 for v in self.balances.values()):
            raise ValueError('negative initial inventory')
        self.pending = {}
        self.used_ids = set()
        self.events = []

    def _post(self, event_id, kind, deltas):
        if not isinstance(event_id, str) or not event_id or event_id in self.used_ids:
            raise ValueError('unique nonempty event ID required')
        values = {key(k): amount(v) for k, v in deltas.items()}
        candidate = dict(self.balances)
        for k, delta in values.items():
            candidate[k] = candidate.get(k, ZERO) + delta
        if any(v < 0 for v in candidate.values()):
            raise ValueError('insufficient funded inventory; event not applied')
        self.balances = candidate
        self.used_ids.add(event_id)
        self.events.append({'id': event_id, 'kind': kind, 'deltas': values})

    @staticmethod
    def _fee(deltas, fee_key, fee):
        fee = amount(fee)
        if fee < 0:
            raise ValueError('fee must be nonnegative; rebates need a separate contract')
        fee_key = key(fee_key)
        deltas[fee_key] = deltas.get(fee_key, ZERO) - fee

    def trade(self, event_id, location, base, quote, side, quantity, price, *, fee_asset, fee):
        quantity, price = amount(quantity), amount(price)
        if base == quote or side not in ('buy', 'sell') or min(quantity, price) <= 0:
            raise ValueError('valid spot pair, side and positive quantity/price required')
        base_key, quote_key = key((location, base)), key((location, quote))
        # Gross sell inventory must exist before proceeds/fees are booked.
        if side == 'sell' and self.balances.get(base_key, ZERO) < quantity:
            raise ValueError('cannot sell an unfunded gross base quantity')
        sign = Decimal('1') if side == 'buy' else Decimal('-1')
        deltas = {base_key: sign * quantity, quote_key: -sign * quantity * price}
        self._fee(deltas, (location, fee_asset), fee)
        self._post(event_id, side, deltas)

    def charge(self, event_id, location, asset, fee):
        deltas = {}
        self._fee(deltas, (location, asset), fee)
        self._post(event_id, 'charge', deltas)

    def begin_transfer(self, event_id, source, destination, asset, quantity, *, fee_asset, fee):
        # Same-asset relocation only. CEX claims, bridges, wraps and redemption
        # change asset identity and require a separate admitted conversion book.
        quantity = amount(quantity)
        if quantity <= 0 or source == destination:
            raise ValueError('positive transfer to different location required')
        key((destination, asset))
        deltas = {(source, asset): -quantity}
        self._fee(deltas, (source, fee_asset), fee)
        self._post(event_id, 'transfer_out', deltas)
        # Quantity is the net receivable; source debits quantity PLUS fee.
        self.pending[event_id] = {'destination': destination, 'asset': asset, 'quantity': quantity}

    def settle_transfer(self, event_id, transfer_id):
        if transfer_id not in self.pending:
            raise ValueError('unknown or already settled transfer')
        transfer = self.pending[transfer_id]
        self._post(event_id, 'transfer_in', {(transfer['destination'], transfer['asset']): transfer['quantity']})
        del self.pending[transfer_id]

    def write_off(self, event_id, location, asset, quantity, *, evidence):
        if not isinstance(evidence, str) or not evidence.strip() or amount(quantity) <= 0:
            raise ValueError('positive evidenced loss required')
        self._post(event_id, 'documented_loss', {(location, asset): -amount(quantity)})
        self.events[-1]['evidence'] = evidence

    def liquidation_nav(self, marks, *, exit_cost_usd, pending_marks):
        """Marks are executable net-of-spread USD unit values before exit_cost.

        Every positive position and pending receivable needs its own admitted
        mark. Zero is allowed only as an explicit evidenced mark, not an imputed
        missing price. Known fees paid earlier are not charged again. Caller
        owns evidence for marks, zero realizability and remaining exit charges.
        Pending marks represent value of the receivable including access/delay;
        they do not authorize spending it before settlement.
        """
        total = ZERO
        for identity, quantity in self.balances.items():
            if quantity == 0:
                continue
            if identity not in marks or marks[identity] is None:
                raise MissingValuation('missing held USD mark: ' + repr(identity))
            mark = amount(marks[identity])
            if mark < 0:
                raise ValueError('negative asset liquidation mark')
            total += quantity * mark
        for transfer_id, transfer in self.pending.items():
            if transfer_id not in pending_marks or pending_marks[transfer_id] is None:
                raise MissingValuation('missing transfer valuation: ' + transfer_id)
            mark = amount(pending_marks[transfer_id])
            if mark < 0:
                raise ValueError('negative receivable liquidation mark')
            total += transfer['quantity'] * mark
        if exit_cost_usd is None:
            raise MissingValuation('unknown remaining exit costs')
        cost = amount(exit_cost_usd)
        if cost < 0:
            raise ValueError('negative exit costs')
        return total - cost


def floor_quantity(quantity, step):
    quantity, step = amount(quantity), amount(step)
    if quantity < 0 or step <= 0:
        raise ValueError('nonnegative quantity and positive lot step required')
    return (quantity // step) * step


def cash_profit(ending_nav, initial_committed_usd):
    capital = amount(initial_committed_usd)
    if capital <= 0:
        raise ValueError('positive total committed USD capital required')
    profit = amount(ending_nav) - capital
    return {'net_cash_profit_usd': profit, 'simple_net_return': profit / capital}


def check_action_clock(signal_close, known_at, decision, fill, timeout_seconds):
    """Check supplied UTC clocks; does not establish historical publication time."""
    from datetime import datetime, timezone
    def parse(value):
        if not isinstance(value, str):
            raise ValueError('ISO UTC timestamp required')
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if value.tzinfo is None or value.utcoffset().total_seconds() != 0:
            raise ValueError('UTC timestamp required')
        return value.astimezone(timezone.utc)
    close, available, choose, execute = map(parse, (signal_close, known_at, decision, fill))
    timeout = amount(timeout_seconds)
    if timeout < 0 or available < close or max(close, available) > choose or execute < choose:
        raise ValueError('noncausal action clock')
    if amount(str((execute - choose).total_seconds())) > timeout:
        raise ValueError('fill exceeds declared timeout')
    return True
