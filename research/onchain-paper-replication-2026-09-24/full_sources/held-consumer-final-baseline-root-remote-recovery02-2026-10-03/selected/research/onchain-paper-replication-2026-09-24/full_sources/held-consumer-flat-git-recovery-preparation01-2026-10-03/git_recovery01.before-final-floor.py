"""Offline recovered-flat Git object proof. No research/runtime/origin authority."""
import argparse,hashlib,json,os,re,shutil,stat,time
from pathlib import Path,PurePosixPath
import archive03 as a
from owned_io import _cleanup
from bounded_git_fd01 import git
SOURCE=a.SOURCE
C6='c6b568d4b1c177ab94ac37fbad462c2decc721c0'
HEX40=re.compile('[0-9a-f]{40}');HEX64=re.compile('[0-9a-f]{64}')
LOOSE=re.compile(r'\.git/objects/[0-9a-f]{2}/[0-9a-f]{38}')
PACK=re.compile(r'\.git/objects/pack/pack-[0-9a-f]{40}\.(pack|idx)')
MAX_CALLS=4096;WALL=300;TOTAL=128*1024**2
require=a.require

def checked_json(root,name,pin):
 require(type(pin) is str and HEX64.fullmatch(pin),'explicit JSON SHA256 required');raw=a.read(root,name);require(a.digest(raw)==pin,'JSON pin differs');value=json.loads(raw);require(a.encode(value)==raw,'canonical JSON required');return value

def row_check(r,commit=False):
 fields={'path','git_mode','object','bytes','sha256'}|({'commit'} if commit else set())
 require(type(r) is dict and set(r)==fields,'lookup row fields');a.path_name(r['path']);require('\n' not in r['path'] and '\r' not in r['path'],'Git path framing')
 require(r['git_mode'] in ('100644','100755') and type(r['bytes']) is int and 0<=r['bytes']<=a.FILE and type(r['object']) is str and HEX40.fullmatch(r['object']) and type(r['sha256']) is str and HEX64.fullmatch(r['sha256']),'lookup type/extent/pins')
 if commit:require(type(r['commit']) is str and HEX40.fullmatch(r['commit']),'lookup commit')

class FlatView:
 def __init__(self,path):self.path=Path(path);self.fd=None;self.pin=None;self.maps={};self.manifests={};self.expected=set()
 @property
 def dest(self):return self.path
 def begin(self):
  p=self.path;require(p.is_absolute() and p.resolve()==p,'canonical existing flat source');self.fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);s=os.fstat(self.fd);self.pin=(s.st_dev,s.st_ino,s.st_mode,s.st_uid);require(s.st_uid==os.geteuid() and stat.S_IMODE(s.st_mode)==0o700,'private flat source');self.check()
 def check(self):
  s=os.fstat(self.fd);p=self.path.lstat();require(self.path.resolve()==self.path and self.pin==(s.st_dev,s.st_ino,s.st_mode,s.st_uid)==(p.st_dev,p.st_ino,p.st_mode,p.st_uid),'flat source namespace changed')
 def body(self,name):
  self.check();r={r['path']:r for r in self.manifests['capsule']['members']}[name];require(r['kind']=='file','regular recovered body required');raw=a.read(self.path,self.maps['capsule'][name]);require(len(raw)==r['bytes'] and a.digest(raw)==r['sha256'],'recovered flat body differs');self.check();return raw
 def finish(self):
  self.check();it=None;seen=set()
  try:
   it=os.scandir(self.fd)
   for e in it:require(e.name in self.expected and len(seen)<65540,'foreign flat member');seen.add(e.name)
   require(seen==self.expected,'missing flat member');self.check()
  finally:_cleanup(() if it is None else (it.close,))
 def close(self):
  if self.fd is not None:fd=self.fd;self.fd=None;_cleanup((lambda:os.close(fd),))

