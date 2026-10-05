"""Exact continuation charged-byte inventory, no Admission/Run/Owner or science imports."""
from pathlib import Path
import json,hashlib,collections,stat
H=Path(__file__).resolve().parent;B=H.parent;CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');PARENT=CAP.parent.parent/'genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01'
sha=lambda b:hashlib.sha256(b).hexdigest()
def load(p,pin=None):
 b=p.read_bytes();assert len(b)<=4194304 and (pin is None or sha(b)==pin);return json.loads(b)
def save(n,x):
 with (H/n).open('x') as f:json.dump(x,f,sort_keys=True,separators=(',',':'));f.write('\n')
t=load(B/'financial-wrapper-compatible-next-phases-investigation01-2026-10-05/NEXT_INPUT_HANDOFF01.json','8430045d2e2f4ffd64b26b72f063328ed5c68194704c81636044ddeb8485ce41');bridge=B/'financial-wrapper-compatibility-final-source-runtime-bridge02-2026-10-04';old=load(bridge/'FINAL_KNOWN_INVENTORY02.json')['inventory'];proof=load(bridge/'SOURCE_INPUT_RUNTIME_PROOF01.json','ac1ed8a157d7ec113ebe1a8e2eb71a917f46572d0cc8b035c1ee850d9b10730c');refs=proof['compatibility_preclaim_external_refs'];machine=load(Path(refs['recovery_machine']['path']),refs['recovery_machine']['sha256']);external={x['path'] for x in list(refs.values())+machine['recovery_receipts']}
closure=load(CAP/t['reuse_base_inputs_except_plan']['source_closure']['path'],t['reuse_base_inputs_except_plan']['source_closure']['sha256']);target={str(CAP/n):h for n,h in closure['installed'].items()};assert len(target)==195 and len(external)==43
core={}
for x in old:
 if x['path'] in target or x['path'] in external:
  if x['path'] in target:assert x['sha256']==target[x['path']]
  core[x['path']]=dict(x,category='target_source' if x['path'] in target else 'external_review_recovery')
assert len(core)==238
extra={}
for role,x in list(t['historical_roles'].items())+list(t['actual_reference_roles'].items()):
 path=str(CAP/x['path']);extra[path]={'path':path,'bytes':x['bytes'],'sha256':x['sha256'],'role':role,'category':'historical_or_reference'}
assert len(extra)==16 and not set(extra)&set(core);core.update(extra)
for x in core.values():
 p=Path(x['path']);s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and p.resolve()==p and s.st_size==x['bytes']<=4194304
full={x['path']:dict(x,category='previous_reference_known') for x in old};full.update(extra)
# Replace the old draft contract by the genuine final old contract for honest accounting,
# not as a valid future continuation Parent. Future bodies remain explicitly unbound.
full.pop(str(PARENT/'REQUEST_DRAFT01.json'));q=load(PARENT/'REQUEST_FINAL01.json','cfecfd3e12d81628b9bc6f10171dd0345ac6e62c5481edccab64e5207254e03d')
for p in [PARENT/'REQUEST_FINAL01.json',Path(q['final_review']['path'])]+[Path(v['path']) for v in q['proofs'].values()]:
 b=p.read_bytes();full[str(p)]={'path':str(p),'bytes':len(b),'sha256':sha(b),'category':'old_final_reference_only_not_future_authority'}
for n,x in [('CONTINUATION_PLAN_DRAFT01.json',t['next_plan']),('PRIOR_DESCRIPTOR_DRAFT01.json',t['wrapper_prior']),('REFERENCE_DESCRIPTOR_DRAFT01.json',t['wrapper_reference'])]:
 save(n,x)
# The known-set scenario retains the old plan and adds two as-yet-unregistered descriptors.
# Future plan/gate/caller/proof replacement deltas are intentionally not guessed.
for n in ['PRIOR_DESCRIPTOR_DRAFT01.json','REFERENCE_DESCRIPTOR_DRAFT01.json']:
 p=H/n;b=p.read_bytes();full[str(p)]={'path':str(p),'bytes':len(b),'sha256':sha(b),'category':'draft_unregistered_descriptor'}
groups=collections.defaultdict(list)
for x in core.values():groups[x['sha256']].append(x)
base=sum(x['bytes'] for x in core.values());unique=sum(v[0]['bytes'] for v in groups.values());assert base==4288237 and unique==4285558
save('CORE_READ_SET01.json',{'schema_version':1,'status':'IMMUTABLE_REQUIRED_SUBSET_LOWER_BOUND','rows':sorted(core.values(),key=lambda x:x['path']),'first_pass_bytes':base,'finish_inclusive_bytes':base*2,'limit':8388608,'excess':base*2-8388608,'excluded_even_from_this_lower_bound':['current registration gate','current base input bodies not already in subset','new descriptors','current final Parent caller/helpers/contract/release/three proofs'],'no_full_validator_or_admission':True})
save('KNOWN_LAYOUT_READ_SET01.json',{'schema_version':1,'status':'OLD_ACCEPTED_REFERENCE_LAYOUT_PLUS_REAL_NEXT_PREREQUISITES_AND_DRAFT_DESCRIPTORS_NOT_FUTURE_AUTHORITY','rows':sorted(full.values(),key=lambda x:x['path']),'first_pass_bytes':sum(x['bytes'] for x in full.values()),'finish_inclusive_bytes':2*sum(x['bytes'] for x in full.values()),'future_deltas_unavailable':['new committed gate/source map','new wrapper-plan registration path','future external Parent/caller/helpers/final contract','actual outcome/full caller recovery and source runtime proof','genuine final release'],'public_validator_executed':False})
save('DEDUPLICATION01.json',{'existing_external_paths_already_coalesced':43,'original_recovery_receipt_bodies_preserved':38,'reference_roles':5,'historical_roles':11,'core_paths':len(core),'unique_hash_groups':len(groups),'remaining_equal_hash_groups':[{'bytes':xs[0]['bytes'],'paths':[x['path'] for x in xs],'coalescence_permitted':False,'reason':'Both exact committed implementation paths independently required by policy target map.'} for xs in groups.values() if len(xs)>1],'existing_canonical_path_additional_saving':0,'even_forbidden_hash_only_collapse_cost':unique*2,'even_forbidden_hash_only_excess':unique*2-8388608,'conclusion':'No byte-preserving same-path layout of all existing mandatory dependencies can fit the unchanged8MiB Reader. No automatic workaround, refund, cap increase, evidence omission or authority is implemented.'})
print(json.dumps({'core_paths':len(core),'core_read_and_finish':base*2,'excess':base*2-8388608,'known_layout_read_and_finish':2*sum(x['bytes'] for x in full.values())}))
