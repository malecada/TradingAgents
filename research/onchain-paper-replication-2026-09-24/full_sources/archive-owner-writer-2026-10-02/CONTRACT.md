# Reserved actual archive writer execution

The next additive boundary executes the maintained ArchivePairLog for an actual
current-owner stage under one durable writer reservation. A public entry captures
and holds the actual owner transition lock through claim, callback, archive
finalization, reservation completion and final local evidence checks. Inner
leases and completion use explicit nonlocking internal ledger operations while
that transition is owned. An expired callback lease or nested public execution
must refuse. No historical writer or completed claim is reopened.

The registered stage scope, event limits, numerical iteration limit, archive
policy and transport are selected from the actual owner/Selection. The caller
may run the maintained CompactMatcher; its return value is not independently
validated by this wrapper. The wrapper finalizes the actual archive, which fully
replays remote events, pins the original source inode/start/terminal/completion,
and after reservation callbacks rechecks local metadata/inventories without
spending an unclaimed extra remote replay. Remote bytes are observed during the
writer's replay, not continuously afterward. Checkpoint/scientific result joins
and producer publication still require the separately implemented stage route.

Failure retains the actual log and writer reservation, poisons the consumed
owner, and preserves primary cause and fatal cleanup. This does not implement
transport metering, replace existing producer/sealer/publication contracts,
permit post-owner-close reads or admit a financial experiment. The future outer
producer integration must arrange this same exclusive transition without
recursive acquisition; merely testing whether a generic Lock is held is not
proof that the calling thread owns it.
