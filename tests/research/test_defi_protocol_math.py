"""Invented quantities only; no historical source or profitability checks."""
import importlib.util
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
LOADER = importlib.util.spec_from_file_location('protocol_math_test', ROOT / 'research/defi-depth-2026-09-15/protocol_math.py')
m = importlib.util.module_from_spec(LOADER)
LOADER.loader.exec_module(m)


class ProtocolMathTest(unittest.TestCase):
    def test_constant_price_round_trip_only_loses_rounding_dust(self):
        for price in (m.Q96 // 4, m.Q96 // 2, m.Q96, 2 * m.Q96, 4 * m.Q96):
            for liquidity in (1, 7, 10**6 + 3):
                paid = m.lp_amounts(liquidity, price, m.Q96 // 2, 2 * m.Q96, mint=True)
                got = m.lp_amounts(liquidity, price, m.Q96 // 2, 2 * m.Q96, mint=False)
                self.assertTrue(all(0 <= a - b <= 1 for a, b in zip(paid, got)))

    def test_inventory_against_independent_rational_integrals(self):
        low, high = Fraction(1, 2), Fraction(3)
        for price in (Fraction(1, 4), low, Fraction(5, 4), high, Fraction(4)):
            clipped = max(low, min(price, high))
            exact = (37 * (1 / clipped - 1 / high), 37 * (clipped - low))
            for mint in (False, True):
                got = m.lp_amounts(37, int(price * m.Q96), int(low * m.Q96), int(high * m.Q96), mint=mint)
                for integer, rational in zip(got, exact):
                    self.assertLessEqual(abs(integer - rational), 1)
                    self.assertGreaterEqual(integer - rational if mint else rational - integer, 0)

    def test_sizing_never_spends_more_than_available(self):
        for price in (m.Q96 // 3, m.Q96, 3 * m.Q96):
            for a, b in ((0, 0), (0, 19), (13, 0), (13, 19), (10**18, 10**6)):
                liquidity = m.lp_liquidity(a, b, price, m.Q96 // 2, 2 * m.Q96)
                used = m.lp_amounts(liquidity, price, m.Q96 // 2, 2 * m.Q96, mint=True)
                self.assertLessEqual(used[0], a)
                self.assertLessEqual(used[1], b)

    def test_range_endpoints_and_token_orientation(self):
        self.assertEqual(m.lp_amounts(12, m.Q96 // 2, m.Q96 // 2, 2 * m.Q96, mint=False), (18, 0))
        self.assertEqual(m.lp_amounts(12, 2 * m.Q96, m.Q96 // 2, 2 * m.Q96, mint=False), (0, 18))
        self.assertEqual(m.lp_amounts(12, m.Q96, m.Q96 // 2, 2 * m.Q96, mint=False), (6, 6))

    def test_growth_outside_range_cannot_earn_inside_fees(self):
        # Global growth100; 40earned below,30above,30inside. Outside fields
        # flip on crossings, while the same inside total stays invariant.
        self.assertEqual(m.fee_inside(100, 60, 30, -20, -10, 10, boundaries_qualified=True), 30)
        self.assertEqual(m.fee_inside(100, 40, 30, 0, -10, 10, boundaries_qualified=True), 30)
        self.assertEqual(m.fee_inside(100, 40, 70, 20, -10, 10, boundaries_qualified=True), 30)
        with self.assertRaises(ValueError):
            m.fee_inside(100, 40, 30, 0, -10, 10, boundaries_qualified=False)

    def test_fee_counter_wrap_and_single_terminal_poke(self):
        self.assertEqual(m.lp_fees(4, m.U256 - m.Q128, m.Q128, already_owed=7), 15)
        # Three sub-unit observations do not each crystallize/round fees when
        # there is only one terminal position update.
        self.assertEqual(m.lp_fees(3, 0, m.Q128 // 2), 1)
        with self.assertRaises(ValueError):
            m.lp_fees(1, 0, m.Q128, already_owed=m.Q128 - 1)

    def test_conversion_and_token_decimal_units(self):
        self.assertEqual(m.converted_units(7, 3, 2), 10)
        self.assertEqual(m.converted_units(7, 3, 2, round_up=True), 11)
        self.assertEqual(m.token_value(1_000_000, 6, Fraction(99, 100)), Fraction(99, 100))
        self.assertEqual(m.token_value(10**18, 18, Fraction(2000)), 2000)

    def test_invalid_inputs_fail_closed(self):
        bad = [lambda: m.uint(True), lambda: m.uint(-1), lambda: m.uint(1 << 256),
               lambda: m.converted_units(1, 1, 0), lambda: m.token_value(1, 6, .99),
               lambda: m.lp_amounts(1, m.Q96, 2 * m.Q96, m.Q96, mint=True),
               lambda: m.lp_amounts(1 << 127, m.Q96, m.Q96 // 2, 2 * m.Q96, mint=True),
               lambda: m.lp_liquidity(1, 1, 0, m.Q96 // 2, 2 * m.Q96)]
        for function in bad:
            with self.assertRaises(ValueError):
                function()


class ProtocolBookTest(unittest.TestCase):
    def setUp(self):
        self.cash = ('base-wallet', 'base:native-usdc:test-contract')
        self.gas = ('base-wallet', 'base:eth')
        self.receipt = ('base-wallet', 'base:lending-claim:test-contract')
        self.book = m.ProtocolBook({self.cash: '100', self.gas: '1'})

    def test_receipt_replaces_principal_without_creating_cash(self):
        self.book.convert('supply', {self.cash: '90'}, {self.receipt: '90'}, fee_key=self.gas, fee='.01', evidence='invented deposit')
        self.assertEqual(self.book.balances[self.cash], 10)
        self.assertEqual(self.book.balances[self.receipt], 90)
        self.assertEqual(self.book.balances[self.gas], Decimal('.99'))
        # Receipt's interest mark represents its value once, not a second
        # interest credit to cash while the receipt is still held.
        self.book.convert('withdraw', {self.receipt: '90'}, {self.cash: '94'}, fee_key=self.gas, fee='.02', evidence='invented redemption')
        self.assertEqual(self.book.balances[self.cash], 104)
        self.assertEqual(self.book.balances[self.receipt], 0)
        self.assertEqual(self.book.balances[self.gas], Decimal('.97'))

    def test_queue_claim_has_no_simultaneous_redemption_cash(self):
        queue = ('eth-wallet', 'eth:withdrawal-queue:request-test')
        self.book.convert('queue', {self.cash: '90'}, {queue: '1'}, fee_key=self.gas, fee='.01', evidence='invented asynchronous claim')
        self.assertEqual(self.book.balances[self.cash], 10)
        with self.assertRaises(m._spot.MissingValuation):
            self.book.liquidation_nav({self.cash: '1', self.gas: '1'}, exit_cost_usd='0', pending_marks={})

    def test_failed_conversion_is_atomic_and_revert_gas_is_separate(self):
        original = dict(self.book.balances)
        with self.assertRaises(ValueError):
            self.book.convert('too-large', {self.cash: '101'}, {self.receipt: '101'}, fee_key=self.gas, fee='.01', evidence='invented')
        self.assertEqual(self.book.balances, original)
        self.assertEqual(self.book.events, [])
        self.book.charge('reverted-tx-gas', *self.gas, '.01')
        self.assertEqual(self.book.balances[self.cash], 100)
        self.assertNotIn(self.receipt, self.book.balances)
        self.assertEqual(self.book.balances[self.gas], Decimal('.99'))

    def test_output_cannot_fund_its_own_transaction_gas(self):
        unfunded = m.ProtocolBook({self.cash: '100'})
        with self.assertRaises(ValueError):
            unfunded.convert('swap-to-gas', {self.cash: '10'}, {self.gas: '1'}, fee_key=self.gas, fee='.01', evidence='invented')
        self.assertEqual(unfunded.balances, {self.cash: Decimal(100)})

    def test_duplicate_identity_and_event_rejected(self):
        with self.assertRaises(ValueError):
            self.book.convert('same-asset', {self.cash: '10'}, {self.cash: '11'}, fee_key=self.gas, fee='0', evidence='invented')
        self.book.convert('one', {self.cash: '10'}, {self.receipt: '10'}, fee_key=self.gas, fee='0', evidence='invented')
        before = dict(self.book.balances)
        with self.assertRaises(ValueError):
            self.book.convert('one', {self.cash: '10'}, {self.receipt: '10'}, fee_key=self.gas, fee='0', evidence='invented')
        self.assertEqual(self.book.balances, before)

    def test_large_balance_debit_does_not_disappear(self):
        book = m.ProtocolBook({self.cash: str(10**30), self.gas: '1'})
        with localcontext() as context:
            context.prec = 2
            book.convert('small-debit', {self.cash: '1'}, {self.receipt: '1'}, fee_key=self.gas, fee='0', evidence='invented')
        self.assertEqual(book.balances[self.cash], Decimal(10**30 - 1))
        self.assertEqual(book.balances[self.receipt], 1)

    def test_inherited_methods_also_use_exact_domain(self):
        book = m.ProtocolBook({self.cash: str(10**30), self.gas: '1'})
        with localcontext() as context:
            context.prec = 2
            book.charge('fee', *self.cash, '1')
            book.trade('trade', self.cash[0], self.receipt[1], self.cash[1], 'buy', '1', '3', fee_asset=self.gas[1], fee='.01')
            nav = book.liquidation_nav({self.cash: '1', self.receipt: '3', self.gas: '100'}, exit_cost_usd='0', pending_marks={})
        self.assertEqual(book.balances[self.cash], Decimal(10**30 - 4))
        self.assertEqual(nav, Decimal(10**30 + 98))

    def test_unsupported_precision_rejected_without_partial_mutation(self):
        for operation in ('convert', 'charge', 'trade', 'transfer'):
            book = m.ProtocolBook({self.cash: str(10**300), self.gas: '1'})
            before = dict(book.balances)
            with self.assertRaises(ValueError):
                if operation == 'convert':
                    book.convert('too-wide', {self.cash: '1'}, {self.receipt: '1'}, fee_key=self.gas, fee='0', evidence='invented')
                elif operation == 'charge':
                    book.charge('too-wide', *self.cash, '1')
                elif operation == 'trade':
                    book.trade('too-wide', self.cash[0], self.receipt[1], self.cash[1], 'buy', '1', '1', fee_asset=self.gas[1], fee='0')
                else:
                    book.begin_transfer('too-wide', self.cash[0], 'other-wallet', self.cash[1], '1', fee_asset=self.gas[1], fee='0')
            self.assertEqual(book.balances, before)
            self.assertEqual(book.events, [])
            self.assertEqual(book.pending, {})


if __name__ == '__main__':
    unittest.main()
