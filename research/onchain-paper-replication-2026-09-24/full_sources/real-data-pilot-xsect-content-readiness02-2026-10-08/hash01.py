"""One bounded hash-only xsect snapshot; no decoding, transfer, archive or removal."""
import datetime,hashlib,importlib.util,json,os,resource,stat,time,traceback
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[3];ROOT=Path('/home/malecada/master_thesis/TradingAgents/data/xsect');OLD=H.parent/'real-data-pilot-xsect-relocation-readiness01-2026-10-08/INVENTORY01.json';P=R/'tradingagents/research/onchain_replication/preservation.py';PREP=H.parent/'real-data-pilot-final22-2026-10-08/PREPARATION_RESULT02.json'
MIB=1024**2;GIB=1024**3;LIMIT=128*MIB;SLACK=128*MIB;BEGIN=time.monotonic();begin=datetime.datetime.now(datetime.timezone.utc).isoformat();progress={'files':0,'bytes':0};reads=0;min_mem=2**63;min_disk=2**63
sourcepin=hashlib.sha256(P.read_bytes()).hexdigest();preppin=hashlib.sha256(PREP.read_bytes()).hexdigest();growth=json.loads(PREP.read_bytes())['builder03_result']['capacity_lower_bounds']['declared_allocated_growth_bytes'];mem_floor=5*GIB//2+LIMIT;disk_floor=growth+10*GIB+SLACK

def save(name,value):
 with (H/name).open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
def headroom():
 global min_mem,min_disk
 available=next(int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'));v=os.statvfs(ROOT);disk=v.f_bavail*v.f_frsize;min_mem=min(min_mem,available);min_disk=min(min_disk,disk)
 if available<mem_floor or disk<disk_floor:raise RuntimeError('headroom below reserved pilot floor')
 if time.monotonic()-BEGIN>1200:raise RuntimeError('finite1200second preparation limit reached')
 return {'mem_available_bytes':available,'disk_available_bytes':disk}
def safe(p):
 for c in p.parts:
  n=c.lower()
  if n in {'keys','apis','.ssh','.aws','.gnupg','hf_token.txt','credentials','credentials.json','id_rsa','id_ed25519','secrets','secrets.json'} or n.startswith('.env') or any(v in n for v in ('private_key','private-key','access_token','secret_key','credential')):raise ValueError('secret-named component refused')
def meta(p):
 safe(p);s=p.lstat()
 if p.resolve(strict=True)!=p or stat.S_ISLNK(s.st_mode):raise ValueError('noncanonical or linked path refused')
 kind='regular' if stat.S_ISREG(s.st_mode) else 'directory' if stat.S_ISDIR(s.st_mode) else 'other'
 if kind=='other' or (kind=='regular' and s.st_nlink!=1):raise ValueError('special or multiply-linked source refused')
 return {'relative_path':str(p.relative_to(ROOT)),'kind':kind,'mode':s.st_mode,'device':s.st_dev,'inode':s.st_ino,'nlink':s.st_nlink,'logical_bytes':s.st_size,'allocated_bytes':s.st_blocks*512,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns}
def scan():
 rows=[];stack=[ROOT];seen=set()
 while stack:
  headroom();p=stack.pop();row=meta(p);key=(row['device'],row['inode'])
  if key in seen:raise ValueError('duplicate inode refused')
  seen.add(key);rows.append(row)
  if len(rows)>100000:raise ValueError('inventory bound exceeded')
  if row['kind']=='directory':
   with os.scandir(p) as it:
    for e in it:safe(Path(e.path));stack.append(Path(e.path))
 return sorted(rows,key=lambda v:v['relative_path'])
def fmatch(fd,row):
 s=os.fstat(fd)
 return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_blocks*512)==tuple(row[k] for k in ('device','inode','mode','nlink','logical_bytes','mtime_ns','ctime_ns','allocated_bytes'))
class CheckedRead:
 def __init__(self,p,row):self.p=p;self.row=row;self.fd=None
 def open(self,mode):
  assert mode=='rb';assert meta(self.p)==self.row
  self.fd=os.open(self.p,os.O_RDONLY|os.O_NOFOLLOW);assert fmatch(self.fd,self.row);return self
 def __enter__(self):return self
 def read(self,n):
  global reads
  assert n==MIB;headroom();assert meta(self.p)==self.row and fmatch(self.fd,self.row)
  data=os.read(self.fd,n);reads+=1
  assert meta(self.p)==self.row and fmatch(self.fd,self.row)
  return data
 def __exit__(self,*args):
  try:
   assert meta(self.p)==self.row and fmatch(self.fd,self.row)
   if hasattr(os,'posix_fadvise'):os.posix_fadvise(self.fd,0,0,os.POSIX_FADV_DONTNEED)
  finally:os.close(self.fd)
