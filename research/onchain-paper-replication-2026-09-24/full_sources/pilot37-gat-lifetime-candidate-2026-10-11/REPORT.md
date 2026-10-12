# GAT local-lifetime candidate — UNINSTALLED_UNQUALIFIED

The candidate is an exact copy of the current streamed GAT source, with one
added statement after scalar attention formation and before weighted aggregation:

```python
del clean, source_score, target_score, e, maximum, numer, denom
```

The source of the comparison is the genuine unchanged
`tradingagents/research/onchain_replication/streamed_gat.py`, SHA
e8355dc4443dc40b64fe2fd0d22f764d47280c655f921e9f1705042e348ec21f,
in source freeze998d353d86d683e8a095ebffb4e539a5c849ca68.
`streamed_gat_candidate.py` is an uninstalled evidence copy. Live source, gates,
claims, runtime selection, Git and STATE were not changed. The earlier memory
investigation directory was not modified.

The original equations, tensor inputs, reductions, order, heads, precision,
block size selection, first-order gradients, dropout/RNG behavior, module
parameters and checkpoint policy are textually unchanged. Only references to
seven no-longer-used forward locals are dropped earlier. Autograd can retain
underlying buffers; no memory reduction, parity result or capacity is claimed.
Numerical correctness and performance remain unqualified.

`LITERAL_PATCH01.diff` contains the one-line forward patch;
`INVERSE_PATCH01.diff` contains its inverse. `PREPARATION01.json` pins source and
candidate bytes. A bounded stdlib AST inspection confirmed that removing the
single added Delete node reconstructs the original AST exactly and that the
test file parses. `STATIC_CHECK01.json` records only those static checks.
No NumPy, SciPy, Torch or project numerical modules were imported or executed.

`test_candidate.py` stages16finite synthetic tests for execution by Root after
current native closure. Twelve direct layer cases cover CPUfloat32/float64,
zero/nonzero dropout, empty/directed/self edges and node masks. Four cases use
the genuine original ReplicationModel/GraphEncoder/temporal path with the fixed
model20f451, synthetic repeated graphs and both eager-streamed and explicit
non-reentrant activation-checkpointed execution. The candidate layer is selected
only during construction of the second synthetic model; the actual model source
remains the comparator and is not replaced. Actual graph payloads and labels are not read; these are small synthetic
tensors only.

The tests compare forward output, first parameter and input gradients (input
for the direct layer), Adam parameter updates and state, and exact RNG state
before/after forward/backward. C05float64(atol1e-8,rtol1e-6) and applicable
C06float32(atol1e-5,rtol1e-4) remain fixed. The checkpointed model retains the
original zero GAT dropout; nonzero dropout is only an isolated synthetic layer
stress case. Tests refuse if the unchanged-source hash no longer matches.

These tests have **not run**. Static syntax success is not numerical success,
backward replay qualification or a memory measurement. A potential later command,
only after Root confirms the current native job is closed, is:

```bash
env PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  RUN_ONLINE_TESTS=0 PYTEST_ADDOPTS= OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 \
  timeout 180 .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  --import-mode=importlib \
  research/onchain-paper-replication-2026-09-24/full_sources/pilot37-gat-lifetime-candidate-2026-10-11/test_candidate.py
```

No test is scheduled or launched by this document. Numerical success would
still require a separately bounded memory comparison and exact selected-source
integration before deployment. No new financial registration or cap increase
is proposed.
