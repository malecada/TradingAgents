# Independent external synthetic result review

Accepted as successful closure of the single authorized external synthetic copy/readback attempt. This is a bounded external recovery result, not an admission of bulk storage, eviction or empirical execution. Review used retained local bytes, receipts, source bindings and process/cgroup observations only. No transfer, SSH request, test or numerical job was repeated.

The exact reviewed binding inventory SHA is `1f106a225ec98245f43c4fab47388a0773300687112dc401cdc4b1d5688f01d6`. All **120 entries** match both current file bytes and their blobs in committed gate `6bbcc0a9a006b9e22b0df8127d96bf3ca3f83ff2`; the inventory itself matches that commit. The guard command pins this same inventory hash in worker argv. The parent reports remote push verification before launch; this review independently checked the local committed gate and did not repeat a remote Git request.

Each of synthetic.bin, copy01/snapshot.bin, copy01/readback.bin and read01/payload.bin is a regular single-link **1,048,576-byte** file. Independent byte comparison to `bytes(range(256)) * 4096` passed for all four, as did SHA-256 `fbbab289f7f94b25736c58be46a994c441fd02552cc6022352e3d86d2fab7c83`. Preservation and fresh-retrieval inventories are exact, their intent/completion bytes agree, receipt hashes join correctly, and the receipt scope equals the reviewed contract hash. No failed.json markers were found in this attempt tree. The source and all downloaded bytes remain retained.

The two silent command diagnostics and two payload download diagnostics all record complete status and child return code zero. Both downloads received exactly 1 MiB within their 30-second command bounds. The second uses the separate transport02 instance with no prior per-upload size state. This is fresh-transport recovery in the same guarded worker, not a separate-process or later-host restoration test. The source/receipt joins and fixed expected bytes provide the independent content comparison. Normal reserved decoded payload is exactly **3,211,264 bytes**, within the 4 MiB contract; framing, handshake and diagnostic overhead retain the stated exclusions.

The raw guard final records phase complete, workload exit zero, no limit reason and verified cleanup after **2.999160738 seconds**. Kernel settings are memory.max 536,870,912 bytes, memory.high 402,653,184 bytes and memory.swap.max zero. CPU readbacks use CPUs 0 and 1. Initial, sampled-final and terminal memory event counters are zero, including OOM and OOM-kill. Peak sampled memory.current is **37,412,864 bytes**; this is sampled cgroup memory, not a continuous peak-RSS bound. Local free space remains above the recorded 10 GiB floor. The unit is inactive/dead with an empty ControlGroup; cleanup stop returned 5, so success is based on the verified terminal/unit observations rather than a claimed successful stop command. At review the recorded cgroup path and monitor PID were absent.

The actual run establishes that the sealed memfd upload path works with the chosen SCP route and that the one prebound synthetic remote member can be retrieved twice with exact content. It does not establish remote immutability, indefinite availability, full raw-store backup, bulk bandwidth, peak-live archive capacity, compact owner/stage/terminal archive integration, local disposal eligibility or any financial result. Prior retained research artifacts were not part of this upload and were not migrated. No repeat of this terminal attempt is justified by this acceptance.

Direct evidence SHA-256:

- complete.json: `1e87cd77cfaf28703e81f2792f4578b2f146f87d1c527b5997feea5516b424a8`
- intent.json: `ea0a197073db52aad1517292e1dbdef246dbf05a021c1e528e79e0f68f4a6422`
- copy01/complete.json: `d5037cb5db11393e89963af58b160961ee864ae5537cc2c67f847c471a526d02`
- read01/complete.json: `ca45fbf0ea2fd99a13dcc7eaaed0ab7323e0a55c72ff5373da368597a5e1f192`
- guard01/final.json: `3c68bebdab9cfe1042088ccd74db9ed23c1c5452745974eb8c75a411e7e45d4c`
- guard01/child_exit.json: `8f37aab7026d70a323da1926912cfca87629a22d60fc82e8ce742f634652e45d`
- guard01/release.json: `82560e2694628ad002f9cc4b76fe2cd7b1b545cc825269f01057f04c6fe268b5`
- external01.log: `e87caa4e43fc0a50c1cf1af63a6eaf38d138795468c46ae872a32dbc04ea9143`
