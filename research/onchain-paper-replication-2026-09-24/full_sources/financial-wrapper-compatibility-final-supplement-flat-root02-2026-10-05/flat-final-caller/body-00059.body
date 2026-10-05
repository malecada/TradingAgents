import ast,copy,hashlib,json,os,re,stat,sys
from pathlib import Path
O=Path(__file__).resolve().parent; F=O.parent
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01')
C=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
H=lambda b:hashlib.sha256(b).hexdigest()
rows={}; assertions=0

def ck(v,m):
 global assertions
 assertions+=1
 if not v:raise AssertionError(m)
def read(p,pin=None):
 p=Path(p);s=p.lstat();ck(p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2,'bounded canonical regular '+str(p))
 b=p.read_bytes();ck(s==p.lstat() and len(b)==s.st_size,'currentness '+str(p));h=H(b)
 if pin:ck(h==pin,'hash '+str(p))
 rows[str(p)]={'sha256':h,'bytes':len(b),'mode':stat.S_IMODE(s.st_mode)};return b

def seal(name,prefix):
 d=F/name;b=read(d/'MANIFEST01.json');ck(H(b).startswith(prefix),'known review seal');m=json.loads(b)
 for r in m['members']:
  p=d/r['path'];s=p.lstat();ck(p.resolve()==p and stat.S_IMODE(s.st_mode)==r['mode'],'manifest path/mode')
  if r['kind']=='file':ck(len(read(p,r['sha256']))==r['bytes'],'manifest length')
  else:ck(r['kind']=='directory' and stat.S_ISDIR(s.st_mode),'manifest type')
 actual={p.relative_to(d).as_posix() for p in d.rglob('*')};ck(actual=={r['path'] for r in m['members']}|{'MANIFEST01.json'},'complete review namespace')
 machine=json.loads(read(d/'MACHINE01.json'));read(d/'REPORT01.md',machine['report_sha256']);return machine

ready=read(P/'REQUEST_READY_FOR_REVIEW01.json','0686608eafb699c0492ba1708a7d61e6f0a6e0ffebbb4e37d9dcba319b6ca914');q=json.loads(ready)
draft=read(P/'REQUEST_DRAFT01.json','e7579251741a865a2955917a3a9dc346ed6710ffc08388f1907c727e95d0a721');old=json.loads(draft)
ck({k for k in q if q[k]!=old[k]}=={'status','proofs'},'exact two changed top fields')
ck(q['proofs']['cumulative']==old['proofs']['cumulative'] and old['proofs']['full_recovery'] is None and old['proofs']['independent_source_input_runtime'] is None,'exact two real proof additions')
ck(q['final_review'] is None,'actual final remains absent')
source=read(P/'parent01.py',q['caller_sha256']);ck(q['caller_sha256']=='424f13b653d970efc4994e76e27f4ff5e8cf732133daab6a956cb1a034299ea0','accepted caller')
for name,h in q['helper_hashes'].items():read(P/name,h)
prior=seal('financial-wrapper-compatibility-parent-source-review01-2026-10-04','dc43830ad8fe17741bc85df2a6ed19da38cb3902c6685f2dce6258b0ef2de3e9')
ck(prior['source_sha256']==q['caller_sha256'] and prior['request_draft_sha256']==H(draft) and prior['decision']=='ACCEPTED_SOURCE_DRAFT_ONLY','source draft reuse')
baseline=seal('financial-wrapper-compatibility-baseline-recovery-review02-2026-10-05','2eca005b')
bridge=seal('financial-wrapper-compatibility-final-source-runtime-bridge02-2026-10-04','e581f20cb295639283e33ca7bdbe9da811baa4eb14637a656d816eb5ddfe3f1b')
proofs={k:json.loads(read(v['path'],v['sha256'])) for k,v in q['proofs'].items()}
full=proofs['full_recovery']; meta=proofs['independent_source_input_runtime']
ck(full['decision']=='accepted-baseline-byte-recovery' and full['future_final_supplement_required'] is True and full['numerical_authority'] is False,'baseline exclusions honest')
ck(full['scope']=={'input_roles':11,'logical_git_objects':407,'original_mode_metadata':True,'parent_draft_files':10,'recovered_archive_bodies':323,'source_pins':354,'source_regular':491,'source_typed':605,'tracked':355},'exact baseline scope')
read(full['review']['path'],full['review']['sha256'])
for k in ['identity','source','design_source','capsule_root','parent_root']:ck(full[k]==q[k],'baseline context '+k)
ck(baseline['decision']=='ACCEPTED_ACTUAL_COMPATIBILITY_BASELINE_BYTE_RECOVERY' and baseline['actual_child_exit']==baseline['actual_root_exit']==0 and baseline['actual_cleanup_failures']==[],'actual baseline outcome')
for ref in baseline['actual_receipts'].values():read(ref['path'],ref['sha256'])
ck(meta['identity']==q['identity'] and meta['source']==meta['design_source']==q['source'] and meta['registration_sha256']==q['registration_sha256'],'source proof context')
ck(meta['decision']=='accepted-source-input-runtime-metadata-only' and meta['numerical_authority'] is False,'source proof scope')
ck(set(meta['compatibility_preclaim_external_refs'])=={a+'_'+b for a in ('review','recovery') for b in ('proof','machine','manifest','report')},'exact eight refs')
for ref in list(meta['compatibility_preclaim_external_refs'].values())+meta['source_parent_evidence']:read(ref['path'],ref['sha256'])
ck(proofs['cumulative']['decision']=='accepted' and proofs['cumulative']['extension_sha256']=='07100b23f9a8c2dfcae98a8647f9f1eeb019f4093192cd4b2576c6a13bf9840e','actual cumulative20')
for n,h in q['source_files'].items():read(C/n,h)
reg=json.loads(read(C/q['registration'],q['registration_sha256']));exp=reg['experiments'][q['identity']]
ck(exp['source_files']==q['source_files'] and exp['parent'] is None and len(reg['experiments'])==13,'source gate scope')
ck(len(q['source_files'])==354 and len(exp['inputs'])==11 and set(exp['inputs'])==set(q['input_hashes']),'354 and 11')
for role,ref in exp['inputs'].items():read(C/ref['path'],ref['sha256']);ck(ref['sha256']==q['input_hashes'][role],'input role')
plan=json.loads(read(C/exp['inputs']['wrapper_plan']['path'])); job=json.loads(read(C/exp['inputs']['execution_job']['path']))
ck(plan['phase']=='complete100' and plan['experiment']==q['identity'],'fixed phase')
for p in (P/'attempt',P/'REQUEST_FINAL01.json',C/'research_runs'/q['identity'],C/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/q['identity']):ck(not os.path.lexists(p),'unused '+str(p))
failed={
'financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01':('4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128','35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450'),
'financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01':('d390980c956aab64d5521698cbb6123ccf01ece94a95277b97755f019adf692b','4b2d7b0d162e80fe2074997baed35f2d6e6c86e5f660872fc2b8e97bb9622558'),
'financial-wrapper-classification-eager-complete100-20261003-01':('2e3bbbbf786f784eadb18bc3cdfea68905610ae773bbbd748ea1b2666b9e61f1','abdaef6f01bd02614782e442e2c102c38faa57e76061cba43b69960f3e389fa6')}
ck({p.name for p in (C/'research_runs').iterdir()}==set(failed)|{'.lock'},'three original runs only')
for identity,pins in failed.items():
 for name,h in zip(('claim.json','failed.json'),pins):read(C/'research_runs'/identity/name,h)
 ck(not os.path.lexists(C/'research_runs'/identity/'complete.json'),'failed not complete')
