import hashlib,json,os,shutil,stat,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;ROOT=Path.cwd();P=F/'financial-genuine-wrapper-root-recordfix-remote01-2026-10-04';G=P/'fresh-recordfix-source325-01.git';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):
 assert v,m
 checks.append(m)
def sig(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read(p):
 s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2 and p.resolve()==p,'canonical regular bounded body');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  ck(sig(os.fstat(fd))==sig(s),'opened actualidentity');b=b''
  while True:
   q=os.read(fd,65536)
   if not q:break
   b+=q;ck(len(b)<=s.st_size,'finite body')
  ck(sig(os.fstat(fd))==sig(s)==sig(p.lstat()) and len(b)==s.st_size,'stable actualbody');return b
 finally:os.close(fd)
def doc(p,pin=None):
 b=read(p);ck(pin is None or sha(b)==pin,'pinned '+p.name);return json.loads(b)
def git(args,data=None):
 r=subprocess.run(['git','--no-replace-objects','-c','protocol.allow=never','--git-dir',str(G),*args],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env={'PATH':'/usr/bin:/bin','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','GIT_OPTIONAL_LOCKS':'0','GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_TERMINAL_PROMPT':'0'});ck(r.returncode==0 and len(r.stdout)<=8*1024**2 and len(r.stderr)<=65536,'bounded local recovered Git only');return r.stdout
r=doc(P/'REMOTE_RECOVERY01.json','0eec2d133f35af75fa6b5c17b16d7f0de24ec1756d957361ea425fd7ddf0d083');s=doc(P/'SELECTED_BODIES01.json','3b0669d065ffa3aa33e7630a1a515ddb83d251a6bd11556bccba130cd153c745');H='2ac9383c2086003e27f28391340832184f9a7221';ck(r['remote_commit']==s['remote_commit']==H and r['fresh_git_root']==str(G),'fresh actualroot committedscope');rows=r['selected_blobs'];ck(len(rows)==r['selected_count']==467 and sum(x['bytes'] for x in rows)==r['selected_logical_bytes']==14864671,'actual467body extent');ck([{k:x[k] for k in ['path','bytes','sha256']} for x in rows]==s['rows'] and [x['path'] for x in rows]==sorted(set(x['path'] for x in rows)),'exact selected rows no duplicates');ck(r['genuine_run_or_native_started'] is False and not (P/'FAILED01.json').exists(),'no reportednative or failed original');ck(git(['cat-file','-t',H]).decode().strip()=='commit','actual recovered immutable commit exists; final FETCH_HEAD changed by explicit blob fetch');ck(all(not os.path.lexists(G/n) for n in ['objects/info/alternates','info/grafts','refs/replace']),'no alternate/graft/replacement Git authority')
commit=git(['cat-file','commit',H]);ck(hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==H,'actual immutablecommit SHA1');treeoid=commit.splitlines()[0].split()[1].decode();treebody=git(['cat-file','tree',treeoid]);ck(hashlib.sha1(b'tree '+str(len(treebody)).encode()+b'\0'+treebody).hexdigest()==treeoid,'actual immutable root tree SHA1');tree={}
for item in git(['ls-tree','-r','-z',H,'--',*[x['path'] for x in rows]]).split(b'\0'):
 if not item:continue
 meta,n=item.split(b'\t');mode,typ,oid=meta.decode().split();ck(typ=='blob' and mode in ('100644','100755'),'fresh selected Git regular');tree[n.decode()]={'git_mode':mode,'git_object':oid}