try:
 initial=headroom();cpus=sorted(os.sched_getaffinity(0)-{0,1});assert cpus,'no nonpilot CPU available';cpu=cpus[0];os.sched_setaffinity(0,{cpu});os.nice(10);resource.setrlimit(resource.RLIMIT_AS,(LIMIT,LIMIT));resource.setrlimit(resource.RLIMIT_FSIZE,(32*MIB,32*MIB))
 save('EXECUTION_START01.json',{'at':begin,'pid':os.getpid(),'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'address_space_limit_bytes':LIMIT,'max_read_bytes':MIB,'max_seconds':1200,'max_entries':100000,'initial':initial,'mem_required_bytes':mem_floor,'disk_required_bytes':disk_floor,'modeled_growth_bytes':growth,'metadata_slack_bytes':SLACK,'preservation_source_sha256':sourcepin,'preparation_sha256':preppin})
 before=scan();save('BEFORE_INVENTORY01.json',before)
 old=json.loads(OLD.read_bytes());previous={x['relative_path']:x for x in old['entries']};current={x['relative_path']:x for x in before}
 differences={'added':sorted(set(current)-set(previous)),'removed':sorted(set(previous)-set(current)),'changed':[k for k in current.keys()&previous.keys() if current[k]!=previous[k]]};save('PREVIOUS_METADATA_DIFF01.json',differences)
 spec=importlib.util.spec_from_file_location('existing_preservation_hash_only',P);pres=importlib.util.module_from_spec(spec);spec.loader.exec_module(pres);assert pres.BLOCK==MIB
 rows=[]
 with (H/'PARTIAL_HASH_ROWS01.jsonl').open('x') as partial:
  for row in before:
   if row['kind']!='regular':continue
   path=ROOT/row['relative_path'];assert row['logical_bytes']<=256*MIB
   checked=CheckedRead(path,row);saved=pres.Path;pres.Path=lambda value:checked if value==path else (_ for _ in ()).throw(ValueError('unexpected hashing path'))
   try:digest=pres.sha256(path)
   finally:pres.Path=saved
   value={**row,'source_path':str(path),'resolved_path':str(path),'bytes':row['logical_bytes'],'expected_sha256':digest,'posix_mode':format(stat.S_IMODE(row['mode']),'04o')};rows.append(value);partial.write(json.dumps(value,sort_keys=True)+'\n');partial.flush();progress['files']+=1;progress['bytes']+=row['logical_bytes']
  os.fsync(partial.fileno())
 after=scan();save('AFTER_INVENTORY01.json',after);assert before==after,'whole source tree changed during hashing';assert hashlib.sha256(P.read_bytes()).hexdigest()==sourcepin
 batches=pres.plan_batches(rows,max_raw_bytes=256*MIB,max_members=4096);save('CONTENT_ROWS01.json',rows);save('BATCHES01.json',{'max_raw_bytes':256*MIB,'max_members':4096,'batches':batches});save('DIRECTORIES01.json',[{**x,'source_path':str(ROOT/x['relative_path']),'posix_mode':format(stat.S_IMODE(x['mode']),'04o')} for x in before if x['kind']=='directory'])
 result={'status':'STABLE_HASH_SNAPSHOT_ONLY','root':str(ROOT),'at_start':begin,'at_end':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-BEGIN,**progress,'directories':sum(x['kind']=='directory' for x in before),'batches':len(batches),'read_calls':reads,'max_raw_batch_bytes':max(b['raw_bytes'] for b in batches),'max_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'user_cpu_seconds':resource.getrusage(resource.RUSAGE_SELF).ru_utime,'system_cpu_seconds':resource.getrusage(resource.RUSAGE_SELF).ru_stime,'min_mem_available_bytes':min_mem,'min_disk_available_bytes':min_disk,'source_sha256':sourcepin,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'previous_metadata_diff':differences,'qualification':'Hash-only stable per-read/whole-tree metadata observations, not writer exclusion, remote recovery, deletion permission, provenance/vintage validation or financial evidence. No payload decoding, archive staging, network, numerical import or native unit.'};save('RESULT01.json',result);print(json.dumps(result,sort_keys=True))
except BaseException as error:
 save('REFUSAL01.json',{'status':'REFUSED_OR_PARTIAL','error_type':type(error).__name__,'reason':str(error),'progress':progress,'elapsed_seconds':time.monotonic()-BEGIN,'min_mem_available_bytes':min_mem,'min_disk_available_bytes':min_disk,'qualification':'Original sources preserved; partial hashes not full snapshot acceptance.'});traceback.print_exc();raise
