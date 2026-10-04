import pathlib, os, stat, json, hashlib, importlib.util, subprocess, datetime, tarfile, io
ROOT=pathlib.Path.cwd(); B=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'; HERE=pathlib.Path(__file__).resolve().parent
D=B/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04'; A=B/'financial-wrapper-compatibility-operational-delta-flat-successor03-2026-10-04'; E=B/'financial-wrapper-compatibility-operational-delta-entry-review04-2026-10-04'
checks=[]; evidence=[]
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 s=p.lstat();ok(stat.S_ISREG(s.st_mode) and s.st_size<=4194304 and p.resolve()==p,'regular bounded canonical '+str(p));b=p.read_bytes();t=p.lstat();ok(tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))==tuple(getattr(t,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')),'stable read '+str(p));return b
def copy(p,name):
 b=read(p);q=HERE/'evidence'/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b);evidence.append({'original':str(p),'copy':name,'bytes':len(b),'sha256':sha(b),'original_mode':stat.S_IMODE(p.lstat().st_mode)});return b
def load(p):return json.loads(read(p))
flat=copy(A/'restore01.py','accepted-flat03.py');ok(sha(flat)=='6d7688080efb716b7a79d1291b4f27e62e0315e5d7a8153b2890d1f9fab35214','accepted pure validator source')
spec=importlib.util.spec_from_file_location('review_flat',A/'restore01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
for name,pin in m.PINS.items():ok(sha(copy(A/name,'flat-dependencies/'+name))==pin,'accepted dependency '+name)
raw=copy(D/'REMOTE_RECOVERY01.json','REMOTE_RECOVERY01.json');ok(sha(raw)=='64c74556c7060fc7d118b5b07354bb737e5c157446ffef8c27fe77ea6cef4d47','actual remote pin');r=json.loads(raw)
sraw=copy(D/'SELECTED_BODIES01.json','SELECTED_BODIES01.json');sel=json.loads(sraw);s_sha=sha(sraw)
xraw=copy(D/'ROOT_REMOTE03_EXIT01.json','ROOT_REMOTE03_EXIT01.json');ok(sha(xraw)=='0f0eba1ace202b735e4a94f7f5b24dadbafbd0dd95173251a7773134f92af916','actual Root exit pin');x=json.loads(xraw)
i=json.loads(copy(D/'ROOT_REMOTE03_INTENT01.json','ROOT_REMOTE03_INTENT01.json'));sp=json.loads(copy(D/'ROOT_REMOTE03_SPAWN01.json','ROOT_REMOTE03_SPAWN01.json'))
draw=copy(D/'ROOT_INSTALLATION_DRAFT01.json','ROOT_INSTALLATION_DRAFT01.json');dr=json.loads(draw)
release_raw=copy(E/'MACHINE01.json','ENTRY_RELEASE04.json');rel=json.loads(release_raw)
ok(sha(release_raw)==i['entry_review_sha256']=='87fbe286ef49481b95eacef2b4791e2330b3ed6abe775e1d605fde70202d249c','genuine exact entry release')
copy(E/'MANIFEST01.json','ENTRY_MANIFEST04.json');copy(E/'REPORT01.md','ENTRY_REPORT04.md')
ok(sha(copy(E/'root_operational_remote04.py','root_operational_remote04.py'))==i['outer_caller_sha256']==rel['root_outer_caller_sha256'],'caller/release/intent join')
ok(sha(draw)==rel['installation_draft_sha256'] and rel['selection_sha256']==s_sha==i['selection_sha256'],'draft selection intent joins')
for name,pin in dr['helpers_and_selection'].items():
 body=copy(D/name,'installed/'+name);ok(len(body)==pin['bytes'] and sha(body)==pin['sha256'],'installed exact '+name)
ok(dr['actual_recovery'] is None and dr['exact_installed_entry_review'] is None and dr['flat_helper_installed'] is False,'original draft NULL fields retained')
ok(i['argv']==sp['argv'] and i['parent_pid']==sp['parent_pid'] and sp['pid']==x['actual_child_pid'] and x['actual_outer_exit']==0 and i['claim_or_native'] is False and x['claim_or_native'] is False,'actual intent spawn root exit')
for name in ['stdout','stderr']:
 body=copy(D/('ROOT_REMOTE03.'+name),'ROOT_REMOTE03.'+name);ok(len(body)==x[name+'_bytes'] and sha(body)==x[name+'_sha256'],'actual root '+name)
stdout=json.loads(read(D/'ROOT_REMOTE03.stdout'));ok(stdout=={k:r[k] for k in stdout},'actual stdout exact remote summary');ok(x['stderr_bytes']==0,'empty actual stderr')
records=m.authenticate_selected(D,r,sel,s_sha);ok(len(records)==15 and r['expected_operations']==55,'accepted pure validation of actual receipt/selected scope')
# Independent checks of every observed operation, samples, and exact raw Git outputs.
ops=r['operations'];obs=r['whole_tree_observations'];ok(len(obs)==563,'all563 complete recorded samples')
for j,o in enumerate(ops):
 ok(o['exit']==o['actual_reaped_exit']==0 and o['cleanup_failures']==[] and o['actual_child_limits']=={'pid':o['pid'],'fsize':[4194304,4194304]},'actual operation lifecycle '+str(j))
for j,o in enumerate(obs):
 ok(o['logical_bytes']<=64*1024**2 and o['allocated_bytes']<=96*1024**2 and o['members']<=32768 and o['seconds']<5 and 1<=o['complete_attempts']<=3,'sample limits '+str(j))
ok(r['initial_owned_allocation']==obs[0] and r['free_bytes']>=10*1024**3,'initial baseline and actual final floor')
commit=sel['remote_commit'];ok(commit==rel['commit']==dr['source_main_commit']=='4d0dbef40c978788ec9ddd9a5e4f4c2d18c52714','actual frozen Main commit')
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_TERMINAL_PROMPT='0')
def git(args,cwd):
 p=subprocess.run(['git',*args],cwd=cwd,env=env,capture_output=True,timeout=15);ok(p.returncode==0 and len(p.stdout)<=4194304,'offline read-only Git '+args[0]);return p.stdout
bare=D/'fresh-operational-source-policy02.git'
head=git(['rev-parse','FETCH_HEAD'],bare);ok(head==(commit+'\n').encode() and sha(head)==ops[7]['stdout_sha256'],'actual FETCH_HEAD join')
tree=git(['ls-tree','-r','-z',commit,'--',*[z['path'] for z in records]],bare);ok(sha(tree)==ops[8]['stdout_sha256'] and len(tree)==ops[8]['stdout_bytes'],'complete actual selected Git tree output');copy(E/'COMMITTED_SELECTED_TREE01.bin','PREENTRY_SELECTED_TREE01.bin');ok(tree==read(E/'COMMITTED_SELECTED_TREE01.bin'),'preentry/actual selected Git tree equality')
tmap={}
for row in tree.split(b'\0')[:-1]:
 left,name=row.split(b'\t');mode,kind,oid=left.decode().split();tmap[name.decode()]=(mode,kind,oid)
for j,z in enumerate(records):
 body=copy(D/'selected'/z['path'],'selected/'+z['path']);ok(body==read(ROOT/z['path']),'selected/current original exact '+z['path']);ok(tmap[z['path']]==(z['git_mode'],'blob',z['git_object']),'Git tree row '+str(j));ok(hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==z['git_object'],'independent blobOID '+str(j))
 for k,out in [(24+2*j,(str(len(body))+'\n').encode()),(25+2*j,body)]:ok(sha(out)==ops[k]['stdout_sha256'] and len(out)==ops[k]['stdout_bytes'],'actual recorded catfile raw output '+str(k))
expected=(commit+'\t'+r['branch']+'\n').encode()
for k in [1,54]:ok(sha(expected)==ops[k]['stdout_sha256'] and len(expected)==ops[k]['stdout_bytes'],'actual initial/final remote HEAD output '+str(k))
# Complete selected canonical archives read only, no restore or extraction.
archives=[]
for relpath,loader,mname,aname in [(m.REL,m.load_capture,'PAYLOAD_MANIFEST01.json','operational-delta01.tar.gz'),(m.FAILED_REL,m.load_failed_capture,'FAILED_PAYLOAD_MANIFEST01.json','failed-remote02.tar.gz')]:
 bundle=D/'selected'/relpath;cap,manifest=loader(bundle);ar=read(bundle/aname);framed=list(m.R.framed_members(ar));ok(len(framed)==len(manifest['members']),'full framed members '+aname)
 with tarfile.open(fileobj=io.BytesIO(ar),mode='r:gz') as tf:
  members=tf.getmembers();ok([t.name for t in members]==[z['path'] for z in manifest['members']],'ordered full members '+aname)
  for t,z in zip(members,manifest['members']):
   ok(t.mode==z['mode'] and t.uid==t.gid==t.mtime==0 and t.uname==t.gname=='','canonical headers '+t.name)
   ok(t.isdir() if z['kind']=='directory' else t.isfile(),'declared member type '+t.name)
   if t.isfile():body=tf.extractfile(t).read();ok(len(body)==z['bytes'] and sha(body)==z['sha256'],'all archived body hashes '+t.name)
 sink=m.R.ExactSink(ar);m.R.tar_stream(ROOT/relpath/'snapshot',manifest,sink);ok(sink.count==len(ar) and sink.hash.hexdigest()==sha(ar),'exact full canonical recompression '+aname)
 m.R.same(ROOT/relpath/'snapshot',manifest);ok(True,'current complete snapshot membership/modes '+aname)
 archives.append({'archive':aname,'sha256':sha(ar),'members':len(manifest['members']),'files':sum(z['kind']=='file' for z in manifest['members']),'body_bytes':sum(z.get('bytes',0) for z in manifest['members'])})
# Original origin path/mode/current source joins, no numerical bodies decoded.
origins=load(D/'selected'/m.REL/'ORIGIN_MAP01.json')
for z in origins['origins']:
 p=pathlib.Path(z['original']);body=read(p);ok(len(body)==z['bytes'] and sha(body)==z['sha256'] and stat.S_IMODE(p.lstat().st_mode)==z['original_mode'],'current original mapped body/mode '+z['path'])
old=B/'financial-wrapper-compatibility-operational-delta-root-remote02-2026-10-04';failed=copy(old/'FAILED01.json','ORIGINAL_FAILED02.json');ok(sha(failed)=='7491cc3c1940b68cab9b218e972a13c925f5ce1ff21d9f0a2f32ee416246268a','immutable prior failed pin');fj=json.loads(failed);ok([o['exit'] for o in fj['operations']]==[0,0,None] and [o['actual_reaped_exit'] for o in fj['operations']]==[0,0,0],'original init null versus actual reaped0 preserved')
oldexit=copy(old/'ROOT_REMOTE02_EXIT01.json','ORIGINAL_ROOT02_EXIT01.json');ok(json.loads(oldexit)['actual_outer_exit']==1,'original root failure stays1')
for n in ['FAILED01.json','flat-operational-delta01','flat-failed-remote02-01','FLAT_RECOVERY01.json','FLAT_INTENT01.json']:
 ok(not os.path.lexists(D/n),'actual absent future/failed namespace '+n)
pids={i['parent_pid'],sp['pid']}|{o['pid'] for o in ops};presence={}
for p in sorted(pids):presence[str(p)]=pathlib.Path('/proc',str(p)).exists();ok(not presence[str(p)],'recorded PID absent '+str(p))
groups={}
for p in pathlib.Path('/proc').iterdir():
 if p.name.isdigit():
  try:body=(p/'stat').read_text();tail=body[body.rindex(')')+2:].split();pg=int(tail[2])
  except (FileNotFoundError,ProcessLookupError,PermissionError):continue
  if pg in pids:groups.setdefault(str(pg),[]).append(int(p.name))
ok(not groups,'recorded Git/receiver group IDs absent now')
current=m.W.census(D);ok(current['logical_bytes']<=64*1024**2 and current['allocated_bytes']<=96*1024**2,'current complete owned root sample')
result={'schema_version':1,'status':'PASS_ACTUAL_REMOTE_ONLY','time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'assertions':len(checks),'checks':checks,'remote_sha256':sha(raw),'root_exit_sha256':sha(xraw),'selection_sha256':s_sha,'commit':commit,'operations':len(ops),'samples':len(obs),'selected_count':len(records),'selected_bytes':sum(z['bytes'] for z in records),'archival_scopes':archives,'sample_maxima':{k:max(z[k] for z in obs) for k in ['logical_bytes','allocated_bytes','members','regular_extent_changes']},'sample_extent_changes_sum':sum(z['regular_extent_changes'] for z in obs),'current_owned_sample':current,'recorded_pids_absent':presence,'matching_current_groups':groups,'evidence':evidence,'flat_recovery':None,'flat_release':False,'numerical_authority':False,'limits':'No continuous census, historical descendant completeness, memory/wire/POSIX/runtime or numerical capacity assertion. Actual root tool session attribution supplied by Root; raw caller/intent/spawn/exit/stdout independently joined.'}
(HERE/'READBACK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:result[k] for k in ['status','assertions','operations','samples','sample_maxima','sample_extent_changes_sum','archival_scopes']}))
