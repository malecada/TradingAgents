# Independent scoped eligible-population inventory review

**The saved scoped inventory is accepted. The reusable helper needs one timing/identity correction before source integration.** Preparation manifest `23b3b5bd8a86d798c726e6b417dfcb7bd60803f19ff8bc54529d9128e53f3e6e`, inventory `df36f171066934b5464ea104fd25ab80c75205f3af06cd4b52bf071b562c6161`, helper `02aa47911f20a792760d7fd4db64cce15d9670731b89682db2e129f158c25a91`.

## Finding — P2: preserve original UTC validation and canonical week identity before reuse

`inventory01.py:12,16` injects a replacement `utc` into the extracted original calendar functions. It omits `provenance.utc:32–41`'s explicit zero-offset/timezone check. A focused counterexample makes `F['stamp']('2024-01-01T01:00:00+01:00')` return that non-UTC spelling, while the original validator raises `ValueError`. Identical function ASTs therefore do not establish identical calendar behavior.

`inventory01.py:32–33` also uses unnormalized `start_utc` strings as week keys. The original producer uses `dataset.py:76`'s `stamp(g.start_utc)` before duplicate detection. In the independent mechanical fixture, adding the same week twice with `Z` and `+00:00`, and different declared graph hashes, is accepted and produces four supported rows. Both timestamps denote the same original calendar week; the producer rejects that ambiguous population. This also allows a sole `+00:00` manifest to be counted missing when required keys use `Z`.

Minimal correction: extract/reuse and pin the original strict `provenance.utc` along with the four calendar/required-weeks functions; key each supplied graph by `F['stamp'](g['start_utc'])` before ambiguity checks and required-week joins. Retain the two small counterexamples as focused controls. The sealed saved artifact should remain unchanged. This is a source-reuse blocker, not a correction to the observed nine manifests: every inspected original graph and fixed calendar timestamp uses explicit UTC `Z`, so neither counterexample changes the saved inventory counts.

## Independently verified actual scope

Only `/home/malecada/master_thesis/TradingAgents-audit-fixes/research_artifacts/onchain-paper-replication-2026-09-24` was enumerated. The fresh snapshot matched 14430 entries, 13 manifest paths and 17347 total manifest file bytes. The nine graph manifest bodies were freshly hashed and their complete declared fields checked. The four price-capture manifest paths/extents were checked without reading their bodies, prices or labels.

There are nine distinct ETH graph-manifest paths/hashes and no BTC graph manifest in that exact scope. All 45 declared member paths are direct regular files with matching declared extents and distinct current device/inode pairs. No array body or NPY header was read or rehashed. Member hashes remain manifest declarations, and distinct file identities do not establish distinct array values, backing storage, runtime object identity or genuine scientific provenance.

The fixed calendar hash, accepted census hash and three source pins matched. Independent UTC arithmetic reconstructed all seven folds for both assets, including full candidate-day counts, original purge boundaries, required weeks, every missing/observed week and status count:

| Fold | Required weeks per asset | BTC observed | ETH observed | Complete graph-supported daily rows per asset |
|---|---:|---:|---:|---:|
| 2018 | 161 | 0 | 0 | 0 |
| 2019 | 162 | 0 | 0 | 0 |
| 2020 | 161 | 0 | 0 | 0 |
| 2021 | 161 | 0 | 0 | 0 |
| 2022 | 161 | 0 | 4 | 0 |
| 2023 | 161 | 0 | 5 | 0 |
| 2024 | 162 | 0 | 9 | 0 |

Each fold contains 1095 or 1096 daily candidates, including its one purged training-label boundary; no missing or failed cell is dropped. The one-day graph-availability lag and all 28 lookback positions were reconstructed. Zero graph-supported rows is a necessary-condition result within these observed graph artifacts. It is not a claim that historical graphs/raw data are globally absent, nor a finalized price-qualified training/test population.

## Exact next implementation requirement and limits

After correcting the helper's UTC/key seam, Root must supply a source-bound per-asset/fold disposition for the whole fixed required-week denominator and immutable price-date membership/availability tied to original price-source evidence. Produce genuine population/binding/assembly and the accepted schema3 training whitelist through the existing producer; do not synthesize train/fold/test hashes from the calendar or replace the population with nine resource weeks. Scientific representation additionally needs complete original components/terminal lineage and current genuine Owner/Binding. Those are separate from this inventory's filesystem facts.

True eligible population, price-qualified exclusion precedence, train/fold/test hashes, real consecutive batches, array-content integrity, runtime aliases, continuous writer exclusion, genuine Owner/Binding, complete representation admission, whole-population capacity and financial/paper-fit results were not tested. The scan is sampled, not an atomic filesystem snapshot. No raw-store/global-disk census, scientific imports, array/price/label decoding, numerical jobs, claim/ledger/registration edits, Main/CAP/Parent changes, Git or network actions occurred. No broader review effort is needed to resolve the demonstrated defect; the exact local UTC/key correction suffices for that question.
