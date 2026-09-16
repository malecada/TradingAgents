# Independent storage review

All 117 retained January 1 column-range bodies match their original base64 receipts byte for byte after direct zstandard decompression. Original input hashes match the committed plan before and after verification. Raw/stored SHA-256, lengths, frame checksums and declared content sizes pass; reported aggregate benchmark totals reconcile exactly. No storage-helper validation routine, network acquisition, Parquet decoding or motif computation was used.

| Same 117 ranges | Bytes |
|---|---:|
| Raw bodies | 118,730,958 |
| Base64 payload characters | 158,308,100 |
| Original receipt JSON | 158,407,617 |
| Original JSON overhead excluding base64 | 99,517 |
| Zstandard bodies | 88,331,098 |

Zstandard bodies occupy 74.40% of raw bytes and 55.76% of original JSON bytes. Compression saved 30,399,860 bytes versus raw bodies and 70,076,519 bytes versus base64 receipts. These comparisons exclude the new metadata, which is accounted for separately below.

| Preserved partial artifact tree | Files | Bytes |
|---|---:|---:|
| baseline_zstd | 117 | 88,331,098 |
| capture_zstd | 454 | 377,443,650 |
| derived_zstd | 231 | 207,616,733 |
| metadata_json | 917 | 1,380,122 |

The partial artifact tree totals 674,771,603 bytes across 1,719 files. Its metadata JSON occupies 1,380,122 bytes. Additional source and derived blobs are distinct data products, not metadata overhead. The partial tree is a snapshot after interruption; it is not a full-week total. Retained original stores remain present, so compressed copies do not imply reclaimed disk space.

The original benchmark recorded 0.499936 seconds of compression and 1.191030 seconds for compression, durable publication and roundtrip verification. Those timings were not independently reproduced. The independently verified compression ratios describe this retained 117-range sample only; no completed seven-day or full-history storage claim follows.
