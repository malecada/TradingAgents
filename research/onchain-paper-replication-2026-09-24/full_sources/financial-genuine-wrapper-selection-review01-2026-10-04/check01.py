import ast,hashlib,json,os,shutil,stat,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;ROOT=Path.cwd();P=F/'financial-genuine-wrapper-root-remote-recovery01-2026-10-03';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):
 assert v,m
 checks.append(m)
def read(p):
 s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2 and p.resolve()==p,'regular canonical bounded input');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  ck(os.fstat(fd)==s,'actual opened identity');out=[];total=0
  while True:
   b=os.read(fd,65536)
   if not b:break
   total+=len(b);ck(total<=s.st_size,'bounded extent');out.append(b)
  ck(os.fstat(fd)==s==p.lstat() and total==s.st_size,'stable body identity');return b''.join(out)
 finally:os.close(fd)
def git(args,data=None):
 r=subprocess.run(['git','--no-replace-objects','-c','protocol.allow=never',*args],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env={'PATH':'/usr/bin:/bin','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','GIT_OPTIONAL_LOCKS':'0','GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_TERMINAL_PROMPT':'0'});ck(r.returncode==0 and len(r.stdout)<=8*1024**2 and len(r.stderr)<=65536,'bounded local Git only');return r.stdout
raw=read(P/'SELECTED_BODIES01.json');ck(sha(raw)=='a9d2a39e42f8fec671fec5972fb213569a2aa370b20c4098e8028186aad09bae','exact selection pin');v=json.loads(raw);ck((json.dumps(v,sort_keys=True,indent=2)+'\n').encode()==raw,'canonical selection');H='cd54c7b8fad26b91d06917621c4862e77b73b2c8';ck(v['remote_commit']==H,'explicit committed selection');rows=v['rows'];names=[r['path'] for r in rows];ck(names==sorted(set(names)) and len(rows)==102 and sum(r['bytes'] for r in rows)==3456055,'exact unique102 extent3456055');ck(11+2*len(rows)==215 and len(rows)<=506 and 215<=1024 and sum(r['bytes'] for r in rows)<=64*1024**2,'effective row and operation budgets');ck(git(['rev-parse','HEAD']).decode().strip()==H,'actual MainHEAD selectedcommit')
committed={}
for ent in git(['ls-tree','-r','-z',H,'--',*names]).split(b'\0'):
 if not ent:continue
 meta,path=ent.split(b'\t');mode,typ,oid=meta.decode().split();committed[path.decode()]={'git_mode':mode,'kind':typ,'git_object':oid}
ck(set(committed)==set(names),'exact committed selected tree');reply=git(['cat-file','--batch'],(''.join(committed[n]['git_object']+'\n' for n in names)).encode());offset=0;joined=[]
for row in rows:
 n=row['path'];p=ROOT/n;meta=committed[n];ck(n.startswith('research/') and Path(n).as_posix()==n and '..' not in Path(n).parts and not any(x in ('.env','keys','apis') for x in Path(n).parts),'safe exact path');ck(type(row['bytes']) is int and 0<=row['bytes']<=4*1024**2 and meta['kind']=='blob' and meta['git_mode'] in ('100644','100755'),'regular selected mode extent');end=reply.index(b'\n',offset);oid,typ,size=reply[offset:end].decode().split();size=int(size);b=reply[end+1:end+1+size];offset=end+size+2
 ck(oid==meta['git_object'] and typ=='blob' and reply[offset-1:offset]==b'\n' and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+b).hexdigest()==oid,'actual Git blob body OID');ck(read(p)==b and sha(b)==row['sha256'] and len(b)==row['bytes'],'complete selected byte joins');mode=stat.S_IMODE(p.lstat().st_mode);ck(meta['git_mode']==('100755' if mode&0o111 else '100644'),'actual executable-mode Git join');joined.append(dict(row,git_mode=meta['git_mode'],git_object=oid,original_filesystem_mode=mode))