ck(set(tree)=={x['path'] for x in rows},'exact recovered selectedtree membership');reply=b''.join(git(['cat-file','--batch'],(''.join(x['git_object']+'\n' for x in rows[i:i+40])).encode()) for i in range(0,len(rows),40));offset=0;joined=[];ops=r['operations'];ck(len(ops)==945 and [x['operation'] for x in ops]==['remote','ls-remote','init','remote','config','config','fetch','rev-parse','ls-tree','fetch']+['cat-file']*934+['ls-remote'],'exact945operation sequence')
for i,row in enumerate(rows):
 n=row['path'];end=reply.index(b'\n',offset);oid,typ,size=reply[offset:end].decode().split();size=int(size);b=reply[end+1:end+1+size];offset=end+size+2;ck(typ=='blob' and oid==row['git_object']==tree[n]['git_object'] and row['git_mode']==tree[n]['git_mode'] and reply[offset-1:offset]==b'\n','recoveredGit row type OID mode');ck(hashlib.sha1(b'blob '+str(size).encode()+b'\0'+b).hexdigest()==oid and sha(b)==row['sha256'] and size==row['bytes'],'recovered actual immutablebody hash');saved=P/'selected'/n;ck(read(saved)==read(ROOT/n)==b and stat.S_IMODE(saved.stat().st_mode)==0o600,'original recoveredGit persistedbody join');sizeop=ops[10+2*i];bodyop=ops[11+2*i];sz=(str(size)+'\n').encode();ck(sizeop['stdout_sha256']==sha(sz) and sizeop['stdout_bytes']==len(sz) and bodyop['stdout_sha256']==sha(b) and bodyop['stdout_bytes']==len(b),'actual size/body operation digest joins');joined.append(dict(row,persisted_mode=0o600))
ck(offset==len(reply),'complete localbatch framing');actual={str(p.relative_to(P/'selected')) for p in (P/'selected').rglob('*') if p.is_file()};ck(actual=={x['path'] for x in rows} and all(not p.is_symlink() for p in (P/'selected').rglob('*')),'exact persistedselected complete membership no redirects');expectedremote=(H+'\t'+r['branch']+'\n').encode();ck(ops[1]['stdout_bytes']==ops[-1]['stdout_bytes']==len(expectedremote) and ops[1]['stdout_sha256']==ops[-1]['stdout_sha256']==sha(expectedremote),'actual firstfinal remoteHEAD raw-output hash join');origin=(r['origin']+'\n').encode();ck(ops[0]['stdout_sha256']==sha(origin) and ops[0]['stdout_bytes']==len(origin),'actual origin outputhash');ck(ops[7]['stdout_sha256']==sha((H+'\n').encode()),'actual fetchedHEAD stdout hash');absent=[]
for op in ops:
 ck(op['exit']==0 and op['cleanup_failures']==[] and isinstance(op['pid'],int) and op['seconds']>=0 and op['seconds']<60 and op['stdout_bytes']<=4*1024**2 and op['stderr_bytes']<=65536,'all successful bounded clean operations');pid=op['pid'];ck(not Path('/proc',str(pid)).exists(),'owned child PID absent')
 try:os.killpg(pid,0)
 except ProcessLookupError:absent.append(pid)
 else:raise AssertionError('owned child process group exists')
