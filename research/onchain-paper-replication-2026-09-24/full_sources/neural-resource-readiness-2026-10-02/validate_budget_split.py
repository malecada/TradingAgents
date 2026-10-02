"""Read-only exact partition and unchanged historical draft checks."""
from pathlib import Path
from collections import Counter
import hashlib,json
P=Path(__file__).resolve().parent
R=P.parents[3]
x=json.loads((P/'budget-split.draft.json').read_bytes())
for key in ['existing61draft_pin','inventory_pin']:
 p=x[key];raw=(R/p['path']).read_bytes()
 assert len(raw)==p['bytes'] and hashlib.sha256(raw).hexdigest()==p['sha256']
old=json.loads((R/x['existing61draft_pin']['path']).read_bytes())
inv=json.loads((R/x['inventory_pin']['path']).read_bytes())
assert old==x['existing61draft_preserved'] and old['proposed_ceiling']==61
assert x['spent_preserved']+x['body_batches_preserved']+x['financial_batches_preserved']+x['proposed_resource_attempts']==x['proposed_cumulative_ceiling']==62
assert x['additional_proposed_slots_relative_to61draft']==1
assert x['additional_proposed_slots_relative_to60allocation']==2
n,r=x['claim_slots']; assert n['requirement_count']==9 and r['requirement_count']==23
assert Counter(i['stage'] for i in n['original_requirements'])=={'neural_checkpoint':9}
assert Counter(i['stage'] for i in r['original_requirements'])=={'neighborhoods':7,'matching':7,'mcm':9}
records=n['original_requirements']+r['original_requirements']
ids=[i['original_id'] for i in records]
assert len(ids)==len(set(ids))==32
assert {i['original_id']:i for i in records}=={i['original_id']:i for i in inv['pending_requirements']}
assert x['adoption'] is x['execution_admitted'] is x['sufficiency_claim'] is False
assert x['refunds']==x['historical_claims_reopened']==x['new_financial_fits']==0
assert x['maximum_unique_fits_unchanged']==1420
for s in x['claim_slots']:
 assert s['attempts_proposed']==1 and s['prospective_experiment_id'] is None and s['registration_sha256'] is None
 assert s['execution_admitted'] is False and s['coverage_credit_granted']==0
print(json.dumps({'status':'PASS','neural_cells':9,'remaining_resource_cells':23,'pending_total':32,'original_records_unchanged':True,'existing61draft_unchanged':True,'proposed_ceiling':62,'adoption':False,'identities_reserved':0,'new_financial_fits':0},sort_keys=True))
