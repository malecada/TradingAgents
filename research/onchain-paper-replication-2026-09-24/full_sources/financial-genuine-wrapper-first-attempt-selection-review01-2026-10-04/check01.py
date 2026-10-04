import ast,hashlib,json,os,shutil,stat,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;ROOT=Path.cwd();P=F/'financial-genuine-wrapper-root-remote-recovery04-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):
 assert v,m
 checks.append(m)
def sig(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read(p):
 s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2 and p.resolve()==p,'regular canonical bounded input');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  ck(sig(os.fstat(fd))==sig(s),'actual opened identity');out=[];total=0
  while True:
   b=os.read(fd,65536)
   if not b:break
   total+=len(b);ck(total<=s.st_size,'bounded extent');out.append(b)
  ck(sig(os.fstat(fd))==sig(s)==sig(p.lstat()) and total==s.st_size,'stable body identity');return b''.join(out)
 finally:os.close(fd)
def git(args,data=None):
 r=subprocess.run(['git','--no-replace-objects','-c','protocol.allow=never',*args],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env={'PATH':'/usr/bin:/bin','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','GIT_OPTIONAL_LOCKS':'0','GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_TERMINAL_PROMPT':'0'});ck(r.returncode==0 and len(r.stdout)<=8*1024**2 and len(r.stderr)<=65536,'bounded local Git only');return r.stdout
raw=read(P/'SELECTED_BODIES01.json');ck(sha(raw)=='c634d82450f8e67fb8480de09141be4b0a834a557139c707b50cab968b734fc2','exact selection pin');v=json.loads(raw);ck((json.dumps(v,sort_keys=True,indent=2)+'\n').encode()==raw,'canonical selection');H='19df9df4361857f99c24b493eb6a9be049bf594b';ck(v['remote_commit']==H,'explicit committed selection');rows=v['rows'];names=[r['path'] for r in rows];ck(names==sorted(set(names)) and len(rows)==394 and sum(r['bytes'] for r in rows)==13056456,'exact unique394 extent13056456');ck(11+2*len(rows)==799 and len(rows)<=506 and 799<=1024 and sum(r['bytes'] for r in rows)<=64*1024**2,'effective row and operation budgets');ck(git(['rev-parse','HEAD']).decode().strip()==H,'actual MainHEAD selectedcommit')
committed={}
for ent in git(['ls-tree','-r','-z',H,'--',*names]).split(b'\0'):
 if not ent:continue
 meta,path=ent.split(b'\t');mode,typ,oid=meta.decode().split();committed[path.decode()]={'git_mode':mode,'kind':typ,'git_object':oid}
ck(set(committed)==set(names),'exact committed selected tree');reply=b''.join(git(['cat-file','--batch'],(''.join(committed[n]['git_object']+'\n' for n in names[i:i+40])).encode()) for i in range(0,len(names),40));offset=0;joined=[]
for row in rows:
 n=row['path'];p=ROOT/n;meta=committed[n];ck(n.startswith('research/') and Path(n).as_posix()==n and '..' not in Path(n).parts and not any(x in ('.env','keys','apis') for x in Path(n).parts),'safe exact path');ck(type(row['bytes']) is int and 0<=row['bytes']<=4*1024**2 and meta['kind']=='blob' and meta['git_mode'] in ('100644','100755'),'regular selected mode extent');end=reply.index(b'\n',offset);oid,typ,size=reply[offset:end].decode().split();size=int(size);b=reply[end+1:end+1+size];offset=end+size+2
 ck(oid==meta['git_object'] and typ=='blob' and reply[offset-1:offset]==b'\n' and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+b).hexdigest()==oid,'actual Git blob body OID');ck(read(p)==b and sha(b)==row['sha256'] and len(b)==row['bytes'],'complete selected byte joins');mode=stat.S_IMODE(p.lstat().st_mode);ck(meta['git_mode']==('100755' if mode&0o111 else '100644'),'actual executable-mode Git join');joined.append(dict(row,git_mode=meta['git_mode'],git_object=oid,original_filesystem_mode=mode))
ck(offset==len(reply),'complete no trailingGitframe');selected=set(names);review_closures=[]
for row in rows:
 if Path(row['path']).name not in ('MANIFEST01.json','MANIFEST02.json'):continue
 p=ROOT/row['path'];m=json.loads(read(p));members=m.get('members',m.get('entries'));regular={str((p.parent/r['path']).relative_to(ROOT)) for r in members if r.get('kind',r.get('type'))=='file'};ck(regular<=selected,'all selected review manifest regular bodies included')
 for r in members:
  q=p.parent/r['path'];s=q.lstat();ck(stat.S_IMODE(s.st_mode)==r['mode'],'review metadata original mode')
  if r.get('kind',r.get('type'))=='file':ck(stat.S_ISREG(s.st_mode) and s.st_size==r.get('bytes',r.get('size')) and sha(read(q))==r['sha256'],'review actual full regular body')
  elif r.get('kind',r.get('type'))=='directory':ck(stat.S_ISDIR(s.st_mode),'review declared directory retained as metadata')
  else:raise AssertionError('unexpected review member kind')
 review_closures.append({'manifest':row['path'],'regular_members':len(regular),'typed_members':len(members)})