ck(len(set(absent))==945,'all945 ownedPIDgroups absent');
import ast
RECOVERED_F=P/'selected/research/onchain-paper-replication-2026-09-24/full_sources'
t=doc(P/'ACTUAL_TERMINAL01.json');intent=doc(P/'INTENT01.json');stdout=read(P/'ACTUAL_LAUNCH01.out');stderr=read(P/'ACTUAL_LAUNCH01.err')
ck(t['actual_exit']==0 and t['actual_remote_receipt_sha256']==sha(read(P/'REMOTE_RECOVERY01.json')) and t['actual_stdout_sha256']==sha(stdout) and t['actual_stderr_sha256']==sha(stderr) and stderr==b'','actual Root terminal streams receipt')
ck(t['actual_session']==67543 and t['actual_start_tool']=='51729d' and t['actual_completion_tool']=='d9c834','original actual tool events')
summary=json.loads(stdout);ck(all(summary[k]==r[k] for k in summary),'actual stdout exact receipt summary')
ck(t['original_parent_intent_sha256']==sha(read(P/'INTENT01.json')) and intent['pid']==intent['pgid']==intent['session']==t['actual_parent_pid']==t['actual_parent_group_session']==268318 and intent['start_ticks']==t['actual_parent_start_ticks']=='14390858','genuine original parent PID/start/session joins')
parent=intent['pid'];ck(not Path('/proc',str(parent)).exists(),'original parent PID absent')
try:os.killpg(parent,0)
except ProcessLookupError:absent.append(parent)
else:raise AssertionError('original parent group remains')
observations=t['current_pid_group_observations'];ck(len(observations)==946 and {x['pid'] for x in observations}==set(absent) and all(x['pid_exists'] is False and x['process_group']=='absent' for x in observations),'all946 original Root absence records independently matched')
I=F/'financial-genuine-wrapper-recordfix-selection-review01-2026-10-04';ck(sha(read(I/'MANIFEST01.json'))=='5ade00e3444e16b6a2f1e6ed73ffdefb8d73c79abf6bae83ac427e2744fde488' and sha(read(I/'READBACK01.json'))==intent['actual_selection_review_sha256']=='b982f14d5877be6d4cc9aefc88d505cc1ea9491a268d0adf03ed74f1648741fc','actual independent selection authority')
ck(intent['selection_sha256']==r['selection_sha256']==sha(read(P/'SELECTED_BODIES01.json')) and intent['selected_remote_commit']==H and intent['source_helper_sha256']==sha(read(P/'recover01.py'))=='0b397ccd0a014f60a414ce79d67dfd53c58a0fb61ca616a6576cc43da4bbf0aa','actual source and selection lineage')
ck(r['status']=='fresh-actual-remote-recordfix-source325-recovered' and len({x['git_object'] for x in rows})==206,'actual current receipt status206objects')
import gzip,io,tarfile,importlib.util
ck(len({x['git_object'] for x in joined})==206,'actual206 unique immutable objects')
rootread=json.loads(read(P/'SELECTION_READBACK01.json'));snapshot_results=[];archived_coverage=set()
for suffix,originname,count,regular in [('review','financial-genuine-wrapper-recordfix-transport-flat-review01-2026-10-04',1771,1482),('capture-review','financial-genuine-wrapper-recordfix-capture-review01-2026-10-04',38,31)]:
 base=RECOVERED_F/('financial-genuine-wrapper-root-recordfix-'+suffix+'-snapshot01-2026-10-04');origin=F/originname;auth=json.loads(read(base/'AUTHENTICATION01.json'));mr=read(base/'manifest.json');manifest=json.loads(mr);raw=read(base/'review.tar.gz');ck(sha(mr)==auth['manifest_sha256'] and sha(raw)==auth['archive_sha256'] and len(raw)==auth['archive_bytes'],'snapshot exact pins')
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
 original_manifest=origin/('MANIFEST01.json' if suffix=='review' else 'MANIFEST03.json');ck(sha(read(original_manifest))==manifest['original_review_manifest_sha256']==auth['source_review_manifest'],'original frozen manifest included')
 original=json.loads(read(original_manifest))
 for r in original.get('members',original.get('entries',[])):
  saved=by[r['path']];ck(r['mode']==saved['mode'],'original review all modes joined')
  if r.get('kind',r.get('type'))=='file':ck(r['sha256']==saved['sha256'] and r.get('bytes',r.get('size'))==saved['bytes'],'original review all frozen file metadata joined')
 ck(len(bodies)==regular,'exact whole review regular count');snapshot_results.append({'origin':str(origin),'typed_members_including_root':count,'regular_bodies':regular,'archive_sha256':sha(raw),'manifest_sha256':sha(mr),'raw_headers':headers,'pax_headers':pax,'literal_symlinks':sum(r['kind']=='lexical-symlink' for r in members),'canonical_recompression':True})
