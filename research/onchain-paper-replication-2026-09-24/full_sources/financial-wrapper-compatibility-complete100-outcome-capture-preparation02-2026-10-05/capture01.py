"""One closed engineering outcome, opaque complete non-Git trees; no fitting authority."""
from pathlib import Path
import hashlib,json,os,stat,sys,time,shutil
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE/'utilities'))
import recovery_pax01 as R
ROOT=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
PARENT=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01')
SOURCE='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41'
IDENTITY='financial-wrapper-classification-eager-complete100-compatibility-20261004-01'
RAW=128*1024**2;GROUP=3*1024**2;PIECES=128;MEMBERS=32768
ROLES=('terminal','root_exit','cleanup','independent_disposition','source407_baseline')
def boundary(start,reserve=0):
 R.require(time.monotonic()-start<120,'capture deadline');R.require(shutil.disk_usage(HERE).free-reserve>=R.FLOOR,'10GiB remaining floor')
def inventory(root,exclude_git=False):
 """Reuse complete typed scan on each original top-level subtree; exclude only CAP/.git."""
 R.require(root.is_absolute() and root.resolve()==root,'canonical original root');pin=R.sig(root.lstat());members=[];names=sorted(p.name for p in root.iterdir())
 for name in names:
  R.path_name(name);p=root/name;s=p.lstat()
  if exclude_git and name=='.git':
   R.require(stat.S_ISDIR(s.st_mode) and p.resolve()==p,'original Git directory required');continue
  if stat.S_ISDIR(s.st_mode):
   m=R.scan(p);members.append({'path':name,'kind':'directory','mode':m['root_mode']});members.extend({**r,'path':name+'/'+r['path']} for r in m['members'])
  else:
   raw=R.read(root,name);R.require(R.sig(p.lstat())==R.sig(s),'original leaf changed');members.append({'path':name,'kind':'file','mode':stat.S_IMODE(s.st_mode),'bytes':len(raw),'sha256':R.digest(raw)})
  R.require(len(members)<=MEMBERS,'whole original count')
 R.require(R.sig(root.lstat())==pin and sorted(p.name for p in root.iterdir())==names,'original root membership changed')
 m={'schema_version':1,'root_mode':stat.S_IMODE(root.lstat().st_mode),'members':sorted(members,key=lambda r:r['path'])};R.validate(m);return m

def signatures(root,m):
 paths=[root]+[root/r['path'] for r in m['members']];pins={}
 for p in paths:
  R.require(p.resolve()==p,'original path redirected');s=p.lstat();R.require(stat.S_ISDIR(s.st_mode) or (stat.S_ISREG(s.st_mode) and s.st_nlink==1),'ordinary original');pins[str(p)]=R.sig(s)
 return pins

def unchanged(pins):
 for n,pin in pins.items():
  p=Path(n);R.require(p.resolve()==p and R.sig(p.lstat())==pin,'retained original/evidence signature changed')

def plan(scopes):
 pieces=[];current=[];logical=0
 for role,m in sorted(scopes.items()):
  R.validate(m)
  for row in m['members']:
   if row['kind']!='file':continue
   R.require(row['bytes']<=GROUP,'original body exceeds fixed 3MiB group; retain and refuse')
   length=row['bytes']
   if current and (logical+length>GROUP or len(current)>=256):pieces.append(current);current=[];logical=0
   current.append({'role':role,'path':row['path'],'bytes':length,'sha256':row['sha256']});logical+=length
 if current:pieces.append(current)
 R.require(len(pieces)<=PIECES and sum(x['bytes'] for p in pieces for x in p)<=RAW,'finite complete raw population')
 return pieces

def write(path,raw,start):
 R.require(len(raw)<=R.FILE,'physical file limit');boundary(start,len(raw)+8192)
 with R.new_file(path) as fd:
  off=0
  while off<len(raw):n=os.write(fd,raw[off:]);R.require(n>0,'complete write');off+=n
  os.fsync(fd)

