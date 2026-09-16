# Matched Ethereum direction comparison — preparation v1

Status: pre-outcome engineering design. No empirical run is admitted or claimed.
The user's September 16 approval authorizes preparation and execution once the
source, retention and lifecycle prerequisites below are resolved. The user
subsequently authorized bounded pulls and supplied the mounted Data partition
at /home/malecada/Data (164.1 GiB available at discovery);
CAPTURE_CHARTER.md freezes the first tranche with free-space protection.
This document freezes the proposed comparison; any change before
admission must retain its version and reason. An executable registration must
bind this document, configuration, all runner dependencies and admitted inputs
before price labels or model outcomes are opened.

## Question and scope

Does a small fixed family of temporal-motif summaries improve next-day ETH/USDT
spot direction forecasts beyond past market information and ordinary on-chain
activity, using identical observations, learner settings and training rules?
This is conditional retrospective information-content research, not a trading
strategy, untouched confirmation or replication of the paper's neural model.
The existing one-day motif observation informed the feature family; that
selection is disclosed. A negative result applies to these summaries and rules,
not every graph representation.

## Target and clocks

One decision is dated D at 00:00 UTC. The binary label is one when the Binance
ETHUSDT spot daily opening price at D+1 exceeds that at D, otherwise zero;
equal prices belong to zero. Label interval is [D,D+1 day). The opening-price
endpoint is a statistical target, not a claim of an executable fill at midnight.
No label or current opening price is a feature. Market inputs use complete UTC
daily bars and quote volume, with finite positive prices and nonnegative volume.

Features for D use source day D−2 or older, consistently in every arm. A graph
day [S,S+1 day) has assumed availability S+2 days (24 hours after day end).
Market bars have assumed availability S+1 day+5 minutes; this also excludes
the immediately preceding bar at a midnight decision. A feature's clock is
the maximum availability of every input in its trailing window. Actual admitted
availability may be later, never earlier than the declared floor. A later
clock excludes the observation for all arms; no carry-forward or date shifting.

These are explicit assumed reporting delays, not evidence that the historical
archive existed then. Graph objects were rewritten in 2025 and historical
publication/vintage is unverified. Neither the lag nor chronology tests remove
that qualification. A prospective data collection would be necessary for a
historically executable availability claim.

## Fixed feature sets

All rolling windows use consecutive calendar days, include the source day and
require every input. No imputation, feature selection, standardization, tuning
or alternative lag search is permitted.

| Arm | Features added |
|---|---|
| M0 | Close-to-close log returns over 1, 7 and 30 days; population standard deviation of daily log returns over 7 and 30 days; log(1+quote volume); log((1+current quote volume)/(1+trailing 7-day mean quote volume)). |
| M1 | For each of eligible transfer events, incident addresses and distinct directed pairs: log(1+count) and log((1+count)/(1+trailing 7-day mean count)). |
| M2 | For each of unique star, dyad and triangle occurrences: log(1+count) and count/(1+eligible events); plus fraction of overlap addresses with a nonzero Local40 role. |

Graph definitions inherit the reviewed native top-level successful positive
transfer graph, exact sentinel normalization, integer-second chain ordering and
inclusive one-hour triple span. Completion-day attribution includes the prior
hour and uses the last event's day. Unique stars are the sum of roles 0–23,
dyads half the sum of roles 24–31, triangles one third of roles 32–39. Role
conservation, nonnegative integer counts and denominator consistency must pass.
An empty overlap-address denominator yields a missing feature and common-row
exclusion; it is never silently converted to a zero fraction.
DOUBLE transfer value supplies eligibility only, never exact value accounting.
Static count features already available from the same graph are the M1 control.

## Sample and fitting

Raw market bars: December 1, 2021 through January 1, 2025 inclusive, to supply
warmup and the final target endpoint. Graph source days: January 1, 2022 through
December 30, 2024, plus December 31, 2021 overlap and December 31, 2024 closing
blocks as needed for complete day-boundary integrity. Existing inventory covers
2022–2024; the earlier overlap is an additional source-admission requirement.
Decisions begin January 9, 2022 after graph warmup; calendar end is January 1,
2025 exclusive. Missing required days remain explicit, never silently replaced.