def chain(view,bundle,request_file,request_sha256,capture_sha256,recovery_sha256):
 """Authenticates both whole archive roles; never reads the original capsule body."""
 bundle=Path(bundle);request_file=Path(request_file);q=checked_json(request_file.parent,request_file.name,request_sha256);a.request(q)
 c=checked_json(bundle,'capture.json',capture_sha256);require(set(c)=={'schema_version','request_sha256','source','archives','scope'} and c['schema_version']==1 and c['source']==SOURCE and c['request_sha256']==request_sha256 and set(c['archives'])=={'capsule','external'},'capture chain')
 rec=checked_json(view.path,'recovery.json',recovery_sha256);require(rec['schema_version']==1 and rec['status']=='fresh-flat-archival-recovery-not-origin-proof' and rec['request_sha256']==request_sha256 and rec['capture_sha256']==capture_sha256 and set(rec['results'])=={'capsule','external'},'recovery chain')
 for flag in ('instantiated_posix_tree','recovered_tree_git_join','runtime_package_bodies_recovered','outside_stores_recovered','research_authority'):require(rec[flag] is False,'archival scope flag')
 view.expected={'recovery.json'}
 for role in ('capsule','external'):
  manifest=q[role+'_manifest'];a.validate(manifest);require(checked_json(bundle,role+'-manifest.json',q[role+'_manifest_sha256'])==manifest,'whole manifest chain');info=c['archives'][role]
  require(set(info)=={'bytes','sha256','manifest_sha256'} and type(info['bytes']) is int and 0<=info['bytes']<=a.FILE and info['manifest_sha256']==q[role+'_manifest_sha256'],'archive manifest join');raw=a.read(bundle,role+'.tar.gz');require(len(raw)==info['bytes'] and a.digest(raw)==info['sha256'],'archive byte join')
  result=rec['results'][role];meta_name=role+'-metadata.json';require(result['metadata_file']==meta_name and result['status']=='fresh-flat-archival-recovery-not-origin-proof' and result['archive_sha256']==info['sha256'] and result['manifest_sha256']==info['manifest_sha256'] and result['members']==len(manifest['members']) and result['root_mode']==manifest['root_mode'],'role recovery join')
  for flag in ('instantiated_posix_tree','recovered_tree_git_join','runtime_package_bodies_recovered','outside_stores_recovered','research_authority'):require(result[flag] is False,'role scope flag')
  meta=checked_json(view.path,meta_name,result['metadata_sha256']);require(set(meta)=={'schema_version','manifest','flat_members','archive'} and meta['schema_version']==1 and meta['manifest']==manifest and meta['archive']==info,'flat typed metadata join')
  files=[r for r in manifest['members'] if r['kind']=='file'];mapping={r['path']:role+'-'+str(i).zfill(5)+'.body' for i,r in enumerate(files)};require(meta['flat_members']==mapping and result['regular_bodies']==len(files),'complete flat body map');view.maps[role]=mapping;view.manifests[role]=manifest;view.expected|=set(mapping.values())|{meta_name}
  sink=a.ExactSink(raw);a.flat_tar_stream(view,manifest,mapping,sink);require(sink.count==len(raw) and sink.hash.hexdigest()==info['sha256'],'complete exact compressed reencoding')
 view.finish();return q

