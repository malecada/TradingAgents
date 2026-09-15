import json,hashlib,time
from pathlib import Path
from tradingagents.research_options_capture.control import inventory,canonical
begin=time.monotonic();root=Path.cwd();items,claims=inventory(root)
result={'scope':'Read-only structural/hash verification of actual retained history; no economic output parsing or empirical execution','history_count':len(items),'complete':sum(x['terminal']=='complete.json' for x in items.values()),'failed':sum(x['terminal']=='failed.json' for x in items.values()),'prior_claims':items,'prior_claims_sha256':hashlib.sha256(canonical(items)).hexdigest(),'elapsed_seconds':time.monotonic()-begin}
assert (result['history_count'],result['complete'],result['failed'])==(19,16,3)
path=root/'research/strategy-search-2026-09-11/reviews/options-current-history-20260915.json'
with path.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
