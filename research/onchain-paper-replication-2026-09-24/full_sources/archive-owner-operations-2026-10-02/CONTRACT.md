# Durable current-owner archive operation reservations

This continuation consumes an accepted prospective selection under the actual
compact owner's nonblocking transition lock. It binds one deterministic fresh
archive-operations namespace next to the owner's compact namespace; the original
stage inventory is unchanged. The selection must still describe a fresh owner.

One writer claim is permitted per actual owned stage. Writer reservation retains
the full stage event capacity for remote payload and three decoded member passes
(upload, copy readback and final writer replay). Each later reader claim reserves
one full event capacity and consumes one of the finite registered verification
slots. A single active operation and nonblocking owner transitions prevent
interleaved claims. Intent publication precedes handing the claim to its caller.
Failure or interrupted intent is spent; no refund, reopen or alternate identity
is provided. All evidence is retained. Control metadata adds an explicit maximum
of three metadata records per possible writer/read and four fixed records.

This is a reservation mechanism, not transfer metering. Raw put(source, member)
cannot bind transferred size safely from a preceding stat: the immutable upload
snapshot needs its own charge before dispatch. Diagnostic overread, protocol
framing and physical storage remain additional bounds. A completion reference
records caller acknowledgement, not scientific verification. No producer,
writer, stage-seal, publication or post-owner-closure route is switched here.
Those integrations must consume claims, check their live leases at each dispatch
and verify the actual content before completion. No empirical admission follows.
