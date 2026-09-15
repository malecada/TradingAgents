# Monitor recovery and VPN question — September 15, 2026

The user reports NordVPN connected to Finland for another effort. No VPN setting
was inspected or changed, and no public endpoint was probed in this check. The
failed custody launch involved local `/proc` memory sampling before a lifecycle
claim or market-data request. There is no evidence attributing it to VPN routing.
The original offending PID/status was not retained, so its exact transition
remains unproven; a process-exit transition is consistent with the observed error.

The launch packet mistakenly pinned the older resource_guard.py although an
existing reviewed resource_guard_v2.py already handles that transition. The
recovery reuses the existing implementation without changing shared/options
source. Its SHA256 and those of its preflight and four focused tests exactly
match research/strategy-search-2026-09-11/reviews/resource-v2-review.md.

Verification completed under the current environment:

- Four focused tests passed: transient missing memory, persistent unknown memory,
  memory/wall/launch failures, and confirmed process disappearance.
- The existing isolated synthetic lifecycle preflight passed under the exact
  v2 CLI: eight invented accounting/statistical books, two toy lifecycles in
  removed temporary repositories and100short synchronous Git helpers.
- Guard exit0, no limit reason,3.9975seconds; peak sampled aggregate432,930,816bytes
  below536,870,912bytes. Nominal20ms sampling plus a bounded retry is not an
  instantaneous hard memory cap. Default two-CPU/120second process contract.

This is engineering verification, not a custody or economic experiment. It
creates no actual shared-root research claim, source request or financial result
and adds no empirical search attempt. The original failed launch, gate, source
and1/6 admission charge remain unchanged. The old custody ID stays consumed;
there is no rerun or rewritten failure.

The next distinct source registration can pin the reviewed v2 monitor and import
179 administrative attempts with cap189. Its own exact source workflow still
needs synthetic preflight and source review, as normal registration work. A new
monitor implementation or VPN change is not currently needed. Current public
API availability has not been tested: later receipts should record the user's
reported Finland VPN route alongside actual request/status evidence, while
Czech-account product eligibility remains a separate evidence requirement.
