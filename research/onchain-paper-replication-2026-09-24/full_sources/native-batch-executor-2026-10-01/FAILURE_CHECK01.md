# Preserved check01 failure and precision correction

check01 CLOSED with one error in 244.458s, exec session31503 exit1;
PythonPID1497328 is absent. Both synthetic cells returned complete before
independent classification metric comparison rejected log_loss. The later
checkpoint/duplicate checks were not reached. No empirical trial was consumed.
Both416 original freeze and164 supplemental source hashes were verified unchanged
before the following source correction. Original test_executor.py and metrics.py
are retained with .check01 suffixes. Historical manifests retain their original
hashes and resolve the old maintained metric bytes through that snapshot or commit
945cadb05f0eabeaecb45d988d4e7c4e07f8a406, not the corrected current file.

The original416-file freeze inherited the representation dependencies but omitted
new executor/test imports. A164-file supplement was created during the active
check, verifying each byte against the already committed source. It is not a
complete pre-launch closure. Corrected check02 uses the complete union before
launch. The temporary fixture's ordinary registered package source checks were
also active; its kernel guard boundary was mocked.

A minimal arithmetic probe reproduced the cause without another fit: float32
probability0.6 is saved as0.6000000238418579. Production float32 logarithm gave
0.5108255743980408, while the independent float64 calculation on that exact saved
value gave0.5108255840295616. At float32 probability1, the frozen upper clipping
bound1-1e-15 rounded to1, yielding NaN from zero times negative infinity. Float32
labels and probabilities also reduced Brier precision. This is metric arithmetic
precision, not a model difference or evidence to relax the verification tolerance.

classification_metrics now converts validated labels and probabilities to float64
before arithmetic. Definitions, threshold, clipping bounds and verification
tolerances remain unchanged. Three new precision regressions initially produced
one failure and two errors in0.019s; corrected metric-check01 passed3 in0.014s.
The existing relevant metric/verification suite passed49 in2.49s, session70696exit0.
The red command's enclosing shell returned0 because it printed the failed log;
the preserved unittest log is the authoritative failed test disposition.

Independent initial review correctly noted check01 did not independently join
saved labels/clocks to expected examples or verify checkpoint bytes/restore.
The corrected synthetic integration adds those checks: exact expected row count,
order/labels/clocks/cell identity, completion/manifest/member hash validation,
optimizer-state presence/terminal cursor, and exact prediction parity after model
state restoration. These are new check02 assertions, not claims about check01.
No model fit or artifact is retried under a closed empirical or test identity.
