"""Read-only opaque composition observations. Never creates a proof, restores, or grants entry."""
import argparse,gzip,hashlib,io,json,os,re,stat,tarfile,time
from pathlib import Path
FILE=4*1024**2; TOTAL=256*1024**2; LIMIT=32768; SECONDS=180
SOURCE='7b056a574e3e7b3c7ba209a39ee6a615e649d60c'
POLICY='ae8fbdc9d13e75fc453b70b5ee633c89fb4577e9b68a35b4147cf1bbd58c6887'
CLOSURE='af61a1de642d029579230fb3980e87eefe8dc5e0e7ba6a965393f194e996c92c'
CHECKER='d0d770b45def89e8e00e81fa1bbb35416034eaace5ecab0f15193fd43b7a32d8'
OLDMAP='ebb1727ccb55678aead9f0d5b5ee43ec81a46019c7fbb13c4b4f76144507bbca'
NEWMAP='2e281f7ca64a12be316424d8e93b0eab28ba0d121214e79ada7249c96930b040'
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
INPUTS_PIN='fbe0caf49038e36a8d245f52a14ce49184b5b5e0b201cf0982283194057d2009'
def h(b):return hashlib.sha256(b).hexdigest()
def canonical(o):return json.dumps(o,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def require(v,msg):
 if not v:raise ValueError(msg)
def unique(pairs):
 d={}
 for k,v in pairs:require(k not in d,'duplicate JSON key');d[k]=v
 return d
def decode(b):return json.loads(b,object_pairs_hook=unique,parse_constant=lambda s:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def sig(s):return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns','st_blocks','st_uid'))
def mode(x):return int(x,8) if isinstance(x,str) else x
def safe(n):
 require(type(n) is str and n and not n.startswith('/') and all(x not in ('','.','..','keys','apis','.env','hf_token.txt') for x in n.split('/')) and len(n.split('/'))<=32,'unsafe relative name');return n
class Reader:
 def __init__(self):self.start=time.monotonic();self.cache={};self.pins={};self.anchors={};self.trees={};self.total=0
 def tick(self):require(time.monotonic()-self.start<SECONDS,'deadline');require(len(self.pins)+len(self.anchors)<=LIMIT,'member bound')
 def anchor(self,p):
  self.tick();require(p.is_absolute() and p.resolve(strict=True)==p,'canonical path');s=p.lstat();require(stat.S_ISDIR(s.st_mode),'directory type')
  q=(s.st_dev,s.st_ino,s.st_mode,s.st_uid);require(p not in self.anchors or self.anchors[p]==q,'ancestor changed');self.anchors[p]=q
 def read(self,p,pin=None,expected_mode=None):
  p=Path(p);self.tick()
  for q in reversed(p.parents):self.anchor(q)
  s=p.lstat();require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=FILE,'regular extent/link')
  require(expected_mode is None or stat.S_IMODE(s.st_mode)==expected_mode,'file mode')
  before=sig(s);require(p not in self.pins or self.pins[p]==before,'changed cached file')
  if p in self.cache:b=self.cache[p]
  else:
   fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK);primary=None;parts=[];count=0
   try:
    require(sig(os.fstat(fd))==before,'open identity')
    while True:
     self.tick();chunk=os.read(fd,min(65536,FILE+1-count))
     if not chunk:break
     parts.append(chunk);count+=len(chunk);require(count<=FILE,'read extent')
    require(sig(os.fstat(fd))==before,'descriptor changed')
   except BaseException as e:primary=e;raise
   finally:
    try:os.close(fd)
    except BaseException as close:
     if primary is None:raise
     BaseException.__dict__['__dict__'].__get__(primary)['secondary_close_failure']=close
   b=b''.join(parts);require(sig(p.lstat())==before and len(b)==s.st_size,'post-close currentness');self.total+=len(b);require(self.total<=TOTAL,'total read bound');self.cache[p]=b;self.pins[p]=before
  require(pin is None or h(b)==pin,'body hash '+str(p));return b
 def j(self,p,pin=None):return decode(self.read(p,pin))
 def tree(self,root,exclude=()):
  root=Path(root);self.anchor(root);found={};pending=[root]
  while pending:
   p=pending.pop();self.tick();s=p.lstat();require(stat.S_ISDIR(s.st_mode),'tree directory')
   with os.scandir(p) as it:
    for e in it:
     self.tick();n=str(Path(e.path).relative_to(root))
     if p==root and e.name in exclude:continue
     safe(n);t=os.lstat(e.path);require(stat.S_ISREG(t.st_mode) or stat.S_ISDIR(t.st_mode),'tree special');require(len(found)<LIMIT,'tree members');found[n]=sig(t)
     if stat.S_ISDIR(t.st_mode):pending.append(Path(e.path))
  old=self.trees.get(root);require(old is None or old==(tuple(exclude),found),'tree changed');self.trees[root]=(tuple(exclude),found);return found
 def finish(self):
  # All read descriptors and scandir iterators have closed before the final global join.
  for root,(exclude,_) in list(self.trees.items()):self.tree(root,exclude)
  for p in list(self.anchors):self.anchor(p)
  for p,s in self.pins.items():self.tick();require(sig(p.lstat())==s,'final whole-reader currentness')
  self.tick()
