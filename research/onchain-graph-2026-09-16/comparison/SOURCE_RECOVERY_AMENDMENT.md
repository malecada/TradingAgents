# Explicit single source-recovery allowance

The user instructed “go ahead” on September 17 after receiving the original
capture's final status and the proposed recovery of missing data. This document
authorizes the concrete engineering-policy amendment reviewed in
`RECOVERY_REVIEW.md` and frozen in `recovery-amendment.json`; a renamed family
alone would not create an allowance.

The original remaining-cohort family has prior attempts 7, cap 8 and one consumed
claim, `eth-remaining-graph-capture-20260916`. Its immutable complete terminal
record reports 563 complete source dates and 521 unavailable dates. Completion
is lifecycle closure, not full data availability. All eight graph predecessor
claims, including earlier failed/partial attempts, remain counted exactly once.
The original family definition, gate, claim, terminal record and raw stores are
unchanged. No completed or failed identity is restarted.

Exactly one new source-recovery claim is granted: cumulative prior 8, additional
allowance 1, effective cap 9. Target identity:
`eth-graph-source-recovery-20260917`. The exact 521 unavailable dates are frozen
in `recovery-cohort.json`, along with 563 dates excluded from all new capture.
Only missing source responses are eligible for HTTP. Six successful prefixes
comprising 233 responses are hash-bound for byte-identical reuse. Old failed
responses remain at their original paths and are not relabelled as successful.

The ordinary lifecycle's family/history checks remain in force for the recovery
registration. A source-specific pre-claim validator additionally checks this
certificate against the original family, original claim/terminal hashes, exact
failed calendar, new experiment contract, independent approval and cumulative
count. It rejects reuse of the certificate or a second recovery allowance for
the same terminal parent under another identity/family. The immutable original
family cap remains 8; the recovery family explicitly imports all eight claims
and binds this reviewed +1 exception, rather than resetting trial history.

The existing economic amendment helper is unsuitable here: it requires a failed
parent and an unchanged cell denominator, whereas this parent is terminal with
unavailable cells and recovery must exclude its completed dates. Its schema and
all financial rules remain unchanged. This narrowly reviewed policy exception
is source-only: no prices, labels, model predictions, economic criteria or fresh
confirmation are admitted. Financial sample exposure remains spent/exploratory.

The allowance does not authorize automatic restart, further recovery claims,
provider substitution, credentials, payment, provider contact or production
actions. An outage ends this finite attempt with explicit unavailable cells.
All evidence remains preserved for any later separately reviewed continuation.
