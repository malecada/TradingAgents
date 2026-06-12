# crypto-quant-agents New Repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the project as a brand-new private GitHub repo `crypto-quant-agents` with fresh git history (no TradingAgents fork lineage) and a fully rewritten README reflecting the current crypto multi-agent + quant-hybrid trading system.

**Architecture:** Materialize a new sibling directory from the source repo's committed tracked tree (`git archive HEAD`), rebrand three files (README, pyproject, CLAUDE.md) in that new dir, make a single root commit, and push to a new private GitHub repo via `gh`. The existing `TradingAgents/` working dir and its GitHub repo are left untouched. The Python package stays named `tradingagents` (no import refactor).

**Tech Stack:** git, GitHub CLI (`gh`), bash, Markdown, TOML.

**Source repo:** `/home/malecada/master_thesis/TradingAgents`
**New repo dir:** `/home/malecada/master_thesis/crypto-quant-agents`

---

### Task 1: Pre-flight — source repo is clean and secret-free

**Files:** none (verification only)

- [ ] **Step 1: Confirm the source working tree is clean**

Run: `cd /home/malecada/master_thesis/TradingAgents && git status --short`
Expected: empty output. If anything prints, STOP — commit or stash it first; `git archive HEAD` only captures committed state and would silently drop working-tree changes.

- [ ] **Step 2: Confirm no real secrets are tracked**

Run: `cd /home/malecada/master_thesis/TradingAgents && git ls-files | grep -E '\.env|secret|credential|\.key$|\.pem$'`
Expected: exactly two lines and nothing else —
```
.env.example
deploy/secrets/.env.hybrid.example
```
If any non-`.example` file appears, STOP and investigate before proceeding.

- [ ] **Step 3: Confirm `gh` is authenticated**

Run: `gh auth status 2>&1 | head -3`
Expected: `✓ Logged in to github.com as malecada`.

---

### Task 2: Materialize the new repo directory from the tracked tree

**Files:**
- Create: `/home/malecada/master_thesis/crypto-quant-agents/` (populated from `git archive HEAD`)

- [ ] **Step 1: Ensure the target directory does not already exist**

Run: `test ! -e /home/malecada/master_thesis/crypto-quant-agents && echo OK || echo EXISTS`
Expected: `OK`. If `EXISTS`, STOP and resolve (rename/remove the stale dir) before continuing.

- [ ] **Step 2: Create the dir and extract the committed tracked tree into it**

Run:
```bash
mkdir -p /home/malecada/master_thesis/crypto-quant-agents
cd /home/malecada/master_thesis/TradingAgents
git archive HEAD | tar -x -C /home/malecada/master_thesis/crypto-quant-agents
```
Expected: no output, exit 0.

- [ ] **Step 3: Verify the extracted tree has code but no gitignored junk**

Run:
```bash
cd /home/malecada/master_thesis/crypto-quant-agents
echo "venv: $(test -e .venv && echo PRESENT || echo absent)"
echo "data: $(test -e data && echo PRESENT || echo absent)"
echo "logs: $(test -e logs && echo PRESENT || echo absent)"
echo "tmp_output: $(test -e tmp_output.txt && echo PRESENT || echo absent)"
echo "readme: $(test -e README.md && echo present || echo MISSING)"
echo "pkg: $(test -d tradingagents && echo present || echo MISSING)"
echo "thesis: $(test -e THESIS_FINDINGS.md && echo present || echo MISSING)"
find . -type f | wc -l
```
Expected: `.venv/data/logs/tmp_output` all `absent`; `readme/pkg/thesis` all `present`; file count ~468.

---

### Task 3: Rewrite README.md in the new dir

**Files:**
- Modify (overwrite): `/home/malecada/master_thesis/crypto-quant-agents/README.md`

- [ ] **Step 1: Replace the entire README with the rebranded content**

Overwrite `/home/malecada/master_thesis/crypto-quant-agents/README.md` with EXACTLY:

````markdown
# crypto-quant-agents

**Multi-agent LLM + quantitative-hybrid trading system for cryptocurrency, with live Binance Futures execution.**

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-Apache--2.0-green)

`crypto-quant-agents` pairs a team of specialized LLM agents — market, on-chain, sentiment, and ML-prediction analysts; bull/bear researchers; an aggressive/conservative/neutral risk-debate panel; and a portfolio manager — with a hardened quantitative baseline and an optional LLM signal modulator. It trades crypto perpetual futures on Binance and ships with a full backtesting harness, a Streamlit analysis UI, and a live monitoring dashboard.

