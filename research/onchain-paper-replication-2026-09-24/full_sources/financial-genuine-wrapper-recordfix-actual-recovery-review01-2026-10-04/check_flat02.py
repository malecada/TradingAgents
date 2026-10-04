import ast,gzip,hashlib,importlib.util,io,json,os,shutil,stat,subprocess,sys,tarfile
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;ROOT=Path.cwd();FLAT=F/'financial-genuine-wrapper-root-recordfix-flat01-2026-10-04';P=F/'financial-genuine-wrapper-root-recordfix-remote01-2026-10-04';RECOVERED_F=P/'selected/research/onchain-paper-replication-2026-09-24/full_sources';S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source');H='649fb8a11089524aaef7843dffeeb90a3a55ca17';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(x,m):
 assert x,m
 checks.append(m)
sys.path.insert(0,str(FLAT));sp=importlib.util.spec_from_file_location('original_flat_readonly',FLAT/'restore01.py');C=importlib.util.module_from_spec(sp);sp.loader.exec_module(C);a=C.R
read=lambda p:a.read(p.parent,p.name)
def doc(p,pin=None):
 b=read(p);ck(pin is None or sha(b)==pin,'exact pin '+p.name);return json.loads(b)
old=doc(O/'MANIFEST01.json','7159276bf22db3ac866674315b4cda2e65f540ac2916b3925b9c8773a0c678c6')
for row in old['members']:ck(sha(read(O/row['path']))==row['sha256'] and stat.S_IMODE((O/row['path']).stat().st_mode)==row['mode'],'all original review and release bytes unchanged')
receipt=doc(FLAT/'RECOVERY01.json','801ad60a0af8098d09e38ce6aea8d1df6d840a1fefc4025f21aec9360d32fec5');remote=doc(P/'REMOTE_RECOVERY01.json','0eec2d133f35af75fa6b5c17b16d7f0de24ec1756d957361ea425fd7ddf0d083');ck(receipt['remote_receipt_sha256']==sha(read(P/'REMOTE_RECOVERY01.json')),'actual remote lineage');joined=remote['selected_blobs']
for row in joined:
 b=read(P/'selected'/row['path']);ck(b==read(ROOT/row['path']) and len(b)==row['bytes'] and sha(b)==row['sha256'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_object'],'all467 actual remote saved/original/OID joins remain')
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

B=RECOVERED_F/'financial-genuine-wrapper-root-recordfix-capture01-2026-10-04';q=doc(B/'request.json');m=doc(B/'source-manifest.json');auth=doc(B/'source-authentication.json');terminal=doc(B/'terminal.json');D=FLAT/'flat-source01';info=receipt['actual'];meta=doc(D/info['metadata_file'],info['metadata_sha256']);ck(meta['manifest']==m and meta['archive']==terminal['archive'],'entire original archive/manifest/flat metadata')
files={r['path']:r for r in m['members'] if r['kind']=='file'};mapping=meta['flat_members'];ck(len(files)==len(mapping)==713 and set(mapping)==set(files) and set(mapping.values())=={f'body-{i:05d}.body' for i in range(713)},'exact713 unique named body mapping')
ck({p.name for p in D.iterdir()}==set(mapping.values())|{'body-metadata.json'} and stat.S_IMODE(D.stat().st_mode)==0o700 and D.resolve()==D,'exact714 private output membership')
bodies={};inodes=[]
for n,leaf in mapping.items():
 p=D/leaf;st=p.lstat();b=read(p);ck(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==0o600 and len(b)==files[n]['bytes'] and sha(b)==files[n]['sha256'] and b==read(S/n),'every original/current/private recovered body')
 bodies[n]=b;inodes.append({'semantic_path':n,'leaf':leaf,'device':st.st_dev,'inode':st.st_ino,'original_mode':files[n]['mode'],'flat_mode':0o600,'bytes':len(b),'sha256':sha(b)})
ck(len({(r['device'],r['inode']) for r in inodes})==713 and stat.S_IMODE((D/'body-metadata.json').stat().st_mode)==0o600 and (D/'body-metadata.json').stat().st_nlink==1,'distinct actual body inodes/private metadata')
ck(a.scan(S)==m and len(m['members'])==986 and info['root_mode']==m['root_mode']==stat.S_IMODE(S.stat().st_mode),'all original current mode/type/root metadata unchanged')
prior=F/'held-consumer-final-released-scope-capture-review01-2026-10-03/check01.py';defs=[n for n in ast.parse(read(prior)).body if isinstance(n,ast.FunctionDef) and n.name in ['decode','recode']];exec(compile(ast.Module(body=defs,type_ignores=[]),str(prior),'exec'));raw=read(B/'source.tar.gz');decoded,framing=decode(raw,m);ck(all(decoded[n]==b for n,b in bodies.items()) and recode(m,bodies)==raw and sha(raw)==info['archive_sha256']=='8d49d60b509bc9c95cd04274127b12387b8070295499dad3d24db63b9a376efb','whole canonical source archive rebuilt from actual flat')
def git(args):
 r=subprocess.run(['git','--no-replace-objects','-c','protocol.allow=never','-C',str(S),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env={'PATH':'/usr/bin:/bin','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','GIT_OPTIONAL_LOCKS':'0','GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1'});ck(r.returncode==0 and len(r.stdout)<=8*1024**2 and len(r.stderr)<=65536,'bounded readonly actual source Git');return r.stdout
entries={}
for row in git(['ls-tree','-r','-z',H]).split(b'\0'):
 if not row:continue
 left,n=row.split(b'\t');mode,typ,oid=left.decode().split();ck(typ=='blob','tracked regular Git');entries[n.decode()]=[mode,oid]
ck(entries==auth['git_entries'] and len(entries)==325,'actual entire325 tracked Git map');allrows={r['path']:r for r in m['members']}
for n,(mode,oid) in entries.items():
 b=bodies[n];ck(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid and ('100755' if allrows[n]['mode']&0o111 else '100644')==mode,'every archived Git OID and original executable mode')
gate=json.loads(bodies[C.GATE]);ck(sha(bodies[C.GATE])==C.GATEHASH,'actual genuine current gate');exp=gate['experiments'][C.IDENTITY];ck(set(exp['source_files'])==set(entries)-{C.GATE} and len(exp['source_files'])==324,'whole324 source pins')
for n,pin in exp['source_files'].items():ck(sha(bodies[n])==pin,'all324 actual recovered source pins')
for role,ref in exp['inputs'].items():ck(sha(bodies[ref['path']])==ref['sha256']==auth['role_hashes'][ref['path']],'all8 actual recovered role joins')
family=gate['families'][exp['family']];ck(family['attempt_budget']==18 and family['prior_attempts']==0 and 'cumulative_budget_extension' not in exp,'unchanged numerical18/prior0')
closure=json.loads(bodies[exp['inputs']['source_closure']['path']]);ck(len(closure['installed'])==194 and sum(n.startswith('tradingagents/') for n in closure['installed'])==149,'actual194implementation149package')
for n,pin in closure['installed'].items():ck(sha(bodies[n])==pin,'all194 implementation bodies')
t=doc(FLAT/'ACTUAL_TERMINAL02.json');intent=doc(FLAT/'INTENT01.json');rootintent=doc(FLAT/'ROOT_EXECUTION_INTENT02.json');final=doc(FLAT/'REQUEST_FINAL02.json','81cd8a27b06d8fc956997ae34693c9f03bae5fa3a7090eb12d00dd0b6b03b71c')
ck(final['release']=={'path':str(O/'FLAT_RELEASE01.json'),'sha256':'758ca0ffcd94a329404150ef70bd8907f521b24c16d965081c830f3da96c8810'} and sha(a.encode({k:v for k,v in final.items() if k!='release'}))=='d8ca6aa59ca6bc6c5c1005cc02ed49b96d3df38b1bc93a7e08e0a1634557424e','actual exact released request only release ref added')
stdout=read(FLAT/'ACTUAL_LAUNCH02.out');stderr=read(FLAT/'ACTUAL_LAUNCH02.err');ck(t['actual_exit']==0 and t['actual_flat_receipt_sha256']==sha(read(FLAT/'RECOVERY01.json')) and t['actual_stdout_sha256']==sha(stdout) and t['actual_stderr_sha256']==sha(stderr) and not stderr and json.loads(stdout)==info,'actual original Root exit and streams')
ck(t['actual_session']==20483 and t['actual_start_tool']=='c4bc3b' and t['actual_completion_tool']=='c5ffe6' and t['original_actual_root_intent_sha256']==sha(read(FLAT/'ROOT_EXECUTION_INTENT02.json')),'actual original tool intent joins')
ck(t['actual_parent_pid']==intent['pid']==rootintent['pid']==275216 and t['actual_parent_start_ticks']==rootintent['start_ticks']=='14444794' and rootintent['pgid']==rootintent['session']==275216,'original parent actual identity/group')
absent=[]
for pid in [275216,268318]+[r['pid'] for r in remote['operations']]:
 ck(not Path('/proc',str(pid)).exists(),'original actual PID absent')
 try:os.killpg(pid,0)
 except ProcessLookupError:absent.append(pid)
 else:raise AssertionError('original actual process group exists')
ck(len(receipt['disk_floor_observations'])==4 and all(n>=a.FLOOR for n in receipt['disk_floor_observations']),'four actual sampled floors')
ck(all(info[k] is False for k in ['instantiated_posix_tree','recovered_tree_git_join','runtime_package_bodies_recovered','outside_stores_recovered','research_authority']) and receipt['original_capture_pid_observed'] is False and receipt['release_of_numerical_work'] is False,'original limited receipt flags preserved')
ck(git(['rev-parse','HEAD']).decode().strip()==H and git(['status','--porcelain','--untracked-files=all'])==b'' and a.scan(S)==m,'complete actual source Git/tree unchanged')
ck(all(not os.path.lexists(S/n) for n in ['research_runs','research_artifacts','fixture_outer']),'actual no claims or native output namespaces');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
out={'schema_version':1,'decision':'COMPLETE_RECORDFIX_SOURCE_BYTE_UNION_ACCEPTED','checks':len(checks),'source':H,'flat_receipt_sha256':sha(read(FLAT/'RECOVERY01.json')),'remote_receipt_sha256':sha(read(P/'REMOTE_RECOVERY01.json')),'prior_remote_manifest_sha256':sha(read(O/'MANIFEST01.json')),'actual_root_terminal_sha256':sha(read(FLAT/'ACTUAL_TERMINAL02.json')),'request_sha256':sha(read(FLAT/'REQUEST_FINAL02.json')),'flat_release_sha256':final['release']['sha256'],'source_archive_sha256':sha(raw),'source_manifest_sha256':info['manifest_sha256'],'flat_metadata_sha256':info['metadata_sha256'],'source_members':986,'source_regular':713,'private_flat_files':714,'tracked':325,'source_pins':324,'implementation':194,'package':149,'inputs':8,'numerical_budget':18,'prior_attempts':0,'numerical_claims':0,'snapshots':snapshot_results,'all_current_original_PIDs_groups_absent':absent,'original_capture44125_PID_history_available':False,'actual_recorded_elapsed_seconds':receipt['elapsed_seconds'],'scope_qualification_sha256':'e2b582748080f0af65fbec17db5f6b37060f8cfeca7b455220a25a32637d1a52','new_Parent_final_verifier_runtime_store_POSIX_capacity_native_authority':False,'actual_inodes':inodes}
(O/'FLAT_READBACK02.json').write_bytes(a.encode(out));print(json.dumps({k:v for k,v in out.items() if k not in ['actual_inodes','all_current_original_PIDs_groups_absent']},indent=2))
