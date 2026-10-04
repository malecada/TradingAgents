import gzip,hashlib,io,json,os,stat,subprocess,sys,tarfile
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;ROOT=F.parents[2];T=F/'financial-wrapper-complete100-baseline-remote01-2026-10-04';B=F/'financial-wrapper-complete100-baseline-capture01-2026-10-04';H=F/'heartbeat-root-checkpoint10-2026-10-04';P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-root-launch-20261004-01');C=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def pinned(p,h):
 b=p.read_bytes();ok(sha(b)==h,'exact '+p.name);return b
pinned(P/'recovery04.py','b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a');sys.path.insert(0,str(P));import recovery04 as R
flatraw=pinned(T/'FLAT_RECOVERY01.json','9cd4a45f050d4267ade7febf5da9e57da2afbefd0e3fd156106d4f8d9b4e4460');flat=json.loads(flatraw);remote=json.loads(pinned(T/'REMOTE_RECOVERY01.json','36cc03869ce63c103e2631bc3b602f3ea9e478c5a50ba6f015f55359bff9816b'));pinned(T/'restore02.py','8b010b28e37978c6ea24eb0e4aaad68d715f4031a102d7396f4627fd501d06e1')
review=F/'financial-wrapper-complete100-baseline-actual-remote-review01-2026-10-04';mr=pinned(review/'MANIFEST01.json','bbf4b73207e9f551f7ccaed0f6a8e4c68f8a743251adb5237eb5e9b3b6cba56d');rows=json.loads(mr)['members'];ok({p.relative_to(review).as_posix() for p in review.rglob('*') if p!=review/'MANIFEST01.json'}=={x['path'] for x in rows}-{'.'},'complete prior review')
for row in rows:
 p=review/row['path'];s=p.lstat();mode=int(row['mode'],8) if isinstance(row['mode'],str) else row['mode'];ok(stat.S_IMODE(s.st_mode)==mode,'prior mode')
 if row['kind']=='file':ok(s.st_size==row['bytes'] and sha(p.read_bytes())==row['sha256'],'prior body')
 else:ok(stat.S_ISDIR(s.st_mode),'prior directory')
