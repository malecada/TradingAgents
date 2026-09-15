# Independent protocol helper review

Reviewer: separate research-reviewer agent broader_design_review, September15.
Scope: original checkout's unfrozen protocol_math.py, authored invented-input
tests, PROTOCOL-ACCOUNTING.md and REMAINING-QUESTIONS.md. No actual financial
data, external requests, isolated live-run changes or options inspection.

## Initial review: changes required

The conversion inherited ambient Decimal precision. With invented cash10^30,
a debit1 and receipt credit1 could leave cash unchanged. This was a helper
precision-domain defect, not a real-data finding. The reviewer required exact
arithmetic or atomic rejection across the new helper's exposed operations,
preserving frozen spot_book.py.

All13initial tests passed, as did2,000independent invented LP mint/burn vectors
against exact rational inventory formulas. Fee growth used correct modular
subtraction and integer flooring; oversized fee debt was conservatively rejected.
Gross prefunded gas checks prevented transaction outputs paying their own gas.

## Re-review: pass for bounded engineering scope

The new subclass now wraps conversion, posting, trading, fees, transfer start and
settlement, write-offs and NAV in256digit local Decimal arithmetic with inexact
result traps. All16authored tests passed. Independent low-ambient-precision
transfer/settlement/write-off checks passed; unsupported-precision settlement,
write-off and NAV were rejected with full state equality. Public inherited
arithmetic coverage is complete. Construction only parses exact values; private
fee arithmetic runs within wrapped callers. The precision defect is fixed.

Source budgets reconcile:18,986reserved RPC subcalls leave6,014; documentary usage
advanced from45to46of60. The two reviewed documents retain missing exit/valuation,
LP counter-history, capacity, source-qualification and selection limits.

## Remaining caller obligations

- Integer width/order checks do not establish valid TickMath limits, spacing,
  correspondence of ticks to square-root bounds or boundary history.
- The boundary qualification flag is an assertion; source-qualified evidence
  must establish initialization/clearing/crossing semantics before use.
- Generic conversion cannot validate a protocol ratio or prevent economic
  duplication through two differently named receipt identities. Adapters must
  enforce correct identity and avoid simultaneous receipt/underlying valuation.
- Missing liquidation evidence stays unavailable. No deployed protocol,
  historical execution, capacity, cash profit or strategy is admitted by this
  engineering review.
