# Independent external recovery verification

Verified actual byte recovery from the configured origin at exact commit `c51e868f8338ee0a8310251afaefe9e0695daf4f` into the new isolated bare repository `/home/malecada/master_thesis/onchain-fixture-isolation/owner-backup-verification-20261002-01/remote.git`. This is stronger than a remote-HEAD observation: the recovery archive and both metadata files were independently downloaded and their contents checked. Remote endpoint and credentials are not recorded in this report.

The server advertised fetch filtering before any fetch was attempted. A depth-one, blob-filtered fetch recovered the requested commit; the remote branch pointed to that same commit at the capability check. The recovered repository contains one commit,3,832 trees and exactly three blobs. Only the recovery archive, retained-tree01.json and execution-result01.json blobs were fetched. A separate local object inventory with lazy fetching disabled verifies those counts.

| Retrieved object | Bytes | SHA256 |
| --- | ---: | --- |
| retained-tree01.tar.gz | 10,494,538 | 82529f2e17a1535620e30898265f31f8b235c749d34189e14cc299eec64ef8bd |
| retained-tree01.json | 948,060 | bf6faa8b80b36e0cd5e7a35bc12e098789648f5c3da51cfbe3553f58fcbecada |
| execution-result01.json | 3,051 | c64c7949d8bcea5a020ee7779597740ccb1ae933896d8276670d2580c27ef379 |

The independently retrieved execution result correctly binds the retrieved manifest and archive hashes. Streaming inspection rehashed all3,822 regular archive members against the independently retrieved manifest, including exact sizes and modes. All file names are unique, canonical, inside the expected `archive-outer-owner-20261002-01` root and exactly equal to the manifest file set. All1,287 directory members have zero payload, canonical names and complete parent joins; links, special entries, duplicate/foreign members and traversal paths were rejected. Totals are5,109 members and31,547,239 logical regular-file bytes. No archive member was extracted or executed.

All eight network/Git retrieval commands completed successfully; the longest took about2.93 seconds. Each had a120-second limit,64MiB per-file ceiling,128MiB isolated-tree ceiling and1MiB command-error/packet-log limits. Retrieved stdout was additionally bounded to the expected object size. The isolated verification tree was23,827,625 bytes before adding final result/object-inventory records. The separate object-inventory command was bounded to30 seconds and1MiB output. No unfiltered fallback, full clone, credential inspection, shared-owner mutation or empirical/model/guard execution occurred.

Machine evidence is REMOTE_RECOVERY01.json, SHA256 `b492273f6719f395c936f9ef885f9996ef682189adeb81453cdf616fd07ad890`. The isolated verifier, bounded raw command logs, downloaded files, bare objects and object inventory remain retained. The shared frozen owner tree was untouched.

This establishes recoverable remote bytes for this exact retained owner bundle at this observation. It does not guarantee future provider availability or permanent retention, independently validate the scientific meaning of every restored file, restore historical inode/allocation/timestamp identity, prove a clean-environment rerun, or authorize rerunning the closed owner identity. Original source/results/failed history remain preserved; code execution and recovery into a live working directory were deliberately outside this verification.
