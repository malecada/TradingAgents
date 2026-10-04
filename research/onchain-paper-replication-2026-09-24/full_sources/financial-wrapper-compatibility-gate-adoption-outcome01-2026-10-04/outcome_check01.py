"""Independent read-only installed outcome authentication; no author entry or lifecycle imports."""
from pathlib import Path
import ast,copy,hashlib,json,os,stat,subprocess,time
D=Path(__file__).resolve().parent;F=D.parent;ROOT=F.parents[2];CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');P=F/'financial-wrapper-compatibility-gate-preview02-2026-10-04';B=F/'financial-wrapper-compatibility-registration-preparation01-2026-10-04';R=F/'financial-wrapper-compatibility-composed-recovery-review02-2026-10-04';N='fixture_inputs/financial_wrapper_compatibility01';OLD='fixture_inputs/financial_wrapper_claimedrun01/gates.json';checks=[];pins={};begun=time.monotonic()
def h(b):return hashlib.sha256(b).hexdigest()
def ok(v,n):
 assert v,n;checks.append(n)
def read(p,pin=None):
 p=Path(p);s=p.lstat();ok(p.is_absolute() and p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304,'bounded canonical regular '+str(p));before=(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns);b=p.read_bytes();t=p.lstat();ok(before==(t.st_dev,t.st_ino,t.st_mode,t.st_nlink,t.st_size,t.st_mtime_ns,t.st_ctime_ns) and len(b)==s.st_size,'postread current '+p.name);ok(pin is None or h(b)==pin,'hash '+p.name);pins[str(p)]={'sha256':h(b),'bytes':len(b),'mode':stat.S_IMODE(s.st_mode)};ok(time.monotonic()-begun<60,'bounded wall');return b
def J(p,pin=None):return json.loads(read(p,pin))
def canonical(q):return json.dumps(q,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def git(*args):
 r=subprocess.run(['git','--no-replace-objects',*args],cwd=CAP,env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL=''),capture_output=True,timeout=10);ok(r.returncode==0 and len(r.stdout)<=4194304,'bounded local Git');return r.stdout
m=J(R/'MANIFEST01.json','4c1bafac000b164f4534e0308169214c9fd7f3f72cab2f4389a1647e6ada3cde');rs={x['path']:x for x in m['members']};actual={p.relative_to(R).as_posix() for p in R.rglob('*') if p!=R/'MANIFEST01.json'};ok(actual==set(rs)-{'.'},'complete actual recovery reviewer seal namespace')
for n,x in rs.items():
 p=R/n;s=p.lstat();mode=int(x['mode'],8) if isinstance(x['mode'],str) else x['mode'];ok(stat.S_IMODE(s.st_mode)==mode,'review literal mode')
 if x['kind']=='file':ok(len(read(p,x['sha256']))==x['bytes'],'review regular body')
 else:ok(x['kind']=='directory' and stat.S_ISDIR(s.st_mode),'review directory')
machine=J(R/'MACHINE01.json','aae1d255e54bf8fb52a82c7c7dff6495df16e1c82b71d448828e28f841db116f');proof=J(R/'RECOVERY_PROOF01.json','c5cf38d2a54682e9b36c0d4462cc07a611fb047cc422803b23d590552511b7a5');read(R/'REPORT01.md','4ddb9c23e2fb98c29dfc994c66d2accf2ee670e6b9d99ea6ce7218e13573618d');ok(machine['decision']=='ACCEPTED_ACTUAL_OPERATIONAL_SOURCE_POLICY_BYTE_RECOVERY' and machine['recovery_proof_sha256']==h(read(R/'RECOVERY_PROOF01.json')) and machine['report_sha256']==h(read(R/'REPORT01.md')),'genuine actual composed recovery proof/report')
closure=J(R/'CLOSURE01.json');ok(len(closure['provenance'])==51 and sum('/receipts/' in x['path'] for x in closure['provenance'])==38,'full38receipt plus13source-evidence copy origins')
for x in closure['provenance']:
 p=Path(x['path']);origin=Path(x['original_path']);ok(read(p,x['sha256'])==read(origin,x['sha256']) and p.stat().st_size==x['bytes'],'literal receipt-original body');ok(stat.S_IMODE(p.lstat().st_mode)==x['copy_mode'] and stat.S_IMODE(origin.lstat().st_mode)==x['original_mode'],'literal original/copy mode')
for ref in machine['recovery_receipts']:
 n=Path(ref['path']).relative_to(R).as_posix();ok(rs[n]['sha256']==ref['sha256'] and rs[n]['kind']=='file','receipt typed member')
