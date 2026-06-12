# Design: `crypto-quant-agents` (new repository + rebrand)

**Date:** 2026-06-12
**Status:** Approved (design), pending implementation plan

## Goal

The repository is still a GitHub fork of `TauricResearch/TradingAgents`, with an
upstream README that describes a stock-focused multi-agent framework. The project
has since become its own thing: a cryptocurrency multi-agent LLM trader fused with
a quant baseline (V2 / V5 MIX), an LLM signal modulator, and a live Binance Futures
deployment. Create a brand-new repository whose name and README reflect what the
project actually does now.

## Decisions (locked with user)

| Decision | Choice |
| --- | --- |
| Git history | Fresh history — single root commit, **no fork lineage** |
| Hosting | New **private** GitHub repo under `malecada/` |
| Name | `crypto-quant-agents` |
| Rename scope | **Repo + README only.** Python package stays `tradingagents` (227 importers, CLI command, entry points untouched) |
| README focus | Both research + usage |

## Approach

### 1. New repository, fresh history

- Create sibling directory `/home/malecada/master_thesis/crypto-quant-agents`.
  The existing `TradingAgents/` working dir **and** the old GitHub repo stay as-is.
- Verify `git status` is clean in the source repo (commit or stash nothing silently).
- Populate the new dir from the **committed tracked tree** only:
  `git archive HEAD | tar -x -C ../crypto-quant-agents`.
  This carries the 467 tracked files (code, tests, `THESIS_FINDINGS.md`, `uv.lock`,
  `deploy/`, `assets/`) and **excludes** every gitignored artifact
  (`.venv/`, `data/`, `logs/`, `results/`, `catboost_info/`, `tmp_output.txt`, etc.).
- `git init` in the new dir, stage everything, single root commit.
- **Secret scan** before any remote push: confirm the only env-like tracked files are
  `*.example` (`.env.example`, `deploy/secrets/.env.hybrid.example`). Real `.env`
  is gitignored and must not appear.
- `gh repo create malecada/crypto-quant-agents --private --source . --push`.

### 2. Files changed before the root commit

Everything carries as-is except:

- **`README.md`** — full rewrite (structure below).
- **`pyproject.toml`** — `description` rewritten to crypto framing; `version`
  reset `0.2.3 -> 0.1.0`. Package `name = "tradingagents"` and the
  `tradingagents = "cli.main:app"` script entry **stay** (no package rename).
- **`LICENSE`** — kept verbatim (Apache 2.0). Apache 2.0 requires attribution, so
  the README carries an **Origin** section crediting the original TradingAgents
  work (arXiv 2412.20138). The project is not a fork but is lawfully derived.
- **`CLAUDE.md`** — title/intro line de-emphasizes the "Crypto-Adapted fork"
  framing; describes the current system directly. Body unchanged.

### 3. README structure (research + usage)

1. Title + one-line tagline.
2. Minimal badges (Python version, license). No upstream marketing.
3. **What it is** — crypto multi-agent LLM trader + quant baseline (V2 / V5 MIX) +
   LLM signal modulator + live Binance Futures execution.
4. **Headline results** — table: V5 MIX Sharpe +3.25 over a 4.5-yr walk-forward;
   hybrid V5 ETH alpha Δ+1.10; live deployment status. Pointer to full findings.
5. **Architecture** — agent pipeline (analysts → researchers → trader → risk → PM),
   the crypto analyst set (market, on-chain, sentiment, prediction), the quant
   baseline, and the hybrid modulator.
6. **Installation** — `uv` and `pip` paths.
7. **Usage** — CLI, Python API (crypto analysis), backtesting, V5 baseline strategy,
   live execution, Streamlit UI, monitor UI.
8. **Configuration** — condensed env-var + config-dict reference, link to `CLAUDE.md`.
9. **Repository layout** — brief tree.
10. **Thesis findings** — pointer to `THESIS_FINDINGS.md`.
11. **Origin & attribution** — Apache 2.0 credit to TradingAgents.
12. **License**.
13. **Disclaimer** — research only, not financial advice.

Removed from the upstream README: Tauric banner image, Discord/WeChat/X/community
badges, i18n translation links, star-history widget, and the marketing intro. The
upstream BibTeX citation moves into the Origin section.

## Explicitly out of scope

- Renaming the `tradingagents` Python package / imports / CLI command.
- Public visibility (private now; can flip later).
- Any change to the live VPS bot or the old repo's `live-v*` tags — the running
  deployment is pinned to the old remote and is untouched by this work.

## Risks / notes

- `git archive HEAD` captures committed state only — any uncommitted tracked change
  in the source repo would be silently dropped. Mitigation: assert clean
  `git status` before archiving.
- The new repo inherits `uv.lock` and the full `pyproject` dependency set, so it is
  runnable immediately after `uv sync`.
- Attribution is a hard requirement, not optional polish — Apache 2.0 §4.

## Verification

- New repo builds a clean tree: `git -C ../crypto-quant-agents log` shows exactly one
  root commit; `git ls-files | wc -l` ~= 468 (the prior 467 tracked files plus this
  committed spec; edits to README/pyproject/CLAUDE.md add no new files).
- No gitignored junk present: `.venv/`, `data/`, `logs/` absent.
- No real secrets: `git ls-files | grep -E '\.env'` returns only `*.example`.
- README renders with no upstream Tauric branding and a working Origin/attribution
  section.
- `gh repo view malecada/crypto-quant-agents` reports private + pushed.
