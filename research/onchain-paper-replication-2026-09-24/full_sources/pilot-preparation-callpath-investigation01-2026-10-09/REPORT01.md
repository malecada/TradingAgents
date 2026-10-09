# Preparation call path (frozen full26; source-only)

Paths below are in tradingagents/research/onchain_replication unless qualified.

real_pilot_import_caller:536–552 loads modules/activates the lease, constructs seven Targets, then calls compact_mcm._prepare on all seven. Those preparation return values are discarded. At558 produce_imported starts again: compact_mcm:295 creates another Target; compact_mcm_batched:431 calls _prepare again, before writing start.json at439–440 or beginning the stage at443. Thus the first MCM intent follows seven eager preparations plus fresh first-graph preparation.

Target construction (imported_mcm_identity:38,52,54,58–59) explicitly requests full boundaries and finishes with check(). check:104–108 adds a full target lease, registered-manifest read, execution.check and final(); final:85 adds another full boundary. _prepare:109 and174 invoke check again. Its job/producer/policy reads at124–129 each use ResearchRun.read_input (lifecycle.py:156–167), which runs _check_source→admit at145–154. This is a concrete repeated Git/source authentication route; cheap _active and compact_owner.verify_current are not themselves full source checks.

Actual reuse is limited: imports reuse Python modules; accepted same-boundary lease results avoid adjacent execution checks; admission deduplicates identical Git extents only within one body batch. Neither caches approval across calls. imported_authority_interval:36 makes boundary=True force full validation regardless of sampling intervals; Lease._full:120–122 checks execution and rereads/authenticates compiled source. No prepare result is reused by produce_imported.

Smallest future operational change: remove the discarded eager Target/_prepare sweep and retain genuine fresh production preparation, all validations and provenance before each stage. This changes failure timing (later-graph refusal can follow earlier completed work), requiring explicit review; it must not imply all-graph prevalidation. No cached authority is needed.

Git-child wait and logical I/O are supplied observations, not profiling attribution. Time per boundary/read/graph hash remains unmeasured; no speed estimate or live change follows.