# Execute exact parsed release functions only. No parent module/preflight/launch import.
sys.path.insert(0,str(P));import recovery04 as R
nodes=ast.parse(source).body
selected=[n for n in nodes if isinstance(n,ast.FunctionDef) and n.name in {'sha','require','reference','contract','validate_release'}]
g={'hashlib':hashlib,'json':json,'Path':Path,'re':re,'R':R,'CAP':C,'PARENT':P,'IDENTITY':q['identity'],'PROOFS':set(q['proofs'])}
exec(compile(ast.Module(body=selected,type_ignores=[]),str(P/'parent01.py'),'exec'),g)
controls=[]
def refused(value,label):
 try:g['validate_release'](value)
 except ValueError as e:controls.append({'case':label,'result':'refused','reason':str(e)})
 else:raise AssertionError('accepted '+label)
refused(q,'actual ready has null final review');refused(old,'original draft')
release={'schema_version':1,'decision':'accepted-exact-one-use-financial-parent','contract_sha256':g['contract'](q),'proof_sha256':{k:v['sha256'] for k,v in q['proofs'].items()},'identity':q['identity'],'source':q['source'],'caller_sha256':q['caller_sha256']}
release_path=O/'FINAL_PARENT_RELEASE01.json'; release_path.write_bytes(R.encode(release))
actual=copy.deepcopy(q);actual['final_review']={'path':str(release_path),'sha256':H(release_path.read_bytes())}
ck(g['validate_release'](actual)==release,'exact real release component acceptance')
for key,value in [('caller_sha256','0'*64),('identity',q['identity']+'-foreign'),('source','0'*40),('status','DRAFT_NOT_RELEASED')]:
 bad=copy.deepcopy(actual);bad[key]=value;refused(bad,'changed '+key)
for role in q['proofs']:
 bad=copy.deepcopy(actual);bad['proofs'][role]['sha256']='0'*64;refused(bad,'wrong '+role+' body pin')
# Final sampled rejoin of all observed original regular bodies, no new authority or mutation.
for name,row in list(rows.items()):ck(H(read(name))==row['sha256'],'terminal sampled body '+name)
result={'assertions':assertions,'files_authenticated':len(rows),'bytes_authenticated':sum(r['bytes'] for r in rows.values()),'request_sha256':H(ready),'contract_sha256':release['contract_sha256'],'release_sha256':actual['final_review']['sha256'],'proof_sha256':release['proof_sha256'],'controls':controls,'source':q['source'],'source_pins':354,'input_roles':11,'actual_failed_claims':3,'highest_claimed_allowance':19,'prospective_ceiling':20,'final_supplement_recovery_required':True,'full_preclaim_8MiB_proven':False,'public_preflight_executed':False,'numerical_execution':False}
(O/'CHECKS01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
(O/'READ_SET01.json').write_text(json.dumps(rows,sort_keys=True,separators=(',',':'))+'\n')
print(json.dumps(result,sort_keys=True))
