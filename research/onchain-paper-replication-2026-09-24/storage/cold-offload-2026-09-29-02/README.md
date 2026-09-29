# Cold-file preservation continuation 02

The user-authorized nine-file move remains incomplete after continuation 01
failed on the host RAM reserve. No body received a verified/evicted receipt, all
nine originals remain unchanged, and the partial remote upload is retained.
Continuation 02 uses a distinct local directory, guard identity and remote prefix.
It never executes the old launcher, modifies its receipts or overwrites its
remote objects. Original historical transport owners remain failed.

The per-file preservation algorithm and eight synthetic checks are unchanged:
upload body, download and hash it, upload/download restoration metadata, publish
durable verified receipt and sidecar, recheck original, then remove the local
body. All eight checks pass in green01.log. Exactly 3,584,497,664 original bytes
remain selected, with no raw transaction, graph or SQLite target.

The only resource changes are the user-requested 10 GiB prospective disk reserve
and a 7,200-second wall limit, allowing for observed upload speed near 1.1 MB/s
plus download verification. The time estimate does not guarantee completion.
Memory remains 256 MiB max/192 MiB high, zero swap, 3 GiB host reserve and 3.5 GiB
startup availability. Transfer allowance remains 8 GiB for this new finite
attempt, one file at a time, 512 MiB maximum body-recovery scratch and 32 MiB/s
rate ceiling. Earlier attempted traffic and partial remote bytes remain spent;
the allowance does not erase them. No paid-resource purchase is involved.

The worker binds and verifies the previous terminal receipt and user disk policy,
refuses an active predecessor or any earlier per-file result requiring reuse,
and performs fresh source/owner, local scratch and remote capacity checks. Eleven
source/input bindings are frozen in bindings.json. No empirical claim or model
fit is created. The successful graph-residency verification was separately
committed and pushed as 0973ba64 before this preparation.

On interruption, retain partial remote/scratch objects and reconcile this exact
guard's receipts. Never repeat this identity. On completion, independently close
the nine body/restoration records, original-path sidecars, terminal cleanup and
actual disk-space recovery before reporting the move successful. Restoration
uses the same verified size/hash and absent-original-path procedure documented
in continuation 01; moving a cold file changes its local availability.
