"""Read-only consolidation layer over the second multi-agent framework (family ``llm-multiagent-v2``).

The framework code lives in ``tradingagents.dossier``, ``tradingagents.agents_v2``, ``tradingagents.reader`` and
``tradingagents.compare`` plus the ``scripts/`` runners. Those files are pinned by sha256 in the run receipts under
``research_runs/llm-v2c*/claim.json`` and stay byte-identical. This package only reads them: a registry of the
registered attempts (:mod:`registry`), a check that no pinned file has changed (:mod:`pins`) and an offline replay
that recomputes each verdict from the registered inputs and compares it with the stored outputs (:mod:`replay`).
Nothing here calls a model, writes into a run directory or reads a sealed window.
"""