ck(offset==len(reply),'complete no trailingGitframe');selected=set(names);review_closures=[]
for row in rows:
 if not row['path'].endswith('/MANIFEST01.json'):continue
 p=ROOT/row['path'];m=json.loads(read(p));regular={str((p.parent/r['path']).relative_to(ROOT)) for r in m['members'] if r['kind']=='file'};ck(regular<=selected,'all selected review manifest regular bodies included')
 for r in m['members']:
  q=p.parent/r['path'];s=q.lstat();ck(stat.S_IMODE(s.st_mode)==r['mode'],'review metadata original mode')
  if r['kind']=='file':ck(stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and sha(read(q))==r['sha256'],'review actual full regular body')
  elif r['kind']=='directory':ck(stat.S_ISDIR(s.st_mode),'review declared directory retained as metadata')
  else:raise AssertionError('unexpected review member kind')
 review_closures.append({'manifest':row['path'],'regular_members':len(regular),'typed_members':len(m['members'])})
C=F/'financial-genuine-wrapper-root-preservation02-2026-10-04';ck({str(p.relative_to(ROOT)) for p in C.iterdir()}<=selected,'all capture scope/support bodies selected');cap=json.loads(read(C/'CAPTURE01.json'));request=json.loads(read(C/'REQUEST01.json'));manifest=json.loads(read(C/'complete-manifest01.json'));ck(cap['source']==request['actual_HEAD']=='868bfa6404a2c34d6e5b6e0932a2baf4b38eb370' and cap['members']==len(manifest['members'])==755 and cap['regular_bodies']==533 and request['complete_tracked']==243,'exact wholecurrent243755533capture');ck(sha(read(C/'complete-source01.tar.gz'))==cap['archive']['sha256']=='497a0ae3c0aba9b5f8bb41e933bed878ba49adf759a880d8a338637d732d1af4','full archive actual selected');support=json.loads(read(F/'financial-genuine-wrapper-full-scope-preservation-review02-2026-10-04/SUPPORT01.json'))
for r in support['members']:ck(str((C/r['path']).relative_to(ROOT)) in selected and sha(read(C/r['path']))==r['sha256'],'exact captured support selection')
T=F/'financial-genuine-wrapper-root-transport-review01-2026-10-03';review=json.loads(read(T/'SOURCE_REVIEW01.json'));source=read(P/'recover_financial01.py');ck(sha(source)==review['source_sha256']=='20a37f3026233ffcd69c6424c38416a27baf01ccc34b1d410f18f5ec0cd59310','exact reviewed transport source');ck(sha(read(T/'SOURCE_REVIEW01.md'))=='32ab339ce1ca415f7cd19879fdc57ec506563fbfc9011be009898380ff63f48a' and sha(read(T/'MANIFEST01.json'))=='3a119f0dd3d01e590eadd2a81379fa5170332567f297d3c6ba9d55bf9333c790','independent transport accepted frozen review');text=source.decode();ck('len(CALLS) < 1024' in text and 'START < 600' in text and 'begun < 60' in text and '10 * 1024**3' in text,'finite source budget predicates unchanged');ck(all(not os.path.lexists(P/n) for n in ['fresh-financial01.git','selected','REMOTE_RECOVERY01.json','FAILED01.json']),'actual transport namespace pristine')
free=shutil.disk_usage(P).free;ck(free>=10*1024**3,'observed current10GiBfloor');ck(git(['rev-parse','HEAD']).decode().strip()==H,'final unchanged selectedMainHEAD');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numericalimports');out={'schema_version':1,'decision':'ACCEPTED_EXACT_LOCAL_FINANCIAL_TRANSPORT_SELECTION_PENDING_ACTUAL_REMOTE','selection_sha256':sha(raw),'committed_source':H,'selected_count':102,'selected_logical_bytes':3456055,'expected_git_operations':215,'effective_maximum_rows':506,'checks':len(checks),'current_financial_source':cap['source'],'archive_sha256':cap['archive']['sha256'],'current_disk_free_bytes':free,'pristine_transport_namespace_verified':True,'remote_origin_independently_verified':False,'actual_remote_recovery':False,'actual_flat_recovery':False,'native_registration_budget_authority':False,'complete_review_regular_closures':review_closures,'joined':joined};(O/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['joined','complete_review_regular_closures']},indent=2))
