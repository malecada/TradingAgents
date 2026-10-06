# Packed archive control successor03 — narrow cleanup/type correction

Predecessor02 and manifest027d9812462e59977dcb64270018d40f938ce6b8fe471b2ef89f2acb9ce34bf8 remain byte-preserved and WITHHELD for these seams. The successor is a candidate only; no live source, Git, gate, data, Owner or native execution changed.

`archive_read_controls.audit` now sends both shard and directory close through the existing `io._cleanup(..., primary=sys.exc_info()[1])`. This retains established actual-fatal precedence, attempts each owned descriptor once and keeps ordinary content/cleanup errors together instead of masking the primary or replacing an earlier close error. No new cleanup framework or descriptor retry is introduced.

`archive_read_control_capacity.policy` now requires exact int type for shard_bytes as well as schema_version. Float4194304.0 is refused directly, before any controls-directory birth.

Only those two candidate files changed. Seven other candidate source files are byte-identical. INVERSE03 records exact before/after hashes and proves literal reversal plus AST equality for all9 files. Original metadata/runtime source pins and ARITHMETIC02 are copied byte-for-byte. Full CANDIDATE03.patch and the two-file DELTA03.patch are provided. Numerical/event/raw-receipt/budget/16-verification arithmetic is unchanged.

## Focused RED02 → GREEN03

Three regression groups exercise the actual audit with synthetic journal bytes and real descriptors. Close faults first reap the actual descriptor, then raise OSError; no descriptor is retried.

1. KeyboardInterrupt, SystemExit and MemoryError primary objects plus both shard/directory close errors:02 returns masking OSError;03 preserves each identical original fatal object.
2. Ordinary receipt mutation plus both close errors:02 returns the last OSError;03 raises CleanupFailure retaining the original ValueError and both actual close exceptions in order.
3. Float shard policy:02 direct policy validation accepts it;03 rejects it. Controls directory is absent on refusal.

Every actual audit case opens2 descriptors and reaps both exactly once. RED02 has the expected nonzero exit; GREEN03 passes all3 groups/3 fatal subcases. Tests run in checkout-local .venv with -B, stdlib source IO, network/subprocess/numerical-import refusal and temporary files confined to this owned directory. The13 prior checks are reused for unchanged behavior; no broad replay/profile matrix was repeated.

Root's independent review of the remaining packed route, exact current baseline, lifecycle/cache bounds, actual scan timing, metadata/source rebinding and admission remain outstanding. No new capacity or execution authority follows from these regressions.