release=[p for p in review.iterdir() if p.is_file() and sha(p.read_bytes())=='dd6dec6d894e42730a2ffab3d7e80a025e858c00aa820594f21a587da410316b'];ok(len(release)==1,'genuine exact flat release')
for row in remote['selected_blobs']:
 b=(T/'selected'/row['path']).read_bytes();ok(b==(ROOT/row['path']).read_bytes() and sha(b)==row['sha256'] and len(b)==row['bytes'],'all17 saved external/current pins');ok(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_object'],'remote GitOID')
bundle=T/'selected'/B.relative_to(ROOT);capture=json.loads((bundle/'CAPTURE01.json').read_bytes());maps={};manifests={};total=0;typed=0
for label,rec in flat['scopes'].items():
 dest=T/('flat-'+label+'01');raw=(dest/'body-metadata.json').read_bytes();ok(sha(raw)==rec['metadata_sha256'],'metadata pin');meta=json.loads(raw);m=json.loads((bundle/(label.upper()+'_MANIFEST01.json')).read_bytes());R.validate(m);ok(meta['manifest']==m and meta['archive']==capture['scopes'][label]['archive'],'complete metadata/modes/archive');mapping=meta['flat_members'];rows=m['members'];files=[x for x in rows if x['kind']=='file'];ok(set(mapping)=={x['path'] for x in files} and len(set(mapping.values()))==len(files),'full unique bodymap');ok({p.name for p in dest.iterdir()}==set(mapping.values())|{'body-metadata.json'},'exact physicalflat namespace');ok(stat.S_IMODE(dest.stat().st_mode)==0o700,'private flat root')
 for row in files:
  p=dest/mapping[row['path']];s=p.lstat();b=p.read_bytes();ok(stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==0o600 and s.st_nlink==1 and len(b)==row['bytes'] and sha(b)==row['sha256'],'every actual restored body')
 archive=(bundle/('complete-'+label+'01.tar.gz')).read_bytes();frames=list(R.framed_members(archive));ok(len(frames)==len(rows),'complete canonicalfooter frame count')
 for (name,t,body),row in zip(frames,rows,strict=True):
  ok(name==row['path'] and t.mode==row['mode'] and (t.isdir() if row['kind']=='directory' else t.isfile()),'frame type/path/mode')
  if row['kind']=='file':ok(body==(dest/mapping[name]).read_bytes(),'frame recovered body equality')
 sink=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=sink,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
   for row in rows:
    t=tarfile.TarInfo(row['path']);t.mode=row['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
    if row['kind']=='directory':t.type=tarfile.DIRTYPE;t.size=0;tar.addfile(t)
    else:b=(dest/mapping[row['path']]).read_bytes();t.size=len(b);tar.addfile(t,io.BytesIO(b))
 ok(sink.getvalue()==archive,'exact canonical compression reencoding');maps[label]=(dest,mapping);manifests[label]=m;total+=len(files);typed+=len(rows)
ok(total==863 and typed==949 and len(maps)==6,'full863/949/six')
def body(label,path):
 d,m=maps[label];return (d/m[path]).read_bytes()
side=json.loads((bundle/'ORIGINAL_ROOT_RECEIPT_MODES01.json').read_bytes());ok(len(side['members'])==7,'seven explicit mode mappings')
for row in side['members']:
 p=Path(row['original_absolute_path']);b=body('support',row['support_snapshot_path']);ok(b==p.read_bytes() and sha(b)==row['sha256'] and stat.S_IMODE(p.stat().st_mode)==row['original_current_mode']==0o664 and row['captured_private_mode']==0o600,'root literal0664 snapshot0600 exactbody')
index=json.loads((bundle/'GIT_OBJECTS01.json').read_bytes());objects=index['reachable_objects'];repo=Path(flat['fresh_original_git']);ok(repo==T/'fresh-original-source339-01.git','fixed fresh reconstructedrepo');env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL='',GIT_NO_REPLACE_OBJECTS='1');calls=[]
def git(args,inp=None,cap=4*1024**2):
 p=subprocess.run(['git','--no-replace-objects','--git-dir',str(repo),*args],env=env,input=inp,capture_output=True,timeout=10);ok(p.returncode==0 and len(p.stdout)<=cap,'bounded offline Git '+args[0]);calls.append({'args':args,'exit':p.returncode,'stdout_bytes':len(p.stdout),'stdout_sha256':sha(p.stdout),'stderr_sha256':sha(p.stderr)});return p.stdout
for start in range(0,len(objects),16):
 batch=objects[start:start+16];raw=git(['cat-file','--batch'],''.join(x['git_object']+'\n' for x in batch).encode());off=0
 for row in batch:
  end=raw.index(b'\n',off);oid,kind,size=raw[off:end].decode().split();size=int(size);b=raw[end+1:end+1+size];off=end+size+2;ok(oid==row['git_object'] and kind==row['kind'] and b==body(row['scope'],row['path']) and len(b)==row['bytes'] and sha(b)==row['sha256'],'all genuine reconstructed object bodies/types');ok(hashlib.sha1(kind.encode()+b' '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid,'actual original GitOID')
 ok(off==len(raw),'exact Gitbatch tail')
source='9dc5c79f738920b52947b4e63fed0397f1b5b207';ok(git(['rev-parse','HEAD']).decode().strip()==source,'actual reconstructedHEAD');git(['fsck','--full','--strict','--no-reflogs',source]);reachable=git(['rev-list','--objects','--no-object-names',source]).decode().splitlines();ok(set(reachable)=={x['git_object'] for x in objects} and len(reachable)==385,'all385 reachable originalobjects')
tree=git(['ls-tree','-r','-z',source]);names=[]
for entry in tree.rstrip(b'\0').split(b'\0'):
 left,path=entry.split(b'\t');mode,kind,oid=left.decode().split();name=path.decode();b=body('capsule',name);names.append(name);ok(kind=='blob' and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid and b==(C/name).read_bytes(),'all339 restored/source/Gitjoins');ok(bool((C/name).stat().st_mode&0o111)==(mode=='100755'),'Git modeclass')
ok(len(names)==339,'current339 tree')
q=json.loads(body('parent','REQUEST_DRAFT01.json'));gate=json.loads(body('capsule',q['registration']));e=gate['experiments'][q['identity']];ok(q['source']==q['design_source']==source and q['proofs']['full_recovery'] is None and q['final_review'] is None,'genuine draft remains NULL')
ok(len(e['source_files'])==338 and e['source_files']==q['source_files'],'338sourcepins')
for n,pin in e['source_files'].items():ok(sha(body('capsule',n))==pin,'every registeredsourcepin')
for role,row in e['inputs'].items():ok(sha(body('capsule',row['path']))==row['sha256']==q['input_hashes'][role],'every8role')
ok(len(e['inputs'])==8 and len(json.loads(body('capsule',e['inputs']['runtime_mapping']['path']))['distribution_records'])==251,'8roles251runtime declarations')
for name in q['helper_hashes']:ok(body('parent',name)==(P/name).read_bytes(),'actual unchanged Parenthelper')
ok(sha(body('parent','parent01.py'))==q['caller_sha256']=='7f28cee688b661584e57466838ecdb79f0e17aa52be7d6f2c04f374326de9fb3','Parent exactcaller')
claims=[n for n in maps['capsule'][1] if n.startswith('research_runs/') and n.endswith('/claim.json')];ok(len(claims)==2,'two spent claims')
for name in claims:ok(name.replace('/claim.json','/failed.json') in maps['capsule'][1] and name.replace('/claim.json','/complete.json') not in maps['capsule'][1],'bothFAILED no coercion')
ok(flat['offline_git_PID_history_recorded'] is False and len(flat['offline_git_operations'])==392 and all(x['exit']==0 for x in flat['offline_git_operations']),'original392 ops; PIDhistory not recorded');ok(all(x['free_bytes']>=10*1024**3 and x['seconds']<180 for x in flat['floor_observations']),'785finite floors')
exitraw=(H/'ROOT_BASELINE_FLAT01_EXIT.json').read_bytes();ex=json.loads(exitraw);ok(ex['actual_outer_exit']==0 and ex['native_or_claim_started'] is False,'actual Root exit0')
for kind in ('stdout','stderr'):
 p=H/('ROOT_BASELINE_FLAT01.'+kind);b=p.read_bytes();ok(len(b)==ex[kind+'_bytes'] and sha(b)==ex[kind+'_sha256'],'Root actual '+kind);(D/p.name).write_bytes(b)
intent=(H/'ROOT_BASELINE_FLAT01_INTENT.json').read_bytes();iv=json.loads(intent);ok(iv['accepted_flat_release_sha256']=='dd6dec6d894e42730a2ffab3d7e80a025e858c00aa820594f21a587da410316b' and iv['actual_remote_receipt_sha256']==flat['remote_receipt_sha256'],'actual Root intentrelease join')
for n,b in [('ROOT_BASELINE_FLAT01_EXIT.json',exitraw),('ROOT_BASELINE_FLAT01_INTENT.json',intent),('FLAT_RECOVERY01.json',flatraw)]: (D/n).write_bytes(b)
(D/'READBACK01.json').write_text(json.dumps({'checks':len(checks),'names':checks,'scopes':flat['scopes'],'files':total,'typed':typed,'offline_review_git_calls':calls,'original_PID_history_recorded':False,'final_request_release_recovered':False,'checkpoint_tensor_decode':False},indent=2)+'\n');print(json.dumps({'checks':len(checks),'bodies':total,'typed':typed,'objects':len(objects)}))
