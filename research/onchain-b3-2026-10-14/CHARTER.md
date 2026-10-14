# Branch B3 charter — whole-graph structure and 20k motifs

Registered 2026-10-14 before any B3 data pass or outcome. Spec:
`docs/superpowers/specs/2026-10-14-onchain-b3-graph-structure-design.md`; numbers in
`config/b3.json`; rules in `gates.json`.

Question: do structural features of the full weekly ETH transaction graph (degree
inequality, connectivity, reciprocity, dense cores, centrality concentration,
clustering, address turnover) or motif features on a 20,000-address graph add
out-of-sample information to price/volume history and activity, for next-day,
next-week and 4-week targets? Development 2017-10 → 2024 (walk-forward 2019–2024);
the sealed ETH window 2025-01-06 → 2026-10-05, never read by B2, is opened once and
only for a committed, non-empty selection. Prior: B2 found no on-chain information
in activity, role flows or top-5,000 motifs.

Declared look-ahead: exchange-share features (`f4_pr_ex_share`, `f4_prv_ex_share`)
and B2's role flows use B2's static 2026 exchange-label snapshot for every year.