def manifest_rows(m):
 rows=m['members'];require(type(rows) is list and len(rows)<=LIMIT,'manifest rows');out={}
 for x in rows:
  n=safe(x['path']);require(n not in out,'duplicate manifest path');require(x['kind'] in ('file','directory'),'manifest kind');require(type(mode(x['mode'])) is int,'mode');out[n]=x
 return out
def seal(r,root):
 m=r.j(root/'MANIFEST01.json');rows={x['path']:x for x in m['members']};q=r.j(root/'MACHINE01.json')
 for n in ['MACHINE01.json','REPORT01.md']:
  x=rows[n];b=r.read(root/n,x['sha256']);require(len(b)==x['bytes'] and x['kind']=='file','review manifest join')
 require(q['report_sha256']==h(r.read(root/'REPORT01.md')),'machine report join');return q

def flat_scope(r,dest,rec,manifest,archive):
 require(rec['status']=='fresh-flat-archival-recovery-not-origin-proof','flat status')
 for k in ['instantiated_posix_tree','recovered_tree_git_join','runtime_package_bodies_recovered','outside_stores_recovered','research_authority']:require(rec[k] is False,'flat exclusions')
 require(stat.S_IMODE(dest.lstat().st_mode)==0o700 and dest.lstat().st_uid==os.getuid(),'private root')
 md=r.j(dest/safe(rec['metadata_file']),rec['metadata_sha256']);require(md['schema_version']==1 and md['manifest']==manifest,'exact original metadata')
 require(md['archive']['sha256']==rec['archive_sha256']==h(archive) and md['archive']['manifest_sha256']==rec['manifest_sha256'],'archive joins')
 rows=manifest_rows(manifest);mapping=md['flat_members'];files={n:x for n,x in rows.items() if x['kind']=='file'}
 require(set(mapping)==set(files) and len(set(mapping.values()))==len(mapping),'one-to-one full mapping');names={safe(n) for n in mapping.values()};require(all('/' not in n for n in names),'flat physical names')
 require(set(r.tree(dest))==names|{rec['metadata_file']},'whole flat membership');bodies={}
 r.read(dest/rec['metadata_file'],rec['metadata_sha256'],0o600)
 for n,x in files.items():
  p=dest/mapping[n];b=r.read(p,x['sha256'],0o600);require(p.lstat().st_uid==os.getuid() and len(b)==x['bytes'],'flat extent owner');bodies[n]=b
 require(len(rows)==rec['members'] and len(bodies)==rec['regular_bodies'] and manifest['root_mode']==rec['root_mode'],'complete scope counts/mode')
 # Deterministic bounded reconstruction validates PAX framing/footer and original modes without extraction.
 sink=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=sink,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
   for x in manifest['members']:
    r.tick();ti=tarfile.TarInfo(x['path']);ti.mode=mode(x['mode']);ti.uid=ti.gid=ti.mtime=0;ti.uname=ti.gname=''
    if x['kind']=='directory':ti.type=tarfile.DIRTYPE;tar.addfile(ti)
    else:ti.size=len(bodies[x['path']]);tar.addfile(ti,io.BytesIO(bodies[x['path']]))
 require(sink.getvalue()==archive,'canonical original archive from actual flat bodies');return bodies,rows

