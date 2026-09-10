# Pre-result engine design review: sizing and price-stop re-entry

Review scope: existing engine and sizing source, saved-input schemas and the already committed diagnostic policy. No saved observation values, policy outcomes or financial metrics were analyzed for this review. No source was edited and no simulation was run. The parent selected the optional-hook architecture, fixed2×2 controls and explicit transition/volatility admission rules below for the forthcoming charter. Implementation still waits for committed registration.

Reviewed checkout: `3202d7982c47bb1472a8f3eb43a0851fd37b1480`.

## Recommended bounded architecture

Reuse `scripts/baseline_strategy_v2.py::run_coin_backtest` and its existing `accounting_step` calls. Add one optional target-policy object with a default of `None`; the default path must remain numerically identical to the saved baseline. Keep `positions` as the immutable saved raw target array. A small separate policy module supplies the four fixed combinations of entry-time/daily sizing and immediate/direction-blocked re-entry. Create a fresh policy instance for every configuration, sleeve and arm; state must never cross those boundaries.

The fixed arms are entry-time/immediate, daily/immediate, entry-time/new-target-episode and daily/new-target-episode. The minimal interface has two responsibilities:

1. A pre-bar decision receives the current index, saved raw target and permanent-halt flag, and returns the finite executable weight plus policy trace metadata. It must not receive the current bar's high, low, close or return. Its volatility array is prepared using the existing causal lag and exact saved decision clock.
2. Notification after an actually executed price-stop exit records the stopped exposure direction for subsequent decisions. The policy must not close positions, charge fees or calculate PnL itself.

This avoids copying the engine or reconstructing its stop dates externally. Each new arm has its own actual position, NAV, price-stop and permanent-halt path. Applying stop dates from the old baseline to another arm would be an invalid shortcut: different sizing and blocked entries can change later stops and halts.

A policy object keeps the stateful logic outside the accounting loop and allows the same pure transition tests to exercise both sizing modes. The exact pre-change engine at `3202d7982c47bb1472a8f3eb43a0851fd37b1480` should be archived before extension. Baseline compatibility must cover all144 previously saved corrected control traces and72 return-index files across the four existing cost cases, not just the36 primary traces.

## Freeze the target contract

For raw target r[i] on saved Date[i], use the same original decision index and causal volatility sigma[i]. The volatility uses Close[i−1]; do not shift the saved target or the derived volatility again. The initial Date[0] is a valuation anchor with no return. Keep the original development-reset warmup, twenty-return sample standard deviation and sqrt252 sizing convention. Do not change sizing annualization to365 while changing its update cadence.

- Entry-time sizing requests the saved target exactly when unblocked.
- Daily sizing preserves `sign(r[i])` and, when nonzero and unblocked, requests `sign(r[i]) * min(3, 0.10 * 0.5 * 3 / sigma[i])`. The fixed confidence is1. This changes when size is updated, not the signal/direction schedule or leverage/Kelly constants.
- A zero saved raw target requests zero in both modes.
- The original min-hold, adaptive early exit and volatility entry gating remain embedded in the saved target path. Do not rebuild those decisions from new PnL, actual stop episodes or raw model-signal changes. In particular, daily sizing does not add a new liquidation rule whenever the volatility percentile gate closes.

The raw target can preserve a direction after its underlying signal has gone flat or changed sign because the original hold/entry rules have not released it. Both controls must follow the saved target direction; using the raw signal instead changes an additional mechanism. The factor wrapper explicitly excludes a subsequent trend filter. The corresponding entry-only-sizing claim does not apply to other classic routes that apply that filter.

## Proposed blocked-re-entry state machine

The parent selected the following interpretation of “until the raw target goes flat or opposite” for the charter:

1. Initially `blocked_direction=0`.
2. At each new bar, a permanent portfolio halt takes precedence and requests zero forever. Neither a raw-direction reset nor a sizing change restarts a halted sleeve.
3. If a direction is blocked, inspect the **saved raw target before any policy suppression or daily resizing**. A zero raw target clears the block and remains flat for this bar. An opposite nonzero raw direction clears the block and may enter that opposite direction on this same decision date. The same raw direction remains blocked, regardless of its magnitude or elapsed time.
4. When unblocked, select the entry-time or daily-sized weight. Keep the block flag separate from the resulting executed position.
5. If this bar subsequently executes a price-stop exit, record the sign of the exposure that actually stopped. The new block first affects the following bar. There is no use of today's intrabar stop event to suppress today's opening exposure.

A flat raw-target observation therefore permits a later return to the original direction; no extra cooldown duration or minimum flat period is introduced. A model-signal flip hidden by the original min-hold/entry gates does not clear the block. A resized weight change, an executed zero caused by suppression, or an invalid sizing input does not clear it either. An opposite entry that immediately hits its own price stop establishes a new block in that opposite direction. If price and permanent portfolio stops coincide, the permanent halt dominates subsequent behavior.

A long-only raw target that never becomes flat after a stop can consequently remain blocked indefinitely. This is an intended consequence of the selected reset definition; it must not be changed after examining outcomes.

## Stop anchors and accounting order

The existing engine already protects the price-stop anchor from same-sign resizing. At [baseline_strategy_v2.py:132](/home/malecada/master_thesis/TradingAgents-audit-fixes/scripts/baseline_strategy_v2.py:132), entry price resets only for a flat-to-nonzero transition or sign change, and uses the previous close. At line191, a risk exit resets the actual previous target and entry price to zero. Preserve these conditions. Daily changes in target magnitude must not reset the3% price-stop anchor, implement a trailing stop, change to a weighted-average entry price, or reset the original target-builder's min-hold clock.

The engine also resets `entry_equity` on any target change at line130. This is a separate equity-based trade-stop channel. The fixed factor contract explicitly uses `stop_loss=1.0` and `take_profit=0`, while its price stop is3% and permanent drawdown halt15% ([factor wrapper constants](/home/malecada/master_thesis/TradingAgents-audit-fixes/scripts/audit_factor_floor_2026_09_10.py:30)). Freeze those exact settings. Do not silently use the CLI's3% equity-stop default or activate take-profit. Changing that unused channel's implementation would unnecessarily broaden this comparison.

Continue to use pretrade NAV for desired notionals, one-way charges on the actual difference from incoming marked holdings, and existing signed daily funding. A resize, sign flip and post-stop re-entry each pass once through the existing opening trade. An executed stop closes marked holdings once using the exit leg's NAV. Blocking following dates does not pay another exit charge. Keep the pre-exit peak/portfolio check, exit charges and post-exit permanent-halt check in their existing order. Do not remove a post-exit threshold crossing, omit the stopped-day funding assumption, compress flat dates, or alter the existing threshold-fill/gap convention.

## Zero and invalid volatility: explicit admission choice

Selected policy: a nonzero, unblocked daily-sizing request requires finite strictly positive sigma. Otherwise the affected arm is unavailable with its date/reason retained. Do not infer cash, reuse an old size, round or cap an undefined ratio, or pass NaN to the engine. The current engine interprets a nonfinite `positions[i]` as `target=None`, meaning retention of existing holdings ([engine](/home/malecada/master_thesis/TradingAgents-audit-fixes/scripts/baseline_strategy_v2.py:128)); that would silently change the requested control.

Zero sigma is a real possible estimator output, distinct from a missing observation, but the ratio still needs a preregistered policy. The old entry sizer returns zero at nonpositive volatility; extending that behavior to daily resizing would introduce a flatten/reopen rule. That alternative is not selected here. Zero sigma on an otherwise admitted nonzero daily request has the explicit unavailable outcome.

Known flat or permanently halted dates do not require a positive volatility estimate to prove the book is flat. Lazy policy resolution can therefore preserve legitimate warmup and cash tails without making an unneeded post-halt sizing request. Missing or malformed source prices still fail the independently frozen market-input admission; an invalid latent target must not become a manufactured zero or reset event.