class ObjectStore:
 """Current acquired private namespace, never inode-birth or POSIX-mode restoration."""
 def __init__(self,path):self.path=Path(path);self.records={};self.fds=[];self.names={};self.files={};self.bytes=0;self.calls=0;self.returned=0;self.deadline=time.monotonic()+WALL
 def budget(self):require(time.monotonic()<self.deadline and self.calls<=MAX_CALLS and self.bytes<=TOTAL and self.returned<=TOTAL,'finite Git proof budget')
 def acquire(self,name,create=False):
  if name:
   parent=str(PurePosixPath(name).parent);parent='' if parent=='.' else parent;pfd=self.check(parent);leaf=Path(name).name;p=self.path/name
   if create:os.mkdir(leaf,0o700,dir_fd=pfd)
   fd=os.open(leaf,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=pfd)
  else:
   p=self.path;require(p.is_absolute() and p.resolve()==p,'canonical supplied empty store');fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
  self.fds.append(fd);s=os.fstat(fd);require(s.st_uid==os.geteuid() and stat.S_IMODE(s.st_mode)==0o700,'acquired namespace must be private0700');self.records[name]=(fd,(s.st_dev,s.st_ino,s.st_mode,s.st_uid));self.names[name]=set();self.check(name);self.check_names(name)
  if name:self.names[parent].add(leaf)
  return fd
 def check(self,name=''):
  fd,pin=self.records[name];p=self.path/name;s=os.fstat(fd);t=p.lstat();require(p.resolve()==p and pin==(s.st_dev,s.st_ino,s.st_mode,s.st_uid)==(t.st_dev,t.st_ino,t.st_mode,t.st_uid),'acquired Git namespace changed')
  if name:self.check(str(PurePosixPath(name).parent) if '/' in name else '')
  return fd
 def check_names(self,name):
  fd=self.check(name);it=None;seen=set()
  try:
   it=os.scandir(fd)
   for e in it:require(e.name in self.names[name] and len(seen)<32772,'foreign Git namespace entry');seen.add(e.name)
   require(seen==self.names[name],'missing Git namespace entry')
  finally:_cleanup(() if it is None else (it.close,))
 def begin(self):
  self.acquire('');self.acquire('objects',True);self.acquire('refs',True);self.create('HEAD',b'ref: refs/heads/unborn\n');self.create('config',b'[core]\nrepositoryformatversion = 0\nbare = true\n')
 def create(self,name,raw):
  a.path_name(name);require(len(raw)<=a.FILE and self.bytes+len(raw)<=TOTAL,'object store file/total bounds');self.budget();parent=str(PurePosixPath(name).parent);parent='' if parent=='.' else parent;fd=None;pfd=self.check(parent);leaf=Path(name).name
  try:
   fd=os.open(leaf,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=pfd);off=0
   while off<len(raw):n=os.write(fd,raw[off:]);require(n>0,'Git object short write');off+=n
   os.fsync(fd);os.lseek(fd,0,os.SEEK_SET);h=hashlib.sha256();count=0
   while True:
    b=os.read(fd,min(65536,len(raw)-count+1))
    if not b:break
    count+=len(b);require(count<=len(raw),'Git object grew');h.update(b)
   s=os.fstat(fd);require(count==len(raw) and h.hexdigest()==a.digest(raw) and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and a.sig(s)==a.sig(os.stat(leaf,dir_fd=pfd,follow_symlinks=False))==a.sig((self.path/name).lstat()),'Git object creation/readback/inode join');self.check(parent);os.fsync(pfd);self.names[parent].add(leaf);self.files[name]={'bytes':len(raw),'sha256':a.digest(raw)};self.bytes+=len(raw);self.storage()
  finally:_cleanup(() if fd is None else (lambda:os.close(fd),))
 def storage(self):
  allocated=sum(os.fstat(fd).st_blocks*512 for fd,pin in self.records.values());logical=0
  for name,r in self.files.items():
   s=(self.path/name).lstat();require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==r['bytes'],'Git store storage type/extent');logical+=s.st_size;allocated+=s.st_blocks*512
  require(logical==self.bytes and logical<=TOTAL and allocated<=TOTAL,'128MiB logical/allocated Git store bound');return allocated
 def verify_files(self):
  self.budget();self.storage()
  for name in self.records:self.check_names(name)
  for name,r in self.files.items():raw=a.read(self.path,name);require(len(raw)==r['bytes'] and a.digest(raw)==r['sha256'],'Git store file changed')
 def query(self,args,request=b''):
  require((args==['cat-file','--batch']) or (len(args) in (4,6) and args[:3]==['ls-tree','-r','-z'] and HEX40.fullmatch(args[3]) and (len(args)==4 or args[4]=='--')),'selected read-only Git operation');require(len(request)<=65536,'Git request bound');self.budget();self.calls+=1;require(self.calls<=MAX_CALLS,'Git call bound')
  for name in self.records:self.check_names(name)
  result=git(self.check(),['--no-replace-objects','--literal-pathspecs','--git-dir=.',*args],request,cap=8*1024**2);self.returned+=len(result);self.budget()
  for name in self.records:self.check_names(name)
  return result
 def object(self,ref,kind):
  require(type(ref) is str and '\n' not in ref and '\r' not in ref and len(ref.encode())<=4096,'Git ref framing');raw=self.query(['cat-file','--batch'],(ref+'\n').encode());end=raw.find(b'\n');require(0<end<128,'Git batch header');head=raw[:end].split();require(len(head)==3 and head[1].decode()==kind and head[2].isdigit(),'Git missing/object type');size=int(head[2]);body=raw[end+1:-1];oid=head[0].decode();require(size<=a.FILE and len(body)==size and raw[-1:]==b'\n' and HEX40.fullmatch(oid) and hashlib.sha1(kind.encode()+b' '+str(size).encode()+b'\0'+body).hexdigest()==oid,'Git object body/OID framing')
  if HEX40.fullmatch(ref):require(oid==ref,'Git requested OID differs')
  return oid,body
 def tree(self,commit,path=None):
  args=['ls-tree','-r','-z',commit]+([] if path is None else ['--',path]);raw=self.query(args);require(raw.endswith(b'\0') or raw==b'','Git tree framing');rows={}
  for item in raw.split(b'\0')[:-1]:
   left,name=item.split(b'\t',1);mode,kind,oid=left.decode().split();name=name.decode('utf-8','strict');a.path_name(name);require(kind=='blob' and mode in ('100644','100755') and HEX40.fullmatch(oid) and name not in rows,'Git tree regular type/mode/duplicate');rows[name]=(mode,oid)
  return rows
 def close(self):
  fds=self.fds;self.fds=[];_cleanup(tuple(lambda fd=fd:os.close(fd) for fd in reversed(fds)))

