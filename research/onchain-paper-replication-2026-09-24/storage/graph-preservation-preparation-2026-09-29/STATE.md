# Graph preservation preparation

The two original completed pilot graph stores comprise12files and1,037,095,664
bytes. Their saved array hashes, file sizes and modification times are captured
in inventory.json; no arrays were decoded or reread by this metadata/stat step.
The existing preservation planner yields3bundles under its512MiB member/batch
ceiling. The largest file is344,248,088bytes, so both completed graphs fit that
existing whole-file mechanism without a representation change.

No upload, round-trip recovery, backup claim or deletion occurred. The existing
59083-file ETH raw backup does not cover these graph arrays. A later bounded
preservation contract must bind this inventory, the current preservation and
transport sources, the existing approved Storage Box connection metadata, unique
local/remote output identities, capacity/transfer limits and exact round-trip
verification. Sources must be rehashed while packing; this inventory alone is
not fresh array verification or an external recovery copy.

The separate Data volume has about23.98GB free at this checkpoint. With a20GiB
floor it can stage one512MiB archive and its recovery copy without using the
narrow root-volume headroom allocated to the prospective graph pilot. Fresh
capacity checks and explicit volume monitoring remain required; no output path
has been reserved by this preparation.

The old interrupted largest-week SQLite is3,755,212,800bytes and exceeds the
existing whole-file512MiB bundle ceiling. It is not included here. Preserving it
remotely needs a separately reviewed streaming/chunked recovery contract or a
larger admitted scratch arrangement; simply increasing the bundle cap would
require two large temporary copies and currently exceed the Data-volume reserve.
The original database remains untouched. New pilot graph/SQLite artifacts will
also require preservation after closure. C16 remains partial.

## Subsequent local relocation

Four reviewed inactive failed-transport tar files were relocated byte-for-byte
to the Data volume; original paths remain symlinks to verified copies. See
relocation-complete.json and relocation-guard01/final.json. All four copies and
original-path reads passed SHA-256 checks; no original transaction, graph or
SQLite file was moved. This is local preservation, not an external backup.
The Data destination must remain mounted and protected while those paths depend
on it. No historical claim/terminal or source manifest was changed.

After relocation, Data free22,207,119,360bytes leaves732,282,880above the20GiB floor.
The earlier two512MiB-copy staging assumption is no longer feasible (short by
341,458,944bytes before additional metadata). A reviewed smaller-batch/streaming
contract or additional capacity is required before graph backup execution. No
backup was started; inventory bytes and broader preservation requirements remain.