C=F/'financial-genuine-wrapper-root-preservation06-2026-10-04'
cap=json.loads(read(C/'CAPTURE01.json'));req=json.loads(read(C/'REQUEST01.json'))
ck(sha(read(C/'CAPTURE01.json'))=='645387e5bede68f778ad4a94c5e3b30c4e9f64bd10aa4cfb1108508939a8b899' and sha(read(C/'REQUEST01.json'))=='fb1f603733d24a5ca7e0eff41242651620b7561de17afc07668e1db102dbeca9','exact failed capture/request')
ck(cap['source']==req['source']=='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0' and [req[k] for k in ('tracked','source_pins','implementation','package')]==[290,289,194,149],'unchanged actual failedsource')
for role,count in [('source',878),('parent',30),('outer',8)]:
 mraw=read(C/(role.upper()+'_MANIFEST01.json'));m=json.loads(mraw);a=read(C/('complete-'+role+'01.tar.gz'))
 ck(sha(mraw)==cap['archives'][role]['manifest_sha256']==req['manifests'][role] and len(m['members'])==cap['members'][role]==count,'full failed manifest lineage '+role)
 ck(sha(a)==cap['archives'][role]['sha256'] and len(a)==cap['archives'][role]['bytes'],'full archive body '+role)
prior=json.loads(read(F/'financial-genuine-wrapper-root-remote-recovery03-2026-10-04/SELECTED_BODIES01.json'))['rows'];lookup={r['path']:r for r in rows}
ck(len(prior)==248 and all(lookup[r['path']]==r for r in prior),'all original248 support rows unchanged')
required=['root-preservation06','first-attempt-closure-review01','first-attempt-capture-review01','first-attempt-preservation-review01','first-attempt-flat-source-review01','root-flat-recovery04','root-first-launch01']
for name in required:
 d=F/('financial-genuine-wrapper-'+name+'-2026-10-04');regular={p.relative_to(ROOT).as_posix() for p in d.rglob('*') if p.is_file()}
 ck(regular<=selected,'whole relevant directory selected '+name)
I=F/'financial-genuine-wrapper-first-attempt-preservation-review01-2026-10-04'
ck(sha(read(I/'MANIFEST01.json'))=='9f58e0dc7b4069e496a4bf343119fdba6882fec0ff2685ac10c6940f08ae9b17','actual fullcapture review pin')
rv=json.loads(read(I/'READBACK01.json'));ck(rv['capture_sha256']==sha(read(C/'CAPTURE01.json')) and all(rv['archives'][k]['archive']==v for k,v in cap['archives'].items()),'full canonical archive review joined')
FR=F/'financial-genuine-wrapper-first-attempt-flat-source-review01-2026-10-04';flat=F/'financial-genuine-wrapper-root-flat-recovery04-2026-10-04'
ck(sha(read(FR/'MANIFEST01.json'))=='0bb4ea9214ec1c393fe2bdddb1eb66cdfafee15bdec11cd281f57837bd33b67c','exact independent transport-flat review')
ck(sha(read(flat/'restore01.py'))=='1b36e40c96045f35ea4a4e6926b9da6a594ab82c0346aa0ddb6c2bbb5aa5c02c' and sha(read(P/'recover_financial04.py'))=='188a60d2dace234a2090024109ca6cf7beb2b3355b1e759631eac8b4160dfb31','reviewed actual helpers unchanged')
for n,pin in req['primitive_sha256'].items():
 p=F/'held-consumer-final-recovery-preparation04-2026-10-03'/n;ck(p.relative_to(ROOT).as_posix() in selected and sha(read(p))==pin,'exact primitive selected')
ck(len({r['git_object'] for r in joined})==235,'235 unique authenticated blobs')
ck((P/'SELECTED_BODIES01.json').relative_to(ROOT).as_posix() not in selected,'local postcommit selection not selfselected')
ck(all(not os.path.lexists(P/n) for n in ['fresh-financial04.git','selected','REMOTE_RECOVERY01.json','FAILED01.json']),'fresh remote namespace absent')
ck(all(not os.path.lexists(flat/n) for n in ['flat-source01','flat-parent01','flat-outer01','INTENT01.json','RECOVERY01.json']),'fresh flat namespace absent')
S=Path(req['roots']['source']);ck(not os.path.lexists(S/'research_runs'),'actual claims namespace absent')
ck(cap['original_parent_terminal_exit'] is None and cap['actual_outer_exit']==1 and cap['numerical_claims']==0 and cap['failed_identity_permanently_reserved'] is True,'preserved actual failure accounting')
free=shutil.disk_usage(P).free;ck(free>=10*1024**3,'actual 10GiB observed floor')
ck(git(['rev-parse','HEAD']).decode().strip()==H,'Main HEAD unchanged during checks')
ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
out={'schema_version':1,'decision':'ACCEPTED_EXACT_FAILED_SCOPE_LOCAL_SELECTION_PENDING_ACTUAL_REMOTE','checks':len(checks),'selection_sha256':sha(raw),'selected_commit':H,'selected_count':394,'selected_logical_bytes':13056456,'expected_git_operations':799,'unique_git_objects':235,'effective_maximum_rows':506,'capture_sha256':sha(read(C/'CAPTURE01.json')),'archives':cap['archives'],'complete_review_regular_closures':review_closures,'disk_free_bytes':free,'fresh_namespaces_absent':True,'actual_remote_or_flat_recovery':False,'numerical_claims':0,'old_identity_reserved':True,'runtime_native_authority':False,'joined':joined}
(O/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('joined','complete_review_regular_closures')},indent=2))