def populate(store,view):
 rows=[r for r in view.manifests['capsule']['members'] if r['kind']=='file' and (LOOSE.fullmatch(r['path']) or PACK.fullmatch(r['path']))];require(rows and len(rows)<=32768 and sum(r['bytes'] for r in rows)<=TOTAL,'finite recovered Git object files');selected={r['path'] for r in rows}
 for name in selected:
  if PACK.fullmatch(name):require(name.rsplit('.',1)[0]+('.idx' if name.endswith('.pack') else '.pack') in selected,'complete pack/index pair required')
 for r in rows:
  name=r['path'][5:];parent=str(PurePosixPath(name).parent)
  if parent not in store.records:store.acquire(parent,True)
  store.create(name,view.body(r['path']))
 store.verify_files();return [{'path':r['path'],'mode':r['mode'],'bytes':r['bytes'],'sha256':r['sha256']} for r in rows]

def verify_lookups(store,commit,rows,view=None,all_current=False):
 require(type(commit) is str and HEX40.fullmatch(commit) and type(rows) is list and 0<len(rows)<=1024,'finite lookup set');store.object(commit,'commit');seen=set();results=[];tree=store.tree(commit) if all_current else None
 for r in rows:
  row_check(r);require(r['path'] not in seen,'duplicate lookup path');seen.add(r['path']);actual=tree if tree is not None else store.tree(commit,r['path']);require(actual.get(r['path'])==(r['git_mode'],r['object']) and (tree is not None or set(actual)=={r['path']}),'Git tree path/mode/OID join');oid,body=store.object(commit+':'+r['path'],'blob');require(oid==r['object'] and len(body)==r['bytes'] and a.digest(body)==r['sha256'],'Git lookup body join')
  if view is not None:
   original={x['path']:x for x in view.manifests['capsule']['members']}[r['path']];require(original['kind']=='file' and original['bytes']==r['bytes'] and original['sha256']==r['sha256'] and r['git_mode']==('100755' if original['mode']&0o100 else '100644') and view.body(r['path'])==body,'current recovered body/semantic owner-executable mode join')
  results.append(r)
 if tree is not None:require(set(tree)==seen,'complete current Git membership')
 return results

