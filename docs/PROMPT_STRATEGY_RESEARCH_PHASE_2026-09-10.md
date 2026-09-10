# Launch prompt: sustained crypto strategy research

This file is a prompt to paste into a new session. Saving it does not start the research phase.

---

Start a new, sustained research and development phase in this repository. The objective is to find a credible, implementable crypto strategy with positive net returns and little exposure to overall crypto prices. Run a methodical research program: investigate, formulate hypotheses, test, diagnose, learn, improve when justified, and continue. Do not stop after proposing a plan, testing one configuration, rejecting one approach, or writing a report while worthwhile work remains.

This prompt explicitly authorizes the new research phase and supersedes the previous instruction to pause after the memory checkpoint. Historical programs and their failed or unavailable outcomes remain preserved; their closed status does not prohibit a separately registered new program. No result is promised, and historical failures must not be relabeled as successes.

## 1. Recover the actual state

Start in `/home/malecada/master_thesis`. Read:

- `AGENTS.md`, `RESEARCH_LOOP_GUIDE.md`, and the applicable research-governance and market-data-provenance skills.
- `TradingAgents-audit-fixes/docs/SESSION_HANDOFF_2026-09-10.md`.
- The canonical audits, current `THESIS_FINDINGS.md`, registration files, financial/correction ledgers, and closed-program/open-lead records referenced there.
- The latest dated-carry decision in `TradingAgents-audit-fixes/docs/carry-feasibility-2026-09-10/INTERPRETATION.md` and the saved factor/risk-policy findings.

Inspect the current branch and working tree before editing. Use the consolidated correction checkout and an appropriate research branch/worktree; preserve existing changes and original source/data worktrees. Verify current counts instead of blindly carrying forward memory. At the last checkpoint there were zero validated strategies, 820 financial-ledger rows, 22 explicitly deferred settlement-blocked cases, and a separate dated-carry measurement with 432 negative conditional scenarios. No strategy evaluation or paper start was pending.

## 2. Keep the objective and practical constraints explicit

- Capital is approximately $1,000 initially, potentially $10,000 if the approach works. Evaluate feasibility at both; success only at $10,000 does not establish feasibility at $1,000.
- Binance is available according to the user; Bitrue is a possible alternative. Verify actual product/account applicability instead of assuming public API access proves tradability.
- Use existing data, free public sources and available local compute. Historical settlement recovery, paid data for those blocked cases and provider contact remain deferred. Do not read credentials, contact providers, purchase resources, place real orders or change production systems.
- Research may examine other possibilities for context, but execution on additional venues or with new commitments is not assumed authorized.
- Measure full-capital net returns after realistic costs and reserves. Assess market exposure quantitatively: BTC/ETH beta with uncertainty, net/gross exposure, residual delta, stress losses, drawdown, collateral and liquidity needs. Dollar neutrality alone is insufficient.
- Report cash profit separately from opportunity cost, stablecoin/fiat conversion assumptions and any illustrative cash benchmark. Tiny gains, low activity and costs excluded from the model must be visible.
- Define justified numerical research thresholds before results, including economic relevance, uncertainty, exposure and risk. Distinguish provisional research assumptions from my investment preferences. Do not impose an arbitrary universal Sharpe floor, lower a failed gate afterward, or call an underpowered test proof of no effect.

## 3. Build a research map, then use it

Create a program charter and a finite, revisable map of plausible mechanisms, not merely a list of indicators or parameter combinations. Combine the repository's evidence with current primary research, official venue specifications and credible public data documentation. Record sources, dates, conflicts and applicability. Literature supplies hypotheses, not evidence that a trade is executable now.

For each family record the mechanism and who plausibly pays for it, earlier experiments and what they actually ruled out, remaining uncertainty, necessary data and costs, compatibility with capital/neutrality, the cheapest informative test and the evidence that would justify deeper work. Identify genuinely different hypotheses versus renamed versions of failed ones.

Rank by expected information gained, plausible economic value, data quality and implementation effort. Cover plausible breadth before concentrating on one near-miss. Re-rank after findings; neither the first backlog nor the last tested family should dictate every subsequent experiment. Reuse working infrastructure and repair only defects that materially affect the next question.

## 4. Execute a repeated learning cycle

For every research question:

1. State the economic hypothesis, its link to earlier evidence, the falsifiable prediction and competing explanations. Identify what changed if revisiting a failed family.
2. Register and commit the exact experiment under a new `gates.json` key before outcomes: inputs, universe, chronology, configurations, costs, baselines, seeds, selection rule, metrics, uncertainty/power method, multiplicity treatment, resource/attempt bounds, success/failure rules and forensics.
3. Run the cheapest informative test first. Advance to executable economics, robustness and confirmation only when preceding evidence justifies it. Do not build a large system around an unmeasured premise.
4. Check implementation and input validity, then analyze both positive and negative results. Separate mechanism failure, excessive costs, unwanted market exposure, insufficient power, unavailable data and a defective measurement. Use appropriate nulls, independent cashflow checks, planted-signal recovery, leakage probes, cost sensitivities and failure-concentration analysis. Preserve every attempted and unavailable case.
5. Write a decision record: what was learned, which explanations were weakened, what remains unknown, whether the result changes any other family, and the highest-value next action.
6. Choose and execute that action: a justified new registered experiment, a narrowly scoped engineering/data correction, advancement to the next evidence stage, deferral for a named dependency, or closure of the specified hypothesis. Update the map and immediately continue to the next eligible item.

