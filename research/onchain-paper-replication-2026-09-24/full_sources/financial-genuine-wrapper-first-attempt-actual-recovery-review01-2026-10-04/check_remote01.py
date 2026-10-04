import hashlib,json,os,shutil,stat,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;ROOT=Path.cwd();P=F/'financial-genuine-wrapper-root-remote-recovery04-2026-10-04';G=P/'fresh-financial04.git';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
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
r=doc(P/'REMOTE_RECOVERY01.json','f1e0a5d30b6a570dfab324ae87a8cab5b4a63695939de8479365765b0702b27e');s=doc(P/'SELECTED_BODIES01.json','c634d82450f8e67fb8480de09141be4b0a834a557139c707b50cab968b734fc2');H='19df9df4361857f99c24b493eb6a9be049bf594b';ck(r['remote_commit']==s['remote_commit']==H and r['fresh_git_root']==str(G),'fresh actualroot committedscope');rows=r['selected_blobs'];ck(len(rows)==r['selected_count']==394 and sum(x['bytes'] for x in rows)==r['selected_logical_bytes']==13056456,'actual394body extent');ck([{k:x[k] for k in ['path','bytes','sha256']} for x in rows]==s['rows'] and [x['path'] for x in rows]==sorted(set(x['path'] for x in rows)),'exact selected rows no duplicates');ck(r['genuine_run_or_native_started'] is False and not (P/'FAILED01.json').exists(),'no reportednative or failed original');ck(git(['cat-file','-t',H]).decode().strip()=='commit','actual recovered immutable commit exists; final FETCH_HEAD changed by explicit blob fetch');ck(all(not os.path.lexists(G/n) for n in ['objects/info/alternates','info/grafts','refs/replace']),'no alternate/graft/replacement Git authority')
commit=git(['cat-file','commit',H]);ck(hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==H,'actual immutablecommit SHA1');treeoid=commit.splitlines()[0].split()[1].decode();treebody=git(['cat-file','tree',treeoid]);ck(hashlib.sha1(b'tree '+str(len(treebody)).encode()+b'\0'+treebody).hexdigest()==treeoid,'actual immutable root tree SHA1');tree={}
for item in git(['ls-tree','-r','-z',H,'--',*[x['path'] for x in rows]]).split(b'\0'):
 if not item:continue
 meta,n=item.split(b'\t');mode,typ,oid=meta.decode().split();ck(typ=='blob' and mode in ('100644','100755'),'fresh selected Git regular');tree[n.decode()]={'git_mode':mode,'git_object':oid}
ck(set(tree)=={x['path'] for x in rows},'exact recovered selectedtree membership');reply=b''.join(git(['cat-file','--batch'],(''.join(x['git_object']+'\n' for x in rows[i:i+40])).encode()) for i in range(0,len(rows),40));offset=0;joined=[];ops=r['operations'];ck(len(ops)==799 and [x['operation'] for x in ops]==['remote','ls-remote','init','remote','config','config','fetch','rev-parse','ls-tree','fetch']+['cat-file']*788+['ls-remote'],'exact799operation sequence')
for i,row in enumerate(rows):
 n=row['path'];end=reply.index(b'\n',offset);oid,typ,size=reply[offset:end].decode().split();size=int(size);b=reply[end+1:end+1+size];offset=end+size+2;ck(typ=='blob' and oid==row['git_object']==tree[n]['git_object'] and row['git_mode']==tree[n]['git_mode'] and reply[offset-1:offset]==b'\n','recoveredGit row type OID mode');ck(hashlib.sha1(b'blob '+str(size).encode()+b'\0'+b).hexdigest()==oid and sha(b)==row['sha256'] and size==row['bytes'],'recovered actual immutablebody hash');saved=P/'selected'/n;ck(read(saved)==read(ROOT/n)==b and stat.S_IMODE(saved.stat().st_mode)==0o600,'original recoveredGit persistedbody join');sizeop=ops[10+2*i];bodyop=ops[11+2*i];sz=(str(size)+'\n').encode();ck(sizeop['stdout_sha256']==sha(sz) and sizeop['stdout_bytes']==len(sz) and bodyop['stdout_sha256']==sha(b) and bodyop['stdout_bytes']==len(b),'actual size/body operation digest joins');joined.append(dict(row,persisted_mode=0o600))
