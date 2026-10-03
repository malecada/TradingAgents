"""Prospective ROOT-only complete B2 byte retention and actual remote recovery.
Never executes capsule code, numerical imports, admission, claims or replay.
"""
import argparse,gzip,hashlib,io,json,os,resource,signal,stat,subprocess,tarfile,time
from pathlib import Path,PurePosixPath
import archive01 as archive
import owned_io as owned
MAX=4194304;GIB=1073741824
CAP=Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-02/source')
A='9742c6ec817dd0917f9f35a52e4b83965ca1cd29'
FIRST='compact-cold-inputs-20261003-01';SECOND='compact-cold-comparison-20261003-01'
BRANCH='research/onchain-paper-replication-2026-09-24'
require=archive.require

def digest(b):return hashlib.sha256(b).hexdigest()
def ref(path):return {'path':str(path),'sha256':digest(archive.read(path))}
def referenced(v):
 require(type(v)is dict and set(v)=={'path','sha256'},'exact absolute reference');b=archive.read(v['path']);require(digest(b)==v['sha256'],'reference changed');return b
def document(root,name):return json.loads(archive.read(root/archive.relative(name)))
def put(directory,name,b):
 require(len(b)<=MAX,'retained file cap');p=directory/archive.relative(name)
 with owned._opened(p,'xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 archive.fsync_dir(p.parent);return {'path':name,'sha256':digest(b),'bytes':len(b)}
def jsonput(directory,name,value):return put(directory,name,(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode())
def sha1(v):require(type(v)is str and len(v)==40 and all(c in '0123456789abcdef' for c in v),'actual commit required')

class Git:
 """Finite file-capped child stdout/stderr, timeout plus owned kill/reap.
 No URL is recorded in metadata. Calls occur only on explicit root invocation.
 """
 def __init__(self,logs):self.logs=logs;logs.mkdir(exist_ok=False);self.calls=0;self.total=0
 def __call__(self,root,*args,input_bytes=None,allow_lazy=False):
  require(self.calls<512,'Git call bound');number=self.calls;self.calls+=1;fds=[];child=None;primary=None
  def cap():resource.setrlimit(resource.RLIMIT_FSIZE,(MAX,MAX))
  def stop():
   if child is not None and child.poll() is None:os.killpg(child.pid,signal.SIGKILL)
  def reap():
   if child is not None:child.wait(timeout=5)
  try:
   out=self.logs/f'{number:04d}.out';err=self.logs/f'{number:04d}.err'
   for p in (out,err):fds.append(os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600))
   stdin=subprocess.DEVNULL
   if input_bytes is not None:
    require(type(input_bytes)is bytes and len(input_bytes)<=65536,'Git request bound');put(self.logs,f'{number:04d}.in',input_bytes);stdin=os.open(self.logs/f'{number:04d}.in',os.O_RDONLY|os.O_NOFOLLOW);fds.append(stdin)
   child=subprocess.Popen(['git','-c','core.hooksPath=/dev/null',*args],cwd=root,stdin=stdin,stdout=fds[0],stderr=fds[1],start_new_session=True,preexec_fn=cap,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_TERMINAL_PROMPT':'0','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_NO_LAZY_FETCH':'0' if allow_lazy else '1'})
   code=child.wait(timeout=60);require(code==0,'Git operation failed; raw stderr retained');b=archive.read(out);errors=archive.read(err);self.total+=len(b)+len(errors);require(self.total<=64*1024**2,'Git retained output aggregate bound');return b
  except BaseException as error:primary=error;raise
  finally:owned._cleanup((stop,reap)+tuple(lambda fd=fd:os.close(fd) for fd in fds),primary=primary)

def blobs(git,root,commit,paths):
 sha1(commit);require(len(paths)<=256 and len(set(paths))==len(paths),'bounded unique Git paths');request=b''.join((commit+':'+str(archive.relative(p))+'\n').encode() for p in paths);raw=git(root,'cat-file','--batch',input_bytes=request);offset=0;result={}
 for name in paths:
  end=raw.find(b'\n',offset);require(end>=offset,'batch header absent');parts=raw[offset:end].split();require(len(parts)==3 and parts[1]==b'blob' and len(parts[0])==40 and all(c in b'0123456789abcdef' for c in parts[0]) and parts[2].isdigit(),'batch nonblob/header');size=int(parts[2]);require(size<=MAX,'blob extent bound');offset=end+1;body=raw[offset:offset+size];offset+=size;require(len(body)==size and raw[offset:offset+1]==b'\n','short blob');offset+=1;result[name]=body
 require(offset==len(raw),'extra batch data');return result

def validate(root,B,draft,git,comparison_release):
 root=archive.direct(root);sha1(B);require(B!=A,'actual new B required');require(not os.path.lexists(root/'.git/objects/info/alternates'),'alternate Git objects forbidden')
 require(git(root,'rev-parse','HEAD').decode().strip()==B and git(root,'rev-list','--parents','-n','1',B).decode().split()==[B,A],'actual B must have sole direct A parent')
 require(draft['source_at_generation']==A and len(draft['exact_four_additions'])==4,'original four-file draft differs');rows=draft['exact_four_additions'];require({r['role'] for r in rows}=={'registration','charter','phase_contract','evolution'} and len({r['capsule_path'] for r in rows})==4,'four roles/paths required');byrole={r['role']:r for r in rows};paths=[str(archive.relative(r['capsule_path'])) for r in rows]
 parts=git(root,'diff-tree','--no-commit-id','--name-status','-r','-z',A,B).decode().split('\0');require(parts[-1]=='' and len(parts[:-1])==8,'exact four Git changes required');changes=list(zip(parts[:-1:2],parts[1:-1:2]));require(set(changes)=={('A',p) for p in paths},'only four added paths allowed')
 bodies=blobs(git,root,B,paths)
 for row in rows:
  b=archive.read(root/row['capsule_path']);require(b==bodies[row['capsule_path']] and len(b)==row['bytes'] and digest(b)==row['sha256'],'four actual body pins differ')
 old=document(root,'cold-registration.json');require(blobs(git,root,A,['cold-registration.json'])['cold-registration.json']==archive.read(root/'cold-registration.json'),'original registration changed')
 new=json.loads(bodies[byrole['registration']['capsule_path']]);require(set(old)==set(new) and {k:v for k,v in old.items() if k!='experiments'}=={k:v for k,v in new.items() if k!='experiments'},'original family/history/datasets changed');require(set(old['experiments'])=={FIRST} and set(new['experiments'])=={FIRST,SECOND} and new['experiments'][FIRST]==old['experiments'][FIRST],'original experiment changed')
 first=old['experiments'][FIRST];second=new['experiments'][SECOND];family=new['families'][first['family']];require(family['attempt_budget']==2 and family['prior_attempts']==0,'finite family changed');allowed={'parent','question','cells','outputs','inputs','charter'};require({k:v for k,v in first.items() if k not in allowed}=={k:v for k,v in second.items() if k not in allowed} and second['parent']==FIRST and second['cells']==['cold-genuine-comparison'] and sorted(second['outputs'])==sorted(['binding.json','journal.json','cold-handoff.json','proof-compare.json']),'comparison scientific contract drift')
 source=first['source_files'];require(source==second['source_files'] and len(source)==195 and sum(p.startswith('tradingagents/') for p in source)==147,'source195/package147 drift')
 current=blobs(git,root,B,list(source));original=blobs(git,root,A,list(source))
 for name,h in source.items():require(digest(archive.read(root/name))==h and current[name]==original[name]==archive.read(root/name),'full source body differs')
 original_inputs=blobs(git,root,A,[v['path'] for v in first['inputs'].values()])
 for v in first['inputs'].values():require(original_inputs[v['path']]==archive.read(root/v['path']) and digest(original_inputs[v['path']])==v['sha256'],'original nine inputs drift')
 require(blobs(git,root,A,['cold_prep/anchor.json'])['cold_prep/anchor.json']==archive.read(root/'cold_prep/anchor.json'),'original anchor declaration drift')
 anchor=document(root,'cold_prep/anchor.json');require(len(anchor['files'])==147 and anchor['files']=={n:h for n,h in source.items() if n.startswith('tradingagents/')},'exact package anchor147 differs');anchored=blobs(git,root,anchor['commit'],list(anchor['files']))
 for name,h in anchor['files'].items():require(digest(anchored[name])==h,'anchor body differs')
 material=document(root,'research_artifacts/compact-cold-engineering-20261003/'+FIRST+'/future-inputs.json');require(len(material['inputs'])==43,'original43 role denominator');inputs={('execution_job' if n=='future_execution_job' else n):v for n,v in material['inputs'].items()}|{'environment':first['inputs']['environment']};require(len(inputs)==44 and inputs==second['inputs'],'actual43→44 role drift')
 for v in inputs.values():require(digest(archive.read(root/archive.relative(v['path'])))==v['sha256'],'original emitted input changed')
 claimraw=archive.read(root/'research_runs'/FIRST/'claim.json');claim=json.loads(claimraw);terminal=document(root,'research_runs/'+FIRST+'/complete.json');require(claim['source']==A and claim['experiment']==first and terminal['claim_sha256']==digest(claimraw) and terminal['status']=='complete' and terminal['source']==A and not (root/'research_runs'/FIRST/'failed.json').exists(),'original materialize claim/terminal differs')
 accepted=document(root,'proof_outer/'+FIRST+'/accepted.json');wait=document(root,'proof_supervise/'+FIRST+'/exit.json');require(accepted['source']==wait['source']==A and accepted['status']==wait['status']=='accepted' and accepted['release']==wait['release'] and wait['controller_exit_code']==0,'original outer/wait differs')
 for r in (accepted['release'],accepted['authentication'],accepted['tail'],wait['accepted_receipt']):require(digest(archive.read(root/archive.relative(r['path'])))==r['sha256'],'original outcome reference differs')
 evolution=json.loads(bodies[byrole['evolution']['capsule_path']]);require(evolution['parent_source']==A and evolution['original_registration']==accepted_release(root,accepted)['registration'] and evolution['current_registration']['path']==byrole['registration']['capsule_path'] and evolution['current_registration']['sha256']==byrole['registration']['sha256'],'original evolution refs differ')
 release=accepted_release(root,accepted)
 for r in (release['runtime'],release['native_environment'],release['sources'],release['phase_contract']):require(digest(archive.read(root/archive.relative(r['path'])))==r['sha256'],'original runtime/source/contract reference drift')
 require(evolution['accepted']==capsule_ref(root,'proof_outer/'+FIRST+'/accepted.json','metadata') and evolution['wait']==capsule_ref(root,'proof_supervise/'+FIRST+'/exit.json','metadata'),'evolution original actual receipt refs drift')
 contract=json.loads(bodies[byrole['phase_contract']['capsule_path']]);require(contract=={'schema_version':1,'identity':SECOND,'experiment':second,'family':family,'expected_outputs':second['outputs']},'committed phase contract differs')
 require(second['charter']=={'path':byrole['charter']['capsule_path'],'sha256':byrole['charter']['sha256']},'committed charter join differs')
 expected={('comparison-registration','registration'),('comparison-charter','charter'),('comparison-phase-contract','phase_contract')};require({(r['role'],r['path'],r['sha256']) for r in evolution['additions']}=={(role,byrole[k]['capsule_path'],byrole[k]['sha256']) for role,k in expected} and len(evolution['additions'])==3,'exact noncyclic three addition rows differ')
 require(type(comparison_release)is dict and set(comparison_release)=={'path','sha256'},'actual installed comparison release reference required')
 envelope_raw=archive.read(root/archive.relative(comparison_release['path']),8192);require(digest(envelope_raw)==comparison_release['sha256'],'installed comparison envelope differs');envelope=json.loads(envelope_raw)
 fields={'schema_version','kind','status','phase','root','source','registration','sources','runtime','native_environment','phase_contract','prior_materialization','cpus','remaining'}
 require(set(envelope)==fields and type(envelope['schema_version'])is int and envelope['schema_version']==1 and envelope['kind']=='cold-proof-outer-release-v1' and envelope['status']=='released' and envelope['remaining']==[] and envelope['phase']=='compare' and envelope['source']==B and envelope['root']==str(CAP),'actual released B envelope absent/draft/drift')
 require(envelope['registration']==capsule_ref(root,byrole['registration']['capsule_path'],'document') and envelope['phase_contract']==capsule_ref(root,byrole['phase_contract']['capsule_path'],'document'),'B envelope four-file bindings differ')
 require(all(envelope[k]==release[k] for k in ('sources','runtime','native_environment','cpus')) and envelope['prior_materialization']=={'accepted':evolution['accepted'],'wait':evolution['wait'],'evolution':capsule_ref(root,byrole['evolution']['capsule_path'],'document')},'original sources/runtime/prior evolution changed')
 for ns in ('research_runs','proof_outer','proof_supervise','research_artifacts/compact-cold-engineering-20261003','research_artifacts/onchain-paper-replication-2026-09-24/runs'):require(not os.path.lexists(root/ns/SECOND),'comparison already born')
 return {'B':B,'A':A,'source_count':195,'anchor_package_count':147,'original_materialization_status':'complete-receipt-byte-joined-not-reexecuted','comparison_roles':44,'comparison_claims_observed':0,'family_budget':2,'family_prior_attempts':0,'scientific_completion':False}

def capsule_ref(root,path,kind):
 b=archive.read(root/archive.relative(path));return {'path':path,'sha256':digest(b),'bytes':len(b),'kind':kind}

def accepted_release(root,accepted):return document(root,accepted['release']['path'])

class Limited:
 def __init__(self,stream):self.stream=stream;self.count=0
 def write(self,b):require(self.count+len(b)<=MAX,'compressed archive4MiB ceiling');n=self.stream.write(b);require(n==len(b),'short archive write');self.count+=n;return n
 def flush(self):return self.stream.flush()

def pack(root,path,rows):
 deadline=time.monotonic()+120
 with owned._opened(path,'xb') as stream:
  writer=Limited(stream)
  with owned._closing(gzip.GzipFile(fileobj=writer,mode='wb',mtime=0,filename='')) as compressed:
   with owned._closing(tarfile.open(fileobj=compressed,mode='w|',format=tarfile.PAX_FORMAT)) as tf:
    for row in rows:
     require(time.monotonic()<deadline,'archive sampled deadline');name=row['path'];require('\\' not in name,'nonportable archive path');item=tarfile.TarInfo('source' if name=='.' else 'source/'+name);item.mode=row['mode'];item.mtime=0;item.uid=item.gid=0;item.uname=item.gname=''
     if row['kind']=='directory':item.type=tarfile.DIRTYPE;tf.addfile(item)
     else:
      b=archive.read(root/archive.relative(name));require(len(b)==row['bytes'] and digest(b)==row['sha256'],'archive original changed');item.size=len(b);tf.addfile(item,io.BytesIO(b))
  stream.flush();os.fsync(stream.fileno())
 archive.fsync_dir(path.parent)

class TarReader:
 """Bound each decompressed parser read before tarfile can allocate a long header."""
 def __init__(self,stream,deadline):self.stream=stream;self.deadline=deadline
 def read(self,n=-1):
  require(type(n)is int and 0<=n<=MAX+8192 and time.monotonic()<self.deadline,'bounded decompressed archive read');return self.stream.read(n)
 def tell(self):return self.stream.tell()
 def seek(self,offset,whence=0):
  require(whence==0 and type(offset)is int and 0<=offset<=GIB+32768*8192+10240 and time.monotonic()<self.deadline,'bounded tar absolute seek');return self.stream.seek(offset,whence)

def unpack(archive_path,root,rows):
 require(len(rows)<=32768 and rows[0]['path']=='.' and rows[0]['kind']=='directory','finite complete root inventory');expected={r['path']:r for r in rows};require(len(expected)==len(rows),'duplicate inventory');root=archive.direct(root);root.mkdir(exist_ok=False);seen=set();total=0;deadline=time.monotonic()+120
 with owned._opened(archive_path,'rb') as stream:
  require(os.fstat(stream.fileno()).st_size<=MAX,'compressed archive bound')
  with owned._closing(gzip.GzipFile(fileobj=stream,mode='rb')) as compressed:
   with owned._closing(tarfile.open(fileobj=TarReader(compressed,deadline),mode='r:')) as tf:
    for member in tf:
     require(time.monotonic()<deadline and len(seen)<32768,'restore sampled count/deadline');p=PurePosixPath(member.name);require(str(p)==member.name and not p.is_absolute() and p.parts and p.parts[0]=='source' and '..' not in p.parts and '\\' not in member.name,'unsafe archive path');name='.' if len(p.parts)==1 else str(PurePosixPath(*p.parts[1:]));require(name in expected and name not in seen,'extra/duplicate archive member');row=expected[name];require(member.mode==row['mode'] and not member.issym() and not member.islnk() and set(member.pax_headers)<= {'path'},'archive mode/link/extended attributes differ');target=root if name=='.' else root/archive.relative(name);require(target.resolve()==target and (target==root or target.parent.is_dir()),'restore redirected/missing parent')
     if row['kind']=='directory':
      require(member.isdir() and member.size==0,'directory type differs')
      if target!=root:target.mkdir(mode=0o700)
     else:
      require(row['kind']=='file' and member.isfile() and member.size==row['bytes']<=MAX and name!='.','file type/extent differs');total+=member.size;require(total<=GIB,'restore logical cap');body=tf.extractfile(member);require(body is not None,'missing member bytes')
      with owned._closing(body):b=body.read(MAX+1)
      require(len(b)==row['bytes'] and digest(b)==row['sha256'],'recovered opaque bytes differ');put(target.parent,target.name,b);os.chmod(target,row['mode'])
     seen.add(name)
 require(seen==set(expected),'missing archive members')
 for row in reversed(rows):
  if row['kind']=='directory':os.chmod(root if row['path']=='.' else root/row['path'],row['mode'])
 archive.verify_tree(root,rows[1:],limit=GIB);require(stat.S_IMODE(root.stat().st_mode)==rows[0]['mode'],'root mode differs');archive.fsync_dir(root)
 canonical=root.parent/(root.name+'.canonical.tar.gz');pack(root,canonical,rows);require(archive.read(canonical)==archive.read(archive_path),'archive has noncanonical or trailing bytes')

def retain(q):
 require(set(q)=={'root','B','draft','comparison_release','destination'},'exact retention request');root=archive.direct(q['root']);require(root==CAP,'fixed actual CAP2 required');out=archive.direct(q['destination']);require(not out.is_relative_to(root) and not root.is_relative_to(out),'separate fresh output');out.mkdir(exist_ok=False);git=Git(out/'git-logs');draft=json.loads(referenced(q['draft']));before=archive.census(root,GIB,time.monotonic()+120);require(len(before)+1<=32768,'whole root-inclusive entry cap');rootpin=archive.sig(root.stat());binding=validate(root,q['B'],draft,git,q['comparison_release'])
 rows=archive.snapshot(root,out/'source',limit=GIB);require(before==archive.census(root,GIB,time.monotonic()+120) and rootpin==archive.sig(root.stat()),'original tree changed during retention');full=[{'path':'.','kind':'directory','mode':stat.S_IMODE(root.stat().st_mode),'bytes':0}]+rows;pack(out/'source',out/'capsule.tar.gz',full);archive.verify_tree(out/'source',rows,limit=GIB);require(before==archive.census(root,GIB,time.monotonic()+120) and rootpin==archive.sig(root.stat()),'original capsule changed before final retention receipt');b=archive.read(out/'capsule.tar.gz');put(out,'draft.json',referenced(q['draft']));report={'schema_version':1,'kind':'whole-post-B2-capsule-byte-retention-not-authority','original_root':str(root),'B':q['B'],'A':A,'binding':binding,'comparison_release':q['comparison_release'],'draft_sha256':digest(archive.read(out/'draft.json')),'archive_sha256':digest(b),'archive_bytes':len(b),'members':full,'files':sum(r['kind']=='file' for r in full),'directories':sum(r['kind']=='directory' for r in full),'logical_bytes':sum(r.get('bytes',0) for r in full),'runtime_store_copied':False,'financial_stores_copied':False,'requires_actual_helper_exit0':True,'actual_remote_recovery':False};jsonput(out,'retention.json',report);return {'status':'retained-bytes-only','retention':ref(out/'retention.json')}

def recover(q):
 require(set(q)=={'repository','remote_commit','retention','archive','draft','code','destination'},'exact recovery request');sha1(q['remote_commit']);repository=archive.direct(q['repository']);out=archive.direct(q['destination']);out.mkdir(exist_ok=False);git=Git(out/'git-logs');commit=q['remote_commit'];remote=git(repository,'ls-remote','origin','refs/heads/'+BRANCH).decode().split();require(remote==[commit,'refs/heads/'+BRANCH],'actual remote branch HEAD differs');url=git(repository,'remote','get-url','origin').decode().strip();repo=out/'repository.git';git(out,'init','--bare',str(repo));git(repo,'config','gc.auto','0');git(repo,'remote','add','origin',url);git(repo,'config','remote.origin.promisor','true');git(repo,'config','remote.origin.partialclonefilter','blob:none');git(repo,'fetch','--no-tags','--depth=1','--filter=blob:none','origin',commit);require(git(repo,'rev-parse','FETCH_HEAD').decode().strip()==commit,'fresh fetched commit differs')
 selected=[q['retention'],q['archive'],q['draft'],*q['code']];require(7<=len(selected)<=16 and len({x['path'] for x in selected})==len(selected),'complete selected source/retention set');saved={}
 for item in selected:
  name=str(archive.relative(item['path']));b=git(repo,'show',commit+':'+name,allow_lazy=True);require(len(b)==item['bytes']<=MAX and digest(b)==item['sha256'] and archive.read(repository/name)==b,'fresh remote/original selected bytes differ');saved[name]=b
 require({Path(r['path']).name for r in q['code']}=={'retention01.py','archive01.py','owned_io.py','PROTOCOL01.md'},'exact code/protocol source closure required')
 for item in q['code']:
  require(saved[item['path']]==archive.read(Path(__file__).parent/Path(item['path']).name),'executing helper/source closure differs')
 for item in selected:put(out,f'selected-{selected.index(item):02d}',saved[item['path']])
 report=json.loads(saved[q['retention']['path']]);b=saved[q['archive']['path']];require(digest(b)==report['archive_sha256'] and len(b)==report['archive_bytes'],'actual retained archive pin');require(digest(saved[q['draft']['path']])==report['draft_sha256'],'retained original draft differs');put(out,'capsule.tar.gz',b);root=out/'source';unpack(out/'capsule.tar.gz',root,report['members']);binding=validate(root,report['B'],json.loads(saved[q['draft']['path']]),git,report['comparison_release']);require(binding==report['binding'],'recovered structural bindings differ');require(git(repository,'ls-remote','origin','refs/heads/'+BRANCH).decode().split()==remote,'remote branch changed during recovery');receipt={'schema_version':1,'status':'actual-remote-selected-blobs-and-whole-B-capsule-byte-recovery','remote_commit':commit,'selected':selected,'original_root':report['original_root'],'recovered_root':str(root),'B':report['B'],'binding':binding,'full_members':len(report['members']),'requires_actual_helper_exit0':True,'restoration_creates_no_authority':True,'numerical_execution':False,'runtime_and_financial_stores_excluded':True};jsonput(out,'recovery.json',receipt);return receipt

def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['retain','recover']);p.add_argument('--request',required=True);p.add_argument('--request-sha256',required=True);a=p.parse_args();q=json.loads(referenced({'path':a.request,'sha256':a.request_sha256}));result=retain(q) if a.mode=='retain' else recover(q);print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
