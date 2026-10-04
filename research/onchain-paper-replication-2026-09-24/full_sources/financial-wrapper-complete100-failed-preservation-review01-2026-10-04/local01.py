from pathlib import Path
import json,hashlib,os,stat,sys,io
D=Path(__file__).resolve().parent;F=D.parent;ROOT=F.parents[2];C=F/'financial-wrapper-complete100-failed-outcome-capture02-2026-10-04';OLD=F/'financial-wrapper-complete100-failed-outcome-capture01-2026-10-04';U=F/'financial-wrapper-complete100-final-supplement-tooling01-2026-10-04/utilities';sys.path.insert(0,str(U));import recovery_pax01 as R
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_bytes());checks=[]
def ok(v,n):assert v,n;checks.append(n)
cap=read(C/'CAPTURE01.json');ok(sha((C/'CAPTURE01.json').read_bytes())=='e9e78f1cc4f33d51ddca968bc80170e83e1a12b6ff2bff9cf301ab25e280fce8','exact actual correctedcapture02');master=read(C/'CAPSULE_MASTER_MANIFEST01.json');index=read(C/'CAPSULE_SHARD_INDEX01.json');ok(sha((C/'CAPSULE_MASTER_MANIFEST01.json').read_bytes())==cap['capsule_master_sha256']==index['master_manifest_sha256'],'master pin');ok(sha((C/'CAPSULE_SHARD_INDEX01.json').read_bytes())==cap['shard_index_sha256'],'index pin')
S=Path(index['original'])
def current():
 rows=[]
 for directory,dirs,files in os.walk(S,followlinks=False):
  if Path(directory)==S:dirs.remove('.git')
  for name in sorted(dirs+files):
   p=Path(directory)/name;s=p.lstat();row={'path':p.relative_to(S).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
   if stat.S_ISDIR(s.st_mode):row['kind']='directory'
   else:
    ok(stat.S_ISREG(s.st_mode)and s.st_nlink==1 and s.st_size<=R.FILE,'original finite plainbody '+row['path']);b=R.read(S,row['path']);row.update(kind='file',bytes=len(b),sha256=sha(b))
   rows.append(row)
 return {'schema_version':1,'root_mode':stat.S_IMODE(S.stat().st_mode),'members':sorted(rows,key=lambda x:x['path'])}
ok(current()==master,'complete actual nonGit source master before');files={r['path']:r for r in master['members']if r['kind']=='file'};dirs={r['path']:r for r in master['members']if r['kind']=='directory'};ok(len(master['members'])==588 and len(files)==475 and len(dirs)==113 and sum(r['bytes']for r in files.values())==23015911,'exact588/475/113/fullbytes')
union={};covered_dirs={};mapping=[];scope_details=[]
for label,row in cap['scopes'].items():
 manifest_raw=(C/(label.upper()+'_MANIFEST01.json')).read_bytes();m=json.loads(manifest_raw);ok(sha(manifest_raw)==row['manifest_sha256']==row['archive']['manifest_sha256'],'manifest complete pin '+label);snapshot=Path(row['snapshot']);ok(R.scan(snapshot)==m,'literal snapshot allmembers '+label);raw=(C/('complete-'+label+'01.tar.gz')).read_bytes();ok(sha(raw)==row['archive']['sha256']and len(raw)==row['archive']['bytes']<=R.FILE,'actual archive pin/bound '+label);frames=list(R.framed_members(raw));ok(len(frames)==len(m['members'])==row['typed_members'],'full actual framing '+label)
 for (name,t,b),r in zip(frames,m['members']):
  ok(name==r['path']and t.mode==r['mode']and t.uid==t.gid==0 and t.mtime==0,'actual canonical header '+label+'/'+name);ok(r['kind']=='directory'and t.isdir()and not b or r['kind']=='file'and t.isfile()and len(b)==r['bytes']and sha(b)==r['sha256'],'actual opaque body '+label+'/'+name)
  if label.startswith('capsule'):
   if r['kind']=='file':ok(name not in union and files[name]==r,'exact once capsule file '+name);union[name]=r;mapping.append({'path':name,'scope':label,'bytes':r['bytes'],'sha256':r['sha256']})
   else:ok(dirs[name]==r,'duplicate parent original mode '+name);covered_dirs[name]=r
 sink=io.BytesIO();R.tar_stream(snapshot,m,sink);ok(sink.getvalue()==raw,'whole canonical compressed inverse '+label);ok(R.scan(snapshot)==m,'stable afterpack '+label)
 if label.startswith('capsule'):ok(sum(r.get('bytes',0)for r in m['members'])<=3*1024**2,'3MiB shard logical bound '+label)
 else:ok(raw==(OLD/('complete-'+label+'01.tar.gz')).read_bytes()and manifest_raw==(OLD/(label.upper()+'_MANIFEST01.json')).read_bytes(),'literal reused old role only '+label)
 scope_details.append({'scope':label,'members':len(m['members']),'files':sum(r['kind']=='file'for r in m['members']),'archive_sha256':sha(raw)})
ok(union==files and covered_dirs==dirs,'complete file anddirectory coverage');ok(mapping==index['file_mapping'],'exact index ordered mapping')
# Independent deterministic3MiB sorted greedy group reconstruction.
groups=[[]];used=0
for name,r in sorted(files.items()):
 if groups[-1]and used+r['bytes']>3*1024**2:groups.append([]);used=0
 groups[-1].append(name);used+=r['bytes']
ok(len(groups)==8,'actual deterministic8shards')
for number,names in enumerate(groups,1):ok(names==[r['path']for r in mapping if r['scope']==f'capsule{number:02d}'],'exact greedy partition '+str(number))
parent=cap['scopes']['parent'];ok(R.scan(Path(parent['original']))==read(C/'PARENT_MANIFEST01.json'),'complete actual failed Parent')
support=Path(cap['scopes']['support']['snapshot']);roots=read(C/'SUPPORT_ROOTS01.json');print('support dirs',sorted(p.name for p in support.iterdir()))
for kind in ('contract','review'):
 origin=Path(roots[kind+'_original']);target=support/('final-contract'if kind=='contract'else 'failed-outcome-review');ok(R.scan(origin)==R.scan(target),'whole original support '+kind)
for row in read(C/'ROOT_EVIDENCE_PATHS01.json'):
 p=Path(row['original']);copy=support/row['support_path'];ok(p.read_bytes()==copy.read_bytes()and sha(p.read_bytes())==row['sha256']and len(p.read_bytes())==row['bytes']and stat.S_IMODE(p.stat().st_mode)==row['mode']==stat.S_IMODE(copy.stat().st_mode),'actual Root evidence literal '+p.name)
required=read(C/'REQUIRED_BODIES01.json');ok(len(required)==35 and sum(r['bytes']for r in required.values())==16481302,'exact35body81op finite map')
for name,row in required.items():
 b=(ROOT/name).read_bytes();ok(len(b)==row['bytes']<=R.FILE and sha(b)==row['sha256'],'actual full requiredbody '+name)
oldcap=read(OLD/'CAPTURE01.json');ok(sha((OLD/'CAPTURE01.json').read_bytes())==cap['prior_failed_capture_sha256'],'old zero capture preserved pin');ok(cap['prior_failed_capture_permanently_withheld']is True,'zero capture explicitly withheld')
ok(all(r['free_bytes']>=R.FLOOR for r in cap['floor_observations']),'every actual floor >=10GiB');ok(current()==master,'whole actual source stable final')
(D/'LOCAL_READBACK01.json').write_text(json.dumps({'checks':len(checks),'checks_detail':checks,'scopes':scope_details,'capsule_regular':len(files),'capsule_directories':len(dirs),'checkpoint_bodies_hashed_not_decoded':29,'actual_external_or_restore':False},indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':len(checks)}))
