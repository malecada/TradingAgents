"""Exact second failed-pilot ordinary preservation source and archive review."""
from pathlib import Path
import hashlib,io,json,stat,tarfile
R=Path.cwd();BASE=Path('research/onchain-paper-replication-2026-09-24');F=BASE/'full_sources'
P=F/'real-data-pilot-second-resource-failed-review01-2026-10-06';H=P/'ordinary-entry01'
I='real-pilot-second-resource-failed-preservation-20261006-01';OI='real-pilot-first-resource-failed-preservation-20261006-01'
S=BASE/'storage'/I;OLD=BASE/'storage'/OI;CAP=F/'real-data-pilot-second-resource-failed-increment01-2026-10-06'
cache={}
def raw(p):
 p=Path(p)
 if p not in cache:
  q=R/p;s=q.lstat();assert q.resolve(strict=True)==q and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
  b=q.read_bytes();z=q.lstat();assert len(b)==s.st_size and (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns);cache[p]=b
 return cache[p]
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def read(p):return json.loads(raw(p))
def ref(p):return {'path':str(p),'sha256':sha(p)}
def write(n,v):
 p=H/n
 with p.open('x') as f:f.write(json.dumps(v,sort_keys=True,indent=2)+'\n')
 return p
e=read(S/'envelope01.json');selection=read(S/'selection01.json');inv=read(S/'INVERSE01.json');capture=read(CAP/'CAPTURE01.json');scope=read(P/'INCREMENT_SELECTION01.json')
prior=read(OLD/'RELEASE_REVIEW01.json');pe=read(OLD/'envelope01.json')
assert sha(OLD/'RELEASE_REVIEW01.json')=='f4e5ffa46af888621c71acb6626e8a00a01b9eb23268de22a3342fb732e6bdbc' and prior['decision']=='accepted'
assert e['identity']==selection['identity']==I and sha(S/'envelope01.json')==inv['envelope']['sha256']=='9cde1f3ef0754c30e7616377bc3e837484bf53c1ab8259216437d114dcd25d74'
assert sha(S/'selection01.json')==inv['selection']['sha256']==e['selection']['sha256']
assert sha(CAP/'CAPTURE01.json')==inv['capture']['sha256']=='82c29777bbdaedf60dd92a26212bc2d61766f5d00f058c89beb243290cf78cda'
assert inv['predecessor']==str(OLD)
for name in ('entry01.py','keep.py'):
 assert raw(S/name).count(I.encode())==raw(OLD/name).count(OI.encode())==1
 assert raw(S/name).replace(I.encode(),OI.encode())==raw(OLD/name)
 assert sha(OLD/name)==prior['evidence'][str(OLD/name)]
assert len(e['source_files'])==12
for p,pin in e['source_files'].items():
 assert sha(p)==pin
 if p not in (str(S/'entry01.py'),str(S/'keep.py')):assert pe['source_files'][p]==pin==prior['evidence'][p]
for k in ('connection','environment','transport','local_only_evidence','scanner_sha256'):assert e[k]==pe[k]
private=e['connection']['path'];assert e['local_only_evidence']==[private] and private not in e['source_files']
assert e['helper']==ref(S/'keep.py')
assert sha(e['environment']['path'])==e['environment']['sha256']
for r in e['evidence']:assert sha(r['path'])==r['sha256']
assert sha(P/'OUTCOME_REVIEW01.json')=='6cb4bdae9a8b1dc13c43811d37b57518d50f967b3e425183a0696e7fc5b4e9d7'
assert sha(P/'INCREMENT_SELECTION01.json')=='e07439c085399448192ba1003f343767a32ce33d2cf95f3c7896f21959717b2d'
assert scope['decision']=='accepted' and capture['selection']==ref(P/'INCREMENT_SELECTION01.json')
expected={r['path']:r for r in scope['files']+scope['directories']};captured={r['path']:r for r in capture['members']}
assert len(expected)==len(captured)==len(capture['members'])==48 and set(expected)==set(captured)
for p,r in expected.items():
 assert captured[p]['kind']==r['kind'] and captured[p]['mode']==r['mode']
 if r['kind']=='regular':assert all(captured[p][k]==r[k] for k in ('bytes','sha256','stat_identity'))