def prove(spec):
 require(type(spec) is dict and set(spec)=={'schema_version','bundle','flat_root','request_file','request_sha256','capture_sha256','recovery_sha256','output_root','expected_file','expected_sha256'} and spec['schema_version']==1,'proof request schema')
 expected_file=Path(spec['expected_file']);e=checked_json(expected_file.parent,expected_file.name,spec['expected_sha256']);require(set(e)=={'schema_version','source','current','selected_c6','historical'} and e['schema_version']==1 and e['source']==SOURCE and type(e['current']) is list and len(e['current'])==246,'Root-frozen246 current lookup worksheet');require(e['selected_c6']['commit']==C6 and len(e['selected_c6']['rows'])==26,'Root-frozen selected26 C6')
 roots=[Path(spec[k]) for k in ('bundle','flat_root','output_root')];require(all(p.is_absolute() and p.resolve()==p for p in roots) and all(not x.is_relative_to(y) for i,x in enumerate(roots) for j,y in enumerate(roots) if i!=j),'separate canonical proof roots');require(shutil.disk_usage(roots[2]).free>=a.FLOOR,'10GiB proof disk floor');view=FlatView(roots[1]);store=ObjectStore(roots[2])
 try:
  view.begin();q=chain(view,roots[0],Path(spec['request_file']),spec['request_sha256'],spec['capture_sha256'],spec['recovery_sha256']);require(all(not roots[2].is_relative_to(Path(q[k])) and not Path(q[k]).is_relative_to(roots[2]) for k in ('capsule_root','external_root','output_root')),'proof store separate from original scopes');store.begin();objects=populate(store,view);current=verify_lookups(store,SOURCE,e['current'],view,True)
  regraw=view.body(q['registration']);require(a.digest(regraw)==q['registration_sha256'],'recovered registration join');reg=json.loads(regraw);exp=reg['experiments']['original-import-held-success-20261003-01'];refs=dict(exp['source_files']);require(len(refs)==204 and len(exp['inputs'])==33,'original source/input scope');refs[q['registration']]=q['registration_sha256'];lookup={r['path']:r['sha256'] for r in current};require(len(refs)==205 and all(lookup.get(n)==pin for n,pin in refs.items()),'all205 source/registration committed recovered joins')
  for ref in exp['inputs'].values():require(a.digest(view.body(ref['path']))==ref['sha256'],'all33 opaque input hashes')
  selected=verify_lookups(store,C6,e['selected_c6']['rows']);history=[]
  if e['historical'] is not None:
   h=e['historical'];require(set(h)=={'lookups','claims'} and len(h['lookups'])==638 and len(h['claims'])==4,'exact historical worksheet scope');groups={};seen=set()
   for r in h['lookups']:
    row_check(r,True);key=(r['commit'],r['path']);require(key not in seen,'duplicate history lookup');seen.add(key);groups.setdefault(r['commit'],[]).append({k:v for k,v in r.items() if k!='commit'})
   for commit,rows in groups.items():history.extend(dict(r,commit=commit) for r in verify_lookups(store,commit,rows))
   required=set();lookups={(r['commit'],r['path']):r for r in history}
   for claim in h['claims']:
    raw=view.body('research_runs/'+claim['identity']+'/claim.json');c=json.loads(raw);terminal=view.body('research_runs/'+claim['identity']+'/failed.json');t=json.loads(terminal);require(a.digest(raw)==claim['claim_sha256'] and a.digest(terminal)==claim['terminal_sha256'] and c['source']==claim['source'] and c['design_source']==claim['design_source'] and c['registration']==claim['registration'] and c['registration_sha256']==claim['registration_sha256'] and c['experiment_id']==t['experiment_id']==claim['identity'] and t['claim_sha256']==a.digest(raw) and t['status']=='failed','original four closed history joins');require(c['effective_attempt_budget']==claim['effective_budget'] and c['family']['attempt_budget']==2 and c['family']['prior_attempts']==0 and 'research_runs/'+claim['identity']+'/complete.json' not in view.maps['capsule'],'preserved failed history budget/disposition')
    selection=dict(c['experiment']['source_files']);selection[c['experiment']['charter']['path']]=c['experiment']['charter']['sha256']
    for name,pin in selection.items():require(lookups[(c['source'],name)]['sha256']==pin,'historical source/charter lookup');required.add((c['source'],name))
    for commit in (c['source'],c['design_source']):
     require(lookups[(commit,c['registration'])]['sha256']==c['registration_sha256'],'historical source/design registration');_,b=store.object(commit+':'+c['registration'],'blob');r=json.loads(b);require(r['program_id']==c['program_id'] and r['experiments'][claim['identity']]==c['experiment'],'original gate experiment join');required.add((commit,c['registration']))
   require(required==set(lookups),'complete original historical lookup union')
  view.finish();store.verify_files();require(shutil.disk_usage(store.path).free>=a.FLOOR,'final10GiBfloor')
  result={'schema_version':1,'status':'fresh-offline-Git-object-joins-from-authenticated-flat-bytes-not-origin-proof','request_sha256':spec['request_sha256'],'capture_sha256':spec['capture_sha256'],'recovery_sha256':spec['recovery_sha256'],'expected_sha256':spec['expected_sha256'],'source':SOURCE,'current_committed_files':len(current),'source_registration_joins':205,'opaque_inputs':33,'selected_c6_paths':len(selected),'historical_lookups':len(history),'historical_status':'verified exact638/four retained source/design gates' if history else 'unavailable; no exact historical worksheet supplied','object_files':objects,'git_operations':store.calls,'git_returned_bytes':store.returned,'full_c6_ancestry':False,'full_original_filesystem':False,'original_posix_modes_instantiated':False,'external_origin_proved':False,'runtime_recovered':False,'outside_stores_recovered':False,'research_authority':False}
  store.create('proof.json',a.encode(result));store.verify_files();return result
 finally:_cleanup((store.close,view.close))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--spec',type=Path,required=True);parser.add_argument('--spec-sha256',required=True);args=parser.parse_args();spec=checked_json(args.spec.parent.resolve(),args.spec.name,args.spec_sha256);prove(spec)
