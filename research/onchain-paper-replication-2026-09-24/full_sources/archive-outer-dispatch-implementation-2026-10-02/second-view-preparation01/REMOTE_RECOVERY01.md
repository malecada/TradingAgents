# Independent remote recovery of the closed two-View attempt

**Verified recovery from the configured origin of exact commit `aff909645ac341b3cd8f004f8c39987ac1ae7fff`.** Remote branch HEAD matched this commit at the capability check. The server advertised filtering before the fresh depth-one `blob:none` fetch. Final isolated object inventory with lazy fetching disabled contains one commit, 3,839 trees and exactly three blobs; no full-clone fallback occurred.

The only remotely retrieved file blobs were:

| File | Bytes | SHA256 |
| --- | ---: | --- |
| retained-tree01.tar.gz | 10,259,036 | `d95e68f8c88ed72495ef99ff72437967c93aa75f5665dd7c837eb5314d90de24` |
| retained-tree01.json | 1,136,382 | `2fe57891f77ea4298082ed055e9711c3c65b0b42b6eb8b99008584e520049616` |
| execution-result01.json | 4,469 | `b94424c117df8b38929cda6c76f56cbdeecf660a5af36f198e22e92fa1f863eb` |

All three hashes and lengths match the requested pins. The remotely retrieved execution result joins the independently retrieved manifest and archive. Streaming the remote archive verified all 3,764 regular members by size, content SHA256 and mode, plus all 1,182 directory members and modes. Exact membership, canonical relative paths, the literal `retained/` root prefix, parent directories, duplicates and prohibited special/link types were checked. The complete 4,946-member tree contains 27,956,390 logical regular-file bytes. No member was extracted, no local original archive was substituted, and no recovered code was executed.

The first verifier fetched all three blobs successfully, then stopped because it incorrectly assumed the archive root prefix was the fixture identity. The actual archive prefix is `retained/`. That original script, failed verification result and every retrieval log remain preserved. A separately saved second verifier corrected only the offline member-prefix assumption and rehashed the same remotely retrieved blobs; it performed no network operations. No fetch or empirical identity was relaunched. The corrected verification completed successfully, including the no-lazy-fetch object inventory.

All eight retrieval-related Git commands exited zero; the longest took approximately 3.032 seconds. The bounded object-inventory command also exited zero. Per-command timeout was 120 seconds, individual file-size limit 64 MiB, isolated-tree allowance 128 MiB and stderr/packet limits 1 MiB. The isolated tree occupied 23,583,046 logical bytes before final report publication. Source endpoint configuration was ephemeral and printable fetch stderr was redacted; no credential or remote URL is shown in these reports.

The isolated bare repository, retrieved blobs, capability trace, raw command logs, initial failed verifier and corrected offline verifier are retained at `/home/malecada/master_thesis/onchain-fixture-isolation/archive-two-view-backup-verification-20261002-01/`. `REMOTE_RECOVERY01.json`, SHA256 `d3bc7757b6e627d6b412533f1aae1d6d12f5ae721293403fbe9ccdb07c14405c`, records their hashes and the explicit correction history.

This establishes recoverable bytes for the complete retained closed two-View root at the observation time. The result's 12 outer evidence references were not separately downloaded in this three-blob verification; their remote contents are not independently attested here. Remote recovery does not convert the failed fixture into a pass, identify its unrecorded transient-hardlink path, establish real SSH transport capacity or prove permanent remote retention. Prior owner/neural recovery evidence was not used as a substitute for this retrieval.

Only these new reports and the separately owned isolated verification directory were written. Shared HEAD, production source, runtime, registrations, inputs, original owner tree and empirical state were not changed. No guard, model, financial job, source mutation or retry of a closed workload occurred.