def capture(roots,output,start,evidence_pins=None):
 """Utility only. Public run authenticates terminal evidence before this call."""
 R.require(output.is_absolute() and output.parent.resolve()==output.parent and not os.path.lexists(output),'fresh output');boundary(start,RAW*2)
 scopes={role:inventory(root,role=='capsule') for role,root in roots.items()};pins=dict(evidence_pins or {})
 for role,root in roots.items():pins.update(signatures(root,scopes[role]))
 R.require(sum(len(m['members']) for m in scopes.values())<=MEMBERS,'combined original count')
 grouping=plan(scopes);output.mkdir(mode=0o700);records=[]
 for i,group in enumerate(grouping):
  boundary(start);shard=output/('piece-%03d'%i);shard.mkdir(mode=0o700);mapped=[]
  for j,item in enumerate(group):
   raw=R.read(roots[item['role']],item['path']);R.require(len(raw)==item['bytes'] and R.digest(raw)==item['sha256'],'original full body pin')
   name='body-%04d.bin'%j;write(shard/name,raw,start);mapped.append({**item,'member':name})
  m=R.scan(shard);R.require(sum(r.get('bytes',0) for r in m['members'])<=GROUP,'3MiB raw shard');write(output/('piece-%03d.json'%i),R.encode(m),start)
  # <=256 short flat names: <=3MiB payload + <=256*1024 framing + record padding <4MiB.
  tar_bound=((sum(512+((r['bytes']+511)//512)*512 for r in m['members'])+1024+10239)//10240)*10240
  R.require(tar_bound+tar_bound//1000+65536<R.FILE,'conservative gzip framing bound')
  archive=R.pack(shard,m,output/('piece-%03d.tar.gz'%i));boundary(start);records.append({'id':i,'manifest':'piece-%03d.json'%i,'archive':'piece-%03d.tar.gz'%i,'archive_pin':archive,'bodies':mapped,'tar_bound':tar_bound})
 for role,root in roots.items():R.require(inventory(root,role=='capsule')==scopes[role],'complete original late membership/body rejoin')
 result={'schema_version':1,'kind':'complete-terminal-opaque-sharded-capture-v1','originals':{r:{'root':str(roots[r]),'manifest':m} for r,m in scopes.items()},'pieces':records,'exclusions':{'capsule':['.git'],'parent':[]},'Git407':'separate authenticated baseline; not captured here','POSIX_instantiation':False,'numerical_authority':False}
 write(output/'CAPTURE01.json',R.encode(result),start)
 # Receipt close is not the success boundary: rejoin the complete retained outputs.
 names={'CAPTURE01.json'}
 for row in records:names.update({'piece-%03d'%row['id'],row['manifest'],row['archive']})
 pins[str(output)]=R.sig(output.lstat())
 R.require(set(p.name for p in output.iterdir())==names,'exact final output namespace')
 for row in records:
  shard=output/('piece-%03d'%row['id']);mp=output/row['manifest'];ap=output/row['archive']
  pins[str(mp)]=R.sig(mp.lstat());pins[str(ap)]=R.sig(ap.lstat())
  raw=R.read(output,row['manifest']);R.require(R.digest(raw)==row['archive_pin']['manifest_sha256'],'retained manifest changed');m=json.loads(raw)
  pins.update(signatures(shard,m));R.same(shard,m)
  raw=R.read(output,row['archive']);R.require(len(raw)==row['archive_pin']['bytes'] and R.digest(raw)==row['archive_pin']['sha256'],'retained archive changed')
 cp=output/'CAPTURE01.json';pins[str(cp)]=R.sig(cp.lstat());R.require(R.read(output,cp.name)==R.encode(result),'final capture receipt changed')
 R.require(set(p.name for p in output.iterdir())==names,'late final output namespace changed')
 # All owned reads/iterators closed before resource sampling and final descriptor-free join.
 boundary(start);unchanged(pins);return result

def ref_read(ref,pins):
 R.require(type(ref)is dict and set(ref)=={'path','sha256'},'actual evidence reference required');p=Path(ref['path']);R.require(p.is_absolute() and p.resolve()==p,'canonical evidence');before=R.sig(p.lstat());raw=R.read(p.parent,p.name);R.require(R.digest(raw)==ref['sha256'] and R.sig(p.lstat())==before,'actual evidence pin');pins[str(p)]=before;return raw

def run(request,request_hash,release,release_hash):
 start=time.monotonic();pins={};raw=ref_read({'path':str(request),'sha256':request_hash},pins);q=json.loads(raw)
 R.require(q['schema_version']==1 and q['identity']==IDENTITY and q['source']==SOURCE and q['status']=='ROOT_FROZEN_TERMINAL_BYTE_CAPTURE','frozen closed outcome required')
 R.require(q['roots']=={'capsule':str(CAP),'parent':str(PARENT)} and set(q['evidence'])==set(ROLES),'fixed complete roots/evidence roles')
 for role in ROLES:ref_read(q['evidence'][role],pins)
 rel=json.loads(ref_read({'path':str(release),'sha256':release_hash},pins))
 R.require(rel=={'schema_version':1,'decision':'ACCEPTED_EXACT_TERMINAL_OUTCOME_BYTE_CAPTURE','request_sha256':request_hash,'source_sha256':R.digest(R.read(HERE,'capture01.py')),'evidence':q['evidence'],'terminal_and_root_exit_authenticated':True,'all_owned_processes_and_cgroup_absent':True,'independent_disposition_authenticated':True,'numerical_authority':False},'genuine different-author exact release required')
 # Recheck every original recorded PID and cgroup path immediately before capture.
 R.require(type(q['owned_pids'])is list and len(q['owned_pids'])<=128 and all(type(p)is int and p>0 for p in q['owned_pids']),'actual closed process census')
 R.require(all(not Path('/proc',str(p)).exists() for p in q['owned_pids']),'owned PID still present')
 R.require(type(q['cgroup_paths'])is list and 1<=len(q['cgroup_paths'])<=16,'actual original cgroup paths')
 for name in q['cgroup_paths']:
  p=Path(name);R.require(p.is_absolute() and p.is_relative_to('/sys/fs/cgroup') and '..' not in p.parts and not os.path.lexists(p),'owned cgroup still present')
 parent=json.loads(ref_read(q['parent_request'],pins));R.require(parent['identity']==IDENTITY and parent['source']==SOURCE and parent['design_source']==SOURCE,'actual original source/identity')
 R.require(type(parent['source_files'])is dict and len(parent['source_files'])==354,'actual registered source pins')
 for name,h in parent['source_files'].items():R.require(R.digest(R.read(CAP,name))==h,'current registered source body differs')
 git_head=R.read(CAP,'.git/HEAD').decode().strip()
 if git_head.startswith('ref: '):git_head=R.read(CAP,'.git/'+R.path_name(git_head[5:])).decode().strip()
 R.require(git_head==SOURCE,'current Git HEAD differs from separately recovered407 source')
 # Public output is one fresh fixed Root namespace, outside both immutable inputs.
 output=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05'
 result=capture({'capsule':CAP,'parent':PARENT},output,start,pins);return result
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--request-sha256',required=True);p.add_argument('--release',type=Path,required=True);p.add_argument('--release-sha256',required=True);a=p.parse_args();run(a.request,a.request_sha256,a.release,a.release_sha256)