def git_graph(objects,head):
 seen=set();pending=[head];trees={}
 def entries(b):
  out=[];i=0
  while i<len(b):
   end=b.index(b'\0',i);prefix=b[i:end];m,n=prefix.split(b' ',1);require(m in (b'40000',b'100644',b'100755'),'Git mode');name=n.decode();safe(name);require('/' not in name,'Git basename');oid=b[end+1:end+21];require(len(oid)==20,'tree truncated');out.append((m.decode(),name,oid.hex()));i=end+21
  require(len({x[1] for x in out})==len(out),'duplicate Git entry');return out
 while pending:
  oid=pending.pop()
  if oid in seen:continue
  require(oid in objects,'missing reachable object');seen.add(oid);kind,b=objects[oid]
  if kind=='commit':
   headers=b.split(b'\n\n',1)[0].splitlines();roots=[x[5:].decode() for x in headers if x.startswith(b'tree ')];require(len(roots)==1,'commit tree');pending.extend(roots+[x[7:].decode() for x in headers if x.startswith(b'parent ')])
  elif kind=='tree':trees[oid]=entries(b);pending.extend(x[2] for x in trees[oid])
  else:require(kind=='blob','Git object type')
 require(seen==set(objects),'exact reachable denominator')
 root=[x[5:].decode() for x in objects[head][1].split(b'\n\n',1)[0].splitlines() if x.startswith(b'tree ')][0];out={};todo=[('',root,0)]
 while todo:
  prefix,oid,depth=todo.pop();require(depth<=32,'Git depth')
  for m,n,child in trees[oid]:
   name=prefix+n
   if m=='40000':require(objects[child][0]=='tree','tree edge');todo.append((name+'/',child,depth+1))
   else:require(objects[child][0]=='blob','blob edge');out[name]=(m,objects[child][1])
 return out

