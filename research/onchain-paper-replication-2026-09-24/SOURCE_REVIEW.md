# Independent Task1 review

Read-only reviewer `source_review` independently inspected the source mathematics,
public artifact evidence and the prepared protocol. The mathematical reconstruction
is executable with prominently declared assumptions; original reproduction is not
eligible. Findings and independent source arithmetic are in SOURCE_AUDIT.md.

Protocol review reconstructed17 distinct prior claims and all34 metadata hashes,
all freeze hashes,44 printed table rows,1540 mapped cells/1400 distinct fits,
875 ETH/525 BTC paper fits,20 diagnostics, and cumulative51 claims. The beta schedule
requires48 iterations under the50 cap. F01–F20/U01–U14 all have dispositions.

Two material configuration gaps were found before fitting and corrected:

1. Frozen the20 diagnostic cell IDs and exact constant/MCM-only/GAT-only/permuted
   input paths, retained trainable blocks, dictionary reuse and label-permutation
   population. Added training-majority and last-direction zero-fit controls.
2. Frozen all neural initialization and bias/forget-gate policies, seed reset,
   and price-scaler population (unique training input dates, no duplicated lookback
   weighting or target-only/test dates, population standard deviation ddof0).

These fixes are visible in config/model.json and config/training.json and their
renewed pre-outcome freeze hashes. No empirical execution occurred. This review
does not certify implementation, actual source completeness, resource feasibility,
backup recovery or empirical numerical agreement. Each later release requires its
own independent review with exact committed source/configuration and input bindings.