preview=J(P/'PREVIEW01.json');ok(preview['status']=='CONCRETE_GATE_PREVIEW_NOT_ADOPTED' and preview['source_before']==git('rev-parse','HEAD').decode().strip()=='7b056a574e3e7b3c7ba209a39ee6a615e649d60c','actual preview source')
ok(not git('status','--porcelain','--untracked-files=no'),'current clean tracked source');names=[n.decode() for n in git('ls-files','-z').split(b'\0') if n];ok(len(names)==len(set(names))==340,'actual340 tracked')
sourcepins={n:h(read(CAP/n)) for n in names};oldgate=J(CAP/OLD,'752c34dfad4df2ca36b5dc4dcb999846f8de01bd1a61c5356092c4e55fbd678c');gate=J(P/N/'gates.json','e1846c9fbd5d1964c867c9c7027e3e9a6009520c07841ed720c035374dbeb806');ok(len(oldgate['experiments'])==12 and len(gate['experiments'])==13,'exact12plus1 definitions');ident=preview['identity'];exp=gate['experiments'][ident];policy=J(P/N/'policy.json','ae8fbdc9d13e75fc453b70b5ee633c89fb4577e9b68a35b4147cf1bbd58c6887')
without=copy.deepcopy(gate);del without['experiments'][ident];ok(without==oldgate,'all old top-level/12definitions literally equal')
ok(ident==policy['consumers']['complete100']['experiment'] and exp['parent'] is None and exp['cells']==[policy['consumers']['complete100']['cell_id']],'exact new reference parentNone topology')
ok(os.path.isdir(CAP/N) and not os.path.lexists(CAP/'research_runs'/ident),'installed inputs and genuinely unused run identity')
prepared={p.name:read(p) for p in (B/N).iterdir()};ok(len(prepared)==13,'original13 fixed bodies');files={p.relative_to(P).as_posix():read(p) for p in (P/N).iterdir()};ok(len(files)==15 and set(files)==set(preview['new_file_pins']),'actual15exact path population')
for n,b in prepared.items():ok(files[N+'/'+n]==b,'literal prepared '+n)
ok(files[N+'/policy-recovery.json']==read(R/'RECOVERY_PROOF01.json'),'actual proof literal registration body')
for n,b in files.items():
 ok(h(b)==preview['new_file_pins'][n],'actual newbody pin');ok(read(CAP/n,preview['new_file_pins'][n])==b,'literal actual installed body');s=(CAP/n).lstat();ok(stat.S_IMODE(s.st_mode)==0o600 and s.st_uid==os.getuid(),'new600 owner')
ok(stat.S_IMODE((CAP/N).lstat().st_mode)==0o700 and (CAP/N).lstat().st_uid==os.getuid(),'new directory700 owner')
status=git('status','--porcelain','--untracked-files=all').decode().splitlines();ok(set(status)=={'?? '+n for n in files},'exact15 untracked no other Git changes')
expected={**sourcepins,**{n:h(b) for n,b in files.items() if n!=N+'/gates.json'}};ok(exp['source_files']==expected and len(expected)==354,'complete exact354sourcepins excludednewgate');ok(len(set(names)|set(files))==355 and not(set(names)&set(files)),'prospective355/15disjoint')
draft=J(B/'EXPERIMENT_DRAFT_NOT_REGISTRATION01.json','edd6e8acc71d35fb1ff31795701d1fb6185fdee3e64b952d805edcd75120780d');prior=copy.deepcopy(exp);prior['source_files']=None;del prior['inputs']['operational_source_compatibility_recovery'];ok(prior==draft['experiment'],'every remaining experiment field equals frozen draft')
ok(len(exp['inputs'])==11,'exact11roles')
for role,ref in exp['inputs'].items():ok(ref['dataset']=='synthetic' and ref['path'] in files and h(files[ref['path']])==ref['sha256'] and expected[ref['path']]==ref['sha256'],'allinput andsource-pin '+role)
ok(set(proof)=={'schema_version','kind','decision','policy_sha256','checker_sha256','historical_map_sha256','target_map_sha256'} and proof['decision']=='accepted' and proof['kind']=='operational_source_compatibility_recovery','genuine sevenfield role');ok(proof['historical_map_sha256']==h(canonical(policy['historical']['installed'])) and proof['target_map_sha256']==h(canonical(policy['target']['installed'])),'canonical map pins')
for n,pin in policy['target']['installed'].items():ok(sourcepins[n]==pin,'actual195 target '+n)
ok(len(policy['target']['installed'])==195,'target195')
training=J(P/N/'training.json','d5276b75491e130bd03d43de28120f72dd792e42af4446382a6c127d387b8ec0');model=J(P/N/'model.json','20f451c08143dd81491b5c9fa0a90243ee6a9363df1fbbfcbd9c45b32f9b054d');recipe=J(P/N/'synthetic_recipe.json','f8b1ec1eed902f3cca76bd7e06d2435accda699173b9a7942d10c37c64f01040');plan=J(P/N/'wrapper_plan.json','122038ae73464e0168cc0184cf9097ead7908c0194f1684b853da337bc66efda');ok(training['epochs']==100 and training['batch_size']==16 and recipe['seed']==11 and recipe['batch']==16 and recipe['lookback']==28 and plan['execution']=='eager' and plan['phase']=='complete100','fixed original100/seed11/batch16/lookback28/eager')
claims=[]
for p in sorted((CAP/'research_runs').glob('*/claim.json')):
 claim=J(p);failed=J(p.parent/'failed.json');ok(not (p.parent/'complete.json').exists(),'FAILED noCOMPLETE');claims.append({'identity':p.parent.name,'claim_sha256':h(read(p)),'failed_sha256':h(read(p.parent/'failed.json')),'disposition':'FAILED_SPENT'});ok(claim['family']['attempt_budget']==18 and claim['family']['prior_attempts']==0,'original base18prior0')