## Required synthetic tests before source freeze

1. **Baseline and default parity:** unchanged API/default and explicit entry-time+immediate policy give identical complete equity/return/trace arrays on hand-derived fixtures; after registration, the baseline must match all144 saved corrected sleeve traces and72 return-index files across the four existing cost cases before any comparative result is interpreted. Preserve dates, fields, stop decisions, cash tails and costs, not merely scalar metrics.
2. **Causal sizing and fixed direction:** perturb future closes and show prior decisions unchanged; exact target/volatility date alignment; preserve raw directions, warmup, clipped size and original entry-gate behavior. A raw signal change without a saved-target change must not release a block.
3. **Stop anchor on resizing, both signs:** enter long at100, later resize with previous close102, then a low98. The original97 stop must remain unhit; resetting to98.94 would incorrectly stop. Mirror for a short. A later true stop uses the original anchor and closes the current resized holding, not the original size.
4. **Raw-direction block transitions:** same-direction requests stay blocked through magnitude changes; raw zero clears; opposite raw direction clears and enters on that date; a later original direction is eligible after a zero reset. A zero executed target from suppression must never clear its own block.
5. **Stop chronology:** a stop notification changes only the next bar; same-bar opposite-stop notification blocks its own stopped direction; price-stop-only, portfolio-only and simultaneous events preserve distinct behavior. A permanent halt cannot be released.
6. **Charges and marked holdings:** hand-derived long/short maintenance, scaling, direct flips, stop exits and next-day entries reconcile NAV=gross+signed funding−fees−impact. Each actual leg is charged once; blocked cash dates have exactly zero holdings, charges and returns. Keep the full clock.
7. **Price-anchor episode resets:** actual flat-to-entry and sign flips reset the anchor; same-sign resize does not. A block release enters from actual flat state. Policy state cannot leak across sleeves or arms.
8. **Bad inputs:** invalid raw targets, mismatched/duplicate clocks, unavailable sigma on an otherwise eligible daily request, zero sigma and legitimate warmup/flat/halted cases follow the frozen admission policy. NaN must never reach the engine's retain-holdings fallback as a requested policy decision.
9. **Provenance and denominators:** fixed18×four core policy arms and two sleeves, all unavailable records retained;72 core configuration-arm and144 core sleeve-arm records. Separately identify the72 original control return files and144 original control traces used for baseline parity; any registered additional cost diagnostics require their own explicit record counts. Input hashes, source/policy commitment, baseline-ledger integrity and immutable output namespace are checked. No old gate, original artifact or spent holdout is reopened.

## Source identities reviewed

| Source | SHA-256 |
| --- | --- |
| `scripts/baseline_strategy_v2.py` | `8de678e024c7ad7dcd63c2d5e4bbca90c2b466ec665309fee87ddf32b29e6572` |
| `tradingagents/accounting.py` | `4ed1f01dda1b17ed3fe413996413704b6810af383ac1beb4a0acfeca226d4d3c` |
| `tradingagents/strategies/v2_sizing.py` | `19c7492c36a68a45a69451cb03ca0b846649692dbbe4e389f9abe77939170e9d` |
| `scripts/audit_factor_floor_2026_09_10.py` | `c2cd3be3c8f7096e6f1311bd031d4253d720c1f329e8e80d497a6b8d33552861` |
| `tradingagents/strategies/factor_risk_diagnostics.py` | `bb4fd507d00aa2ba2c543d0d237ae50e6328213054971eaab115c0c21e6fbc21` |

No engine defect requiring an unrelated repair was identified in this bounded review. The two controls intentionally change future exposures, cashflows and stop/halt paths; their results would be retrospective policy comparisons on a previously inspected development window, not fresh strategy validation. Statistical criteria and a prospective validation plan belong in the new registration, not in the target-policy implementation.