def run(prerequisites_only=False):
 r=Reader();cfg=r.j(Path(__file__).resolve().parent/'INPUTS01.json',INPUTS_PIN);P={k:Path(v) for k,v in cfg['paths'].items()};receipts=[]
 for path,x in cfg['fixed'].items():require(len(r.read(Path(path),x['sha256']))==x['bytes'],'fixed extent')
 def receipt(p):
  b=r.read(p);receipts.append({'path':str(p),'sha256':h(b)});return decode(b)
 for role,decision in [('baseline_review','ACCEPTED_ACTUAL_COMPLETE_BASELINE_BYTES_AND_ORIGINAL_GIT'),('old_review','COMPLETE_FAILED_SCOPE_BYTE_UNION_ACCEPTED'),('policy_review','ACCEPTED_EXACT_CONCRETE_POLICY_ONLY')]:
  q=seal(r,P[role]);require(q['decision']==decision,'genuine predecessor decision');receipts.extend({'path':str(P[role]/n),'sha256':h(r.read(P[role]/n))} for n in ['MACHINE01.json','REPORT01.md','MANIFEST01.json'])
 policy=r.j(P['policy']/'POLICY01.json',POLICY);closure=r.j(P['policy']/'SOURCE_CLOSURE01.json',CLOSURE);oldmap=policy['historical']['installed'];newmap=policy['target']['installed']
 require(h(canonical(oldmap))==OLDMAP and h(canonical(newmap))==NEWMAP and closure['installed']==newmap,'exact maps');require(len(oldmap)==194 and len(newmap)==195 and sum(oldmap.get(n)==v for n,v in newmap.items())==191,'194/195/191')
 oldflat=receipt(P['old_root']/'FLAT_RECOVERY01.json');oldcap=r.j(P['old_capture']/'CAPTURE01.json');old={};oldrows={};old_scopes={}
 for role,rec in oldflat['scopes'].items():
  manifest=r.j(P['old_capture']/(role.upper()+'_MANIFEST01.json'));archive=r.read(P['old_capture']/('complete-'+role+'01.tar.gz'),rec['archive_sha256']);bodies,rows=flat_scope(r,P['old_root']/('flat-'+role+'01'),rec,manifest,archive);old_scopes[role]=bodies
  require(h(r.read(P['old_capture']/(role.upper()+'_MANIFEST01.json')))==rec['manifest_sha256'],'old manifestpin')
  if role.startswith('capsule'):
   for n,b in bodies.items():require(n not in old,'old file overlap');old[n]=b
   for n,x in rows.items():require(n not in oldrows or oldrows[n]==x,'directory metadata agreement');oldrows[n]=x
 require(len(oldrows)==588 and len(old)==475,'whole old capsule denominator')
 require(oldrows==manifest_rows(r.j(P['old_capture']/'CAPSULE_MASTER_MANIFEST01.json')),'full old master')
 baseline=receipt(P['baseline_root']/'FLAT_RECOVERY01.json');oldobjects={}
 for role in ['git1','git2','git3']:
  rec=baseline['scopes'][role];m=r.j(P['baseline_capture']/(role.upper()+'_MANIFEST01.json'));a=r.read(P['baseline_capture']/('complete-'+role+'01.tar.gz'),rec['archive_sha256']);b,_=flat_scope(r,P['baseline_root']/('flat-'+role+'01'),rec,m,a);require(not(set(b)&set(oldobjects)),'object overlap');oldobjects.update(b)
 require(len(oldobjects)==385,'old recovered objects385')
 snapshot=P['delta']/'snapshot';basis=r.j(snapshot/'COMPOSITION_BASIS01.json');current=manifest_rows(basis['current589_manifest']);protected=manifest_rows(r.j(P['adoption_review']/'PROTECTED_NON_TARGET585.json'));changes={x['path']:x for x in basis['new_source_changes']};require(len(current)==589 and len(protected)==585 and len(changes)==4,'589/585/4')
 require(set(protected)==set(current)-set(changes) and all(protected[n]==current[n]==oldrows[n] for n in protected),'all585 original metadata unchanged')
 actual=r.tree(CAP,('.git',));require(set(actual)==set(current),'actual whole589 namespace')
 composition={}
 for n,x in current.items():
  s=(CAP/n).lstat();require(stat.S_IMODE(s.st_mode)==mode(x['mode']),'current original mode')
  if x['kind']=='directory':require(stat.S_ISDIR(s.st_mode),'current directory');continue
  original=r.read(CAP/n,x['sha256']);require(len(original)==x['bytes'],'current extent')
  if n in changes:b=r.read(snapshot/'current-source'/n,changes[n]['new_sha256'])
  else:b=old[n]
  require(original==b,'complete current body basis');composition[n]=b
 for n,pin in oldmap.items():require(h(old[n])==pin,'historical full194body map')
 for n,pin in newmap.items():require(h(composition[n])==pin,'target full195body map')
 require(sum(n.startswith('tradingagents/') for n in newmap)==150,'150 package bodies')
 claims=[]
 for n,b in composition.items():
  if n.startswith('research_runs/') and n.endswith('/claim.json'):
   q=decode(b);failed=n[:-10]+'failed.json';complete=n[:-10]+'complete.json';require(failed in composition and complete not in composition,'original FAILED remains');f=decode(composition[failed]);claims.append({'identity':n.split('/')[1],'claim_sha256':h(b),'failed_sha256':h(composition[failed]),'budget':q.get('effective_attempt_budget',q['family']['attempt_budget'])})
 require(len(claims)==3 and max(x['budget'] for x in claims)==19,'three spent/highest19')
 for q in policy['consumers'].values():require(not any(x['identity']==q['experiment'] for x in claims),'future identity unspent')
 index=r.j(snapshot/'SOURCE_GIT394_METADATA01.json');objects={};newobjects={}
 for x in index['objects']:
  oid=x['oid'];require(oid not in objects,'duplicate object')
  if x['body_basis']=='actual-old385-recovery':b=oldobjects[oid]
  else:b=r.read(snapshot/safe(x['body_basis']));newobjects[oid]=b
  require(len(b)==x['bytes'] and h(b)==x['sha256'] and hashlib.sha1(x['type'].encode()+b' '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid,'opaque logical object identity');objects[oid]=(x['type'],b)
 require(len(objects)==394 and len(newobjects)==9 and set(oldobjects)==set(objects)-set(newobjects),'385+9exact394')
 tracked=git_graph(objects,SOURCE);require(len(tracked)==340,'340 tracked denominator')
 for n,(m,b) in tracked.items():require(composition[n]==b and bool(mode(current[n]['mode'])&0o111)==(m=='100755'),'complete340 Git/current joins')
 # Bind actual source HEAD by reading ref metadata only. No Git process, lazy fetch, or imports.
 head=r.read(CAP/'.git/HEAD').decode().strip()
 if head.startswith('ref: '):head=r.read(CAP/'.git'/safe(head[5:])).decode().strip()
 require(head==SOURCE,'actual source HEAD')
 require(h(composition['tradingagents/research/onchain_replication/operational_source_compatibility.py'])==CHECKER,'actual compatible02 helper')
 report={'schema_version':1,'status':'PREREQUISITES_VERIFIED_NOT_RECOVERY','policy_sha256':POLICY,'checker_sha256':CHECKER,'historical_map_sha256':OLDMAP,'target_map_sha256':NEWMAP,'closure_sha256':CLOSURE,'source':SOURCE,'original_capsule_typed':588,'current_typed':589,'protected_typed':585,'tracked':340,'implementation':195,'package':150,'old_git_objects':385,'new_git_objects':9,'total_git_objects':394,'failed_claims':claims,'highest_actual_allowance':19,'recovery_receipts':receipts,'recovery_proof':None,'numerical_authority':False,'excluded':['POSIX reconstruction','installed runtime package bodies','unrelated stores','full capacity','final caller/gate/registration supplement'],'sampled_currentness':'finite namespace/descriptor/signature joins; no atomic or continuous immutability guarantee'}

 # Actual completed external transfer and its exact preserved input modes remain separate from new flat modes.
 D=P['receiver'];remote=receipt(D/'REMOTE_RECOVERY01.json');rm=seal(r,P['remote_review']);profile=r.j(D/'COMPLETED_REMOTE03_READ_ONLY_SELECTED_MODE_PROFILE01.json');selected=D/'selected'
 require(profile['actual_receiver_root']==str(D) and profile['actual_selected_root']==str(selected),'fixed receiver profile')
 require(profile['actual_remote_receipt_sha256']==h(r.read(D/'REMOTE_RECOVERY01.json')) and profile['selection_sha256']==h(r.read(D/'SELECTED_BODIES01.json')),'profile actual receipt selection')
 require(profile['actual_remote_outcome_review_sha256']==h(r.read(P['remote_review']/'MACHINE01.json')) and profile['actual_remote_outcome_review_manifest_sha256']==h(r.read(P['remote_review']/'MANIFEST01.json')),'profile genuine review bodies')
 require(rm['decision']=='ACCEPTED_ACTUAL_REMOTE_BYTES_WITHHELD_FLAT_ENTRY_RM1','original byte-only acceptance')
 require(set(r.tree(selected))==set(manifest_rows(profile['full_manifest'])),'actual selected full namespace')
 for n,m in profile['directory_modes'].items():
  p=selected if n=='.' else selected/safe(n);st=p.lstat();require(stat.S_ISDIR(st.st_mode) and stat.S_IMODE(st.st_mode)==m and st.st_uid==profile['expected_owner_uid'],'original directory mode owner')
 require(len(profile['files'])==15 and len(profile['directory_modes'])==7,'exact original7dirs15files')
 for n,x in profile['files'].items():require(len(r.read(selected/safe(n),x['sha256'],x['mode']))==x['bytes'] and (selected/n).lstat().st_uid==profile['expected_owner_uid'],'actual selected extent owner')
 require(remote['expected_operations']==55 and len(remote['operations'])==55 and remote['selected_count']==15 and remote['selected_logical_bytes']==507946,'actual denominator15/55/507946')
 for x in remote['selected_blobs']:
  b=r.read(selected/safe(x['path']),x['sha256']);require(len(b)==x['bytes'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['git_object'],'actual selected logical GitOID')
 for x in remote['operations']:require(x['exit']==x['actual_reaped_exit']==0 and x['cleanup_failures']==[] and x['actual_child_limits']=={'fsize':[FILE,FILE],'pid':x['pid']},'original actual child success bounds')
 require(remote['free_bytes']>=10*1024**3,'actual remote floor')
 report['selected_original_modes_preserved']=True
 if prerequisites_only:r.finish();report.update(bytes_read=r.total,files_read=len(r.cache));return report
 # A source-only preparation can reach here only if genuine prospective outcomes actually exist.
 D=P['receiver'];draft=r.j(D/'ROOT_FLAT04_INSTALLATION_DRAFT01.json');require(draft['source_sha256']=='17f4ee85d2408cdc1b678e107e82b6e19b674b4b941f1fa51f40f17bbedef282','installed04 source')
 for n,x in draft['helpers_and_metadata'].items():require(len(r.read(D/safe(n),x['sha256'],x['mode']))==x['bytes'],'installed closure')
 newflat=receipt(D/'FLAT_RECOVERY01.json');post=receipt(D/'FLAT_POSTWRITE_OBSERVATION01.json');ex=receipt(D/'ROOT_FLAT05_EXIT01.json');intent=receipt(D/'ROOT_FLAT05_INTENT01.json');spawn=receipt(D/'ROOT_FLAT05_SPAWN01.json');entry=seal(r,P['entry_review'])
 require(entry['decision']=='ACCEPTED_EXACT_ONE_USE_OPERATIONAL_FLAT_ENTRY_ONLY' and intent['entry_review_sha256']==h(r.read(P['entry_review']/'MACHINE01.json')),'actual entry authority chain')
 require(intent['installation_draft_sha256']==h(r.read(D/'ROOT_FLAT04_INSTALLATION_DRAFT01.json')) and intent['outer_caller_sha256']==h(r.read(P['control']/'root_operational_flat05.py'))==entry['root_outer_caller_sha256'],'actual caller draft')
 require(ex['actual_outer_exit']==ex['actual_child_exit']==0 and ex['parent_failure_type'] is None and ex['cleanup_failures']==[] and ex['actual_child_pid']==spawn['pid'],'actual successful Root terminal')
 require(not Path('/proc',str(spawn['pid'])).exists(),'flat process absent')
 for name in ['stdout','stderr']:
  b=r.read(D/('ROOT_FLAT05.'+name));require(h(b)==ex[name+'_sha256'] and len(b)==ex[name+'_bytes'],'raw Root stream')
 require(entry['owned_root']==str(D) and entry['installation_draft_sha256']==h(r.read(D/'ROOT_FLAT04_INSTALLATION_DRAFT01.json')) and entry['flat_helper_sha256']==draft['source_sha256'] and entry['flat_execution_released'] is True and entry['remote_execution_released'] is False and entry['numerical_authority'] is False,'exact entry release scope')
 require(not os.path.lexists(D/'FLAT_FAILED01.json'),'no contradictory failure terminal')
 require(ex['native_or_claim_started'] is False and ex['remote_relaunched'] is False and ex['actual_inherited_child_fsize']==[FILE,FILE],'actual control exclusions')
 require(newflat['capture_sha256']==h(r.read(P['delta']/'CAPTURE01.json')) and newflat['failed_capture_sha256']==h(r.read(P['failed_delta']/'CAPTURE01.json')) and newflat['original_mapping_sha256']==h(r.read(P['delta']/'ORIGIN_MAP01.json')),'both actual capture origins')
 require(newflat['actual_root_exit'] is None and newflat['posix_tree_restored'] is False and newflat['whole_fit_capacity'] is None and newflat['numerical_release'] is None and newflat['native_or_claim_started'] is False,'retain original unknowns/exclusions')
 require(newflat['status']=='COMPLETE_OPERATIONAL_DELTA_AND_FAILED_ROOT_FLAT_BYTES' and newflat['source']==SOURCE and newflat['policy_sha256']==POLICY,'new actual receipt domain')
 require(newflat['remote_receipt_sha256']==h(r.read(D/'REMOTE_RECOVERY01.json'))==draft['remote_receipt_sha256'] and newflat['selection_sha256']==h(r.read(D/'SELECTED_BODIES01.json'))==draft['selection_sha256'],'new receipt external chain')
 require(post['recovery_sha256']==h(r.read(D/'FLAT_RECOVERY01.json')),'actual postwrite sidecar')
 require(newflat['read_only_selected_mode_profile_sha256']==h(r.read(D/'COMPLETED_REMOTE03_READ_ONLY_SELECTED_MODE_PROFILE01.json')),'original775 profile')
 newbodies={}
 for role,recname,sub,manifest,archive in [('delta','restored','flat-operational-delta01','PAYLOAD_MANIFEST01.json','operational-delta01.tar.gz'),('failed_delta','failed_restored','flat-failed-remote02-01','FAILED_PAYLOAD_MANIFEST01.json','failed-remote02.tar.gz')]:
  m=r.j(P[role]/manifest);a=r.read(P[role]/archive);rec=newflat[recname];require(rec['manifest_sha256']==h(r.read(P[role]/manifest)),'new manifest pin');bodies,rows=flat_scope(r,D/sub,rec,m,a);newbodies[role]=bodies
  snap=P[role]/'snapshot'
  for n,b in bodies.items():require(r.read(snap/n)==b,'new flat/captured exact body')
 require(len(newbodies['delta'])==33 and len(newbodies['failed_delta'])==31,'both complete body denominators')
 for n,x in changes.items():require(newbodies['delta']['current-source/'+n]==composition[n],'recovered new source')
 for oid,b in newobjects.items():require(newbodies['delta']['new-git-objects/'+oid+'.body']==b,'all9 recovered new objects')
 require(newbodies['delta']['policy/POLICY01.json']==r.read(P['policy']/'POLICY01.json') and newbodies['delta']['policy/SOURCE_CLOSURE01.json']==r.read(P['policy']/'SOURCE_CLOSURE01.json'),'recovered exact policy closure')
 for x in r.j(P['delta']/'ORIGIN_MAP01.json')['origins']:
  b=newbodies['delta'][x['path']];p=Path(x['original']);require(r.read(p,x['sha256'])==b and stat.S_IMODE(p.lstat().st_mode)==x['original_mode'],'all delta original mode/body joins')
 require(1<=len(newflat['whole_tree_observations'])<=64 and 1<=len(ex['whole_owned_observations'])<=128,'fixed observation denominators')
 require(newflat['whole_tree_policy']=={'allocated':100663296,'sample_seconds':5,'depth':32,'file':4194304,'floor':10737418240,'logical':67108864,'members':32768,'samples':8192},'fixed policy')
 for o in ex['whole_owned_observations']+newflat['whole_tree_observations']+[post['observation']]:require(o['logical_bytes']<=64*1024**2 and o['allocated_bytes']<=96*1024**2 and o['members']<=32768,'sampled whole caps')
 r.finish();report.update(status='COMPLETE_COMPOSED_BYTES_OBSERVED_REQUIRES_INDEPENDENT_REVIEW',bytes_read=r.total,files_read=len(r.cache),new_flat_bodies=64,actual_root_exit=0);return report
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--prerequisites-only',action='store_true');args=parser.parse_args()
 try:result=run(args.prerequisites_only)
 except BaseException as error:
  print(json.dumps({'schema_version':1,'status':'REFUSED','exception_type':type(error).__name__,'reason':str(error),'recovery_proof':None,'numerical_authority':False},sort_keys=True));raise
 print(json.dumps(result,sort_keys=True,indent=2))
