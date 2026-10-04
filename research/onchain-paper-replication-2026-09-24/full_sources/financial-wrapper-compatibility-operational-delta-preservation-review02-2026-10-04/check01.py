from pathlib import Path
import json,hashlib,stat,os,subprocess,io,gzip,tarfile
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';O=Path(__file__).parent;C=F/'financial-wrapper-compatibility-operational-delta-capture02-2026-10-04';S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');V=F/'financial-wrapper-compatibility-root-source-adoption-review01-2026-10-04'
h=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes())
def scan(root):
 out=[]
 for d,ds,fs in os.walk(root,followlinks=False):
  if Path(d)==S:ds.remove('.git')
  for n in ds+fs:
   p=Path(d)/n;t=p.lstat();x={'path':p.relative_to(root).as_posix(),'mode':stat.S_IMODE(t.st_mode)}
   if stat.S_ISDIR(t.st_mode):x['kind']='directory'
   else:
    assert stat.S_ISREG(t.st_mode) and t.st_nlink==1
    b=p.read_bytes();x.update(kind='file',bytes=len(b),sha256=h(b))
   out.append(x)
 return sorted(out,key=lambda x:x['path'])
def git(root,args,body=None):return subprocess.run(['git','--no-replace-objects',*args],cwd=root,input=body,capture_output=True,check=True,timeout=30).stdout
cap=J(C/'CAPTURE01.json');m=J(C/'PAYLOAD_MANIFEST01.json');snap=C/'snapshot'
assert h((C/'CAPTURE01.json').read_bytes())=='61f3560c6fc64b7122f12a690ab728407803c7bb3c3406fd1a754456e207f939'
assert h((C/'PAYLOAD_MANIFEST01.json').read_bytes())==cap['manifest_sha256']=='a04069280b7bf7b49fc075e640109f935f65b292fe69e1f4e96342bc08ad246e'
assert scan(snap)==m['members'] and stat.S_IMODE(snap.stat().st_mode)==m['root_mode']
assert len(m['members'])==41 and sum(x['kind']=='file' for x in m['members'])==33
orig=J(C/'ORIGIN_MAP01.json');assert h((C/'ORIGIN_MAP01.json').read_bytes())==cap['origin_map_sha256']
for x in orig['origins']:
 p=Path(x['original']);b=p.read_bytes();assert stat.S_IMODE(p.stat().st_mode)==x['original_mode'] and len(b)==x['bytes'] and h(b)==x['sha256'] and b==(snap/x['path']).read_bytes()
raw=(C/'operational-delta01.tar.gz').read_bytes();assert h(raw)==cap['archive']['sha256'] and len(raw)==cap['archive']['bytes']
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as t:
 ms=t.getmembers();assert len(ms)==len(m['members'])
 for a,x in zip(ms,m['members']):
  assert a.name==x['path'] and a.mode==x['mode'] and a.uid==a.gid==a.mtime==0 and a.uname==a.gname==''
  if x['kind']=='file':assert a.isfile() and a.size==x['bytes'] and t.extractfile(a).read()==(snap/x['path']).read_bytes()
  else:assert a.isdir() and a.size==0
out=io.BytesIO()
with gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0) as gz:
 with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as t:
  for x in m['members']:
   a=tarfile.TarInfo(x['path']);a.mode=x['mode'];a.uid=a.gid=a.mtime=0;a.uname=a.gname=''
   if x['kind']=='directory':a.type=tarfile.DIRTYPE;t.addfile(a)
   else:b=(snap/x['path']).read_bytes();a.size=len(b);t.addfile(a,io.BytesIO(b))
