# Decision 17 — minimum option buyer components fit, performance untested

The sole options-entry-20260911 completed from
b46f06a095ab7c8bbf712372780c884abec2663c after committed and remotely verified
source freeze. All15cells completed, zero unavailable; ten immutable outputs
occupy74,601bytes and retain1,337rawresponsebytes. The seven source slots ran
2026-09-11T10:52:05.702666 through10:52:12.088181UTC; capture closed at
10:52:12.751877UTC before premium/fee/size interpretation. Resource guard passed
at14.116seconds and128,741,376bytes sampled aggregate RSS. Receipt verification
and independent actual source/selection/Fraction accounting review pass.

## Exact component result

The fixed metadata/time/index recipe selected BTC-261002-77000-C and
ETH-261002-2450-C. October2 is the nearest eligible expiry to the30-day target,
about20.88days from the admitted reference; a nearer calendar date was not
invented. Eligible counts are61BTC calls of327 matching-underlying calls and
74ETH calls of288. Neither selection used premium, Greeks, spread or capital fit.
Both selected minimum quantities are0.01, exact step0.01 and unit1.

| Component | BTC call | ETH call |
|---|---:|---:|
| Best ask per quantity unit | 2,810.000 | 126.6000 |
| Minimum premium USDT | 28.10000 | 1.266000 |
| Entry including0.00024fee scenario | 28.2848640753 | 1.2719156679 |
| Entry including0.00030fee scenario | 28.3310800941 | 1.2733945849 |
| Displayed best ask quantity | 4.00 | 57.27 |

All eight combinations (asset,1,000/10,000capital,both fee assumptions) satisfy
the necessary component-fit and displayed-size conditions. The same minimum
ticket is compared with each capital amount; capital does not resize the trade.
The10% premium fee cap binds in neither scenario. Premium is ask times quantity;
unit is not multiplied into premium again. These are not actual commissions
or order fills, and option purchase is not being recommended.

Independent reconstruction checked all1,678saved metadata projections, ten
parent contracts, exact selection and request URLs/clocks, seven rawresponses,
all hashes/denominators and80exact Fraction cash/quantity assertions. Reports
are reviews/check_options_entry_actual.py and options-entry-actual-review.{json,md}.
No material defect was found. The saved metadata clock, asynchronous REST
responses, lack of a mark event clock and account applicability remain qualified.
Model Greeks do not establish true delta or an executable hedge.

## What changed and what did not

These current buyer tickets contradict a blanket claim that minimum option
premium alone must exclude a1,000USDT account. The tested component fits well
inside both capital amounts under both explicitly assumed fees. This is useful
capital information, not evidence that the complete delta-hedged strategy is
feasible or profitable. Seller opening margin, hedge collateral and lot rounding,
portfolio/netting rules, access and actual fees remain unverified. Historical
EOHSummary field/clock semantics and the earlier RVIV forecast failure are not
resolved by these current observations. No expected return, confidence interval,
power, beta, annual relevance or liquidation claim was calculated. Graduation
remains false; zero strategies are validated.

## Next justified action

The third/final initial options question is spent with its positive component
finding retained. No automatic book or paper session follows. The coverage audit
will determine whether this finding exposes another affordable prerequisite or
requires the named account/clearing/history/future-observation inputs. Do not
reject the family merely because its initial allowance is used.

Proceed with the identified two-request daily dated-mark source question after
its separately reviewed cumulative +1 extension is concrete and tested. It
supports the distinct long-dated/short-perpetual mechanism, with matched daily
valuation of both derivatives, and preserves every old dated/carry claim. The
previous repair certificate is consumed and cannot be reused. The original
frozen v1 verifier's live-ledger limitation requires explicit independently
reviewed historical snapshot verification in the additive successor; no silent
filtering or cap change is permitted. The source question does not grant a
later economic book, and absent dated marks do not erase the existing narrower
terminal-cash route. Continue meaningful research; no stopping condition is
established at this checkpoint.
