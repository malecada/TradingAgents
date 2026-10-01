# Registered compact MCM output adapter

Maintained `compact_mcm_publication.py` binds numeric publication and current-owner
reads to an actual `compact_owner.Owner`, its completed required MCM stage, and
the exact `compact_mcm_output_input` selected in both registered execution job
and producer plan. The backend must be explicitly compact. Existing old native
production and dated `OwnedJournal` routes remain unchanged.

The registered policy has exactly `schema_version`, `backend`,
`max_artifact_bytes` and `max_workflow_output_bytes`. Each required graph reserves
its full artifact allowance plus an 8192-byte wrapper receipt. The entire required
graph population must fit that separate allowance before any graph is published.
Artifact allowance includes raw float32 bytes and its bounded manifest. This
does not replace the owner's retained matching/score-evidence budget or measure
physical allocation, numerical scratch, memory mapping, page cache or runtime.

Outputs occupy exclusive derived paths under
`research_artifacts/onchain_compact_outputs/<workflow>/<experiment>/<stage>/`.
Failed partial publication persists and poisons the owner. Existing namespaces
are refused. The receipt pins the exact Binding by canonical hash, includes the
claim hash and selected policy hash, and binds the stage and numeric artifact
receipts. Receipt serialization is preflighted before namespace creation. The
owner's transition lock prevents overlapping transitions through this interface.

Reads require the current active owner and registered policy. A final callback-
free wrapper verification occurs after the nested numerical mapping has completed
all its exit callbacks. Cold reuse, successor admission and terminal-owner reads
are not supplied by this adapter.

## Saved evidence and limits

| Identity | Result | Preserved evidence |
| --- | --- | --- |
| red01 | 4 missing-module failures, 60.58s, session83347 exit1 | `red01.log` |
| check01 | 1 failed, 3 passed, 76.57s, session39703 exit1 | `check01.log`, `publication-check01.py`, `test-check01.py` |
| red02 | 2 failed, 1 passed, 3 deselected, 76.00s, session3765 exit1 | `red02.log`, `publication-red02.py`, `test-red02.py` |
| check02 | 3 passed, 3 deselected, 75.49s, session32513 exit0 | `check02.log` |

Check01 exposed a full Binding record exceeding the receipt cap after numeric
publication. The bounded hash reference and preflight correct that failure.
Red02 includes successful corrected publication/verification/read-only mapping
and aggregate owner closure, plus two reproduced review findings: changing the
receipt or adding a foreign wrapper entry in the underlying reader's final exit
callback was previously accepted. The callback-free check after nested exit is
the correction verified by check02, together with successful actual-owner
publication/verification/mapping/aggregate closure. The other three refusal
cases remain the earlier-source check01 evidence; no combined final-source
six-case run is claimed. No engineering or empirical process remains active.
Independent acceptance is retained in `FINAL_REVIEW.md`, SHA-256
`bcb46d7614f69cfc9b95537703ee9bb56e54fcbdd9f577af39b4be5b04b60bf9`.
Saved failure-log whitespace is preserved verbatim; source/document diff checks
exclude those immutable log bytes.

The fixtures use actual temporary committed ResearchRun registrations, source
and input checks, first-owner Binding, compact owner and fourteen numerical MCM
comparisons. The kernel guard boundary is mocked. Their zero-pair dictionary
stage is only an ownership-sequencing fixture; the MCM dictionary comes from the
scalar fixture. Consequently these checks do not establish scientific sampling
or dictionary training provenance, full-size resource feasibility, a registered
native representation or any financial result. The external scientific scope
still must be derived by the full producer from admitted inputs. The receipt's
`representation_admitted` remains false; no FeatureJournal event or representation
seal is fabricated. All 1,420 financial fits remain pending.
