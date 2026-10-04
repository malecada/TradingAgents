# Historical fund-cohort evidence investigation

Task11 / Tables5–6 remain **blocked_cohort**. A complete, immutable public **candidate** containing65 Ethereum addresses was recovered, but no evidence authenticates it as the cohort used by Çelik and Sefer. Counts, names and chronological plausibility do not establish author reuse. No empirical admission, fitting, label substitution or change to the original coverage occurred.

## Original-paper requirement

The retained paper (DOI10.1007/s10614-025-10940-1; accepted25March2025; published18April2025) identifies Etherscan Fund accounts,65 entities and25 Alameda associations in §5.4. The short controlling extract is “all‘fund’accounts from Etherscan, which consists of 65 entities” (spacing normalized only). There is no address list, collection timestamp or formal Etherscan reference in that paragraph. General §4.1 specifies2016–2024 weekly transaction graphs; §4.2's rolling-window date inconsistency remains. Neither the exact fund-period denominator nor induced-only versus external-neighbor filtering is specified. [Original publisher article](https://link.springer.com/article/10.1007/s10614-025-10940-1).

Original SOURCE_AUDIT.md, TABLE_COVERAGE.md, paper.txt and controlling paper.pdf hashes are retained in READBACK01.json. The paper PDF hash is a0d569b0dea57b7a9b728f4af9971ec8715c1df46dafa070ea25bdc8547c408f. The prior author-code audit was not repeated.

## Authenticated historical candidate

The public collector repository brianleect/etherscan-labels contains `data/etherscan/accounts/fund.json` at immutable commit923aba72c7e2d0682f7ae6194b6140bd90668dc9 (committer timestamp1October2023,18:22:35Z). The complete4512-byte body has SHA256d9965a407e7ca3e6739b3b6304cdcdc5e25e9d9e8a6a24d7e877d357a916adcf and Git blob0dc90e1a00873e5ab650e0169b3836371e769252. Its size, blob hash and100644 Git mode match the repository tree. File-specific history attributes that body to commit7218e6ed354a154b110b93d43850139fb27bbb3d,16June2023,18:39:41Z. The commit API response includes this file but only300 files overall; no completeness claim is made for that API response's entire commit file listing. [Pinned original collector body](https://github.com/brianleect/etherscan-labels/blob/923aba72c7e2d0682f7ae6194b6140bd90668dc9/data/etherscan/accounts/fund.json).

The candidate has65 distinct valid lowercase20-byte address strings.25 labels are numbered Alameda Research1–27 excluding18 and21. Two additional addresses have Alameda deposit labels, yielding27 Alameda-prefixed names in total. Thus25 is consistent with counting numbered labels, but that interpretation is not authenticated for the original paper. The complete address list and labels are derived exclusively from the pinned body, without performance-based selection.

The earlier26March2023 collector version contains64 addresses; the later version adds Amber Group at0xe11970f2f3de9d637fb786f2d869f8fea44195ac, with no removed addresses or changed labels. This concrete vintage difference prevents treating any historical Fund list as interchangeable. The collector README declares an Ethereum scrape date18June2023, whereas this file's commit is dated16June; these dates are retained separately, not coerced into an exact scrape time. Collector Git timestamps establish repository history, not the original Etherscan label creation dates or the paper's acquisition date. [Pinned earlier body](https://github.com/brianleect/etherscan-labels/blob/b4616b998f7e0e1debc7a4b2136a5687f9defdce/data/etherscan/accounts/fund.json).

The repository carries an MIT license, retained with its notice. This supports preserving the collector artifact under that license; it does not attest to Etherscan's underlying labels, third-party ownership or permission for unrelated data collection. No scraper was executed, login used or credentials inspected. [Pinned license](https://github.com/brianleect/etherscan-labels/blob/923aba72c7e2d0682f7ae6194b6140bd90668dc9/LICENSE).

## Separate primary research lead

Coquidé, Cazabet and Tovanich's17September2024 arXiv v1 describes65 Fund accounts and27 Alameda addresses, explaining the18/21 deposit-name exceptions. Its dataset endsMarch2023; its analysis beginsJanuary2018 and explicitly includes ego–alter interactions. It links the exact Etherscan category. This is a useful independent historical lead, not an original-paper citation or proof of shared data. No Coquidé/Cazabet/Tovanich reference appears in retained Çelik–Sefer text. Its different dates and account-count interpretation cannot be transplanted into Tables5–6. [Primary author preprint, §3–5](https://arxiv.org/html/2409.10949v1).

The same authors'26August2025 journal extension explicitly reports90 Fund addresses as ofDecember2024 and cites the public collector used above. It coversJanuary2018–December2024, retains27 Alameda addresses and provides processed data on request. It corroborates changing cohorts and supplies the collector provenance lead, not an authorization to replace65 by90. [Primary journal extension](https://link.springer.com/article/10.1007/s41109-025-00712-z).

Indexed Etherscan material identifies Alameda Research25 at0x84d34f4f83a87596cd3fb6887cff8f17bf5a7b83 and attributes its label to Larry Cermak's wallet list. Current indexed labelcloud counts are90 Fund accounts and29 Alameda accounts. These are modern/search-index observations only. Direct category/address web reads returned403; a bounded public Wayback CDX query timed out. No historical Etherscan snapshot or original Cermak list was authenticated. Search hits from secondary sites were discovery leads only, not substantive evidence. [Etherscan address](https://etherscan.io/address/0x84d34f4f83a87596cd3fb6887cff8f17bf5a7b83), [labelcloud](https://etherscan.io/labelcloud).

## Deterministic membership and remaining requirements

ORDERED_ADDRESSES01.txt sorts the65 authentic lowercase addresses lexicographically, one ASCII address per LF line with a final LF. SHA256:3e63058e9e7d567116ac9314fca8de32db9f167a8b4743b3d8076056b86d3e0f. ORDERED_MEMBERSHIP01.json preserves address-label pairs in that order, compact sorted-key JSON plus final LF; SHA256:16d6f4bfe94461482b49653719bcf50a97fe42dbc8779b0be0f1513ee0cc2542. These are candidate membership fingerprints, not experiment IDs or registration approvals.

An explicitly labeled prospective historical-cohort reconstruction could freeze this exact candidate before fitting **only if** the governing plan/specification permits that distinct assumption and Root completes registration. It must not be described as exact original replication. No such decision is made here.

Required before original matching can be claimed:

1. An authenticated author artifact or original dated acquisition record linking all65 addresses to Tables5–6; a matching count is insufficient.
2. Exact list acquisition date, label vintage, inclusion/exclusion rule and treatment of the two deposit labels, entities versus addresses, EOAs/contracts and changing labels.
3. Ethereum chain identity, native/internal/token transaction classes, successful/failed transaction policy, spam/token rules, direction, multiplicity and weighting.
4. Whether edges are induced within65 or include external counterparties, any expansion depth, deduplication and weekly-boundary/timezone rules.
5. Exact fund-specific date range, rolling folds, missing/empty-week handling, price-only baseline denominator and resolution of2016–2024 versus two-year-training chronology.
6. For any prospective reconstruction: frozen assumption disclosure, public-source/license and availability review, original source/data preservation, deterministic dataset joins and genuine pre-outcome admission. Historical labels must not be asserted as contemporaneously available trading signals.

All retrieval was bounded, unauthenticated public GET. No provider/author contact, purchase, upload, numerical import, fitting, empirical claim or original-state mutation occurred. The local manifest preserves this investigation only and does not establish external recovery.
