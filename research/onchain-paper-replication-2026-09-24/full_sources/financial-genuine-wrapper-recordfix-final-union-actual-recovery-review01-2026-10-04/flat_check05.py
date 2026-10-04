import ast,hashlib,json,os,shutil,stat,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;ROOT=Path.cwd();P=F/'financial-genuine-wrapper-root-recordfix-final-remote01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
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
raw=read(P/'SELECTED_BODIES01.json');ck(sha(raw)=='07eb83d17a4ba0e7521fac189f6fdccd91a5e2d3d43a863ca92eed21de1a0de1','exact selection pin');raw_selection=raw;v=json.loads(raw);ck((json.dumps(v,sort_keys=True,indent=2)+'\n').encode()==raw,'canonical selection');H='712fee46e11dece8138ab08778a1f9819a10cad3';ck(v['remote_commit']==H,'explicit committed selection');rows=v['rows'];names=[r['path'] for r in rows];ck(names==sorted(set(names)) and len(rows)==82 and sum(r['bytes'] for r in rows)==5662993,'exact unique82 extent5662993');ck(11+2*len(rows)==175 and len(rows)<=506 and 175<=1024 and sum(r['bytes'] for r in rows)<=64*1024**2,'effective row and operation budgets');ck(git(['rev-parse','HEAD']).decode().strip()==H,'actual MainHEAD selectedcommit')
committed={}
for ent in git(['ls-tree','-r','-z',H,'--',*names]).split(b'\0'):
 if not ent:continue
 meta,path=ent.split(b'\t');mode,typ,oid=meta.decode().split();committed[path.decode()]={'git_mode':mode,'kind':typ,'git_object':oid}
ck(set(committed)==set(names),'exact committed selected tree');reply=b''.join(git(['cat-file','--batch'],(''.join(committed[n]['git_object']+'\n' for n in names[i:i+40])).encode()) for i in range(0,len(names),40));offset=0;joined=[]
for row in rows:
 n=row['path'];p=ROOT/n;meta=committed[n];ck(n.startswith('research/') and Path(n).as_posix()==n and '..' not in Path(n).parts and not any(x in ('.env','keys','apis') for x in Path(n).parts),'safe exact path');ck(type(row['bytes']) is int and 0<=row['bytes']<=4*1024**2 and meta['kind']=='blob' and meta['git_mode'] in ('100644','100755'),'regular selected mode extent');end=reply.index(b'\n',offset);oid,typ,size=reply[offset:end].decode().split();size=int(size);b=reply[end+1:end+1+size];offset=end+size+2
 ck(oid==meta['git_object'] and typ=='blob' and reply[offset-1:offset]==b'\n' and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+b).hexdigest()==oid,'actual Git blob body OID');ck(read(p)==b and sha(b)==row['sha256'] and len(b)==row['bytes'],'complete selected byte joins');mode=stat.S_IMODE(p.lstat().st_mode);ck(meta['git_mode']==('100755' if mode&0o111 else '100644'),'actual executable-mode Git join');joined.append(dict(row,git_mode=meta['git_mode'],git_object=oid,original_filesystem_mode=mode))
ck(offset==len(reply),'complete no trailingGitframe');selected=set(names)