ck(offset==len(reply),'complete localbatch framing');actual={str(p.relative_to(P/'selected')) for p in (P/'selected').rglob('*') if p.is_file()};ck(actual=={x['path'] for x in rows} and all(not p.is_symlink() for p in (P/'selected').rglob('*')),'exact persistedselected complete membership no redirects');expectedremote=(H+'\t'+r['branch']+'\n').encode();ck(ops[1]['stdout_bytes']==ops[-1]['stdout_bytes']==len(expectedremote) and ops[1]['stdout_sha256']==ops[-1]['stdout_sha256']==sha(expectedremote),'actual firstfinal remoteHEAD raw-output hash join');origin=(r['origin']+'\n').encode();ck(ops[0]['stdout_sha256']==sha(origin) and ops[0]['stdout_bytes']==len(origin),'actual origin outputhash');ck(ops[7]['stdout_sha256']==sha((H+'\n').encode()),'actual fetchedHEAD stdout hash');absent=[]
for op in ops:
 ck(op['exit']==0 and op['cleanup_failures']==[] and isinstance(op['pid'],int) and op['seconds']>=0 and op['seconds']<60 and op['stdout_bytes']<=4*1024**2 and op['stderr_bytes']<=65536,'all successful bounded clean operations');pid=op['pid'];ck(not Path('/proc',str(pid)).exists(),'owned child PID absent')
 try:os.killpg(pid,0)
 except ProcessLookupError:absent.append(pid)
 else:raise AssertionError('owned child process group exists')
ck(len(set(absent))==799,'all799 ownedPIDgroups absent');
t=doc(P/'ACTUAL_TERMINAL01.json');intent=doc(P/'ACTUAL_REMOTE_INTENT01.json');stdout=read(P/'ACTUAL_RECOVERY01.out');stderr=read(P/'ACTUAL_RECOVERY01.err')
ck(t['actual_exit']==0 and t['actual_remote_receipt_sha256']==sha(read(P/'REMOTE_RECOVERY01.json')) and t['actual_stdout_sha256']==sha(stdout) and t['actual_stderr_sha256']==sha(stderr) and stderr==b'','original actual terminal/streams/receipt')
summary=json.loads(stdout);ck(all(summary[k]==r[k] for k in summary),'stdout actual receipt fields')
ck(t['actual_session']==52647 and t['actual_start_tool']=='62484a' and t['actual_completion_tool']=='4ca30b','original actual tool record')
I=F/'financial-genuine-wrapper-first-attempt-selection-review01-2026-10-04'
ck(intent['remote_commit']==H and intent['selection_sha256']==r['selection_sha256']==sha(read(P/'SELECTED_BODIES01.json')),'actual intent selection')
ck(intent['independent_selection_review_manifest_sha256']==sha(read(I/'MANIFEST01.json'))=='6daefa3a5403af7ad23ac3e9dd276f29edc4326f06b22c7afc0192a0d54ce381','exact independent selection release')
ck(doc(I/'READBACK01.json')['fresh_namespaces_absent'] is True and intent['one_use'] is True,'original fresh namespace review and one-use intent')
ck(sha(read(P/'recover_financial04.py'))=='188a60d2dace234a2090024109ca6cf7beb2b3355b1e759631eac8b4160dfb31','unchanged reviewed transport')
capbase=P/'selected/research/onchain-paper-replication-2026-09-24/full_sources/financial-genuine-wrapper-root-preservation06-2026-10-04'
cap=doc(capbase/'CAPTURE01.json','645387e5bede68f778ad4a94c5e3b30c4e9f64bd10aa4cfb1108508939a8b899');q=doc(capbase/'REQUEST01.json',cap['request_sha256'])
ck(cap['source']==q['source']=='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0' and [q[k] for k in ['tracked','source_pins','implementation','package']]==[290,289,194,149],'actual fetched original source authority')
for role,count in [('source',878),('parent',30),('outer',8)]:
 m=doc(capbase/(role.upper()+'_MANIFEST01.json'),cap['archives'][role]['manifest_sha256']);a=read(capbase/('complete-'+role+'01.tar.gz'))
 ck(len(m['members'])==cap['members'][role]==count and sha(a)==cap['archives'][role]['sha256'] and len(a)==cap['archives'][role]['bytes'] and q['manifests'][role]==cap['archives'][role]['manifest_sha256'],'complete recovered archive and manifest '+role)
