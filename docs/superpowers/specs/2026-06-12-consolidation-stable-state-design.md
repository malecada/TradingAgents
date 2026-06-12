# Consolidation to Stable State — Design / Runbook

Date: 2026-06-12
Repo: TradingAgents
Goal: collapse 24 local branches / 9 worktrees / 2 stashes into a single stable
`main` that equals deployed production (`live-v2.4.1`), with all unique work
preserved and dead code trimmed under a test gate.

## Framing decisions (user-approved)

1. **Target topology:** `main` becomes production (`live-v2.4.1`); archive the rest.
2. **Cleanup risk:** conservative, test-gated (only provably-dead code, behavior-preserving refactor, 187-test gate before+after each batch).
3. **Carry-sleeve branch (`fix/binance-order-timeout`):** archive as a tag; `main` stays pure production. Carry sleeve re-enters later via a proper deploy cycle.

## Ground truth (verified 2026-06-12)

- Production `live-v2.4.1` = `fix/monitor-live-holdings-v23` @ d70d17f.
- `main` @ e0bb1b2 is 0 ahead / 56 behind production → **clean fast-forward**.
- `feature/hybrid-v5-live-deploy` is fully contained in production.
- Carry sleeve (5 files), matplotlib/hmmlearn deps, §31.4b/c/§32 doc corrections live ONLY on `fix/binance-order-timeout` — NOT in prod. `min_notional` IS already in prod.
- Bot runs on the VPS at `live-v2.4.1`; making `main` = `live-v2.4.1` changes nothing for the running bot. **No redeploy.**

## Branch fate map

**Group 1 — already in `main`, delete (no archive needed):**
onchain-features-p1, pit-sentiment-p1, pit-sentiment-p2, v5-8coin-expansion,
v5-8coin-live, binance-ban-handler, c1-portfolio-weight, parity-gaps-v2.1.4,
v5-live-deploy-hotfixes, v5-parity-regen, v5-parity-warmup,
v5-rebacktest-parity-rewire, v5-rebacktest-python-path, v5-telegram-drawdown-alert.

**Group 2 — fully in production, delete:**
feature/hybrid-v5-live-deploy (0 ahead of prod), fix/monitor-live-holdings
(1 superseded commit, origin gone), fix/monitor-live-holdings-v23 (= production →
becomes `main`, then branch deleted).

**Group 3 — unique work NOT in prod, tag `archive/<name>` then delete:**
- feature/hybrid-modulator → `archive/hybrid-modulator` (§23.9/23.11)
- feature/market-analyst-v2 → `archive/market-analyst-v2` (rejected; 9 dirty files in worktree to fold first)
- feature/sentiment-analyst-v3 → `archive/sentiment-analyst-v3` (rejected, §23.12)
- feature/v5-sltp-sweep-intrabar → `archive/v5-sltp-sweep-intrabar` (§30)
- feature/v5-sltp-wf-split → `archive/v5-sltp-wf-split` (§31)
- fix/binance-order-timeout → `archive/carry-sleeve` (carry sleeve, funding fix, §31.4b/c/§32 docs)

**Keep:** `main` only.

## Loose-state triage (nothing discarded blind)

- 2 stashes on `main`: inspect; if not already landed, capture as `archive/stash-0`,
  `archive/stash-1` (commit on a detached snapshot, tag it); else drop.
- 7 dirty worktrees: fold real changes into that branch BEFORE archiving its tag;
  confirm junk before discarding. **Production worktree `hotfix-v232` has 1 dirty
  file — inspect first.** market-analyst-v2 worktree has 9.
- Untracked `catboost_info/`, `logs/` → add to `.gitignore`.

## Execution order

0. **Safety snapshot** — record all branch heads / worktrees / stashes to
   `docs/superpowers/specs/2026-06-12-consolidation-SNAPSHOT.txt`. (DONE)
1. **Triage** stashes + dirty worktrees (commit-to-branch or confirm junk).
2. **Archive** Group-3 branches + stashes as `archive/*` tags.
3. **FF `main` → `live-v2.4.1`**; checkout `main` in primary worktree; run full test suite; verify green.
4. **Remove** all worktrees except primary; **delete** every local branch except `main`.
5. **Dead-code + refactor** on `main`: scan for modules/scripts with no inbound
   refs in the live import graph; remove in approved batches; behavior-preserving
   refactor of unfinished stubs only. Test gate before+after each batch.
6. **(GATED — needs explicit go)** push FF'd `main` + `archive/*` tags to origin;
   delete the ~16 stale `origin/*` branches.

## Rollback

Every pre-change branch head is in the snapshot file and (Group 3) in `archive/*`
tags. Group 1/2 work is contained in `main`/production. Nothing is unrecoverable
until step 6 (remote deletion), which is gated on explicit approval.
