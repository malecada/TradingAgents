### Task H2: Holdout one-shot

**Files:**
- Output (preds): `data/rebuild/preds_holdout/` (per the frozen routing)
- Output: `data/rebuild/holdout/result.json`
- Modify: `THESIS_FINDINGS.md` (append §41)

- [ ] **Step 1: Regenerate predictions through the holdout** (frozen config only, `--trade-date 2026-07-01`, `--days` extended accordingly (2063), same purge/rolling flags; `allow_holdout=True` on the ledger call — the ONLY place it is ever used). Carry: extend the C2 stressed series to 2026-07-01 with identical parameters.
- [ ] **Step 2: Run the frozen sleeves + portfolio on 2025-04-01→2026-07-01 exactly as written in `frozen_portfolio.json`.** One run. No parameter changes regardless of outcome.
- [ ] **Step 3: Evaluate the deploy gate** (gates.json `holdout_deploy`): portfolio net SR > 0.5, maxDD < 15%, each sleeve contribution ≥ 0, random-entry placebo p < 0.05 (reuse the placebo pattern from `validate_v5_mix.py` under causal convention). Write `result.json` with PASS/FAIL per criterion and per sleeve.
- [ ] **Step 4: Append THESIS_FINDINGS §41** — holdout table, gate evaluation, final verdict per sleeve, and the explicit statement of what ships to Phase 4 (possibly: carry only; possibly nothing — both are valid recorded outcomes).
- [ ] **Step 5: Commit** — `git add THESIS_FINDINGS.md data/rebuild/holdout/ && git commit -m "exp(rebuild): §41 holdout one-shot + deploy verdict"`
- [ ] **Step 6: Handoff** — Phase 4 (live integration) and Phase 5 (LLM re-test) get their own brainstorm+plan cycles seeded by `data/rebuild/holdout/result.json`.

---

