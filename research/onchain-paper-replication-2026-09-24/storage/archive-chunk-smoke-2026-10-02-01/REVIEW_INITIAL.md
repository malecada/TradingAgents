# Independent external smoke-run review

External release withheld pending the two boundaries below and final committed binding/gate evidence. Source/test/log inspection only; no SSH request, upload, test or guard launch was performed by the reviewer.

## AT1 — external actions lack their own fresh guard/source boundary

run.py's Transport.run and Transport.get invoke the subprocess receiver without calling the source/guard lease. archive.preserve performs one check and then calls remote mkdir and put consecutively. A successful mkdir may take up to its 30-second command bound before SCP begins. A guard/source revocation during that interval is therefore not checked immediately before upload, contrary to the contract's before-every-external-action promise.

Require a transport-owned live callback immediately before every subprocess, including mkdir/put through run and get's direct receiver. A network-free regression should revoke the callback after mkdir and prove that the upload child cannot start. Preserve the archive's post-callback content checks; adding this boundary must not move an unverified mutation after final content verification.

## AT2 — upload byte reservation is sampled, not an enforced input cap

The inherited transfer.py Transport.put reserves `Path(source).stat().st_size`, then launches SCP with the pathname. SCP opens that path later. Replacement or growth between reservation and SCP open can send more decoded payload than was reserved. A 30-second timeout and 32 Mbit/s rate bound are much larger than the stated 4 MiB payload budget. The download side has an actual expected-byte receiver cap; upload does not currently provide the corresponding guarantee.

Use an upload path that pins the opened source and admits its exact extent/hash, then supplies an explicitly bounded byte stream to the uploader, retaining failure evidence. Alternatively the stated budget must be narrowed to sampled accounting with a frozen-source assumption; that would not establish the advertised hard payload bound. Prefer enforcement with a local reserve-to-open growth/replacement counterexample. Remote immutability is a separate, explicitly unclaimed property.

## Evidence and scope

The inspected receiver drains stderr to a bounded tail, caps stdout to expected bytes plus the detecting byte, has finite command waits and kills/waits the direct child on failure. Strict known-host, BatchMode and explicit identity options are inherited from the preserved transport. No credential contents were read. Remote member names are restricted, remote directory creation is exclusive, and downloads use exclusive local linking followed by removal of only the staging name. Intermediate dual links remain failure evidence. The normal decoded payload reservation is 1,048,576 uploaded bytes plus two 1,081,344-byte dd caps, or 3,211,264 bytes, below the 4 MiB allowance. SSH framing/handshake overhead is excluded.

The combined saved log reports **34 passed in 0.47 seconds**. The three new transport cases run local subprocesses and verify bounded download/excess/budget behavior and remote-name refusal. They do not prove actual SSH/SCP behavior, AT1/AT2, production launch-gate enforcement, remote durability or independent host recoverability. Local archive AC1/AC2 corrections are separately recorded in REVIEW02.md.

At inspection, bindings.json had 120 entries and every entry matched current bytes; the inherited transport, runner, contract and transport test were included. Manifest SHA was `104a339af72b02c41e766082bf887e007122d9a3190cac025796073fc5c44ef4`. The launcher compares that manifest to HEAD and pins its hash into guarded argv; the worker repeats file-map hashing. This is useful static protection, but final post-correction manifest/commit equality and its pending gate test must be checked before release. No claim that the current uncommitted gate is already admitted is made.

The intended 512 MiB/384 MiB, zero swap, two-CPU, 180-second guard and 10 GiB local floor match the reviewed resource API calls. This is only one deterministic 1 MiB synthetic member and two readbacks, using existing storage. It is not bulk capacity/throughput, remote retention availability, eviction, compact terminal archive substitution or empirical admission.

Inspected runner SHA-256: `e3879cd33b6e979f3fece61a9914aac9dcce40d81d131081c77347cde304da08`.
