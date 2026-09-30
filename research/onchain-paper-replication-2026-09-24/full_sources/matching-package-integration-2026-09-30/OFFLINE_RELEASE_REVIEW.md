# Independent finite offline release review

## Initial finding — manifest closure

Initial release withheld for one material source-closure issue. The initial `run_offline.py:20–27` reads the local `source-bindings.json` and checks each listed file against both current bytes and `--source`, but does not compare the manifest itself with that commit. An altered local manifest could omit a file and still pass; recording its hash in the guard owner does not establish that the altered closure was committed or reviewed. Compare the complete raw manifest with `git show <source>:<manifest-relative-path>` before parsing or iteration. This does not require a self-hash inside the manifest.

Initial launcher SHA-256: `83b10916f744eaba92dc70593fc344c106c8c9f2f23faecd045eb2fc6401e9b2`.
Initial binding-manifest SHA-256: `65caf20eb8349df985279abd5697ae662852e33e7dc928da98d43996b548cc29`.
Protocol SHA-256: `85d8ada9d52194ebf2bc5320ae10913b981acbd7cc8a77df60622a29a7f1ecf9`.

All 178 initial file entries independently matched current bytes; all 163 inherited entries remained present with unchanged hashes. The 15 additions are six maintained source modules, the new test, and eight compact implementation/protocol/derivation/review/log/launcher files. The `offline01` identity did not exist at inspection. The initial finding concerns enforceable dispatch closure, not an observed source mismatch.

## Other inspected conditions

The launcher requires a full 40-character source commit and matching current HEAD. The named command is the repository `.venv/bin/python -B scripts/verify_offline.py`, which separates the standard and neural reviewed offline batches. The new normal-import test falls within its explicit `tests/research` inventory. No empirical experiment main is selected.

The requested guard arguments are 3 GiB memory.max, 2.75 GiB memory.high, zero swap, 3 GiB host reserve, 6 GiB startup memory, 10 GiB disk floor and 3,600 seconds. The existing guard creates the receipt directory exclusively, derives two CPU affinities, checks kernel controls and per-thread affinity before workload release, enforces the finite boundaries and requires a fresh monitor lease. A pre-dispatch systemd query rejects active or activating replication units. This is a coordinated one-owner workflow, not a global race-proof admission lock against an unrelated simultaneous launcher; dispatch must retain the stated no-competing-owner condition.

A final accepted launcher must be committed and pushed with its exact manifest and both independent review documents before dispatch. The future execution commit is supplied by `--source` and retained with the manifest hash in guard ownership; a commit value need not be embedded in its own source bytes. Verify the pinned runtime and fresh resource/owner conditions at dispatch, then freeze source and HEAD. Existing receipt identity, a failed preflight or a terminal guard must not be repurposed as permission to retry.

After one invocation, independently reconcile both raw test summaries, final and child-exit receipts, actual memory.high/max/OOM counters, cleanup, exact PID/start identity and cgroup absence, and current versus committed bindings. Focused source acceptance and this prospective review are not a broad-suite pass, empirical admission or financial result. No tests, profiles or array-body reads were performed for this review.

## Corrected release acceptance

The manifest-closure finding is resolved in the corrected launcher. It now obtains the manifest's repository-relative path and compares its full raw bytes against `git show <supplied-source>:<path>` before JSON parsing and file iteration. Missing or uncommitted manifest bytes fail before guard creation. The only launcher change is this comparison; the only binding-manifest change is the new launcher hash. The original launcher and manifest are retained byte-exact in `review-draft01/`, with the initial hashes recorded above.

Corrected launcher SHA-256: `8d4db241c688661a5fc6250b5dc7a8ae8917d7ae04e4a4ce832212b2d2ebb69e`.
Corrected binding-manifest SHA-256: `2262884a7c96159779cfae45b2c4b2707852471dfed63f8ce25f41b04e355697`.

All 178 corrected entries were rehashed successfully; the prior 163 remain unchanged. No `offline01` receipt existed at the final review check. The exact corrected preparation is accepted for one finite named offline invocation after commit/push of the manifest, listed files and independent reviews, with fresh runtime/resource/owner checks and the supplied commit matching actual HEAD. No execution or success is inferred from this acceptance. The closure requirements and limitations above remain in force.