import gzip,io,tarfile,importlib.util
ck(len({x['git_object'] for x in joined})==65,'actual65 unique immutable objects')
rootread=json.loads(read(P/'SELECTION_READBACK01.json'));snapshot_results=[];archived_coverage=set()
for suffix,originname,count,regular in [('final-review','financial-genuine-wrapper-recordfix-final-union-capture-review01-2026-10-04',64,44)]:
 base=F/('financial-genuine-wrapper-root-recordfix-'+suffix+'-snapshot01-2026-10-04');origin=F/originname;auth=json.loads(read(base/'AUTHENTICATION01.json'));mr=read(base/'manifest.json');manifest=json.loads(mr);raw=read(base/'review.tar.gz');ck(sha(mr)==auth['manifest_sha256'] and sha(raw)==auth['archive_sha256'] and len(raw)==auth['archive_bytes'],'snapshot exact pins')
 members=manifest['members'];by={r['path']:r for r in members};ck(len(by)==len(members)==count and list(by)==sorted(by) and set(by)=={'.'}|{p.relative_to(origin).as_posix() for p in origin.rglob('*')},'whole snapshot current original membership')
 for r in members:
  p=origin if r['path']=='.' else origin/r['path'];st=p.lstat();ck(stat.S_IMODE(st.st_mode)==r['mode'],'snapshot every original mode')
  if r['kind']=='file':ck(stat.S_ISREG(st.st_mode) and len(read(p))==r['bytes'] and sha(read(p))==r['sha256'],'snapshot every original body');archived_coverage.add(p.relative_to(ROOT).as_posix())
  elif r['kind']=='directory':ck(stat.S_ISDIR(st.st_mode),'snapshot directory type')
  else:ck(r['kind']=='lexical-symlink' and stat.S_ISLNK(st.st_mode) and os.readlink(p)==r['target'],'literal symlink target only')
 # Bound decompression before a tar parser can interpret any PAX metadata.
 with gzip.GzipFile(fileobj=io.BytesIO(raw)) as gz:
  chunks=[];size=0
  while True:
   b=gz.read(65536)
   if not b:break
   size+=len(b);ck(size<=192*1024**2,'bounded snapshot inflated size');chunks.append(b)
 inflated=b''.join(chunks);offset=0;headers=0;pax=0
 while True:
  h=inflated[offset:offset+512];ck(len(h)==512,'complete raw512 header');offset+=512
  if h==bytes(512):ck(inflated[offset:offset+512]==bytes(512) and not any(inflated[offset:]),'canonical zero footer');break
  headers+=1;ck(headers<=65538,'bounded raw header count');checksum=int(h[148:156].strip(b'\0 ') or b'0',8);ck(sum(h[:148])+256+sum(h[156:])==checksum,'raw header checksum');length=int(h[124:136].strip(b'\0 ') or b'0',8);kind=h[156:157];ck(kind in [b'0',b'5',b'2',b'x'] and length<=4194304,'bounded allowed header kind/extent')
  body=inflated[offset:offset+length];ck(len(body)==length,'complete raw member extent');padding=(-length)%512;ck(not any(inflated[offset+length:offset+length+padding]),'zero member padding');offset+=length+padding
  if kind==b'x':
   pax+=1;ck(length<=8192,'bounded PAX before interpretation');i=0;keys=[]
   while i<len(body):
    j=body.index(b' ',i);n=int(body[i:j]);record=body[j+1:i+n];ck(n>j-i+1 and i+n<=len(body) and record.endswith(b'\n'),'PAX exact record framing');key=record.split(b'=',1)[0];ck(key in [b'path',b'linkpath'] and key not in keys,'PAX path/linkpath only unique');keys.append(key);i+=n
   ck(i==len(body),'complete PAX framing')
 bodies={}
 with tarfile.open(fileobj=io.BytesIO(inflated),mode='r:') as tar:
  ts=tar.getmembers();ck([t.name for t in ts]==[r['path'] for r in members if r['path']!='.'],'exact tar sorted member names')
  for t in ts:
   r=by[t.name];ck(t.mode==r['mode'] and t.uid==t.gid==0 and t.uname==t.gname=='' and t.mtime==0,'every canonical tar metadata field')
   if r['kind']=='file':
    ck(t.isfile() and t.size==r['bytes'],'regular tar type/extent');b=tar.extractfile(t).read();ck(sha(b)==r['sha256'] and b==read(origin/t.name),'every snapshot opaque archive body');bodies[t.name]=b
   elif r['kind']=='directory':ck(t.isdir() and t.size==0,'tar directory metadata')
   else:ck(t.issym() and t.size==0 and t.linkname==r['target']==os.readlink(origin/t.name),'tar lexical symlink never followed')
 output=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=output,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
   for r in members:
    if r['path']=='.':continue
    t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
    if r['kind']=='directory':t.type=tarfile.DIRTYPE;t.size=0;tar.addfile(t)
    elif r['kind']=='lexical-symlink':t.type=tarfile.SYMTYPE;t.linkname=r['target'];t.size=0;tar.addfile(t)
    else:t.size=r['bytes'];tar.addfile(t,io.BytesIO(bodies[r['path']]))
 ck(output.getvalue()==raw,'whole canonical snapshot exact recompression')
 original_manifest=origin/'MANIFEST02.json';ck(sha(read(original_manifest))==manifest['original_review_manifest_sha256']==auth['original_review_manifest_sha256'],'original frozen manifest included')
 original=json.loads(read(original_manifest))
 for r in original.get('members',original.get('entries',[])):
  saved=by[r['path']];ck(r['mode']==saved['mode'],'original review all modes joined')
  if r.get('kind',r.get('type'))=='file':ck(r['sha256']==saved['sha256'] and r.get('bytes',r.get('size'))==saved['bytes'],'original review all frozen file metadata joined')
 ck(len(bodies)==regular,'exact whole review regular count');snapshot_results.append({'origin':str(origin),'typed_members_including_root':count,'regular_bodies':regular,'archive_sha256':sha(raw),'manifest_sha256':sha(mr),'raw_headers':headers,'pax_headers':pax,'literal_symlinks':sum(r['kind']=='lexical-symlink' for r in members),'canonical_recompression':True})
