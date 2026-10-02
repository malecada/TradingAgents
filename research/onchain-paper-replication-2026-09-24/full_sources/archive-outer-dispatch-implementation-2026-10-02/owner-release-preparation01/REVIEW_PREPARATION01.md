# Independent isolated-fixture preparation review

The source/runtime mapping is accepted as preparation only. No launcher or fixture execution is released by this document. Independent Git reconstruction verified all 1,873 regular blobs, their exact object identities/modes, sizes and SHA256 values against source commit `824489afa2aa5eba39ebf1af456681120ac9e0fb`. The total is 18,815,116 bytes. The declared conservative Python/config selection has no omitted committed member, and the prospective spec source map matches the manifest exactly. The proposal fixture remains SHA256 `db501e6a07dc7fad1e904d46deeb057e3df1c809a31e3ca0db5af9cb37cacf57`.

Manifest SHA256: `4a1ebd8a06daa1e45ea04bed7497bf24fba7e15b8d57363ecc4284c86b4e8937`. Prospective spec SHA256: `e1cca099a0098fa1b35b507a6bdeaab4e8fe02999ed5d58a1e88059cbc8b6528`. The source commit and later shared HEAD are explicitly distinguished. Recorded missing namespace-package init files are not silently invented. The mapping correctly distinguishes an exported source tree from a Git checkout and does not propose a fabricated HEAD or shared-venv symlink.

The runtime version inventory is metadata observation, not binary/ABI or import-origin verification. A final release must bind the exact interpreter and invocation, establish isolated package/test/helper resolution despite the editable installation, retain third-party plugin restrictions and account for the helper's real Torch import. Before/after source hashes and generated synthetic Git/source/registration records must be retained. This review did not import research, Torch or test modules.

The concrete launcher must establish the claimed controls before releasing the test process:

- A separately verified external cgroup memory.max of 3 GiB; the fixture's mocked internal guard provides no protection. Capture cgroup identity, actual readback and events, with child/descendant cleanup evidence on every termination path.
- A complete-invocation 1,800-second deadline covering fixture setup/teardown and descendants. Document any bounded independent cleanup interval separately; a Python child timeout alone is insufficient.
- A genuinely bounded aggregate 1-GiB owned allocation domain covering source snapshots, fixture roots, temporary/generated Git files, caches and logs, or an explicit revised claim. Polling and per-file RLIMIT_FSIZE do not establish a hard aggregate allocation limit. Include deleted-but-open files if claiming allocation, and identify any output outside the enforced domain.
- A 4-MiB combined log sink with no unbounded capture buffer, explicit overflow disposition and retained partial bytes. A sampled file-size check is insufficient for a hard log bound.
- A fresh 10-GiB local free-floor check and truthful runtime monitoring semantics. Free space shared with unrelated processes cannot be guaranteed continuously by periodic polling; that limitation must be explicit rather than called a hard global floor.

Exact final source/launcher/spec/runtime bindings, fresh one-shot namespace, absence of another substantial job and immediate host admission remain coordinator release requirements. All failed construction/preflight/launch evidence and terminal identities must be preserved; no existing historical namespace can be reused. This preparation permits no SSH, empirical fitting or network execution.

Each proposed case contains one representation. The intended success/late-failure/local cases can establish actual owner/public-route and cross-stage behavior once executed, but do not establish spending across a second View/representation. Numerical/financial fits, real SSH behavior and original graph feasibility remain outside this synthetic proof.
