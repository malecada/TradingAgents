# Standard-batch failures: ambient disk space leaked into tiny fixtures

Maintained owner offline01 standard batch ended with35failed/2739passed and
97subtests passed in1096.39s. All35 failures are the identical OSError from
fullpanel/hash_audit.py:_space, before the intended hash-audit assertion. Fourteen
occur in test_onchain_fullpanel_hash_audit.py and21 in
 test_onchain_fullpanel_resume_hash.py. standard-failures.json retains every
failed test node ID and both maintained test hashes. The full parent child.log
remains live because the neural batch is still running.

The historical hash-audit component retains its frozen20GiB free-space floor
plus1MiB allocation margin. The current replication guard uses the separately
authorized10GiB floor. Preflight available disk21,550,129,152bytes only exceeded
the old20GiB floor by roughly72MiB. Temporary synthetic fixtures then consumed
that margin; a later observed available20,138,999,808bytes remained well above
the active guard's10GiB floor, but below the historical component's20GiB floor.
No historical source or old policy should be rewritten to suppress these tests.

The two synthetic test modules currently use real shutil.disk_usage during
fixture construction. Their explicit low-disk rejection tests cannot reliably
reach their controlled failure because fixture construction may already fail.
Proposed correction after the current source freeze releases: add scoped
autouse fixtures that replace only the dynamically loaded audit module's shutil
namespace with a small namespace exposing deterministic disk_usage. Keep ample
simulated capacity for the existing invented hash fixtures. Existing low-space
tests must still override that local namespace and exercise actual refusal
before intent/allocation. Never mock _space or mutate the process-wide shutil
module. Add regressions that make the real shutil.disk_usage fail if consulted,
then prove append/audit still work through the isolated fixture namespace.

Original maintained test bytes are preserved as .original snapshots. Isolated
copies include proposed regression tests and a path-depth correction only;
the fixture correction has NOT been applied or verified. A focused pytest
invocation on these isolated copies was refused before import by conftest.py's
reviewed-file policy; red01.log retains the usage error. It is not a failing
counterexample run or a successful test. Do not bypass collection admission.
The actual35 standard failures are the existing failure evidence.

Next: await full guard termination and source/owner cleanup closure. Then add
the regressions to the already admitted maintained tests, reproduce them through
the reviewed pytest path, apply the scoped fixture correction, run both admitted
modules and independently review the diff. A fresh committed source/binding
closure and new exclusive broad-verification identity are required. The original
offline01 remains failed even if its neural batch succeeds. No empirical identity,
financial fit, historical source or spent budget is repeated by this correction.