C=F/'financial-genuine-wrapper-recordfix-capture-preparation01-2026-10-04';sys.path.insert(0,str(C));sp=importlib.util.spec_from_file_location('selected_source_capture',C/'capture01.py');module=importlib.util.module_from_spec(sp);sp.loader.exec_module(module);a=module.R;cap=F/'financial-genuine-wrapper-root-recordfix-capture01-2026-10-04';q=json.loads(read(cap/'request.json'));m=json.loads(read(cap/'source-manifest.json'));ck(a.scan(module.CAP)==m==q['manifest'],'actual whole corrected source986 stable');ck(a.encode(module.authenticate())==read(cap/'source-authentication.json'),'actual325Git324pins8roles194149 current source authority')
prior=F/'held-consumer-final-released-scope-capture-review01-2026-10-03/check01.py';defs=[n for n in ast.parse(read(prior)).body if isinstance(n,ast.FunctionDef) and n.name in ['decode','recode']];exec(compile(ast.Module(body=defs,type_ignores=[]),str(prior),'exec'));archive=read(cap/'source.tar.gz');body,framing=decode(archive,m);ck(recode(m,body)==archive and sha(archive)=='8d49d60b509bc9c95cd04274127b12387b8070295499dad3d24db63b9a376efb','whole source archive canonical recompression')
for r in m['members']:
 if r['kind']=='file':ck(body[r['path']]==a.read(module.CAP,r['path']),'every archived current source body')
