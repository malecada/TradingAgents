# Independent second-continuation review — September 18, 2026

Decision: approve exactly one source-only continuation, `eth-graph-source-resume2-20260918`, cumulative prior10/cap11. No unresolved material defect was found in the reviewed contract. The prior run is terminal and its worker and launcher have exited. No financial experiment, numerical graph reconstruction or further certificate use is approved.

## Parent evidence and stop cause

The parent `eth-graph-source-resume-20260917` closed at00:16:13.979615UTC. Terminal SHA256 is `de1147b69190d5d3048103c79d0a9929651295bbbf1d108dab7e26419a435006`. Independent reconstruction checked claim/gate links, all509exact output hashes, all507dated output-to-logical/physical-manifest links, exact index/summary/cell agreement,61complete dates and446unavailable dates. All445dates after October8made zero logical or physical requests.

Direct source inspection identifies October8logical request14 as the stop trigger. Physical requests14–17 each returned status206 with `TimeoutError: The read operation timed out`; retained partial body lengths are191618,16813,0and16813bytes. The elapsed gaps between the preceding receipt and next request are5.005,15.006and45.006seconds. All13earlier logical responses succeeded. This is transient read-timeout exhaustion under the frozen four-attempt policy, not access denial, object mutation, storage exhaustion or an integrity failure.

Across the parent, physical request count is5941and received bytes7122542296. There are exactly three attempts beyond the first attempt, all belonging to the exhausted logical request. Independent hash/size checks covered all41760manifest-listed source files; final reconstruction also checked directory membership and every day's unique raw inode and allocated metadata totals. Retained new raw bytes are5287611372and allocated metadata133455872. No failed partial body was dropped from the accounting. All1528closure import objects match their source and destination bytes, sizes and hashes.

The resource receipt reports exit0, no limit reason,8086.133873seconds and515801088bytes sampled peak process-tree RSS. Resource sampling was not independently replayed. At the final closure audit, PIDs607888and608637 no longer existed. Neither process was interrupted or modified by this review.

## Continuation admission and preservation

The446new dates exactly match parent unavailable cells;638prior completed dates are excluded. The sole October8prefix contains13successful logical responses and39files, all independently hash/size matched to the original selected evidence. Original clocks, physical attempt mappings, hardlinks and all four failed responses remain preserved in the old checkout. Only successful prefix files are copied into the new run.

The frozen engine `resume_graph.py` is unchanged from the prior approved source. `resume2_check.py` differs from its predecessor only in the cohort filename. Run, launcher and starter changes select the new identity, admission/checker modules, exclusive output paths,446date denominator and conservative baselines. The reviewed new admission policy preserves all ten predecessor identities, failed/unavailable outcomes and cumulative exposure, binds the parent gate/claim/terminal/index, and allows exactly one additional source claim. The different mechanism label routes the explicit amendment; it does not reset the history.

Final parent accounting is65417153516raw bytes and1072979968metadata bytes. The62GiBraw baseline exceeds the former; the1024MiBprior metadata baseline exceeds the latter by761856bytes. The new run reserves another128MiB for lifecycle/log overhead, charging1152MiBmetadata up front. An explicit admission check rejects parent accounting above either baseline. Independent policy checks passed12scope/amendment tests and both added baseline tests. The reviewed actual parent index also passes that check.

The inherited four-attempt policy,5/15/45second delays, denial/global-stop rules, immutable attempt receipts, selected-body hardlinks, unique-body accounting,120GiBraw/2GiBmetadata caps,20GiBfree-disk floor plus reserves,8GiBsampled process-tree guard and two CPUs remain unchanged. The charter's timeout wording was corrected during review:30seconds is socket/read inactivity, not a total-request deadline. Observed request14lasted about105seconds because partial progress preceded the timeout. No engine behavior was changed to shorten or extend that timeout.

Draft review verified63source hashes,34non-placeholder input hashes, charter hash, target contract and policy/baseline consistency. The two approval/review input hashes must be filled and the final certificate regenerated before normal/custom admission against committed source. This is a release binding step, not a request for another user confirmation.

## Limits

No live HTTP, job mutation, numerical transaction-row decoding, price parsing or financial experiment was performed. This review does not establish whole-panel numerical integrity, canonicality, duplicate/boundary handling, historical point-in-time availability, motifs, model/forecast performance, PnL, fees, funding or execution. Future provider health, new-run completion, reboot recovery, repeated monitoring delivery and worst-case resource enforcement remain untested. Unchanged-engine capacity tests were not rerun here; the prior review and retained synthetic evidence remain applicable. Raw stores still have no independently verified off-device backup.

Approval covers one new identity only. Before launch, bind these review files into the final gate/certificate, pass ordinary/custom admission, commit/push and verify the remote source, and use a fresh execution checkout. Subsequent continuations require their own concrete cumulative contract and review; this certificate cannot be reused.

Reviewed key hashes:

- `resume_graph.py`: `43cc2c2e468f74bf7bdcc37cb2d32382f7bd800a0c29c01f0bdbf4fd004712dd`
- `resume2_check.py`: `34d13c64dcea4430110de663279412fae21858bd281194f14b549dcf2a0cd69a`
- `resume2_run.py`: `a86ed06728a297a120d7a49282b40e3f9ae10c42e8f5fb91cdf78ee031dcc328`
- `resume2_admission.py`: `5c6b535b77ed2a5f006bcd6cda4eb4bbe106df051eda50c86127a0d50cdacdb4`
- `resume2_launch.py`: `745c85ea4bcd58b70771086b7c09c004764991e6f48a72f528083fbd96483257`
- `resume2_start.py`: `c89716908ef7b0ea501681a744c9428ca8330e200e9788ac4277ca85896b973a`
- `RESUME2_CHARTER.md`: `0b458087e575e34bd2cc714da4de789c7742ea5f3e5a7d983dfab653a39cb66c`
- `resume2-cohort.json`: `e4a13c2956dc15b009fdfa3d5f73265e172950a6cca3a9d8382f31003b3aded9`
- `resume2-history.json`: `85994fdd49ef0b16a2a78211ffcb5d03791f69e8c6c34100fd06363ab14b4d6c`
