import json
from pathlib import Path
from tradingagents.research.onchain_replication import real_pilot_import_caller as caller,compact_policy,stage_retention
F=Path("research/onchain-paper-replication-2026-09-24/full_sources")
p=json.loads((F/"real-data-pilot-diagnostic-composition01-2026-10-08/pilot_draft02.json").read_bytes());caller.validate_plan(p)
c=json.loads((F/"real-data-pilot-capacity-selection03-2026-10-08/compact_policy.json").read_bytes())
compact_policy.validate(c["stage_policy"],kind="mcm",pairs=72495392)
stage_retention.validate(c["stage_policy"]["restart_retention"],c["stage_policy"]["pair"])
print(json.dumps({"status":"ACTUAL_INSTALLED_METADATA_SCHEMAS_PASS","graphs":len(p["graph_inputs"]),"examples":len(p["graph_sequences"]),"outputs":len(p["outputs"]),"empirical_execution":False}))