U=F/'financial-genuine-wrapper-root-recordfix-final-union01-2026-10-04';um=json.loads(read(U/'union-manifest.json'));ua=json.loads(read(U/'UNION_AUTHENTICATION01.json'));ur=read(U/'union.tar.gz');ub,uframe=decode(ur,um);ck(recode(um,ub)==ur and sha(ur)==ua['archive']['sha256']=='441fe2bb20203213d72fac1d2b0b59e1ada3c8a608bf1a5474a02464a0214237','full final union canonical recompression');ck(sha(read(U/'union-manifest.json'))==ua['archive']['manifest_sha256'],'union manifest authentication');mapping=json.loads(ub['ORIGINAL_TREES01.json']);ck(sha(ub['ORIGINAL_TREES01.json'])==ua['union_mapping_sha256'],'actual complete original mapping')
A=F/'financial-genuine-wrapper-recordfix-final-union-recovery-preparation01-2026-10-04';sp=importlib.util.spec_from_file_location('source_union_adapter',A/'restore_union01.py');adapter=importlib.util.module_from_spec(sp);sp.loader.exec_module(adapter);q={'archive':{'bytes':len(ur),'sha256':sha(ur)},'manifest':{'sha256':sha(read(U/'union-manifest.json'))}};semantic=adapter.authenticate_union(q,um,read(U/'UNION_AUTHENTICATION01.json'),ub['ORIGINAL_TREES01.json']);ck(semantic['original_regular_members']==275 and semantic['original_typed_members']==306 and semantic['original_trees']==11,'exact original denominators');ck(len(um['members'])==307 and sum(r['kind']=='file' for r in um['members'])==276,'full ordinary union307/276')
coverage=selected|archived_coverage;original_bodies={}
for tree in mapping['scope_trees']:
 root=Path(tree['original_root']);rows=tree['members'];names={'.'}|{p.relative_to(root).as_posix() for p in root.rglob('*')};ck(names=={r['path'] for r in rows},'fresh complete actual original tree membership '+tree['scope'])
 for r in rows:
  p=root/r['path'];s=p.lstat();ck(stat.S_IMODE(s.st_mode)==r['mode'],'each original mode')
  if r['kind']=='directory':ck(stat.S_ISDIR(s.st_mode),'each original directory type')
  elif r['kind']=='lexical-symlink':ck(stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'],'literal original link only')
  else:
   b=read(p);ck(b==ub[r['union_path']] and sha(b)==r['sha256'] and len(b)==r['bytes'],'every original275 body mapped from canonical archive');original_bodies[str(p)]=b
   if p.is_relative_to(ROOT):coverage.add(p.relative_to(ROOT).as_posix())
# Source-only prep/review are actually selected in full; not merely copied manifests.
for dirname,manifestpin in [('financial-genuine-wrapper-recordfix-final-union-recovery-preparation01-2026-10-04','4cdd415f9f318c5931da073709383825e8c7e9edcf5b6d601253d2fe2f8f86be'),('financial-genuine-wrapper-recordfix-final-union-recovery-review01-2026-10-04','c8de8680f235ef0d0fc685a5ad05717f0f919c5df2f56b239cc62648f34f06b2')]:
 d=F/dirname;mr=read(d/'MANIFEST01.json');ck(sha(mr)==manifestpin,'actual accepted source review manifest');mrj=json.loads(mr);ck({p.relative_to(d).as_posix() for p in d.rglob('*')}=={r['path'] for r in mrj['members']}|{'MANIFEST01.json'},'full current source-only scope')
 for r in mrj['members']:
  p=d/r['path'];ck(stat.S_IMODE(p.lstat().st_mode)==r['mode'],'source-only original mode')
  if r['kind']=='file':ck(p.relative_to(ROOT).as_posix() in selected and sha(read(p))==r['sha256'],'complete source-only selected witness bytes')
# All original caller/binder/verifier review manifest entries must be present in their original tree or explicit sibling schema provenance.
manifest_joins=0;relocated_manifest_witnesses=[]
for path,raw_body in original_bodies.items():
 p=Path(path)
 if p.name not in ('MANIFEST01.json','MANIFEST02.json','MANIFEST_ACTUAL02.json'):continue
 doc=json.loads(raw_body)
 for row in doc.get('members',doc.get('entries',[])):
  kind=row.get('kind',row.get('type'))
  if kind!='file':continue
  target=p.parent/row['path']
  if str(target) not in original_bodies:
   matches=[Path(other).parent/row['path'] for other,otherraw in original_bodies.items() if otherraw==raw_body and str(Path(other).parent/row['path']) in original_bodies and sha(original_bodies[str(Path(other).parent/row['path'])])==row['sha256']]
   ck(bool(matches),'copied manifest resolved by exact original manifest and actual archived witness body');target=sorted(matches)[0];relocated_manifest_witnesses.append({'copied_manifest':str(p),'member':row['path'],'actual_original_body':str(target),'sha256':row['sha256']})
  ck(sha(original_bodies[str(target)])==row['sha256'],'original complete applicable manifest body');manifest_joins+=1
ck(sha(read(P/'recover01.py'))=='0b397ccd0a014f60a414ce79d67dfd53c58a0fb61ca616a6576cc43da4bbf0aa','unchanged accepted transport algorithm')
ck(all(os.path.lexists(P/n) for n in ['fresh-recordfix-source325-01.git','selected','REMOTE_RECOVERY01.json','INTENT01.json']) and not os.path.lexists(P/'FAILED01.json'),'actual single closed transport namespace')
ck(not os.path.lexists(module.CAP/'research_runs'),'zero genuine source claims');free=shutil.disk_usage(P).free;ck(free>=10*1024**3,'current observed disk floor');ck(git(['rev-parse','HEAD']).decode().strip()==H,'Main unchanged during independent review');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
receipt_raw=read(P/'REMOTE_RECOVERY01.json');ck(sha(receipt_raw)=='c8a23f7b834a61e8da93dc1793ffcb6937559e558eee07f0c3a9cbad05893f51','actual original remote receipt');receipt=json.loads(receipt_raw);terminal_raw=read(P/'ACTUAL_TERMINAL01.json');terminal=json.loads(terminal_raw);intent=json.loads(read(P/'INTENT01.json'));ops=receipt['operations'];repo=Path(receipt['fresh_git_root']);ck(repo==P/'fresh-recordfix-source325-01.git','actual exact fresh repo');ck(receipt['remote_commit']==H and receipt['selection_sha256']==sha(raw_selection) and receipt['selected_count']==82 and receipt['selected_logical_bytes']==5662993 and receipt['genuine_run_or_native_started'] is False,'actual receipt selection joins')
ck(terminal['actual_exit']==0 and terminal['actual_session']==23468 and terminal['actual_start_tool']=='c48e3f' and terminal['actual_completion_tool']=='4bfb18' and terminal['remote_receipt_sha256']==sha(receipt_raw),'Root original tool terminal joins')
for n,pin in terminal['files'].items():b=read(P/n);ck(len(b)==pin['bytes'] and sha(b)==pin['sha256'],'actual terminal stream/intent body pins')
ck(read(P/'ACTUAL_REMOTE01.err')==b'','original empty stderr');stdout=json.loads(read(P/'ACTUAL_REMOTE01.out'));ck(stdout=={k:receipt[k] for k in stdout} and stdout['status']==receipt['status'],'actual original stdout receipt joins')
ck(intent['selection_review_sha256']==sha(read(O/'SELECTION_FINAL02.json')) and intent['selection_sha256']==sha(raw_selection) and intent['pid']==terminal['actual_parent_pid']==318227 and intent['start_ticks']==terminal['actual_parent_start_ticks']=='14828800','original observed parent identity and selected review')
expected=['remote','ls-remote','init','remote','config','config','fetch','rev-parse','ls-tree','fetch']+['cat-file']*164+['ls-remote'];ck([x['operation'] for x in ops]==expected and len(ops)==175,'actual finite operation sequence')
absent=[]
for pid in [intent['pid'],intent['pgid']]+[r['pid'] for r in ops]:
 ck(not Path('/proc',str(pid)).exists(),'actual recorded PID now absent')
 try:os.killpg(pid,0)
 except ProcessLookupError:pass
 else:raise AssertionError('recorded process group remains')
 absent.append(pid)
for op in ops:ck(op['exit']==0 and op['cleanup_failures']==[] and 0<=op['stdout_bytes']<=4194304 and 0<=op['stderr_bytes']<=65536,'actual successful drained bounded operation')
remote_line=(H+'\t'+receipt['branch']+'\n').encode();ck(all(r['stdout_sha256']==sha(remote_line) and r['stdout_bytes']==len(remote_line) for r in (ops[1],ops[-1])),'recorded original first/final remote HEAD exact output joins')
names=[r['path'] for r in joined]
ft=git(['--git-dir='+str(repo),'ls-tree','-r','-z',H,'--',*names]);ck(ft==git(['ls-tree','-r','-z',H,'--',*names]),'actual fresh immutable selected tree equals original committed tree');ck(sha(ft)==ops[8]['stdout_sha256'] and len(ft)==ops[8]['stdout_bytes'],'original fetched tree raw-operation output join')
ck(git(['--git-dir='+str(repo),'cat-file','commit',H])==git(['cat-file','commit',H]),'actual fetched immutable commit bytes')
reply=b''.join(git(['--git-dir='+str(repo),'cat-file','--batch'],(''.join(r['git_object']+'\n' for r in joined[i:i+40])).encode()) for i in range(0,len(joined),40));offset=0
ck(receipt['selected_blobs']==[{k:r[k] for k in ('path','bytes','sha256','git_mode','git_object')} for r in joined],'all actual recovered rows exact immutable original map')
ck({p.relative_to(P/'selected').as_posix() for p in (P/'selected').rglob('*') if p.is_file()}==set(names),'complete selected saved namespace no extras')
for i,row in enumerate(joined):
 end=reply.index(b'\n',offset);oid,kind,size=reply[offset:end].decode().split();size=int(size);body=reply[end+1:end+1+size];offset=end+size+2;saved=P/'selected'/row['path'];ck(oid==row['git_object'] and kind=='blob' and size==row['bytes'] and sha(body)==row['sha256'] and body==read(saved)==read(ROOT/row['path']),'every actual fetched/saved/original opaque body');ck(stat.S_IMODE(saved.lstat().st_mode)==0o600,'saved actual private body mode');szop,bop=ops[10+2*i:12+2*i];size_raw=(str(size)+'\n').encode();ck(szop['stdout_sha256']==sha(size_raw) and szop['stdout_bytes']==len(size_raw) and bop['stdout_sha256']==sha(body) and bop['stdout_bytes']==len(body),'both actual original cat-file raw output hashes')
ck(offset==len(reply),'fresh Git no trailing batch output');ck(receipt['free_bytes']>=10*1024**3 and terminal['actual_git_operations']==175 and terminal['recorded_git_groups_currently_absent']==175,'original terminal floor/count evidence')
ck(sha(read(O/'MANIFEST02.json'))=='abb68db8626862793417ca99d431db468285ad1a85d0227dd33324447bc2d131','original selection manifest preserved')
FP=F/'financial-genuine-wrapper-root-recordfix-final-flat01-2026-10-04';D=F/'financial-genuine-wrapper-recordfix-final-union-flat-20261004-01';frraw=read(D/'RECOVERY01.json');ck(sha(frraw)=='e49fccaffb383ce0e8cc223f9b3609a6abc8e5e5ed7f76559aa1305b07db02cb','exact actual final flat receipt');fr=json.loads(frraw);fmraw=read(D/'flat/body-metadata.json');ck(sha(fmraw)=='ac91452fc5498a85e7dc5d287ab27e15f6ff7ab89c6b1f98dd4d796f5ee97cb5'==fr['actual']['metadata_sha256'],'exact actual flat metadata');fm=json.loads(fmraw);ck(fm['manifest']==um and fm['archive']==ua['archive'],'actual full manifest and original mode metadata');ck(fr['remote_receipt_sha256']==sha(receipt_raw) and fr['union_semantic_joins']==semantic and fr['actual']['regular_bodies']==276 and fr['actual']['members']==307,'actual flat/source remote and denominator joins')
ck(set(p.name for p in D.iterdir())=={'RECOVERY01.json','intent.json','request.json','flat'},'exact closed actual output namespace');ck(stat.S_IMODE(D.lstat().st_mode)==stat.S_IMODE((D/'flat').lstat().st_mode)==0o700,'actual private output directories');filemap=fm['flat_members'];ck(set(filemap)=={r['path'] for r in um['members'] if r['kind']=='file'} and len(set(filemap.values()))==276,'one-to-one every276 actual flat body');ck(set(p.name for p in (D/'flat').iterdir())==set(filemap.values())|{'body-metadata.json'},'all277privatefiles noextra');inodes=set();flatb={}
for n,leaf in filemap.items():
 p=D/'flat'/leaf;s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600 and (s.st_dev,s.st_ino) not in inodes,'actual distinct private original flat inode');inodes.add((s.st_dev,s.st_ino));b=read(p);ck(b==ub[n],'each actual flat body equals canonical original archive');flatb[n]=b
