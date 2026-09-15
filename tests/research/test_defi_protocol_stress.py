from fractions import Fraction as F
import importlib.util
from math import isqrt
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parents[2]/'research/defi-depth-2026-09-15'
s=importlib.util.spec_from_file_location('stress_test',HERE/'protocol_stress.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
Q=1<<96
class StressTests(unittest.TestCase):
 def test_price_direction_and_common_usd_shock(self):
  self.assertEqual(p.shocked_sqrt_price(Q,1,4,operating_arbitrage_path=True),Q//2)
  self.assertEqual(p.shocked_sqrt_price(Q,4,1,operating_arbitrage_path=True),2*Q)
  self.assertEqual(p.shocked_sqrt_price(Q,F(1,2),F(1,2),operating_arbitrage_path=True),Q)
 def test_exact_integer_sqrt_inequality(self):
  for f0 in [F(1,10),F(1,3),F(7,5),F(19,7)]:
   for f1 in [F(1,2),F(3,4),F(5,2)]:
    result=p.shocked_sqrt_price(Q+13,f0,f1,operating_arbitrage_path=True)
    exact=(Q+13)**2*f0/f1
    self.assertLessEqual(result**2,exact);self.assertGreater((result+1)**2,exact)
 def test_declining_asset_accumulates_and_no_il_double_debit(self):
  args=(10**18,Q,Q//100,Q*100)
  before=p.accounting.lp_amounts(*args,mint=False)
  after=p.lp_stress_inventory(*args,F(1,4),1,operating_arbitrage_path=True)
  self.assertGreater(after['token0_base_units'],before[0]);self.assertLess(after['token1_base_units'],before[1]);self.assertEqual(after['incremental_shock_fees'],0)
  # Independent finite-range formulas for S=Q/2, a=Q/100, b=100Q.
  self.assertEqual(after['token0_base_units'],10**18*(200-1)//100)
  self.assertEqual(after['token1_base_units'],10**18*(Q//2-Q//100)//Q)
 def test_invalid_path_or_catastrophe_not_silently_priced(self):
  for factor in [0,-1,0.5,True]:
   with self.assertRaises(ValueError):p.shocked_sqrt_price(Q,factor,1,operating_arbitrage_path=True)
  with self.assertRaises(ValueError):p.shocked_sqrt_price(Q,1,1,operating_arbitrage_path=False)
  with self.assertRaises(ValueError):p.shocked_sqrt_price(p.MIN_SQRT,F(1,4),1,operating_arbitrage_path=True)
 def test_ideal_participation_distinguishes_total_and_incremental_liquidity(self):
  lower,upper=p.fixed_flow_participation_bounds(10,90)
  self.assertEqual((lower,upper),(F(9,10),F(1)))
  for historical in [90,100,1000]:self.assertLessEqual(lower,F(historical,historical+10))
if __name__=='__main__':unittest.main()
