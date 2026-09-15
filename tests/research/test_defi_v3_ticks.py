"""Invented tick configuration checks; no protocol state or returns."""
from decimal import Decimal, localcontext, ROUND_CEILING
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
LOADER = importlib.util.spec_from_file_location('depth_v3_ticks', ROOT / 'research/defi-depth-2026-09-15/v3_ticks.py')
m = importlib.util.module_from_spec(LOADER)
LOADER.loader.exec_module(m)


class TickMathTest(unittest.TestCase):
    def test_official_endpoint_and_zero_vectors(self):
        self.assertEqual(m.sqrt_at_tick(-887272), 4295128739)
        self.assertEqual(m.sqrt_at_tick(0), 1 << 96)
        self.assertEqual(m.sqrt_at_tick(887272), 1461446703485210103287273052203988822378723970342)

    def test_moderate_ticks_against_high_precision_power(self):
        with localcontext() as context:
            context.prec = 100
            for tick in (-10000, -1000, -1, 1, 1000, 10000):
                independent = ((Decimal('1.0001') ** tick).sqrt() * Decimal(1 << 96)).to_integral_value(rounding=ROUND_CEILING)
                self.assertEqual(m.sqrt_at_tick(tick), int(independent))

    def test_global_monotonicity_and_relative_mathematical_error(self):
        ticks = list(range(-887272, 887273, 7919)) + [887272]
        values = [m.sqrt_at_tick(tick) for tick in ticks]
        self.assertTrue(all(a < b for a, b in zip(values, values[1:])))
        # Endpoint upward rounding is a material relative error at the tiny
        # end; separate it from the Q128 intermediate approximation.
        with localcontext() as context:
            context.prec = 100
            for tick, value in zip(ticks, values):
                exact = (Decimal('1.0001') ** tick).sqrt() * Decimal(1 << 96)
                self.assertLess(abs(Decimal(value) - exact), 1 + exact * Decimal('1e-18'))

    def test_usable_full_range_at_spacing_60(self):
        low, high = m.position_bounds(-887220, 887220, 60)
        self.assertGreater(low, m.MIN_SQRT)
        self.assertLess(high, m.MAX_SQRT)
        for a, b in ((-887272, 887220), (-887220, 887272), (60, -60), (0, 0)):
            with self.assertRaises(ValueError):
                m.position_bounds(a, b, 60)

    def test_invalid_values_rejected(self):
        for tick in (True, -887273, 887273, 1.0):
            with self.assertRaises(ValueError):
                m.sqrt_at_tick(tick)
        for spacing in (True, 0, -1, 1 << 23):
            with self.assertRaises(ValueError):
                m.position_bounds(-60, 60, spacing)


if __name__ == '__main__':
    unittest.main()