ck(stat.S_IMODE((D/'flat/body-metadata.json').lstat().st_mode)==0o600,'actual metadata0600');ck(recode(um,flatb)==ur,'canonical archive reproduced from actual flat bodies');ck(adapter.authenticate_union(q,um,read(U/'UNION_AUTHENTICATION01.json'),flatb['ORIGINAL_TREES01.json'])==semantic,'actual recovered original mapping authenticates')
proposal=json.loads(read(FP/'REQUEST_PROPOSAL01.json'));fqraw=read(FP/'REQUEST_FINAL02.json');fq=json.loads(fqraw);ck(sha(fqraw)=='45a42675bd874f804427f2a41a45f10d3acb20f5722310667bb3aff0bd9de96c' and read(D/'request.json')==fqraw,'actual final request unchanged at output');ck({k:v for k,v in fq.items() if k!='release'}=={k:v for k,v in proposal.items() if k!='release'} and proposal['release'] is None,'only genuine release field bound');ck(adapter.reference(fq['release'])==read(O/'FLAT_RELEASE04.json') and adapter.contract(fq)=='6a18658b55c71cfd16e7fb76b2bff14a1c714f7f03b16c3f587c79b675080beb','exact original released contract');ck(sha(read(O/'FLAT_RELEASE04.json'))=='cfa32047544e7c2345940357ab36e97def073f244906d7e68dbf815541acbada','genuine release preserved')
ft_raw=read(FP/'ACTUAL_TERMINAL01.json');ft=json.loads(ft_raw);fi=json.loads(read(FP/'ACTUAL_INTENT01.json'));oi=json.loads(read(D/'intent.json'));ck(ft['actual_tool']=='e3494f' and ft['actual_exit']==0 and ft['actual_session'] is None and ft['flat_receipt_sha256']==sha(frraw) and ft['actual_request_sha256']==sha(fqraw),'actual direct tool terminal no invented session');ck(fi['pid']==ft['actual_parent_pid']==oi['pid']==324148 and fi['start_ticks']==ft['actual_parent_start_ticks']=='14876828','actual observed original flat parent identity');flat_absent=[]
for pid in (fi['pid'],fi['pgid']):
 ck(not Path('/proc',str(pid)).exists(),'actual original flat PID absent')
 try:os.killpg(pid,0)
 except ProcessLookupError:pass
 else:raise AssertionError('actual original flat group remains')
 flat_absent.append(pid)