It began as a crypto adaptation of the multi-agent [TradingAgents](https://arxiv.org/abs/2412.20138) framework and grew into a standalone research codebase for a master's thesis investigating whether multi-agent LLM reasoning adds alpha on top of a strong quant baseline.

## Headline results

Master's-thesis backtests — walk-forward, out-of-sample, look-ahead controlled. Research only; not financial advice.

| Strategy | Sharpe | Return | Max DD | Window |
| --- | --- | --- | --- | --- |
| V5 MIX — 4-coin, per-coin feature routing | **+3.25** | +787% | −4.9% | 4.5-yr WF |
| V5 MIX — 8-coin expansion | +3.97 | +1053% | −4.8% | 4.5-yr WF |
| Hybrid V5 LLM modulator — ETH, Δ vs pure V5 | +1.10 | — | — | 1-yr, bootstrap CI [+0.60, +1.56] |

The quant baseline (LightGBM term-structure consensus + vol-targeted Kelly sizing + SMA trend filter) is the workhorse. The LLM modulator adds robust alpha on ETH but not universally. Full empirical record: [`THESIS_FINDINGS.md`](THESIS_FINDINGS.md).

## Architecture

Agents are organized like a trading firm and orchestrated with LangGraph:

```
Analysts (parallel)            market · on-chain · sentiment · prediction
  → Bull / Bear Researchers    structured investment debate
    → Research Manager         synthesis
      → Trader                 BUY / HOLD / SELL proposal
        → Risk Panel           aggressive / conservative / neutral debate
          → Portfolio Manager  final 5-level rating → execution
```

- **Crypto analysts** — Binance/CoinGecko OHLCV + 150+ technical indicators; on-chain metrics (funding rates, TVL, gas, stablecoin supply); multi-source sentiment (Alpha Vantage news, Reddit, Google News, macro); ML price forecasts (Random Forest / ARIMA / LightGBM, multi-horizon, pooled multi-coin).
- **Quant baseline** — V2 / V5 MIX sizing primitives in `tradingagents/strategies/`, shared by backtest and live execution.
- **Hybrid modulator** — optional LLM layer that scales the quant signal per coin.
- **Execution** — Binance Futures wrapper (testnet by default), pre-trade risk checks, SQLite trade journal, and a live monitor UI.

## Installation

Requires Python ≥ 3.10.

```bash
# with uv (recommended — uses the committed lockfile)
uv sync

# or with pip
pip install -e .
```

Provide API keys by copying the example file:

```bash
cp .env.example .env
# OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, ALPHA_VANTAGE_API_KEY, ...
# BINANCE_API_KEY / BINANCE_API_SECRET for live trading
```

## Usage

**Interactive CLI:**
```bash
tradingagents          # or: python -m cli.main
```

**Python API — single crypto analysis:**
```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config["asset_class"] = "crypto"
ta = TradingAgentsGraph(
    selected_analysts=["market", "onchain", "prediction"],
    config=config,
)
final_state, signal = ta.propagate("bitcoin", "2025-01-15")
# signal: BUY | OVERWEIGHT | HOLD | UNDERWEIGHT | SELL
```

**Quant baseline backtest (V2 / V5 MIX):**
```bash
python scripts/evaluate_models_multi.py --coins bitcoin ethereum \
    --horizons 1 3 7 14 --models lgb --output-dir data/multi_2coins_v2
python scripts/baseline_strategy_v2.py --pred-dir data/multi_2coins_v2 --symmetric
```

**Live execution (testnet by default):**
```python
from tradingagents.execution.runner import LiveRunner

runner = LiveRunner(config={
    "asset_class": "crypto",
    "execution": {"live_mode": False, "dry_run": True},
})
signal, result = runner.run_single("bitcoin")
```

**Streamlit analysis UI:** `streamlit run app.py`
**Live monitor UI + VPS deployment:** see [`deploy/`](deploy/).

## Configuration

Behavior is controlled by `.env` and the config dict in
`tradingagents/default_config.py` — `asset_class`, `llm_provider`,
`deep_think_llm` / `quick_think_llm`, analyst selection, and execution limits.
Environment-variable overrides (`LIVE_MODE`, `STOP_LOSS_PCT`, `LEVERAGE`,
`MAX_OPEN_POSITIONS`, …) support container and cloud deployment. Full reference:
[`CLAUDE.md`](CLAUDE.md).

## Repository layout

```
tradingagents/      core package — agents, dataflows, models, strategies, execution, backtesting, llm_clients
cli/                Typer CLI
scripts/            model evaluation, backtests, baseline-strategy scripts
deploy/             VPS systemd units, deploy scripts, live monitor UI
tests/              pytest suite
app.py              Streamlit analysis dashboard
THESIS_FINDINGS.md  full empirical record of thesis experiments
```

## Origin & attribution

This project began as a crypto adaptation of **TradingAgents: Multi-Agents LLM
Financial Trading Framework** (Xiao, Sun, Luo & Wang, 2024) and remains a derivative
work distributed under the upstream Apache 2.0 license.

```bibtex
@misc{xiao2025tradingagentsmultiagentsllmfinancial,
  title  = {TradingAgents: Multi-Agents LLM Financial Trading Framework},
  author = {Yijia Xiao and Edward Sun and Di Luo and Wei Wang},
  year   = {2025},
  eprint = {2412.20138},
  archivePrefix = {arXiv},
  primaryClass  = {q-fin.TR},
  url    = {https://arxiv.org/abs/2412.20138}
}
```

## License

Apache License 2.0 — see [`LICENSE`](LICENSE).

## Disclaimer

Research software built for a master's thesis. Cryptocurrency trading carries
substantial risk. Nothing in this repository is financial, investment, or trading
advice. Use at your own risk and test on paper/testnet before risking real capital.
````

- [ ] **Step 2: Verify no upstream Tauric branding survives**

Run: `cd /home/malecada/master_thesis/crypto-quant-agents && grep -iE 'tauric|wechat|discord|readme-i18n|star-history' README.md || echo CLEAN`
Expected: `CLEAN`.

- [ ] **Step 3: Verify attribution is present**

Run: `cd /home/malecada/master_thesis/crypto-quant-agents && grep -c '2412.20138' README.md`
Expected: `2` (the arXiv link in the intro + the BibTeX url).

---

### Task 4: Update pyproject.toml metadata in the new dir

**Files:**
- Modify: `/home/malecada/master_thesis/crypto-quant-agents/pyproject.toml`

- [ ] **Step 1: Rewrite the description line**

In `/home/malecada/master_thesis/crypto-quant-agents/pyproject.toml`, replace:
```toml
description = "TradingAgents: Multi-Agents LLM Financial Trading Framework"
```
with:
```toml
description = "crypto-quant-agents: multi-agent LLM + quant-hybrid cryptocurrency trading system"
```

- [ ] **Step 2: Reset the version**

In the same file, replace:
```toml
version = "0.2.3"
```
with:
```toml
version = "0.1.0"
```

Leave `name = "tradingagents"`, the `[project.scripts]` entry, and everything else unchanged (no package rename).

- [ ] **Step 3: Verify the edits**

Run: `cd /home/malecada/master_thesis/crypto-quant-agents && grep -E '^name|^version|^description' pyproject.toml`
Expected:
```
name = "tradingagents"
version = "0.1.0"
description = "crypto-quant-agents: multi-agent LLM + quant-hybrid cryptocurrency trading system"
```

---

### Task 5: Retitle CLAUDE.md in the new dir

**Files:**
- Modify: `/home/malecada/master_thesis/crypto-quant-agents/CLAUDE.md`

- [ ] **Step 1: Replace the title line**

In `/home/malecada/master_thesis/crypto-quant-agents/CLAUDE.md`, replace the first line:
```markdown
# TradingAgents (Crypto-Adapted)
```
with:
```markdown
# crypto-quant-agents
```

Leave the rest of the file unchanged — the existing intro paragraph already credits the TradingAgents origin and describes the crypto system accurately.

- [ ] **Step 2: Verify**

Run: `cd /home/malecada/master_thesis/crypto-quant-agents && head -1 CLAUDE.md`
Expected: `# crypto-quant-agents`.

---

### Task 6: Initialize fresh git history and make the root commit

**Files:**
- Create: `/home/malecada/master_thesis/crypto-quant-agents/.git/`

- [ ] **Step 1: Initialize a new repo and stage everything**

Run:
```bash
cd /home/malecada/master_thesis/crypto-quant-agents
git init -q
git add -A
```
Expected: no errors.

- [ ] **Step 2: Confirm gitignored junk did NOT get staged**

Run: `cd /home/malecada/master_thesis/crypto-quant-agents && git status --short | grep -E '\.venv|^.. data/|^.. logs/' || echo CLEAN`
Expected: `CLEAN` (the carried-over `.gitignore` excludes these; nothing to stage).

- [ ] **Step 3: Create the single root commit**

Run:
```bash
cd /home/malecada/master_thesis/crypto-quant-agents
git commit -q -m "Initial commit: crypto-quant-agents

Multi-agent LLM + quant-hybrid cryptocurrency trading system with live
Binance Futures execution. Derived from TradingAgents (arXiv:2412.20138),
Apache 2.0. Fresh history; no fork lineage.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```
Expected: commit succeeds.

- [ ] **Step 4: Verify exactly one root commit exists**

Run: `cd /home/malecada/master_thesis/crypto-quant-agents && git log --oneline && git rev-list --count HEAD`
Expected: one line of log output; count `1`.

---

### Task 7: Pre-push secret scan in the new repo

**Files:** none (verification only)

- [ ] **Step 1: Confirm only example env files are tracked**

Run: `cd /home/malecada/master_thesis/crypto-quant-agents && git ls-files | grep -E '\.env|secret|credential|\.key$|\.pem$'`
Expected: exactly —
```
.env.example
deploy/secrets/.env.hybrid.example
```
If anything else appears, STOP and remove it from the index before pushing.

- [ ] **Step 2: Spot-check example files contain no real values**

Run: `cd /home/malecada/master_thesis/crypto-quant-agents && grep -RInE 'sk-[A-Za-z0-9]{20}|AKIA[0-9A-Z]{16}' .env.example deploy/secrets/.env.hybrid.example || echo CLEAN`
Expected: `CLEAN`.

---

### Task 8: Create the private GitHub repo and push

**Files:** none (remote operation)

- [ ] **Step 1: Create the private repo from the local dir and push**

Run:
```bash
cd /home/malecada/master_thesis/crypto-quant-agents
gh repo create malecada/crypto-quant-agents \
    --private \
    --source . \
    --remote origin \
    --description "Multi-agent LLM + quant-hybrid cryptocurrency trading system with live Binance Futures execution" \
    --push
```
Expected: repo created; default branch pushed; prints the new repo URL.

- [ ] **Step 2: Verify the remote is set and the push landed**

Run:
```bash
cd /home/malecada/master_thesis/crypto-quant-agents
git remote -v
gh repo view malecada/crypto-quant-agents --json name,visibility,defaultBranchRef -q '"\(.name) \(.visibility) \(.defaultBranchRef.name)"'
```
Expected: `origin` → `github.com:malecada/crypto-quant-agents`; repo view prints `crypto-quant-agents PRIVATE main` (branch name may be `master` depending on git default — note whichever it is).

---

### Task 9: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Confirm the old repo is untouched**

Run: `cd /home/malecada/master_thesis/TradingAgents && git remote -v && git log --oneline -1`
Expected: `origin` still `github.com:malecada/TradingAgents.git`; HEAD unchanged from before this work (the spec/plan doc commits are expected; no rebrand edits landed here).

- [ ] **Step 2: Confirm the new repo tree is clean and complete**

Run:
```bash
cd /home/malecada/master_thesis/crypto-quant-agents
git status --short || true
echo "files: $(git ls-files | wc -l)"
head -1 README.md
```
Expected: clean status; ~468 files; README first line `# crypto-quant-agents`.

- [ ] **Step 3: Report the new repo URL to the user.**

---

## Self-Review

**Spec coverage:**
- Fresh history / new private repo → Tasks 2, 6, 8. ✓
- Tracked-tree-only, no junk → Task 2 (archive) + Task 6 Step 2. ✓
- Secret scan → Tasks 1 + 7. ✓
- README rewrite (research + usage, no Tauric branding, attribution) → Task 3. ✓
- pyproject description + version, package name unchanged → Task 4. ✓
- CLAUDE.md retitle → Task 5. ✓
- LICENSE kept (Apache attribution) → carried via archive, credited in README Origin. ✓
- Old repo/dir untouched → Task 9 Step 1; all edits occur in the new dir only. ✓
- Out of scope (package rename, public, VPS bot) → honored; not touched. ✓

**Placeholder scan:** No TBD/TODO; README content is complete verbatim; all commands concrete with expected output.

**Consistency:** Paths use `/home/malecada/master_thesis/crypto-quant-agents` throughout; package name `tradingagents` preserved consistently in README usage examples and pyproject; file count ~468 used consistently (Task 2 / Task 9).

**Note on branch name:** `git init` may produce `master` or `main` depending on the user's git `init.defaultBranch`. Task 8 records whichever it is rather than assuming.