Twelve predeclared test folds cover each calendar month of 2024, with expanding
training on all admitted earlier decisions from January 9, 2022. At each month
start, training label_end must be no later than fold start minus one day. This
purges the most recent label and accommodates reporting latency. No fitting
within a month and no early stopping. Thus the initial training period is nearly
two years and grows; this is not the paper's exact split. No validation set is
used because all model settings are fixed without outcome-driven tuning.

Every arm uses the same finite-row mask, folds, labels and LightGBM 4.6.0:
100 trees, maximum depth 3, 7 leaves, learning rate .05, minimum child samples
30, L2 penalty 1, seed 42, two threads, deterministic column-wise mode. No
hyperparameter search. The training-majority direction is an accuracy baseline;
its degenerate probabilities are reported transparently, not a competitive
probabilistic baseline. Probabilistic comparison is between M0/M1/M2.

## Outcomes and decisions

Retain all dated probabilities, labels, exclusions and training/test counts.
Report accuracy, balanced accuracy, Brier score and log loss, monthly and pooled.
Primary contrast is M2 minus M1 mean log loss (negative favours motifs). M1 minus
M0 is a secondary activity diagnostic. Other metrics are descriptive; none may
replace the primary contrast after inspection.

Estimate a paired 95% percentile interval using 2,000 moving-block bootstrap
draws, seed 42, block length 14 consecutive days. Use non-circular overlapping
blocks with starts 0 through n−14, sample blocks until n observations and truncate
the last block. All contrasts use identical sampled indices. The pooled 2024
test requires all 366 daily predictions; gaps make the primary inference
unavailable, while available-row descriptive metrics and missing dates remain
reported. Intervals are conditional on these fitted predictions and this year;
they do not represent all retraining uncertainty or establish cross-regime
generalization. Monthly descriptive differences expose concentration.

A follow-up neural experiment is supported only if the primary interval lies
entirely below zero and the M2−M1 monthly mean log loss is negative in at least
8 of 12 months. This is a single exploratory screening rule, not an adoption or
profitability threshold. Failure is inconclusive about other graph methods;
unavailable data/inference is distinct from a negative result. No performance
target from the paper is an acceptance criterion. There is no PnL, fee, funding,
portfolio, execution or convention-swap claim in this classification experiment.

## Admission and preservation still required

1. Confirm sufficient disk and a recoverable retention destination. The observed
   selected-column estimate is 130.75 GiB before optional zstd recompression;
   the single-day .74396 ratio suggests about 97.3 GiB payload only. This is not
   a capacity bound. Receipts, derived vectors, working space and backup need
   additional measured allowances. Preserve prior stores; never delete captures
   after extracting features or omit hash/integrity columns merely to fit.
2. Complete an independently reviewed continuation of the interrupted seven-day
   pilot using retained captures. Original identity remains terminal failed;
   Jan2–4 sources and Jan5 captures are reused only after verification. No motif
   panel is currently admitted. Source/continuation gates must retain exhausted
   6/6 lineage allowance and explicitly review any extension before claiming.
3. Freeze and admit bounded public spot OHLCV capture and complete graph capture,
   exact object identities, warmup boundaries, resource/disk/network ceilings,
   request receipts and independently checked manifests. Existing futures bars
   cannot silently substitute for spot. No current cache meets all spot fields.
4. Independently review model/feature timing using synthetic adversarial cases,
   then admit actual panel integrity without fitting outcomes. Commit exact
   lifecycle registration and inputs before evaluation. The future financial
   family must link all six graph predecessors and prior ETH direction exposure;
   a new family name does not reset those histories. This preparation consumes
   no empirical allowance and creates no ResearchRun claim.
5. Execute a single registered matched comparison from a fixed preserved HEAD
   under the existing 8 GiB aggregate sampled-RSS/two-CPU guard, without an
   elapsed/CPU-duration kill. Retain attempted, failed and unavailable cells.
   Independently verify predictions and inference, preserve and push reviewed
   evidence, and verify remote recovery before claiming backup.

The historical ETH 2022–2024 sample is already inspected in prior forecasting
and factor studies. See SOURCE_INVENTORY.md and the unchanged original study
STATE.md/pilot failure receipts. No fresh confirmation or validated strategy
is created by this preparation.
