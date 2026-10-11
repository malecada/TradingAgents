# One synthetic serializer timing

One execution completed exit0 (tool chunk a53ea0); no failures, empty stderr. No research module was imported. AST extraction executed only original provenance canonical_bytes/thaw and accepted serializer02 _current_bytes. Source/review pins are in RESULT01.json and checked before extraction.

The exact fixture is retained as FIXTURE01.json; measure01.py preserves its construction, including tuple tags. It contains421 synthetic nested source records,67 synthetic input references and7 graph-shaped metadata records. These are invented scalar metadata, not genuine inputs, graph arrays or authority. Both functions received the SAME object each call. Every output was freshly serialized and byte-compared; no successful serialization or validation was cached.64 timed calls (32 per route), fixed ABBA order,16 calls per block. Initial equality checks were untimed.

Canonical output:79166bytes, SHA256 7e2e045ee21b780cbbc69e594f869454d907f51be717f86bc14ee7107d8c3535.

| Route |32-call wall seconds|32-call CPU seconds|Wall milliseconds/call|
|---|---:|---:|---:|
| Original canonical_bytes |0.073414968|0.073994523|2.2942|
| Serializer02 |0.032289594|0.032004560|1.0090|

Candidate elapsed was about56.0% lower on this one plain-container synthetic fixture. This includes identical output-equality comparisons. It is not a confidence interval, actual Target/lease cost, pilot saving or capacity result. Frozen-mapping fallback performance was not measured; no previous review matrix was replayed. Compiler/audit-hook/currentness semantics outside the accepted candidate scope are not strengthened by this timing.

Actual interpreter Python3.13.13; CPU affinity exactly{3}; nice10; hard/soft CPU10seconds, AS512MiB, FSIZE4MiB; external wall timeout15seconds. Whole script measured0.112273151seconds wall/0.111998794seconds CPU, ru_maxrss19032KiB. Active native CPUs0,1 were not used. No actual Target/Owner/Lease/Run, scientific/native package imports, live receipt/process reads, arrays, benchmark workers or source changes. No rerun is needed for this bounded observation.
