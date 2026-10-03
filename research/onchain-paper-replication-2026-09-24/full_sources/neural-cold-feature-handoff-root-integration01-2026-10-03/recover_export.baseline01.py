"""Fresh actual remote export recovery; no research or numerical execution."""
import hashlib,json,os,stat,subprocess,sys,tarfile
from pathlib import Path,PurePosixPath

ROOT=Path.cwd();HERE=Path(__file__).resolve().parent;MAX=4194304
COMMIT=sys.argv[1]
assert len(COMMIT)==40 and all(c in '0123456789abcdef' for c in COMMIT)
def digest(b):return hashlib.sha256(b).hexdigest()
def call(args,cwd=ROOT):
 result=subprocess.run(['git',*args],cwd=cwd,capture_output=True,timeout=60)
 assert result.returncode==0 and max(len(result.stdout),len(result.stderr))<=MAX
 return result.stdout
def put(p,b):
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
branch='research/onchain-paper-replication-2026-09-24'
assert call(['ls-remote','origin','refs/heads/'+branch]).decode().split()[0]==COMMIT
out=HERE/'export-recovery01';out.mkdir(mode=0o700)
repo=out/'repository.git';call(['init','--bare',str(repo)])
call(['remote','add','origin',call(['remote','get-url','origin']).decode().strip()],repo)
call(['config','remote.origin.promisor','true'],repo)
call(['config','remote.origin.partialclonefilter','blob:none'],repo)
call(['fetch','--depth=1','--filter=blob:none','origin',COMMIT],repo)
assert call(['rev-parse','FETCH_HEAD'],repo).decode().strip()==COMMIT
rows=[]
for name in ('SOURCE_EXPORT_RETENTION01.json','source-export01.tar.gz','request-export01.json','export01.log','recover_export01.py'):
 path=HERE/name;raw=call(['show',COMMIT+':'+str(path.relative_to(ROOT))],repo)
 assert raw==path.read_bytes();put(out/name,raw)
 rows.append({'path':str(path.relative_to(ROOT)),'sha256':digest(raw),'bytes':len(raw)})
retained=json.loads((out/'SOURCE_EXPORT_RETENTION01.json').read_bytes())
archive=out/'source-export01.tar.gz'
assert archive.stat().st_size==retained['archive_bytes'] and digest(archive.read_bytes())==retained['archive_sha256']
expected={r['path']:r for r in retained['members']}
assert len(expected)==len(retained['members'])==235
owned=out/'source';owned.mkdir(mode=0o700);seen=set();logical=files=directories=0
with tarfile.open(archive,'r:gz') as tf:
 for member in tf:
  name=member.name;p=PurePosixPath(name)
  assert name==str(p) and not p.is_absolute() and '..' not in p.parts and '\\' not in name and '\x00' not in name
  assert name in expected and name not in seen and member.mode==expected[name]['mode']
  row=expected[name];dest=owned if name=='.' else owned/name
  assert dest.resolve()==dest and (dest==owned or dest.parent.is_dir())
  if row['kind']=='directory':
   assert member.isdir() and member.size==0 and row['bytes']==0
   if dest!=owned:dest.mkdir(mode=member.mode)
   os.chmod(dest,member.mode);directories+=1
  else:
   assert row['kind']=='file' and member.isfile() and name!='.' and member.size==row['bytes']<=MAX
   stream=tf.extractfile(member);assert stream is not None
   with stream:raw=stream.read(MAX+1)
   assert len(raw)==row['bytes'] and digest(raw)==row['sha256']
   put(dest,raw);os.chmod(dest,member.mode);files+=1;logical+=len(raw)
  seen.add(name)
assert seen==set(expected) and files==retained['files']==200 and directories==retained['directories']==35 and logical==retained['logical_bytes']==3403631
actual=set()
for p in [owned,*owned.rglob('*')]:
 name='.' if p==owned else str(p.relative_to(owned));actual.add(name);row=expected[name];s=p.lstat()
 assert stat.S_IMODE(s.st_mode)==row['mode']
 if row['kind']=='directory':assert stat.S_ISDIR(s.st_mode)
 else:assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==row['bytes'] and digest(p.read_bytes())==row['sha256']
assert actual==seen
receipt={'schema_version':1,'status':'fresh-actual-remote-source-export-recovered','remote_commit':COMMIT,'selected_blobs':rows,'archive_sha256':retained['archive_sha256'],'members':235,'files':files,'directories':directories,'logical_bytes':logical,'source_count':retained['source_count'],'package_count':retained['package_count'],'actual_numerical_jobs':0,'qualification':'Actual selected remote Git bodies and complete initial source export freshly recovered into a separate owned tree; exact original names, membership, modes, lengths and all file SHA256 hashes verified. No installed runtime, empirical stores, later Git/source A, input preparation, registration, Owner/Binding or scientific proof is recovered or implied. Original exported capsule and retained archive remain unchanged; no research identity is opened or replayed.'}
put(HERE/'REMOTE_SOURCE_EXPORT_RECOVERY01.json',(json.dumps(receipt,indent=2,sort_keys=True)+'\n').encode())
print(json.dumps({k:receipt[k] for k in ('status','remote_commit','members','files','directories','logical_bytes','actual_numerical_jobs')}))