ck(cap['original_parent_terminal_exit'] is None and cap['actual_outer_exit']==1 and cap['numerical_claims']==0 and cap['failed_identity_permanently_reserved'] is True,'original failed source semantics preserved')
flat=F/'financial-genuine-wrapper-root-flat-recovery04-2026-10-04'
ck(all(not os.path.lexists(flat/n) for n in ['flat-source01','flat-parent01','flat-outer01','INTENT01.json','RECOVERY01.json']),'original flat remains unexecuted')
ck(r['status']=='fresh-actual-remote-financial-source290-failed-parent-outer-recovered' and len({x['git_object'] for x in rows})==235,'exact actual recovery status and235OIDs')
ck(not os.path.lexists(Path(q['roots']['source'])/'research_runs'),'actual source claims absent')
review=P/'selected/research/onchain-paper-replication-2026-09-24/full_sources/financial-genuine-wrapper-first-attempt-preservation-review01-2026-10-04'
ck(sha(read(review/'MANIFEST01.json'))=='9f58e0dc7b4069e496a4bf343119fdba6882fec0ff2685ac10c6940f08ae9b17','recovered full canonical capture independent review')
rv=doc(review/'READBACK01.json');ck(rv['capture_sha256']==sha(read(capbase/'CAPTURE01.json')) and all(rv['archives'][k]['archive']==v for k,v in cap['archives'].items()),'recovered complete canonical archive review joins')
free=shutil.disk_usage(P).free;ck(free>=10*1024**3 and r['free_bytes']>=10*1024**3,'actual recorded and current observed floor')
ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
out={'schema_version':1,'decision':'ACCEPTED_ACTUAL_FAILED_SCOPE_REMOTE_RECOVERY_PENDING_FRESH_FLAT','checks':len(checks),'receipt_sha256':sha(read(P/'REMOTE_RECOVERY01.json')),'parent_terminal_sha256':sha(read(P/'ACTUAL_TERMINAL01.json')),'intent_sha256':sha(read(P/'ACTUAL_REMOTE_INTENT01.json')),'selection_sha256':r['selection_sha256'],'recovered_commit':H,'selected_count':394,'logical_bytes':13056456,'operations':799,'actual_recorded_elapsed_seconds':r['elapsed_seconds'],'all_owned_PIDs_and_groups_absent':absent,'archives':cap['archives'],'captured_financial_source':cap['source'],'tracked':290,'source_pins':289,'source_members':878,'parent_members':30,'outer_members':8,'disk_free_bytes':free,'actual_flat_recovery':False,'numerical_claims':0,'original_identity_reserved':True,'runtime_registration_native_authority':False,'qualification':'Original Root operation and terminal digest records joined against actual fetched immutable Git and saved/original bodies. Initial/final remote HEAD raw text hash authenticated; no network rerun or separate per-operation rawstdout asserted. Full canonical archive verification joins the exact independently accepted unchanged archive bodies.','joined':joined}
(O/'REMOTE_READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['joined','all_owned_PIDs_and_groups_absent']},indent=2))