A single failed configuration is not automatically a failed family. A negative quote snapshot does not show that an opportunity never exists. Conversely, a near-pass is not permission to keep changing parameters. A follow-up must address an evidenced failure mechanism or a distinct prediction and explain why it is more informative than switching directions. If that case cannot be made, close the question and move on. Do not force a minimum number of attempts on a demonstrably untenable premise.

Apply family-level attempt budgets cumulatively across renamed variants and child experiments. An extension needs a documented information-value justification before its new outcomes; creating another registration does not reset the family's search history or budget.

## 5. Make adaptation honest

Explicitly distinguish discovery, development and confirmation. New registered exploratory variants may use already exposed development data, labeled as such, with the complete cumulative search history retained. This does not make those data fresh or reverse an earlier verdict. Record all result-informed branches and their parent hypotheses; do not count closely related trials as independent discoveries or reset multiplicity when renaming a family.

Freeze rules and selection before genuinely unseen confirmation. Previously inspected windows and spent holdouts remain spent. If enough untouched history is unavailable, specify and collect a prospective sample; do not claim fresh evidence by rearranging old data. Handle repeated looks and sequential decisions under a predeclared valid procedure. Never keep checking a prospective result until significance appears. While one candidate waits for evidence, continue independent useful research rather than manufacturing more confirmation from the same sample.

If an LLM contributes to a trading signal or decision, respect its training cutoff and possible memorization of historical outcomes; ordinary chronological train/test splits do not remove that leakage.

## 6. Preserve the repaired accounting and data standards

Use explicit cash/base quantities or valid simple-return accounting. Never book log returns as arithmetic trading PnL; retain the required convention-swap diagnostic solely as a forensic check. Include actual instrument identity, timing, lot limits, bid/ask execution, fees, funding or settlement, spot principal, collateral, cash wallets and all material economic legs.

Do not zero-fill unknown funding, substitute last closes for unknown settlements, merge different contract incarnations, drop unavailable samples silently, assume zero transfer/borrow costs when relevant, or treat public depth as realized fills. Model dependence between both legs and margin needs along the path, not just terminal wealth. Conditional assumptions stay conditional in conclusions. Keep raw responses, timestamps, hashes, source commits, transformations and denominator reconciliations. A material harness bug requires a preserved, separately registered correction of affected results, not an undocumented rerun.

## 7. Maintain continuity and use independent review

Keep concise durable files for the program charter, research map, prioritized backlog, current state, literature/evidence notes, experiment decisions and re-entry prompt. Reuse existing registries and ledgers where appropriate. Separate financial experiments from engineering checks and quote measurements. Preserve earlier records and add the required new ones.

Use parallel agents for independent literature/source checks, bounded implementation and adversarial review. Give mutations a clear owner; avoid racing shared data or ledgers. The coordinator must reconcile conflicting reviews and integrate the evidence. A candidate needs review by an agent that did not build or select it.

After each completed experiment, retain results and forensics, update findings/state, commit and back up the research branch. Save exact next actions and safe job-resumption instructions. Do not repeat a completed financial run or overwrite immutable outputs merely because context was lost.

Provide concise progress updates with the current question, finding, qualification and next action. Do not ask routine permission for authorized local research, free public-data collection, registration, implementation or testing. Ask only for a material missing preference or an external action outside these boundaries, and continue independent work meanwhile. Do not promise background work or install recurring jobs implicitly. If runtime or context limits force a checkpoint, mark the program incomplete and leave it resumable; that is not research exhaustion.

## 8. Use defensible stopping criteria

Continue until one of these conditions is established:

- **A candidate earns progression toward use:** justified economic and exposure gates pass, execution/capital assumptions are supported, independent review passes, and adequately sized untouched confirmation plus prospective paper/shadow evidence support the frozen claim. A promising backtest is only an intermediate stage. Local paper/shadow simulation without real orders can follow its committed admission protocol; production changes or real capital require separate explicit authorization. Report what has been validated and its limits, not a guarantee of future profits.
- **The feasible research space is exhausted under stated constraints:** every materially plausible family in the maintained map has an evidence-backed disposition, justified follow-ups have been addressed, and a final independent coverage review finds no affordable informative gap. Explain the covered domain and exclusions; do not claim that every conceivable strategy has been disproved. Identify which changes in data, costs, access, capital or waiting time could reopen a question.
- **All useful progress is blocked:** record the exact missing input, resource or future observation; distinguish deferred from rejected; preserve a concrete resumption plan. Do not idle-spin or repeatedly restate the same blocker.

Do not declare completion merely because the first idea failed, a shortlist ended, a session became long or a report was written. Do not continue indefinitely by inventing cosmetic variants either. Thoroughness means covering meaningful alternatives and resolving uncertainties, not accumulating the largest number of backtests.

Begin now: recover the evidence, establish the new program and ranked map, select the first justified question, commit its registration and carry out the first bounded investigation. Then follow the results into the next eligible action without waiting for me to repeatedly say “continue.”
