# Independent actual release review — September 15, 2026

Decision: **approve the exact claimed release and corrected v2 finite launcher
for transfer and one launch within the committed lease**. The unused v1 launcher
is retained and is not approved for execution. Remote extraction and runtime
hashes must match the local approved bytes before the launcher is started.

## Actual claim and source

The actual claim is `options-timing-20260915`, SHA-256
`550c753279b8ae290ca988c9a23d5201b18ef4fd85b3c405a2f6e8a1078e8a73`.
Execution and design source are both
`22bdf6c17398425e2a22855e88f9a501b4f2f3f4`, recorded as pushed and separately
queried equal before the exclusive claim. Claim start is 10:02:56.191462 UTC.
The guarded actual admission and independent protocol check passed in 38.010
seconds with 74,690,560 bytes sampled aggregate RSS.

Independent byte reconstruction reproduced the approved target contract SHA-256
`0104d1ea8752a21c59c4dd682cebad0e1bd385cc98c7ef375f49c5433670a944`
and prior twenty-identity SHA-256
`4fca19ec6a6d2b39a25400c3e9833af9302f5518af473f789c9c6dc0733f19c5`.
The copied claim equals the authoritative live claim. The actual committed
registration, sixth grant, approval, preflight and every referenced report match
their physical hashes and the claim's source commit. The actual twenty-one
identity denominator was inspected: sixteen complete, four failed and this one
active claim. Every prior claim, terminal, output and failed-parent control hash
is unchanged. The new active claim has empty control and output directories and
no terminal. No financial values were evaluated.

## Exact package

Local package:
`/home/malecada/master_thesis/research-deployment/options-timing-20260915/release-22bdf6c`.
Remote package:
`/opt/thesis-research/options-timing-20260915/release-22bdf6c`.
The archive SHA-256 is
`b018c2a53c5af4f1a041bf492fde3d6de99ed5af47b341f04a73a6ee9c90ce1f`.
All ten regular archive members were read without extraction and independently
matched the ten local package files and retained release manifest. No symlink or
extra member is present. Executable/scientific package members also match the
committed source bytes.

The externally anchored assignment SHA-256 is
`375d70df4656f8ad851b038ffaabb0cf61bb71115aadd750ac2d8dc9a933d4a3`.
Bootstrap SHA-256 is
`fb123634d66dcf22cb8db49663febb3baf207af64ad3847cdcaa6b9f05ab7b1e`.
The assignment binds the copied claim, exact source commit, host `pck-preds-1`,
canonical actual data root `/opt/thesis-research/options-timing-20260915/data`,
fixed entry 11:00 UTC, lease start 10:58 UTC and lease expiry October 30 at
11:01 UTC. The raw-only authority and exact source allowlist are preserved.
The bootstrap verifies the complete inventory before importing the worker and
rejects unpinned initialization/shadow modules. It checks host/data identity and
requires isolated Python 3.13.13 with bytecode writes disabled.

## Launcher correction and approval

The initial launcher had a material boundary gap: after its one sleep it checked
only the 10:59 upper bound, and it did not recheck time after bootstrap hashing.
A backward wall-clock step could reach worker import before the lease; a delayed
hash or forward step could reach execution after the bootstrap refusal time.
This finding was reported before execution. The initial file remains preserved
at SHA-256
`32b6ae6adfea32fc16e67a61f5e63cb2913f5d1f6895675bf14e52bde559b2e4`.

The approved replacement is
`research/strategy-search-2026-09-11/launch-options-timing-20260915-v2.sh`,
SHA-256
`abf99bf272063d63c17852c6c2f331032c04f63067b2364dbd2ef3a1cf5fe9b5`.
Its actual text was inspected and `bash -n` passed. It now checks
10:58:00 <= wall time < 10:59:00 immediately after the finite sleep and again
after bootstrap hash verification immediately before `exec`. The lower and
upper checks close the identified gap without changing source, claim, phase,
lease or source caps.

The launcher permits at most 7,200 seconds of inert pre-lease sleep, takes an
exclusive nonblocking launch lock, and enables noclobber before opening its
one-use log. It does not import or run the worker during that wait, does not
schedule recurrence, and contains no restart loop. The shell SHA check anchors
the bootstrap before isolated `python3.13 -I -B` execution. Exact assignment,
package and new data paths match the approved release. Existing runtime reuse
is read-only at the previously verified dedicated Python distribution beneath
the old research root; it does not modify the old capture tree or shared system
Python. Final wall checks cannot constitute a continuous clock proof; the frozen
worker's independent lease and wall/monotonic checks remain required.

## Execution boundary and limitations

The local review/claim evidence must be committed and pushed before transfer and
launch as planned. The extracted remote inventory, launcher SHA and isolated
runtime must be checked against these approved bytes. The sole actual data root
must remain absent until the admitted worker creates it. No systemd, recurring
wakeup, automatic restart or replacement claim is approved.

This review performed no remote mutation, worker execution, market request or
financial evaluation. It proves the local source/claim/release bindings and the
specific launcher correction. Runtime resource guards, three-second source
availability, complete funding, actual fees/fills and margin stress remain
conditional as recorded in the final admission review. A later source failure
retains the consumed allowance and full unavailable denominator; it does not
authorize replay. Zero strategies are validated.
