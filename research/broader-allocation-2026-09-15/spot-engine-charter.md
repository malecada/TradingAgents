# Funded spot-account synthetic admission

Experiment allocation-spot-engine-20260915; admission5/6, parent terminal
allocation-cash-terms-20260915. Retain import179/cap189. After this fourth actual
claim usage183/189, five admission slots consumed including the original
unclaimed custody failure. One precision/selection admission, four fixed
financial recipes and one confirmation remain. No new requests:22/100 unchanged.

Question: does the narrow signed-inventory ledger correctly enforce funded
balances, all initial capital, fees, transfer conservation, missing values and
supplied causal clocks on fixed invented examples? Exactly19cases and one
engine-cases.json output, identities in spot-engine-spec.json. All amounts,
expected literal values and order are frozen in engine_admission.py before
execution. These are synthetic checks, not market returns or an economic gate.

Reuse Decimal patterns and existing lifecycle/guard. spot_book.py is additive;
no legacy engine, options source/worker or original raw store is modified.
Buys debit quote, sells debit base, fees debit their actual asset once, overspend
rejects atomically. All starting fee inventory belongs in initial USD capital.
Same-asset transfers debit source plus fee and retain an unspendable receivable
until settlement. Identity-changing CEX-to-token, bridge, wrap or redemption
routes are outside this adapter. Supplied receivable marks include access/delay;
settlement cannot create wealth by counting source and destination twice.

Every positive held quantity and receivable needs an explicit USD mark. Unknown
marks/remaining exit charges raise unavailable errors. Explicit zero is allowed
only under admitted loss/realizability evidence in an eventual book; the engine
cannot establish that evidence itself. Real losses remain in NAV. Initial capital
is not only the traded sleeve. The illustrative log diagnostic does not enter
the signed cash book. No fees are charged twice through marks plus separate
charges; caller must admit the split between executable mark and remaining costs.

Supplied UTC clocks distinguish signal close, availability, decision, execution
and timeout. Historical publication or realizable quotes are not established by
passing this syntax/ordering check. Proposed daily-bar proxy example: decision
first-day00:05, execute second-day00:00 within86100seconds; actual proxy use
still needs a separate frozen financial contract. No historical policy result
or executable strategy is produced. Full exchange filters, actual scheduler,
LP/lending/staking and inference remain outside this narrow admission.

Use pinned Python3.13.13, v2guard120seconds/512MiB/twoCPU, output at most1MiB.
Commit exact source/charter/gate/inputs before execution, metadata admission,
standard lifecycle and verifier, independent reconstruction of literal examples
and input hashes. A mismatch raises an error; any partial/failed attempt remains
charged and cannot be silently retried. Nineteen checks do not count as19alpha
trials, establish fee/access facts, or restore a spent sample.