C=F/'financial-genuine-wrapper-recordfix-capture-preparation01-2026-10-04';sys.path.insert(0,str(C));sp=importlib.util.spec_from_file_location('selected_source_capture',C/'capture01.py');module=importlib.util.module_from_spec(sp);sp.loader.exec_module(module);a=module.R;cap=RECOVERED_F/'financial-genuine-wrapper-root-recordfix-capture01-2026-10-04';q=json.loads(read(cap/'request.json'));m=json.loads(read(cap/'source-manifest.json'));ck(a.scan(module.CAP)==m==q['manifest'],'actual whole corrected source986 stable');ck(a.encode(module.authenticate())==read(cap/'source-authentication.json'),'actual325Git324pins8roles194149 current source authority')
prior=F/'held-consumer-final-released-scope-capture-review01-2026-10-03/check01.py';defs=[n for n in ast.parse(read(prior)).body if isinstance(n,ast.FunctionDef) and n.name in ['decode','recode']];exec(compile(ast.Module(body=defs,type_ignores=[]),str(prior),'exec'));archive=read(cap/'source.tar.gz');body,framing=decode(archive,m);ck(recode(m,body)==archive and sha(archive)=='8d49d60b509bc9c95cd04274127b12387b8070295499dad3d24db63b9a376efb','whole source archive canonical recompression')
for r in m['members']:
 if r['kind']=='file':ck(body[r['path']]==a.read(module.CAP,r['path']),'every archived current source body')

r=doc(P/'REMOTE_RECOVERY01.json')
ck(sha(read(P/'SCOPE_QUALIFICATION02.json'))=='e2b582748080f0af65fbec17db5f6b37060f8cfeca7b455220a25a32637d1a52','exact scoped exclusions retained')
flat=F/'financial-genuine-wrapper-root-recordfix-flat01-2026-10-04';ck(all(not os.path.lexists(flat/n) for n in ['flat-source01','INTENT01.json','RECOVERY01.json','FAILED01.json']),'actualflat remains unexecuted')
ck(not os.path.lexists(module.CAP/'research_runs'),'actual zero numerical claims');free=shutil.disk_usage(P).free;ck(free>=10*1024**3 and r['free_bytes']>=10*1024**3,'actual current and recorded diskfloor');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
out={'schema_version':1,'decision':'ACCEPTED_ACTUAL_RECORDFIX_REMOTE_RECOVERY_PENDING_FRESH_FLAT','checks':len(checks),'receipt_sha256':sha(read(P/'REMOTE_RECOVERY01.json')),'actual_root_terminal_sha256':sha(read(P/'ACTUAL_TERMINAL01.json')),'actual_parent_intent_sha256':sha(read(P/'INTENT01.json')),'actual_parent_pid':parent,'actual_parent_start_ticks':intent['start_ticks'],'selection_sha256':r['selection_sha256'],'selected_commit':H,'selected_count':467,'logical_bytes':14864671,'unique_git_objects':206,'operations':945,'original_parent_and_all_child_PIDs_groups_absent':absent,'actual_recorded_elapsed_seconds':r['elapsed_seconds'],'snapshots':snapshot_results,'source':'649fb8a11089524aaef7843dffeeb90a3a55ca17','source_archive_sha256':sha(archive),'source_members':986,'source_regular':713,'tracked':325,'source_pins':324,'scope_qualification_sha256':sha(read(P/'SCOPE_QUALIFICATION02.json')),'original_capture44125_PID_history_available':False,'actual_flat_recovery':False,'numerical_claims':0,'runtime_store_POSIX_native_authority':False,'qualification':'Actual immutable fetched Git/saved/original bodies and original operation digest records authenticated offline. Initial/final remote text digests join exact commit and branch; no network rerun or separately retained operation stdout asserted. Historical metadata-only witness exclusions remain unchanged.','joined':joined}
(O/'REMOTE_READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('joined','original_parent_and_all_child_PIDs_groups_absent')},indent=2))