stdout=read(FP/'ACTUAL_FLAT01.out');ck(sha(stdout)==ft['actual_stdout']['sha256'] and len(stdout)==ft['actual_stdout']['bytes'] and json.loads(stdout)==ft['original_result']==fr['actual'],'actual flat original stdout result');ck(read(FP/'ACTUAL_FLAT01.err')==b'' and ft['actual_stderr_bytes']==0,'actual empty stderr');ck(len(fr['observed_free_bytes'])==4 and min(fr['observed_free_bytes'])>=10*1024**3,'allfour recorded10GiB floors');ck(all(fr[k] is False for k in ['lexical_links_followed','posix_tree_instantiated','research_authority','runtime_or_empirical_stores']),'actual helper limited archival flags unchanged')
# Earlier Source flat remains an actual714-body namespace, reverified without replay.
OLD=F/'financial-genuine-wrapper-root-recordfix-flat01-2026-10-04';oldreceipt=read(OLD/'RECOVERY01.json');ck(sha(oldreceipt)=='801ad60a0af8098d09e38ce6aea8d1df6d840a1fefc4025f21aec9360d32fec5','original actual Source flat receipt');oldmeta=read(OLD/'flat-source01/body-metadata.json');ck(sha(oldmeta)=='0e8cfc5bba519e4c364446eb67f547276bcb5e79d0f1b14bf32ea168a67aaf83','original fullSource flat metadata');om=json.loads(oldmeta);ck(om['manifest']==m and set(om['flat_members'])=={r['path'] for r in m['members'] if r['kind']=='file'},'full986 original Source mode mapping');ck({p.name for p in (OLD/'flat-source01').iterdir()}==set(om['flat_members'].values())|{'body-metadata.json'} and len(set(om['flat_members'].values()))==713,'all714 historical Source private files');sourceflat={};sourceinodes=set()
for n,leaf in om['flat_members'].items():
 p=OLD/'flat-source01'/leaf;s=p.lstat();ck(stat.S_IMODE(s.st_mode)==0o600 and s.st_nlink==1 and (s.st_dev,s.st_ino) not in sourceinodes,'original Source flat private distinct inode');sourceinodes.add((s.st_dev,s.st_ino));b=read(p);ck(b==a.read(module.CAP,n),'every recovered Source body still equals current original');sourceflat[n]=b
