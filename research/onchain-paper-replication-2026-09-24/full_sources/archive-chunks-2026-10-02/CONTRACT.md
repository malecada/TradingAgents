# Bounded archive chunk prototype

Task 8 storage engineering; no empirical admission or history migration.
Implement a transport-neutral immutable chunk round trip with a maximum 8 MiB
member, trusted expected hash/extent, source snapshot, exclusive local attempt,
exclusive remote object directory and independently retrieved bytes. A returned
receipt binds the declared scientific scope, transport identity, remote member
and verified content. Fresh retrieval checks pinned receipt bytes and fetched
content without needing the original local source. Every failure retains local
and remote partial evidence and refuses replay of the same local attempt.

The caller must supply an already frozen member, trusted source hash, actual
transport with exclusive mkdir, bounded put/get, finite deadlines, network
budget and OS guard. The prototype does not prove closure/eligibility from a
hash, remote immutability, remote independence, crash-atomic filesystem snapshots,
physical storage upper bounds or caller admission. It never evicts any source or
cache file and does not yet change compact log/checkpoint/terminal readers.

Tests use a filesystem-backed transport as a synthetic remote only. Production
SSH adapter and actual external round trip require their own bounded verification.
The first integration target is sealed compact event chunks, preserving all
event bytes and ordering; scientific algorithms and production dimensions stay
unchanged. Eviction remains unavailable until remote readback is integrated with
full owner/stage/terminal validation and independently reviewed.
