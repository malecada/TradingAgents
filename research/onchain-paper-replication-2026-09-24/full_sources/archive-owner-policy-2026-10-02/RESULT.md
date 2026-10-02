# Registered archive-policy selection prerequisite

archive_owner_policy.select implements the read-only registered selection
boundary for a fresh actual compact_owner.Owner. Execution-job and producer-plan
selection, the bound descriptor, admitted archive input, current owner/source
authority and transport identity must agree. Selection records are immutable;
checking them or deriving a per-stage writer policy rechecks that authority.
Remote prefixes bind the full owner identity and required stage name.

Conservative allowances cover the complete fixed required-stage population:
maximum remote event bytes, writer/read/reference metadata and a finite count of
stage verifications. Decoded event transfer accounting includes upload, copy
readback, writer-finalization replay and declared cold reads. The engineering
verification-count cap is1024 per stage. Physical allocation, SSH framing,
provider staging and other scientific payloads remain excluded.

## Retained verification

- red01: 13 missing-module failures in168.21s, session25266 exit1.
- check01: 14 passed in252.86s, session10550 exit0. These are actual fresh
  synthetic ResearchRun/Binding/Owner fixtures with a mocked OS guard. Cases
  cover matching registration, fixed stage population, distinct writer prefixes,
  returned-policy isolation, wrong selection/hash/budgets, source-input change,
  terminal owner, endpoint drift and wrong owner/input types.
- REVIEW_INITIAL found AOP1: a valid stage could be created by a late external
  owner boundary after the initial freshness check. The source and tests are
  preserved as policy-check01.py and test-check01.py.
- review-red01: one failed, one passed,14deselected in35.13s. Direct already-
  started refusal passed; actual owner.begin injection through the second owner
  boundary demonstrated retroactive selection.
- The correction rechecks empty stages and no active stage callback-free after
  all selection checks. The future consuming adapter still needs the owner
  transition lock; this sampled check is not an atomic execution claim.

No namespace or remote transfer is created by selection itself. The tests leave
the owner namespace with only its original owner record except where an actual
valid stage is deliberately created for the freshness regressions. No financial
experiment or historical claim is replayed.

## Exact remaining integration

This is a prerequisite, not the completed archived owner backend. It does not
install a writer, meter or spend operation allowances, or change existing owner,
producer, publication and terminal routes. An explicit adapter must consume the
selection under owner authority, durably reserve finite write/read identities,
enforce transport and metadata allowances and bind the archive route through
those downstream contracts. Score/checkpoint retention and whole-workflow
physical accounting remain open; execution_admitted is false.

## Accepted correction

check02 CLOSED: 3 passed, 13 deselected in73.92s, session14361 exit0.
This targeted run covers the registered positive path, already-started refusal
and actual late-stage injection. The baseline14 and corrected targeted3 are
separate results; no full final16-case result is claimed. Independent final
review accepted AOP1 closure, REVIEW_FINAL.md SHA256
5b7720ada60ffe504ac5f9adcdf65423f597c1b9857c56e464363bfb6137803a.
No active verification process or source freeze remains.
