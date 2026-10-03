# Source audit — September 24, 2026

The published architecture is recoverable at the conceptual/equation level. The
original cryptocurrency experiment's data identities and numerical configuration
have not been recovered. `exact_reproduction_eligible=false`. This does not block
an explicitly qualified independent implementation.

## Retained primary evidence

- Çelik and Sefer, Computational Economics 67:2055–2076 (2026), accepted March25
  2025, online April18 2025. [Publisher PDF](https://link.springer.com/content/pdf/10.1007/s10614-025-10940-1.pdf)
  retained unchanged as `sources/paper.pdf`, SHA256
  `a0d569b0dea57b7a9b728f4af9971ec8715c1df46dafa070ea25bdc8547c408f`.
  CC BY4.0, attribution to Peker Celik and Emre Sefer; license
  <https://creativecommons.org/licenses/by/4.0/>. `paper.txt` is a derived text
  extraction; the PDF controls. Algorithm1 and Figures2–4 were visually inspected,
  along with Eq1. System Poppler was used after bundled Poppler failed its GLIBC
  requirement. No scientific content was inferred from that failure.
- [First-author project](https://github.com/nebipeker/Analyzing-Transaction-Graphs-for-Price-Prediction-of-Bitcoin),
  sole advertised branch main, no advertised tags, HEAD
  `6ba8bda1dc5f4b4eca20ba64fc3beeda9ed8d570`. Full reachable history retained as
  `sources/author-history.txt`; filenames in `author-tree.txt`; 51 notebooks
  inspected statically without execution. Code-cell keyword inventory and byte
  hashes are in `notebook-static-audit.json`. No motif/MCM implementation found.
  README and project report describe BTC2010–2015 and Node2Vec/statistical models,
  with GNN development future work. The report separately states weekly
  March2011–September2013 data. Repository MIT license retained. These are related
  predecessor artifacts, not evidence of the paper's2016–2024 experiments.
- Public repository lists for `nebipeker`, `seferlab`, `ozu-mlfinbio-lab` were
  inspected. [seferlab/gnn_price](https://github.com/seferlab/gnn_price) is an
  unchanged fork with the identical HEAD, not a later implementation. API response
  retained as `sources/lab-repository.json`. Search queries included exact paper
  title/code/supplement and both authors/motif/GitHub. No experiment-linked
  supplement or original fund cohort was found. This is a bounded public search,
  not proof that no private or unindexed artifact exists. Publisher data
  availability directs readers to author request; no contact was made.
- Cited Wang et al.2023 molecular MCM has an
  [author-linked implementation](https://github.com/yifeiwang15/MotifConv), HEAD
  `c350e307a16f4ae8e517546cf8263531f77888cd`, MIT. Audited code is retained under
  `sources/cited-motifconv/` with manifest. It provides method context, not crypto
  hyperparameter evidence. Its kernel has slack nodes, an additional size scaling,
  molecular similarities and absolute score handling absent from the target
  paper; these are NOT silently inherited. Its alpha1,beta1→30,growth1.075 serve
  only as an explicitly declared independent numerical starting choice.
- Hou et al.2020, DOI10.1109/ACCESS.2020.2983953, cited for HLSTM, has a
  [public accepted manuscript](https://www.researchgate.net/publication/340304753_Hierarchical_Long_Short-Term_Memory_Network_for_Cyberattack_Detection).
  Independent reviewer inspected §III.C/Fig2/Eqs3–4: shared lower LSTM on columns
  of an11×11 reshaping of121 features, then upper LSTM on resulting128-vectors.
  A temporal4×7-day adaptation is declared, not recovered crypto code.
- WatchYourStep's [primary paper](https://arxiv.org/html/1710.09599) defines
  attention-weighted transition powers and joint graph-likelihood optimization.
  The comparator configuration records that objective rather than a generic GAT.

## Scientific discrepancies requiring decisions

1. Eq1/2: s1=edge, s2=node; Algorithm1 reverses these symbols. Argument meaning
   controls in code. Literal Algorithm1 line7 has half the outgoing compatibility
   sum. It is not generally the derivative of Eq2. The literal algorithm is the
   reconstruction path; a derivative-corrected solver would be a new named variant.
2. Algorithm1 has one row/column normalization per temperature and
   beta←beta(1+beta_r); prose describes convergence and increments. The rendered
   algorithm controls. Rectangular matrices cannot have all row/column sums1;
   only final hard injectivity is claimed. No hidden padding/slack is added.
3. Eq1's2sqrt(l1*l2) denominator means directed one-edge self matching has edge
   score0.5. Preserve it literally and count ordered aggregated edges for l.
   Eq2 and Eq1 weight terms differently: solver approximation need not maximize
   normalized similarity. Empty-edge extension is explicitly an assumption.
4. Source provider, event filtering, direction, exact attributes, pooling, horizon,
   weekly availability, optimizer, widths and seed list are missing. Config files
   label one implementation choice; no number is claimed as a recovered setting.
5.2016 start plus two-year training yields eligible tests2018–2024. The statement
   that every year2016–2024 is tested cannot be reconciled without earlier data.
6. Table1 BTC LSTM MAE32.21>RMSE32.17 and SVM34.15>33.99 violate MAE≤RMSE beyond
   displayed rounding on a common weighting. Table4 sqrt(MSE) differs from RMSE
   for whale variants; different aggregation could explain that latter discrepancy.
   BTC whale MAPE worsens13.62→13.88. Table3 GraphWave/GIN can exceed proposed
   accuracy despite the narrative. Retain every reported value without correction.
7. Table2 ETH proposed and LSTM accuracy/precision/recall imply incompatible class
   prevalences under pooled binary metrics. Fold/macro conventions might explain
   it, but are unspecified. Report named conventions separately and preserve masks.
8. The65 fund entities including25 Alameda entities lack addresses/cohort vintage.
   Exact fund coverage remains blocked. No modern list substitutes for it.
9. “P100 with52GB memory” does not specify52GB VRAM. Current inventory is15GiB
   host RAM, CPU-only PyTorch2.10.0+cu128, no usable CUDA. Capacity remains unproven.

Independent source review was performed by the read-only `source_review` reviewer;
its findings are incorporated above. No empirical byte decoding or fitting was
part of this audit. Full source acquisition and numerical reproduction remain pending.
