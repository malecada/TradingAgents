# Independent design review — September 15, 2026

Reviewer: independent `research-reviewer` agent, task
`/root/broader_design_review`, requested specifically for the user's independent
review requirement. Read-only review; coordinator owned all document changes.

## Initial review, retained verbatim except file-link formatting

**Changes required before design sign-off; no financial experiment is admitted.** One material inference inconsistency needs correction. Remaining details can be resolved with investment preferences and exact preregistration.

### Blocking finding

**R1 — Power target does not match the complete adoption gate.**

The protocol requests 80% power at a true annual incremental benefit of $20/$200, while adoption also requires the observed benefit to reach $20/$200. Under the document’s normal sampling illustration, an unbiased estimate exceeds its true mean with probability 50%; the full conjunctive gate therefore cannot have 80% power at that boundary. Testing only whether the expected difference exceeds zero does not measure adoption probability.

**Impact:** A statistical power calculation could incorrectly admit confirmation as adequately powered for the actual decision.

**Required correction:** Distinguish statistical rejection power from complete-gate power. The proposed correction—evaluating joint gate power at a separately declared planning alternative above the effect thresholds—resolves this issue if the design specifies which power requirement controls admission. Include absolute profit, all required benchmark contrasts, risk and doubled-cost conditions in joint simulations; identify any component that cannot be estimated credibly. Hypothetical alternatives such as 10% absolute profit and 4% incremental benefit must remain planning assumptions, not forecasts or investment preferences.

### Nonblocking clarifications before registration

**R2 — Define development promotion separately from final adoption.**

“Qualify for confirmation” lacks an explicit eligibility rule. The preceding adoption gate includes confidence bounds, while the protocol correctly prohibits inferential validation on previously inspected data with unknown historical multiplicity.

Specify the descriptive development screening conditions, followed by the existing minimum-benefit ranking and tie-breakers. Reserve the confirmatory inference verdict for untouched evidence. Otherwise promotion could become discretionary after outcomes or inadvertently demand invalid historical inference.

**R3 — Make the simple-allocation conclusion explicit.**

H1 supplies benchmarks; only H2–H5 can enter confirmation. This is coherent for testing added policy value, but a useful simple allocation has no adoption route under a rule requiring positive benefit over every primary comparator, including itself.

Explicitly provide feasibility, risk and absolute cash-profit verdicts for the simple allocations, while reserving incremental-superiority claims for the four candidate recipes. This preserves the user’s broader objective without expanding the candidate budget.

### Assessment of other reviewed controls

The design adequately specifies whole-capital accounting, separate absolute and benchmark-relative claims, comparable cash economics, unavailable cells, inherited search history, no same-bar execution, untouched confirmation and preservation of the ongoing options study. The four-candidate/ten-benchmark/two-capital/three-cost grid is internally consistent at 84 cells per window.

Exact ancestry imports, historical allowance amendments, execution sources, cash access, inference assumptions and accepted investment preferences remain explicit admission dependencies. Their incompleteness is acknowledged rather than presented as an executable registration.

### Claims not tested

This review inspected the proposed documents, inventory, operative state and selected historical gate/report text. It did **not** independently recount all ledger records, verify every anchor hash or raw-store preservation claim, inspect market arrays, reconstruct economic results, verify current venue/account terms, check the remote options worker, validate executable accounting code, or establish statistical power. No financial experiment, registration or ledger was changed.

After R1 is corrected and R2–R3 clarified, the appropriate status is **design-ready pending investment preferences and the stated admission work**, not experiment-ready.

## Coordinator disposition

All three findings were accepted. DESIGN now specifies descriptive development
promotion and benchmark-only feasibility/absolute verdicts. PROTOCOL separates
statistical rejection power from the full decision gate and makes joint-gate
power at the hypothetical above-threshold alternative the confirmation-admission
criterion. The reviewer then read the revised sections independently.

## Follow-up verdict, verbatim

**R1–R3 resolved in the revised sections.**

- **R1:** Confirmation admission now requires ≥80% simulated joint gate power at fixed, above-threshold hypothetical alternatives. Statistical rejection power at the 2% boundary is reported separately.
- **R2:** Development promotion is explicitly descriptive, preserves all predeclared cohorts, and does not claim confidence-bound validation on spent evidence.
- **R3:** Simple allocations receive implementation, risk and absolute cash-profit reporting without requiring superiority to themselves or silently expanding the candidate budget.

**Disposition: design-ready pending investment preferences and the documented admission work; no financial experiment admitted.** This follow-up checked only the requested revisions, not empirical power or implementation.
