"""Independent metadata-only final target binding reconstruction."""
from pathlib import Path
import json,hashlib,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];P=ROOT/'research/strategy-search-2026-09-11'
def read(p):return json.loads(p.read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
gate=read(P/'gates-dated-mark.json'); name='dated-mark-20260911'
target={k:v for k,v in gate['experiments'][name].items() if k!='budget_extension'}
parent=read(ROOT/'research_runs/dated-book-amended-20260911/claim.json')
baseline=parent['experiment'];manifest=read(P/'dated-extension-changes.json')
delta={}
for key in set(baseline)|set(target):
 if key not in baseline or key not in target or canon(baseline[key])!=canon(target[key]):
  delta[key]={side:{'present':key in value,**({'value':value[key]} if key in value else {})} for side,value in [('before',baseline),('after',target)]}
assert manifest=={'schema_version':1,'baseline_experiment':parent['experiment_id'],'target_experiment':name,'baseline_contract_sha256':sha(canon(baseline)),'target_contract_sha256':sha(canon(target)),'changes':delta}
inventory={};family=gate['families'][target['family']];old_specs=[]
for folder in sorted((ROOT/'research_runs').iterdir()):
 if folder.name.startswith('.'):continue
 claim=read(folder/'claim.json')
 if claim['family']['mechanism_id']!=family['mechanism_id']:continue
 assert folder.name!=name,'target already claimed'
 assert claim['family']==family
 terminal=[p for p in [folder/'complete.json',folder/'failed.json'] if p.exists()];assert len(terminal)==1
 inventory[folder.name]={'claim_sha256':sha((folder/'claim.json').read_bytes()),'terminal':terminal[0].name,'terminal_sha256':sha(terminal[0].read_bytes())}
 old=json.loads(subprocess.check_output(['git','show',claim['source']+':'+claim['registration']],cwd=ROOT));old_specs.append(old)
 for group in ['families','experiments','datasets']:
  for key,value in old[group].items():assert gate[group][key]==value,(group,key)
 latest=subprocess.check_output(['git','show',parent['source']+':'+claim['registration']],cwd=ROOT)
 assert (ROOT/claim['registration']).read_bytes()==latest
assert len(inventory)==4 and inventory==read(P/'dated-extension-prior-inventory.json')
assert family['attempt_budget']==4 and family['prior_attempts']==1
for path,digest in target['source_files'].items():assert sha((ROOT/path).read_bytes())==digest,path
for item in [target['charter'],*target['inputs'].values()]:assert sha((ROOT/item['path']).read_bytes())==item['sha256']
preflight=read(P/'dated-extension-preflight.json');assert preflight['status']=='pass' and preflight['target_experiment']==name and preflight['change_manifest_sha256']==sha((P/'dated-extension-changes.json').read_bytes())
assert len(preflight['reports'])==10
for item in preflight['reports']:assert sha((ROOT/item['path']).read_bytes())==item['sha256']
# Preserve every object from the latest otherwise unrelated options registration too.
latest=read(P/'gates-options-entry.json')
for group in ['families','experiments','datasets']:
 for key,value in latest[group].items():assert gate[group][key]==value,(group,key)
report={'passed':True,'scope':'Final local source/metadata bindings only; no admission, network or financial calculation. Commit/design equality remains an execution-time requirement.','target_contract_sha256':sha(canon(target)),'change_manifest_sha256':sha((P/'dated-extension-changes.json').read_bytes()),'preflight_sha256':sha((P/'dated-extension-preflight.json').read_bytes()),'inventory_sha256':sha((P/'dated-extension-prior-inventory.json').read_bytes()),'current_prior_program_claims':len(inventory),'historical_administrative_units':1,'original_cap':4,'consumed_effective_cap':5,'named_target_only_effective_cap':6,'source_pin_count':len(target['source_files']),'runtime_pin_count':len(target['runtime_hashes']),'preflight_reports_checked':10}
(Path(__file__).parent/'dated-extension-bindings-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