ck(recode(m,sourceflat)==archive,'whole original Source archive reproduced from actual historical flat bodies')
parent=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-root-launch-20261004-01');pqraw=original_bodies[str(parent/'REQUEST_FINAL02.json')];pq=json.loads(pqraw);ck(sha(pqraw)=='28f2ae5340d38ac71450c8947c5b1ad30ac4192481da81596684445c9cf9b52e','actual final Parent request body');ck(pq['source']==pq['design_source']=='649fb8a11089524aaef7843dffeeb90a3a55ca17' and pq['identity']=='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01','exact current source/design/fixed identity');ck(sha(a.encode({k:v for k,v in pq.items() if k!='final_review'}))=='873fba4ce39446dc34d741c25d757a1db756fa15e4b6b4c674e7f9bf18e6589d','exact actual Parent released contract')
for proof in list(pq['proofs'].values())+[pq['final_review']]:ck(sha(original_bodies[proof['path']])==proof['sha256'],'each actual Parent proof recovered from final archive')
records=pq['runtime_mapping']['distribution_records'];ck(len(records)==251,'all251 original runtime metadata pins');metadata_checks=0
for row in records:
 p=Path(row['record']);s=p.lstat();ck(stat.S_ISREG(s.st_mode) and p.resolve()==p and s.st_size<=4*1024**2,'bounded actual installed metadata reader permits hardlinks');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:b=os.read(fd,s.st_size+1);ck(sig(os.fstat(fd))==sig(s)==sig(p.lstat()) and len(b)==s.st_size and sha(b)==row['record_sha256'],'actual stable runtime RECORD only hash')
 finally:os.close(fd)
 metadata_checks+=1
