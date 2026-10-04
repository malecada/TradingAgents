from pathlib import Path
import json,hashlib,collections,stat
H=Path(__file__).resolve().parent;B=H.parent;r=json.loads((H/'READ_INVENTORY01.json').read_bytes());groups=collections.defaultdict(list)
for kind in ['inputs','target_source','external','recovery_receipts','unchanged_helpers']:
 for row in r[kind]:groups[row.get('sha256')].append({'kind':kind,**row})
rows=[]
for pin,items in groups.items():
 if pin and len(items)>1:
  eligible=all(x['kind'] in ('external','recovery_receipts') for x in items)
  rows.append({'sha256':pin,'bytes_each':items[0]['bytes'],'members':items,'coalescible_in_new_external_layout_only':eligible,'charged_savings_if_eligible':2*items[0]['bytes']*(len(items)-1) if eligible else 0,'constraint': 'One new canonical path can satisfy both external roles if exact original filenames/modes and both typed seals are retained' if eligible else 'Distinct source/input/Parent roots or fixed path map must each be authenticated; identical bytes do not permit path substitution or hash-only cache'})
assert len(rows)==9 and sum(x['charged_savings_if_eligible'] for x in rows)==271114
PV=B/'financial-wrapper-compatibility-concrete-policy-review01-2026-10-04';manifest=json.loads((PV/'MANIFEST01.json').read_bytes());m={x['path']:x for x in manifest['members']};layout=[]
for name in ['MACHINE01.json','REPORT01.md','REVIEW_PROOF01.json','MANIFEST01.json']:
 p=PV/name;b=p.read_bytes();entry={'relative_path':'concrete-policy/'+name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'original_path':str(p),'literal_mode':stat.S_IMODE(p.lstat().st_mode),'new_absolute_path':None,'requires_new_actual_copy_and_seal':True}
 if name!='MANIFEST01.json':assert entry['literal_mode']==m[name]['mode'] and entry['sha256']==m[name]['sha256']
 layout.append(entry)
result={'duplicate_body_groups':rows,'external_layout':layout,'eligible_groups':3,'total_saving_charged_bytes':271114,'all38_original_receipt_bodies_required':True,'all13_source_evidence_origins_required':True,'original_recovery_proof_c5cf_bytes_must_remain_unchanged':True,'new_recovery_machine_and_manifest_required':True,'second_fixed_body_coalescence_available':False,'second_option_condition':'Future Parent proof bodies may share an already-required exact path only if the independently authored proof is genuinely identical and satisfies both semantic roles. Existing composed proof cannot substitute for full final Source/Parent recovery. No such additional identical qualifying proof currently exists. If final measured bodies exceed residual203429 unique bytes, stop and obtain separately reviewed byte-preserving dependency-layout change; no cap increase or dropped evidence is justified.'}
(H/'DUPLICATE_PATHS01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'groups':len(rows),'eligible':3,'charged_saving':271114,'new_known_charged':7981750,'all_future_budget_charged':406858,'all_future_budget_unique':203429}))
