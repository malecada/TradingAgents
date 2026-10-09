from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;F=H.parent;R=Path.cwd();C=F/'mcm-batched-numeric-execution01-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[C/'numeric_execution.py',C/'MANIFEST01.json',C/'RESULT03.json',C/'TEST02.log',C/'TEST03.log',F/'matching-exact-numeric-reuse-review03-2026-10-09/SOURCE_REVIEW01.json',F/'mcm-immutable-pair-executor-review02-2026-10-09/SOURCE_REVIEW01.json',H/'reproduce.py',H/'RESULT01.json',H/'TEST01.log',H/'REPORT.md']
assert sha(paths[0])=='51d8f87f2dfc3392638e2302a4be59b100cb7cab370efc7e2a44156afe653544'
out={'decision':'withheld','scope':'source-only numeric occurrence closure','findings':[{'function':'read_file','failure':'close masks body refusal'},{'function':'NumericExecution._complete_batch','failure':'summary close masks original write failure'}],'required_change':'Preserve primary errors and attach close failures in both inner child-descriptor scopes; cleanup-only failures must propagate.','unchanged_numeric_proof_reused':True,'arrays_or_authority_execution':False,'key_equivalence_independently_recomputed':False,'whole_capacity_or_transport_admission':False,'evidence':{str(p.relative_to(R)):sha(p) for p in paths}}
(H/'WITHHELD01.json').write_text(json.dumps(out,indent=2)+'\n');print(sha(H/'WITHHELD01.json'))
