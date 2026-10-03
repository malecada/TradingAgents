# Optional held fixture dispatch01 — independent source review

Disposition: **WITHHELD**, one material preflight defect HFD1. No genuine admission, Owner, numerical workload, native unit or historical rerun was executed.

Reviewed candidate `resource_fixture.py` SHA-256 `d18078bc522272c4834e54623e41dcbc7a0a9f86573e670d4292fd0e1feac80d`, manifest `f7209b4555872c05480b1fa4d9405e733213ef1969da54a489f51e8e74cc2a44`. All 12 manifest members matched actual lengths/hashes. Preserved baseline `d92c0a92d877190f93f106ce505511ed59ceef050308fe5c32c29e13a7665028` equals actual Source03 resource_fixture bytes. Exact inverse whole-source equality outside selection/preflight was independently checked. Program, mechanism, parent/history admission, numerical/scalar body, Owner/terminal and cleanup methods remain unchanged.

## HFD1 — one-way selector join admits a plan that the actual consumer rejects later

Locations: candidate `resource_fixture.py:123–138`; actual Source03 `held_score_consumer.py:100–108`; candidate `resource_fixture.py:297–304`.

Preflight checks `all(item.get(k)==v for k,v in s.items())`, then chooses its optional held branch only if the job selection has `held_score_consumer_input`. It does not reject a reserved held selector present only in the producer plan, or an unknown reserved `held_score_` field present only there.

Two deterministic counterexamples were executed against extracted actual selection/preflight statements and the actual held `_route` predicates, with explicitly synthetic metadata/stand-in classes:

1. Remove `held_score_consumer_input` from the job selection; retain it in the producer plan; register exactly the original four outputs. The fixture preflight output seam accepts. The actual consumer rejects `held job/plan selection differs`.
2. Keep the valid shared selector and six outputs; add `held_score_typo` only to the producer plan. The same preflight accepts. The consumer rejects `unknown held selection`.

These are source-boundary counterexamples, not a claim that genuine Owner execution occurred. The callable source shows the consequence: execute invokes resource_binding/open_first and prepares the imported Owner/Targets before entering compact MCM `_prepare`/consumer checks. Thus malformed prospective selections can consume a real attempt and create durable Owner evidence before a deterministic refusal that belongs in preflight. The consumer still refuses; no unauthorized successful read was demonstrated.

Required narrow correction: before branching, inspect both original job and producer dictionaries for unknown reserved `held_score_` keys; require the optional field to be absent from both, or present as the same nonempty string in both. Then run the existing registered-policy and six-output branch. Keep valid unselected legacy selections and the original four-output predicate unchanged. Preserve candidate01 and both retained counterexamples; use a new candidate/version for correction.

## Accepted bounded observations

The baseline source refuses the selected metadata case; the candidate passes it. Independent checks reject eight malformed-policy/output cases: missing target, extra/missing output, missing plan selector, boolean part size, oversized policy, original-output collision and path traversal. Actual read-boundary MemoryError, KeyboardInterrupt and SystemExit sentinels preserve exact identity through the new preflight fragment. These use a qualified stand-in registered read and are not new descriptor/IO/native proofs.

The candidate reuses actual held `_policy` with exact target population, registered distinct output names, aligned finite part size and finite member/read limits. It requires the two readbacks to be disjoint from the original four and the resulting set to equal all experiment outputs. Its schema admits only the original key set or that set plus the one explicit selector; malformed job-side aliases/extras remain refused. Normal registered input authentication is supplied by unchanged `original_dictionary._read_registered`; no caller hash replaces it.

The 8KiB held-policy test is an acceptance limit applied **after** the original bounded reader returns. That reader's actual transient body ceiling is 2MiB (`original_dictionary.py:233–246`), with 64KiB reads and descriptor/signature/hash checks. This candidate does not promise an 8KiB pre-read allocation ceiling. No new unbounded reader was introduced. Original descendant IO and failure propagation were not re-proved by these metadata checks.

The author's 14-case green log and retained baseline failures were inspected and hash-authenticated. Independent `check_dispatch01.py` adds the two missing reverse-join counterexamples, exact fatal identity checks and inverse byte reconstruction; results are retained in `check_dispatch01.log` and `COUNTEREXAMPLES01.json`. No author's expected result was substituted for the independent findings.

## Remaining requirements

After correction and independent source acceptance, actual Root integration must rebind the changed source hash/commit and complete 199-source/148-package origin and anchor closure. Genuine 13-role input/runtime/source/native/whole-tree checks, finite reviewed registration and cumulative spent history, fresh retention/external recovery and current resource eligibility remain separate. No new module is added by this candidate, but unchanged file count is not unchanged source identity.

The real two-target held stream/consumer, six registered outputs and genuine failure cases remain unexecuted. The separate 27-variant/16-class suite, scientific Published/cold authority, remote transport/retirement, numerical capacity and financial results are not established. The original closed attempts and exhausted cold family are unaffected.