ok(claims==preview['actual_history'] and len(claims)==3,'exact three originalhistory');ok(preview['actual_highest']==19 and preview['actual_spent_failed']==3 and preview['prospective_amendment']==20,'observed19 prospective20 no refund')
# Complete unchanged589 nonGit capsule, original types/modes/hashes, independent of tracking.
base=J(F/'financial-wrapper-compatibility-root-integration01-2026-10-04/SOURCE_ADOPTION_AFTER589.json');typed={x['path']:x for x in base['members']};current=set()
for root,ds,fs in os.walk(CAP,followlinks=False):
 if Path(root)==CAP:ds.remove('.git')
 for name in ds+fs:
  p=Path(root)/name;n=p.relative_to(CAP).as_posix();current.add(n)
  if n==N or n in files:continue
  x=typed[n];s=p.lstat();ok(s.st_uid==os.getuid(),'original owner');ok(stat.S_IMODE(s.st_mode)==x['mode'],'capsule originalmode '+n)
  if x['kind']=='file':ok(len(read(p,x['sha256']))==x['bytes'],'capsule currentbody '+n)
  else:ok(stat.S_ISDIR(s.st_mode),'capsule directory '+n)
ok(current==set(typed)|set(files)|{N} and len(current)==605,'exact605 namespace with preserved589')
# Original logical Git population, read-only bounded batch-less object reads, no updates.
index=J(F/'financial-wrapper-compatibility-operational-delta-capture02-2026-10-04/snapshot/SOURCE_GIT394_METADATA01.json');oids=git('rev-list','--objects','--all','--no-object-names').decode().splitlines();ok(len(oids)==len(set(oids))==394 and set(oids)=={x['oid'] for x in index['objects']},'current original394Git set')
for x in index['objects']:
 b=git('cat-file',x['type'],x['oid']);ok(len(b)==x['bytes'] and h(b)==x['sha256'],'current original Git body '+x['oid'])
# Genuine Root execution records and source-only release, not inferred outcomes.
O=F/'financial-wrapper-compatibility-gate-root-adoption01-2026-10-04';A=F/'financial-wrapper-compatibility-gate-adoption-review01-2026-10-04'
intent=J(O/'INTENT01.json','fdf3bc5c88ff63d28fdaa21c367a505706f1426ffa2d267a75b34bb4d754e49b9')
terminal=J(O/'INSTALLED_NOT_COMMITTED01.json','9a3dae176d72c821a050b8cf5f4ff1d18ed8d53522bd0fdcffb9d5d5f480bb39')
exit_record=J(O/'ACTUAL_ROOT_EXIT01.json','40a1acf1e37d8accf39ee04071840233d82094d2b7ff43c3cfa7ee8ffb983dbf')
source=read(F/'heartbeat-root-checkpoint10-2026-10-04/root_compatibility_gate_adopt01.py','f8aad6a7eab5f484036ae27d8c25ba1620be651c437644fcd8aca218686982c8')
release=J(A/'MACHINE01.json','3479af171fb3a36c40ff3f37a85c66ea5365ae7680368a17463b27653a3193dc');seal=J(A/'MANIFEST01.json','42dd629442d2ba3b554a1c497cbea7258efbc0eedb1afb75ae2c09dbe7f7b4a1');read(A/'REPORT01.md','7e1e0265d40896f1b68d273df5e1b66e5864f91285510648a1c707e7a9f7acc0')
for role in ('machine','manifest','report'):
 ref=intent['review'][role];ok(read(Path(ref['path']),ref['sha256'])==read(A/({'machine':'MACHINE01.json','manifest':'MANIFEST01.json','report':'REPORT01.md'}[role])),'actual invoked release '+role)
