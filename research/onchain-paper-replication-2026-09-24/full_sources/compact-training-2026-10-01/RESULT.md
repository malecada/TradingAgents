# Compact training population admission

Maintained `compact_training.py` joins an actual current compact Owner to an
explicit `compact_training_input` selected in both registered producer plan and
execution job. The descriptor binds that input's exact SHA-256. Its control
object contains only schema version1 and the exact ExampleManifest hash. The
full descriptor is reconstructed from actual resident graphs, examples, fold,
seed and configuration, with exact numerical/compact execution identities.

Before graph iteration, selected input schema, descriptor and registered graph
manifest references are checked. Actual graphs must match that population and
source lineage. Actual example rows, order, membership hashes, fold clocks,
price-input ordering and graph availability at each sequence step are checked.
UTC-normalized start uniqueness rejects equivalent-format duplicates. The
training population includes only graphs starting inside the training interval
and available strictly before its end, with the existing sampler's ordering and
fold-bound dictionary settings. Insufficient centers are refused before sampling.

The route exposes read-only views and pins its owner, configuration and resident
graph references. Its inner lease checks those pins before and after the external
owner lease, under the explicitly frozen resident-input contract. Full `check()`
revalidates graph/example content and registered source/input metadata. Admission
must precede matching-stage creation; an already admitted route remains checkable
while its current owner proceeds. No sampling or output namespace is created.

Graph manifests use existing bounded, same-device, canonical-path metadata reads
with exact registered hashes and file signatures. Live owner leases accompany
those reads; complete source/input verification brackets the admission boundary.
Repeating the full source-checkout scan separately for every small graph manifest
is unnecessary. This is a boundary implementation choice, not a throughput,
physical resource or full-size memory-capacity result.

## Retained fresh checks

| Identity | Result | Evidence |
| --- | --- | --- |
| red01 | 8 missing-module failures,94.69s,session35372 exit1 | `red01.log` |
| check01 | Interrupted after1failure/2passes,126.57s,session66315 exit2 | `check01.log`, `training-check01.py`, `test-check01.py` |
| red02 | 1 failed,11 deselected,15.77s,session53489 exit1 | `red02.log`, `training-red02.py`, `test-red02.py` |
| check02 | 12 passed,169.87s,session40869 exit0 | `check02.log`, `training-check02.py`, `test-check02.py` |
| red03 | 1 failed,12 deselected,15.65s,session79996 exit1 | `red03.log` |
| check03 | 2 passed,11 deselected,30.28s,session72763 exit0 | `check03.log` |

Check01 exposed a datetime being passed to a string-only calendar function. The
check was deliberately stopped with SIGINT after reproducing it; the old attempt
was not relaunched. The corrected path converts the step through `stamp` and
compares normalized UTC instants, accepting equivalent Z/+00:00 formatting.

Red02 reproduced mutation of the route's seed inside the last external owner
callback. Route integrity now brackets that callback. Check02 covers successful
actual admission, metadata-first refusals, altered graph/example/seed/config/fold
joins, even registered future input, immutable views, revoked ownership, metadata
drift, full resident graph/example drift and admission-before-stage behavior.

Independent review then found raw-string uniqueness could allow two separately
registered graphs for the same UTC weekly start. Red03 demonstrates the different
literal starts and identical UTC start. The correction normalizes before the
uniqueness check; check03 verifies that refusal and successful actual supplied-
population admission/recheck. Earlier twelve-case evidence and this final-source
targeted check remain distinct; no combined current thirteen-case run is claimed.
All checks are terminal. Saved raw failure logs retain their original whitespace.

## Limits and next interface

Fixtures use actual temporary ResearchRun/source/input registration and compact
owner checks, with mocked kernel guard enforcement. Their supplied ExampleManifest
deliberately contains two train and two test rows from the larger synthetic
calendar, with recomputed exact hashes. This proves exact registered supplied
membership, not a complete calendar/exclusion denominator or independently
reconstructed prices, labels or Fold.member_hash/coverage. Existing full
denominator and source-admission gates remain required.

The route record explicitly sets `sample_provenance_admitted=false`. It does not
accept arbitrary SampleManifest objects, reconstruct weighted draws, publish
sampler evidence, fit a dictionary, select native production, seal FeatureJournal
or authorize an empirical run. Resident objects are supported; mapped population
admission remains separate. Next implement durable bounded sampler publication
from this route, verify its RNG/draw/artifact evidence, and consume that proof in
the compact dictionary producer under the accepted capacity/count contract.
Coverage77/109 and all1420 pending financial fits are unchanged.

Independent [review](REVIEW.md) accepted this bounded contract. Review SHA-256:
`6e1f52cb30c887908b74e9e18455dfc63505124bd37dbe8ac28175c3f477459e`.
