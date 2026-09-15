# R1-only additive admission runtime

This copy preserves the original research_amended files unchanged. The only
semantic differences are:

1. `admit` accepts only defi-depth-r1-20260915 through the exact gates-r1-v2 path.
2. Historical amendment verification uses strictly earlier UTC claim timestamps
   for that historical certificate's predecessor inventory. Equal timestamps are
   rejected. All current claims still participate in admission/history/budgets.

The old verifier counted two subsequent dated-family claims against an earlier
certificate, preventing unrelated R1 admission. No financial/source calculation,
window, budget increment or existing record is changed. The original family's
single-increment, failed-parent, immutable-invariant and review bindings remain.
The new package has separately frozen runtime hashes. No general research grant.