for n in ('MACHINE01.json','REPORT01.md'):
 row=next(x for x in seal['members'] if x['path']==n);ok(h(read(A/n))==row['sha256'],'sealed source release body')
ok(release['decision']=='ACCEPTED_EXACT_ROOT_GATE_METADATA_ADOPTION_ONLY' and release['root_adopter_sha256']==h(source) and release['allowed_new_file_pins']==preview['new_file_pins'],'exact predecessor release')
ok(intent['new_file_pins']==terminal['new_file_pins']==preview['new_file_pins'] and intent['root_adopter_sha256']==terminal['root_adopter_sha256']==h(source),'actual execution exact source/files')
ok(intent['preview_sha256']==terminal['preview_sha256']==h(read(P/'PREVIEW01.json','b725fa4f1f6b071cf910eeb24edab11aaa20c9e50475fcda54dc5e1dcc15c0d2')),'actual preview binding')
ok(all(terminal[k]==v for k,v in intent.items() if k!='status'),'intent terminal continuity')
ok(terminal['whole_before']==589 and terminal['whole_after']==605 and terminal['new_files']==15 and terminal['Admission_or_Run_started'] is False,'terminal exact scope')
ok(exit_record['actual_exit_code']==0 and exit_record['receipt_sha256']==h(read(O/'INSTALLED_NOT_COMMITTED01.json')) and exit_record['caller_sha256']==h(source) and exit_record['process_pid_unrecorded'] is None,'actual tool exit separate unrecorded PID remainsNULL')
ok(set(p.name for p in O.iterdir())=={'INTENT01.json','INSTALLED_NOT_COMMITTED01.json','ACTUAL_ROOT_EXIT01.json'},'complete Root outcome directory')
ok(set(p.name for p in (CAP/'research_runs').iterdir())=={x['identity'] for x in claims}|{'.lock'},'exact three original failed namespaces')
protected=J(F/'financial-wrapper-compatibility-root-source-adoption-review01-2026-10-04/PROTECTED_NON_TARGET585.json','23a0daa64f68930a3f211d46a8a10e4054af13d189b04715a6ea0e25b3451719')
# Current signatures are independently captured now. Historical full signatures were checked in the actual adopter, not persisted as a pre-adoption map.
def sig(s):return [s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_uid,s.st_gid]
current_signatures={n:sig((CAP/n).lstat()) for n in sorted(current)}
for p,x in list(pins.items()):ok(h(read(Path(p)))==x['sha256'],'final current rehash')
for n,x in current_signatures.items():ok(sig((CAP/n).lstat())==x,'final whole605 signature rejoin')
ok(git('rev-parse','HEAD').decode().strip()=='7b056a574e3e7b3c7ba209a39ee6a615e649d60c' and not git('diff','--cached','--name-only'),'unchanged HEAD and empty stage')
out={'schema_version':1,'decision':'ACTUAL_INSTALLED_METADATA_INDEPENDENTLY_AUTHENTICATED','checks':len(checks),'checked_files':pins,'current605_signatures':current_signatures,'actual_claims':claims,'exact_git_stage_commit_paths':sorted(files),'new_file_pins':preview['new_file_pins'],'old589_body_type_mode_preserved':True,'old394_git_objects_preserved':True,'old_signature_history':'actual adopter full-signature predicate passed; no independently durable pre-adoption signature map exists','actual_root_exit':exit_record,'actual_highest_claimed_allowance':19,'actual_failed_spent_attempts':3,'prospective_amendment':20,'tracked_before_commit':340,'prospective_tracked':355,'source_pins':354,'roles':11,'numerical_authority':False,'claim_authority':False}
(D/'READBACK01.json').write_text(json.dumps(out,indent=2)+'\n');(D/'EXACT_GIT_SCOPE01.json').write_text(json.dumps({'root':str(CAP),'source_before':preview['source_before'],'files':preview['new_file_pins'],'count':15,'root_only':True,'broad_staging_allowed':False,'native_authority':False},indent=2)+'\n');print(len(checks),len(pins))
