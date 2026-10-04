from pathlib import Path
import json,hashlib,stat,os,subprocess,sys,datetime
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'financial-wrapper-compatibility-operational-delta-capture02-2026-10-04';D.mkdir(mode=0o700);snap=D/'snapshot';snap.mkdir(mode=0o700)
U=F/'financial-wrapper-complete100-failed-root-remote03-2026-10-04/utilities';sys.path.insert(0,str(U));import recovery_pax01 as P
S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');I=F/'financial-wrapper-compatibility-root-integration01-2026-10-04';V=F/'financial-wrapper-compatibility-root-source-adoption-review01-2026-10-04';C=F/'financial-wrapper-compatibility-root-policy01-2026-10-04'
def h(b):return hashlib.sha256(b).hexdigest()
def J(p):return json.loads(p.read_bytes())
def put(p,o):P.put(p,o)
def git(*args):return subprocess.run(['git','--no-replace-objects',*args],cwd=S,capture_output=True,check=True,timeout=20).stdout
assert h((U/'recovery_pax01.py').read_bytes())=='a054d5922899b53579f4220ff3b427dc050dff075cb5470b43ff55e621b97eb2'
assert git('rev-parse','HEAD').decode().strip()=='7b056a574e3e7b3c7ba209a39ee6a615e649d60c';current=P.scan(S) if False else J(I/'SOURCE_ADOPTION_AFTER589.json')
# Independently rejoin complete current membership, not only selected code.
actual=[]
for root,ds,fs in os.walk(S,followlinks=False):
 if Path(root)==S:ds.remove('.git')
 for name in ds+fs:
  p=Path(root)/name;s=p.lstat();row={'path':p.relative_to(S).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISDIR(s.st_mode):row['kind']='directory'
  else:
   assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2;raw=p.read_bytes();row.update(kind='file',bytes=len(raw),sha256=h(raw))
  actual.append(row)
actual.sort(key=lambda x:x['path']);assert current['members']==actual and len(actual)==589
origins=[]
def copy(src,rel):
 raw=src.read_bytes();assert len(raw)<4*1024**2;p=snap/rel;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(raw);os.chmod(p,stat.S_IMODE(src.stat().st_mode));origins.append({'path':rel,'original':str(src),'bytes':len(raw),'sha256':h(raw),'original_mode':stat.S_IMODE(src.stat().st_mode)})
for x in J(I/'SOURCE_ADOPTION_DRAFT01.json')['implementation_source_changes']:copy(S/x['path'],'current-source/'+x['path'])
for p in sorted(C.iterdir()):
 if p.is_file():copy(p,'policy/'+p.name)
for n in ['SOURCE_ADOPTION_DRAFT01.json','OLD_IMPLEMENTATION194.json','TARGET_IMPLEMENTATION195.json','SOURCE_ADOPTION_RESULT01.json','SOURCE_ADOPTION_AFTER589.json','SOURCE_ADOPTION_PREFLIGHT01.json','SOURCE_ADOPTION_ATTEMPT01.json','root_source_adopt04.py']:copy(I/n,'root-adoption/'+n)
A=F/'financial-wrapper-compatibility-actual-source-adoption-review01-2026-10-04'
for n in ['MACHINE01.json','MANIFEST01.json','READBACK01.json','REPORT01.md','check01.py']:copy(A/n,'actual-adoption-review/'+n)
old=J(V/'ORIGINAL_GIT385.json');oldrows={x['oid']:x for x in old['objects']};oids=sorted({x.split()[0].decode() for x in git('rev-list','--objects','--all').splitlines()});assert len(oids)==394 and set(oldrows)<=set(oids);rows=[]
for oid in oids:
 kind=git('cat-file','-t',oid).decode().strip();body=git('cat-file',kind,oid);assert hashlib.sha1(kind.encode()+b' '+str(len(body)).encode()+b'\0'+body).hexdigest()==oid
 row={'oid':oid,'type':kind,'bytes':len(body),'sha256':h(body)}
 if oid in oldrows:assert row==oldrows[oid];row['body_basis']='actual-old385-recovery'
 else:
  rel='new-git-objects/'+oid+'.body';p=snap/rel;p.parent.mkdir(exist_ok=True);p.write_bytes(body);os.chmod(p,0o600);row['body_basis']=rel
 rows.append(row)
assert sum(x['body_basis']!='actual-old385-recovery' for x in rows)==9
put(snap/'SOURCE_GIT394_METADATA01.json',{'schema_version':1,'actual_source':'7b056a574e3e7b3c7ba209a39ee6a615e649d60c','old_source':'9dc5c79f738920b52947b4e63fed0397f1b5b207','objects':rows,'actual_old385_basis':{'root':str(F/'financial-wrapper-complete100-baseline-remote01-2026-10-04/fresh-original-source339-01.git'),'flat_receipt_sha256':'9cd4a45f050d4267ade7febf5da9e57da2afbefd0e3fd156106d4f8d9b4e4460','independent_acceptance_machine_sha256':h((F/'financial-wrapper-complete100-baseline-actual-flat-review01-2026-10-04/MACHINE01.json').read_bytes())},'qualification':'Nine new opaque logical Git bodies plus actual recovered385. This is no POSIX Git-store archive, installed-runtime body recovery or numerical authority.'})
# Every source delta and protected body has an explicit actual externally recovered basis.
put(snap/'COMPOSITION_BASIS01.json',{'schema_version':1,'target_source_design':'7b056a574e3e7b3c7ba209a39ee6a615e649d60c','current589_manifest':current,'protected585_manifest_sha256':h((V/'PROTECTED_NON_TARGET585.json').read_bytes()),'old_full_failed_byte_recovery_machine_sha256':'171c1f7f37934d661b75d241500df637d8155515ac86965b40bcc6821ec6cb0b','old_full_failed_flat_receipt_sha256':'7f806b4a71a15128accc699f221441305bfbfa56eeff48179e9cd96d44ba6c17','old385_flat_receipt_sha256':'9cd4a45f050d4267ade7febf5da9e57da2afbefd0e3fd156106d4f8d9b4e4460','new_source_changes':J(I/'SOURCE_ADOPTION_DRAFT01.json')['implementation_source_changes'],'excluded':['Future registration/gate/inputs/caller/envelope/release','Installed runtime package bodies','POSIX source-tree reconstruction','Whole empirical fit capacity']})
manifest=P.scan(snap);put(D/'PAYLOAD_MANIFEST01.json',manifest);archive=P.pack(snap,manifest,D/'operational-delta01.tar.gz');assert archive['bytes']<4*1024**2
put(D/'ORIGIN_MAP01.json',{'schema_version':1,'origins':origins})
put(D/'CAPTURE01.json',{'schema_version':1,'status':'FROZEN_OPERATIONAL_SOURCE_POLICY_DELTA_NOT_EXTERNAL_RECOVERY','timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'snapshot':str(snap),'source_design':'7b056a574e3e7b3c7ba209a39ee6a615e649d60c','policy_sha256':h((C/'POLICY01.json').read_bytes()),'manifest_sha256':h((D/'PAYLOAD_MANIFEST01.json').read_bytes()),'archive':archive,'typed':len(manifest['members']),'files':sum(x['kind']=='file' for x in manifest['members']),'raw_bytes':sum(x.get('bytes',0) for x in manifest['members']),'new_git_objects':9,'original_git_basis_objects':385,'total_reachable_git_objects':394,'current_complete_nongit_members':589,'new_target_bodies':4,'preserved_unchanged_nongit_members':585,'origin_map_sha256':h((D/'ORIGIN_MAP01.json').read_bytes()),'native_or_Run_started':False,'actual_external_or_flat_receipt':None})
print(h((D/'CAPTURE01.json').read_bytes()),manifest['schema_version'],len(manifest['members']),archive)