ck(not os.path.lexists(module.CAP/'research_runs') and not os.path.lexists(parent/'attempt'),'zero current claims and unused actual new Parent');ck(a.scan(module.CAP)==m,'fresh final Source complete stable scan');ck(sha(read(O/'MANIFEST04.json'))=='52a2c0f5f94890b38721cc2f1de93ebe04913023b31faa27568e8cc169d376a1','alloriginal review manifests remain immutable')
result={'schema_version':1,'decision':'COMPLETE_FINAL_SOURCE_CALLER_REVIEW_BYTE_UNION_ACCEPTED','checks':len(checks),'source':'649fb8a11089524aaef7843dffeeb90a3a55ca17','tracked':325,'source_pins':324,'implementation':194,'package':149,'source_full_members':986,'source_flat_bodies':713,'final_ordinary_members':307,'final_flat_bodies':276,'final_private_files_with_metadata':277,'original_trees':11,'original_typed_members':306,'original_regular_bodies':275,'capture_review_snapshot_regular':44,'capture_review_literal_links':10,'source_flat_receipt_sha256':sha(oldreceipt),'final_flat_receipt_sha256':sha(frraw),'actual_remote_receipt_sha256':sha(receipt_raw),'flat_metadata_sha256':sha(fmraw),'final_flat_request_sha256':sha(fqraw),'parent_request_sha256':sha(pqraw),'actual_flat_terminal_sha256':sha(ft_raw),'runtime_metadata_hashes_checked':metadata_checks,'actual_flat_pid_and_group_absent':flat_absent,'claims':0,'native_or_numerical_release':False,'installed_runtime_bodies_or_empirical_stores':False,'posix_instantiation':False,'native_capacity':False,'capture44125_pid_history':'unavailable','qualification':'Complete authenticated archival byte union with literal metadata; fresh runtime/native eligibility remains separate. Original helper authority flags unchanged.'}
(O/'FLAT_READBACK05.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