assert capture['regular_count']==38 and capture['directory_count']==10 and capture['original_regular_bytes']==395772 and capture['fresh_external_recovery'] is None
assert selection['count']==len(selection['files'])==1 and selection['directories']==[]
row=selection['files'][0];archive=Path(row['path'])
assert capture['archive']=={k:row[k] for k in ('path','sha256','bytes')}
assert selection['total_bytes']==selection['max_body_bytes']==row['bytes']==481280
assert sha(archive)==row['sha256']=='beec1ce98ef3214a8486a01af03e939301f2966369faf39f29cb4362d65e87d6'
s=archive.lstat();assert row['mode']==stat.S_IMODE(s.st_mode) and row['nlink']==s.st_nlink==1 and row['stat_identity']==[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
assert selection['disk_floor_bytes']==10*1024**3 and selection['owned_tree_limit_bytes']==5*1024**3 and selection['transport_payload_budget_bytes']==8*1024**3
assert selection['remote']=='research-backups/onchain-paper-replication-2026-09-24/'+I
with tarfile.open(fileobj=io.BytesIO(raw(archive)),mode='r:') as tf:
 seen=set()
 for m in tf.getmembers():
  p=m.name.rstrip('/');assert p in expected and p not in seen and not Path(p).is_absolute() and '..' not in Path(p).parts;seen.add(p);r=expected[p];assert m.mode==r['mode']
  if r['kind']=='directory':assert m.isdir() and m.size==0
  else:
   assert m.isfile() and not m.issym() and not m.islnk() and m.size==r['bytes']
   with tf.extractfile(m) as stream:b=stream.read(m.size+1)
   assert len(b)==m.size and hashlib.sha256(b).hexdigest()==r['sha256']
 assert seen==set(expected)
for n in ('preflight01.json','launch-attempt01.json','guard01','intent.json','complete.json','failed.json','outer-exit01.json'):assert not (S/n).exists() and not (S/n).is_symlink()
check={'schema_version':1,'decision':'accepted','identity':I,'envelope_sha256':sha(S/'envelope01.json'),'archive':capture['archive'],
 'archive_original_streams':1,'regular_count':38,'directory_count':10,'total_names':48,'unpacked_regular_bytes':395772,'all_member_bytes_names_modes_joined':True,
 'exact_entry_helper_single_identity_inverse':True,'unchanged_other_source_pins':10,'total_source_pins':12,'one_use_namespace_unused':True,
 'private_body_opened':False,'transport_native_claim_invoked':False,'external_recovery':None,'predecessor_release':ref(OLD/'RELEASE_REVIEW01.json'),
 'qualification':'Local archive/member and exact source/entry composition only; fresh entry controls and actual external recovery still required.'}
cp=write('CHECK01.json',check)
evidence=dict(e['source_files'])
for p in [S/'envelope01.json',S/'selection01.json',S/'INVERSE01.json',CAP/'CAPTURE01.json',P/'OUTCOME_REVIEW01.json',P/'INCREMENT_SELECTION01.json',P/'MANIFEST01.json',OLD/'RELEASE_REVIEW01.json',OLD/'envelope01.json',OLD/'entry01.py',OLD/'keep.py',Path(e['environment']['path']),H/'review01.py',cp]:evidence[str(p)]=sha(p)
assert private not in evidence and str(archive) not in evidence
release={'schema_version':1,'decision':'accepted','identity':I,'envelope_sha256':sha(S/'envelope01.json'),'evidence':dict(sorted(evidence.items())),
 'scope':'ONE ordinary preservation of the481280-byte failed02 increment archive containing38actual regular metadata/log bodies395772bytes and10typed directory names/modes, including the separate actual resource journal.',
 'check':ref(cp),'archive':capture['archive'],
 'qualification':'Reused exact released entry/helper with one fixed-ID literal each and unchanged10other source pins. Mandatory actual committed/released bodies and remote HEAD, runtime, unused namespace, absent competing native/claim, fresh3.5GiB RAM and complete recovery scratch plus10GiBfloor remain required. Native256MiBmax/192MiBhigh/zeroSwap/3GiBreserve/14400seconds and5GiBowned/8GiBpayload unchanged. Original scientific02 remains permanentlyFAILED/spent. No deletion, scientific run, budget refund, capacity, external recovery or transport success is granted.',
 'private_connection':'Unchanged local-only opaque reference; not opened.',
 'not_tested':['No fresh native/physical/process/remote-Git preflight, transport or network invoked.','No external recovery yet; one actual returned archive must receive independent byte/member acceptance.','No scientific/raw/runtime/graph/numerical bodies or financial claims tested.']}
rp=write('RELEASE_REVIEW01.json',release);mp=write('MANIFEST01.json',{'schema_version':1,'decision':'accepted','identity':I,'files':[ref(H/'review01.py'),ref(cp),ref(rp)]})
print(json.dumps({'release':ref(rp),'manifest':ref(mp),'check':ref(cp),'evidence_count':len(evidence),'decision':'accepted'},sort_keys=True))
