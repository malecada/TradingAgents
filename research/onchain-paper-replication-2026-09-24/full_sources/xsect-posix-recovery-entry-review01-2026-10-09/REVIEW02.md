# Source review02: filesystem correction accepted

Source-only acceptance applies to restore.py f3b1f132a9474c8e3f5df7eb30e885b465bd75e65930a063bfbd634d0da49dad and unchanged bind.py48ab44cdbc4dce983c8fc7112cd6cf14578f4cd4056863b577a6249da1ba815b. Earlier review/tests remain preserved and cover the unchanged integration.

The exact literal inverse removes only the new target-parent canonical/same-device/allocation-block check and final eligibility call, recovering prior reviewed restore hash78ca4a2b. Actual read-only metadata checks confirm the fixed target parent shares ROOT's device and reports4096-byte fragment size; the same extracted source branch refuses4097. Source pins in the updated draft match. Added eligibility after all batches rechecks actual closure, remaining modeled reserve and floor before whole verification. No repeated matrix, positive closure fixture, network, original data or restoration was used.

These changes resolve the prior report's target-filesystem entry condition at source level and current metadata observation; final launch still repeats the checks. CHECK02/TEST02 preserve results. Draft and unavailable final evidence remain unadmitted. Actual29batch backup binding, native22/backup closure, exact final contract/release and fresh headroom remain required. No final release is issued.
