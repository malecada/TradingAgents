# Fixed synthetic custody and drift admission

Experiment `allocation-custody-20260915`, admission question1/6. No real market
input, price query, expected return, annualization or strategy ranking.
Question: how do preliminary exposure/custody arrangements compare with a descriptive
50% concentration threshold at the specified invented valuation nodes,
and are the remaining implementation terms actually established?

Inputs: frozen custody-spec.json and ancestry-crosswalk.json. The input-window
timestamp denotes only the existing authored specification, not a market sample.
All underlying legacy history remains exposed/spent under HISTORY. This synthetic
question creates no untouched economic evidence and selects no trading recipe.

Capital10,000; initial crypto fractions0,0.25,0.50,1.00; invented price factors
1.0,2.0,0.2, with no trades or transfer during a node. Crypto starts as a funded
holding; fiat cash has zero synthetic interest, fees and FX by fixture definition.
No such zeros are assumed for real economics. Three wallet architectures:

- `single_venue`: crypto and all cash lost with one venue.
- `venue_bank`: crypto at one venue, all cash at one independent bank. Complete
  loss of either custodian is included; bank insurance/recovery is not assumed.
- `venue_two_banks`: crypto at one venue; cash split equally between two
  independent banks. Each custodian can suffer complete loss; independence and
  bank availability are invented assumptions, not established account facts.

4 fractions ×3 factors ×3 architectures =36 fixed synthetic cells. Mark crypto
quantity value by the factor and preserve cash. For each, compute current NAV,
crypto exposure, each named wallet value, maximum single-wallet loss as a
fraction of current NAV, and net market loss relative to initial capital. Report
the descriptive concentration comparison at <=0.50. This is not the 30% realized drawdown
gate or the complete combined stress suite. Bank, insurance, self-custody,
correlated failures, transfer/prefund requirements and tax/FX are not established.

Keep six separate unavailable implementation cells: account/entity eligibility,
cash yield and access, custody recovery/independence, transfer/prefund timing,
actual fees/FX, and executable monthly action/depth. Total denominator42.
The user has chosen to disclose total Binance failure as a separate potential
100% loss, with50% governing market/stablecoin stress. Thus the synthetic custody
comparison is explanatory; it is not the active market/stablecoin acceptance
gate. Bank arrangements are counterfactual diagnostics, not the user setup.
These unavailable cells prevent a complete implementability pass even if all
invented structural cells at an allocation fit. More initial capital cannot
change the homogeneous loss fractions; scale and fixed-cost feasibility remain
separate questions. No numerical C_plus is justified by this diagnostic alone.

Resources: one process, two CPUs,512MiB sampled RSS,120seconds wall; zero network;
1MiB output maximum. Run through ResearchRun, immutable `custody.json`, complete
42-cell terminal denominator and separate lifecycle verifier. Parent null denotes
the new allocation decision root, not zero ancestry. Prior178/cap189 and six
admission/four development/one confirmation category limits follow ADMISSION.

Independent checks use literal wallet balances and ratios, test both sides of
the exact50% boundary, verify capital invariance, nonfinite/negative inputs and
the full denominator. No log-return convention diagnostic applies: this is a
literal hypothetical quantity/wealth calculation without trading returns.
After closure, retain source/receipt/review and advance only to the fixed source
question. A 50% sizing change is not automatically granted by any passed node.