assert out.getvalue()==raw
basis=J(snap/'COMPOSITION_BASIS01.json');current=scan(S);assert current==basis['current589_manifest']['members'] and len(current)==589
by={x['path']:x for x in current};protected=J(V/'PROTECTED_NON_TARGET585.json');assert h((V/'PROTECTED_NON_TARGET585.json').read_bytes())==basis['protected585_manifest_sha256']
assert len(protected['members'])==585
for x in protected['members']:assert by[x['path']]==x
old=J(snap/'root-adoption/OLD_IMPLEMENTATION194.json');target=J(snap/'root-adoption/TARGET_IMPLEMENTATION195.json');assert len(target)==195 and sum(n.startswith('tradingagents/') for n in target)==150 and sum(target.get(n)==p for n,p in old.items())==191
for n,p in target.items():assert h((S/n).read_bytes())==p
meta=J(snap/'SOURCE_GIT394_METADATA01.json');rows=meta['objects'];oldrows=[x for x in rows if x['body_basis']=='actual-old385-recovery'];new=[x for x in rows if x['body_basis']!='actual-old385-recovery'];assert len(rows)==394 and len(oldrows)==385 and len(new)==9
B=Path(meta['actual_old385_basis']['root']);proof=F/'financial-wrapper-complete100-baseline-actual-flat-review01-2026-10-04';assert h((proof/'MACHINE01.json').read_bytes())==meta['actual_old385_basis']['independent_acceptance_machine_sha256']=='49e0ad65d23f34496963b09e82cb8744d0e56c6d5c1a598af48f7154bd0e9122';assert h((proof/'FLAT_RECOVERY01.json').read_bytes())==meta['actual_old385_basis']['flat_receipt_sha256']
for root,rr in [(S,rows),(B,oldrows)]:
 data=git(root,['cat-file','--batch'],('\n'.join(x['oid'] for x in rr)+'\n').encode());off=0
 for x in rr:
  end=data.index(b'\n',off);assert data[off:end].split()==[x['oid'].encode(),x['type'].encode(),str(x['bytes']).encode()];b=data[end+1:end+1+x['bytes']];assert h(b)==x['sha256'] and hashlib.sha1(x['type'].encode()+b' '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['oid'];assert data[end+1+len(b):end+2+len(b)]==b'\n';off=end+2+len(b)
  if x['body_basis']!='actual-old385-recovery':assert b==(snap/x['body_basis']).read_bytes()
 assert off==len(data)
assert sorted(x['oid'] for x in rows)==sorted({x.split()[0].decode() for x in git(S,['rev-list','--objects','--all']).splitlines()})
assert git(S,['rev-parse','HEAD']).decode().strip()==meta['actual_source']==basis['target_source_design']
assert git(S,['rev-parse','HEAD^']).decode().strip()==meta['old_source']
tracked=git(S,['ls-tree','-rz','HEAD']).split(b'\0')[:-1];assert len(tracked)==340
for line in tracked:
 a,n=line.split(b'\t');mode,kind,oid=a.split();assert mode==b'100644' and kind==b'blob';b=(S/n.decode()).read_bytes();assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest().encode()==oid
fp=F/'financial-wrapper-complete100-failed-full-recovery-review03-2026-10-04';assert h((fp/'MACHINE01.json').read_bytes())==basis['old_full_failed_byte_recovery_machine_sha256']
assert scan(S)==current and scan(snap)==m['members']
result={'schema_version':1,'decision':'ACCEPTED_LOCAL_OPERATIONAL_DELTA_COMPOSITION_ONLY','capture_sha256':h((C/'CAPTURE01.json').read_bytes()),'manifest_sha256':cap['manifest_sha256'],'archive_sha256':h(raw),'typed':41,'regular':33,'logical_bytes':sum(x.get('bytes',0) for x in m['members']),'canonical_reencoding_equal':True,'original_origin_rows_verified':len(orig['origins']),'current_nongit_members':589,'protected_unchanged':585,'implementation_paths':195,'package_paths':150,'old_equal_implementation_paths':191,'tracked':340,'current_source':meta['actual_source'],'recovered_old_git_objects':385,'new_git_objects':9,'total_current_git_objects':394,'actual_old385_basis':meta['actual_old385_basis'],'old_failed_byte_machine_sha256':basis['old_full_failed_byte_recovery_machine_sha256'],'selected_scope_files':[{'path':x['path'],'bytes':x.get('bytes'),'sha256':x.get('sha256'),'mode':x['mode']} for x in m['members'] if x['kind']=='file'],'actual_external_delta_recovery':False,'numerical_authority':False}
(O/'READBACK01.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS complete41/33 source589/585 implementation195/150 currentGit394=actualrecovered385+new9 canonicalarchive')
