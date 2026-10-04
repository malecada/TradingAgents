from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;F=D.parent
names={
'policy':'financial-wrapper-compatibility-root-policy01-2026-10-04',
'policy_review':'financial-wrapper-compatibility-concrete-policy-review01-2026-10-04',
'delta':'financial-wrapper-compatibility-operational-delta-capture02-2026-10-04',
'failed_delta':'financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04',
'old_capture':'financial-wrapper-complete100-failed-outcome-capture02-2026-10-04',
'old_root':'financial-wrapper-complete100-failed-root-remote03-2026-10-04',
'old_review':'financial-wrapper-complete100-failed-full-recovery-review03-2026-10-04',
'baseline_capture':'financial-wrapper-complete100-baseline-capture01-2026-10-04',
'baseline_root':'financial-wrapper-complete100-baseline-remote01-2026-10-04',
'baseline_review':'financial-wrapper-complete100-baseline-actual-flat-review01-2026-10-04',
'adoption':'financial-wrapper-compatibility-root-integration01-2026-10-04',
'adoption_review':'financial-wrapper-compatibility-root-source-adoption-review01-2026-10-04',
'actual_adoption_review':'financial-wrapper-compatibility-actual-source-adoption-review01-2026-10-04',
'receiver':'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04',
'remote_review':'financial-wrapper-compatibility-operational-delta-remote-outcome-review03-2026-10-04',
'flat_source_review':'financial-wrapper-compatibility-operational-delta-flat-source-mode-review04-2026-10-04',
'entry_review':'financial-wrapper-compatibility-operational-delta-flat-entry-review05-2026-10-04',
'control':'heartbeat-root-checkpoint10-2026-10-04'}
# Correct source review directory is discovered by exact machine body pin, without executing anything.
for p in F.glob('financial-wrapper-compatibility-operational-delta-*review04-2026-10-04/MACHINE01.json'):
 if hashlib.sha256(p.read_bytes()).hexdigest()=='c1f124a6952a3006d8b4f6f4669cf0d5a2768343cfbd94f7004d586505f76f98':names['flat_source_review']=p.parent.name
paths={k:str(F/v) for k,v in names.items()}; pins={}
def pin(p):
 assert p.is_file() and p.stat().st_size<=4194304
 pins[str(p)]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
for role in ['policy','policy_review','delta','failed_delta','old_capture','baseline_capture','old_review','baseline_review','actual_adoption_review','adoption_review','remote_review','flat_source_review']:
 for p in sorted(Path(paths[role]).iterdir()):
  if p.suffix in ('.json','.gz') and p.name not in ('READBACK01.json','CURRENT02.json'):pin(p)
for role in ['old_root','baseline_root']:
 for n in ['FLAT_RECOVERY01.json','REMOTE_RECOVERY01.json']:pin(Path(paths[role])/n)
for n in ['SOURCE_ADOPTION_AFTER589.json','SOURCE_ADOPTION_DRAFT01.json']:pin(Path(paths['adoption'])/n)
for n in ['ROOT_FLAT04_INSTALLATION_DRAFT01.json','REMOTE_RECOVERY01.json','SELECTED_BODIES01.json','ROOT_REMOTE03_EXIT01.json','COMPLETED_REMOTE03_READ_ONLY_SELECTED_MODE_PROFILE01.json']:pin(Path(paths['receiver'])/n)
pin(Path(paths['control'])/'root_operational_flat05.py')
obj={'schema_version':1,'paths':paths,'fixed':pins,'future_required_names':['FLAT_RECOVERY01.json','FLAT_POSTWRITE_OBSERVATION01.json','ROOT_FLAT05_INTENT01.json','ROOT_FLAT05_SPAWN01.json','ROOT_FLAT05_EXIT01.json','ROOT_FLAT05.stdout','ROOT_FLAT05.stderr'],'future_independent_outcome_review':'Required separately by Root before issuing actual recovery proof; this checker emits observations only.'}
(D/'INPUTS01.json').write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n')
print(len(pins),names['flat_source_review'])
