# Local transport extraction checks

The maintained module no longer depends on a dated job script. Explicit SSH
configuration replaces the embedded smoke connection. The original sealed
snapshot, conservative block reservation, strict remote member names, exclusive
local publication and 16 KiB stderr tail remain. Deadline parameters reject
nonfinite values; the budget rejects invalid numeric types. Receiver polling
checks the caller lease, and cleanup kills the owned child process group.

The checkout-local locked runtime check passed: Python 3.13.13, no version
mismatches, lock sync check exit 0. `source-manifest.json` binds source, tests,
preserved predecessors and lockfile. `source01.py.txt` and `tests01.py.txt` retain
the source reviewed with check02.

Checks, all closed:

- `red01.xml`: exit 1, 22 setup errors, 0.23 s. The required production module was
  absent. This is retained as a missing-module setup failure, not a behavioral
  regression result.
- `green01.xml`: exit 0, 22 passed, 0.59 s. Exact, short, excess and failed child
  downloads; sealed upload despite source growth; lease refusal; timeout;
  200,003-byte stderr stream bounded to its last 16,384 bytes; budget rejection;
  path/connection validation; explicit stable identity.
- `check02.xml`: exit 0, 29 passed, 1.12 s; session 67854 closed. Includes 24 new
  tests and five predecessor tests. Added active-child lease revocation and a
  real archive_chunks preserve/readback/fresh-retrieve sequence using temporary
  local child storage, plus refusal of an existing remote object directory.
- `git diff --check`: exit 0. No broad offline or actual-owner test was launched
  by this worker; the coordinator explicitly limited this run to focused tests.

Exact focused invocation (change only the XML basename for earlier passes;
predecessor file was included only in check02):

```bash
env -u PYTEST_ADDOPTS PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 RUN_ONLINE_TESTS=0 \
  .venv/bin/python -B -m pytest -q -p no:cacheprovider --import-mode=importlib \
  tests/research/onchain_replication/test_archive_transport_production.py \
  tests/research/onchain_replication/test_archive_transport.py \
  --junitxml=research/onchain-paper-replication-2026-09-24/full_sources/archive-transport-production-2026-10-02/check02.xml
```

Plugin autoload, cache and inherited pytest options follow the reviewed named
offline command. Repository admission and audit hooks remained active; 26
encountered unreviewed files were withheld. Native child processes are local
Python programs explicitly declared in the reviewed tests, not an OS network
sandbox claim.

Limits: synthetic children do not establish actual SSH/SCP interoperability,
remote availability or off-device recovery. Linux memfd and `/proc` are required.
Payload reservations exclude SSH framing, stderr, filesystem overhead and
resource usage. The process deadline excludes snapshot preparation and allows a
separate ten-second forced-cleanup wait. Failed uploads can leave partial remote
objects; no refund or retry is granted. Transport identity uses a new explicit
configuration namespace, so historical smoke receipts are not silently reused.
Public command attributes and lease implementation remain trusted caller inputs.
Producer/owner integration, physical accounting and external admission remain
outside this extraction. No financial or empirical conclusion follows.
