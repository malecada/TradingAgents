# Independent final-report review

Review date: September 10, 2026. Scope: `docs/diagnostics-2026-09-10/RESULTS.md`, the saved forecast result and prior interpretation, `verification/risk-interpretation.md`, implementation/test records, and Markdown table structure. No strategy, diagnostic, fit, resampling, source or data mutation occurred. Full output arithmetic and preservation are covered independently by the result reviewer.

**Verdict: PASS on numerical reporting and interpretation, with two minor wording recommendations and completion links to populate before publication.** The reviewed report SHA-256 was `f4fad79726a19df5b399b83a746dfa8ae29babb2bc825fc2ce5f37bae0da57f3`.

## Findings

1. Replace “Every mean-return comparison is worse than its zero baseline” with “Every mean-return comparison has worse point loss than its zero baseline.” All four point estimates are negative, but the ETH hourly interval spans zero. The remainder of the report already restricts formal inference appropriately.
2. Replace “the missing October 28, 2024 20:00 UTC origin” with “the unavailable October 28, 2024 20:00 UTC hour.” The variance row exists and is unscoreable, whereas the volume origin was omitted and is inserted with an unavailable mask. The report correctly states that bootstrap time is retained; this change makes the source-state distinction precise.
3. At review time, linked `verification/result-review.md` and `verification/preservation-final.json` were not yet present. Populate the final completion artifacts before publication, or label the links pending. The existing `result-review.json` already supplies independent result evidence; this is a completion-document issue, not an empirical discrepancy.

## Checks and conclusions

- All sixteen rounded loss improvements, conditional intervals, eligible Holm values and stability descriptors match the saved forecast result. All four volume comparisons have adjusted p = 0.0079960019990005; twelve ineligible slots remain unavailable and enter the family as one. The report does not turn ETH hourly variance's positive conditional interval into a formal discovery.
- Forecast loss percentages are explicitly distinguished from investment returns. Volume MASE scaling, the original declared baselines, retained fallback observations, 32,000 valid stored bootstrap draws, unresolved nesting, wider historical selection and absent direction AUC intervals are described consistently. Historical lower LGB scalar losses are contextual and do not become a new paired competitor comparison.
- The factor narrative agrees with the existing risk interpretation on 44,640 sleeve-date rows, 8,873 active observations, 4,458 above-reference cases, 939 active gate-closed dates, 852 stops and the 726/93/25/8 successor categories. The nominal 15% entry proxy is distinguished from realized account volatility and continuous targeting. Overlapping sleeve observations are not presented as independent experiments or pooled money.
- Re-entry costs, maintenance turnover and halt-crossing charges are not added twice or interpreted as sufficient proof of an improved counterfactual. The four motivating sleeves remain explanatory examples. The one post-exit threshold crossing is described as a boundary observation rather than a claim that removing fees would fix the path.
- The proposed follow-ups are explicit future registered comparisons. The text does not claim that resizing, cooldowns, lower volume error or changing a halt will produce profitability. Prior sizing attempts, spent holdouts, the separate sleeve-index construction, price/funding/stop assumptions and the 22 deferred settlement cases remain disclosed.
- Registration `38d9a67e6ff042cb1fd870877b3e0222f40fdc08`, execution source `cd8d9e3f064bb40273ba493e597e371e6f199b66`, both result hashes and the financial-ledger identity match the existing evidence. The stated 57 forecast tests and 80 factor tests match `forecast-green.txt` and `risk-final-tests.txt`, respectively. No unchanged tests were repeated for this report review.
- All four Markdown tables have consistent column counts. Their data-row counts are 4 provenance entries, 16 forecast comparisons, 4 motivating sleeves and 36 full-grid factor sleeves; no raw pipe in an identifier splits a table cell.

No numerical correction, source change, data change or empirical rerun is requested by this review.

## Scoped resolution

All three review items are addressed. The report now specifies worse **point loss** for mean returns and an **unavailable hour** for the masked timestamp. Both linked completion artifacts are present: `result-review.md` reports PASS, and `preservation-final.json` has status PASS. The current report SHA-256 is `bb45dac70df06b5d3644a8e4c5f33769c4bf5a9c67b5b5f544f9ac799779cb98`. **Final report verdict: PASS, with no outstanding review items.** This resolution checked only the two wording changes, linked completion statuses and report hash; no broader review, tests or empirical calculations were repeated.
