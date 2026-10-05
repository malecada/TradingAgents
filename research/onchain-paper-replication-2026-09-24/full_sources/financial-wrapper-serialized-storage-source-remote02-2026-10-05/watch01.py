"""Fixed sampled whole writable-tree policy; no kernel aggregate-quota claim."""
import os,stat,time,shutil,sys,hashlib
from pathlib import Path
_io=Path(__file__).resolve().parent/'utilities/owned_io.py'
if hashlib.sha256(_io.read_bytes()).hexdigest()!='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb':raise ValueError('owned IO pin')
sys.path.insert(0,str(_io.parent))
import owned_io as IO
POLICY={'logical':64*1024**2,'allocated':96*1024**2,'members':32768,'depth':32,'file':4*1024**2,'sample_seconds':5,'floor':10*1024**3,'samples':8192}
def require(v,m):
 if not v:raise ValueError(m)
def signature(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_blocks)
class ChangingTree(ValueError):pass
def _sample(root,owned_fetch_objects=None):
 root=Path(root);require(root.is_absolute() and root.resolve()==root,'canonical owned root');begun=time.monotonic();rows=[];logical=allocated=0;saved={};device=root.stat().st_dev
 if owned_fetch_objects is not None:
  require(isinstance(owned_fetch_objects,Path) and owned_fetch_objects.is_absolute() and owned_fetch_objects.resolve()==owned_fetch_objects and owned_fetch_objects.name=='objects' and owned_fetch_objects.is_relative_to(root) and owned_fetch_objects!=root,'canonical owned fetch objects scope')
  scope=owned_fetch_objects.lstat();require(stat.S_ISDIR(scope.st_mode) and scope.st_dev==device,'owned fetch objects directory/device')
 def visit(p,depth):
  nonlocal logical,allocated
  require(depth<=POLICY['depth'] and time.monotonic()-begun<POLICY['sample_seconds'],'finite complete census');s=p.lstat();require(p.resolve()==p and s.st_dev==device and (stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode)),'owned tree type/path/device');require(len(rows)<POLICY['members'],'whole member cap');saved[p]=signature(s);allocated+=s.st_blocks*512
  if stat.S_ISREG(s.st_mode):
   require(s.st_size<=POLICY['file'],'owned per-file/hardlink bound')
   if s.st_nlink!=1:
    require(owned_fetch_objects is not None and p.is_relative_to(owned_fetch_objects) and s.st_nlink>1,'owned per-file/hardlink bound')
    raise ChangingTree('owned regular hardlink observed: '+str(p.relative_to(root))+' nlink='+str(s.st_nlink))
   logical+=s.st_size
  require(logical<=POLICY['logical'] and allocated<=POLICY['allocated'],'whole logical/allocated cap');rows.append((str(p.relative_to(root)),s.st_size,s.st_blocks*512))
  if stat.S_ISDIR(s.st_mode):
   # Iteration is closed before final descriptor-free whole namespace rejoin.
   it=None;primary=None
   try:
    it=os.scandir(p);names=[]
    for e in it:
     require(len(names)+len(rows)<POLICY['members'] and time.monotonic()-begun<POLICY['sample_seconds'],'bounded directory enumeration');names.append(e.name)
   except BaseException as error:primary=error
   IO._cleanup(() if it is None else (it.close,),primary=primary)
   if primary is not None:raise primary
   for name in sorted(names):visit(p/name,depth+1)
 visit(root,0)
 require(shutil.disk_usage(root).free>=POLICY['floor'],'10GiB disk floor')
 extent_changes=0
 for p,s in saved.items():
  require(time.monotonic()-begun<POLICY['sample_seconds'],'census deadline')
  require(p.resolve()==p,'changed canonical path')
  current=p.lstat();now=signature(current)
  require(current.st_dev==device and (stat.S_ISDIR(current.st_mode) or stat.S_ISREG(current.st_mode)),'owned rejoin type/device')
  if stat.S_ISREG(current.st_mode):
   require(current.st_size<=POLICY['file'],'owned rejoin per-file/hardlink bound')
   if current.st_nlink!=1:
    require(owned_fetch_objects is not None and p.is_relative_to(owned_fetch_objects) and current.st_nlink>1,'owned rejoin per-file/hardlink bound')
    raise ChangingTree('owned rejoin regular hardlink observed: '+str(p.relative_to(root))+' nlink='+str(current.st_nlink))
   if now[:4]!=s[:4]:raise ChangingTree('owned regular identity changed')
   # Count both observed endpoints of every regular body. Growing Git pack
   # extents do not imply incomplete directory membership. This is a sampled
   # bound, not immutable body content or a continuously atomic quota.
   logical+=max(s[4],now[4])-s[4]
   allocated+=max(s[7],now[7])*512-s[7]*512
   extent_changes+=int(now!=s)
  elif now!=s:raise ChangingTree('incomplete/changing directory census refused')
  require(logical<=POLICY['logical'] and allocated<=POLICY['allocated'],'whole rejoin logical/allocated cap')
 require(shutil.disk_usage(root).free>=POLICY['floor'],'10GiB disk floor')
 require(time.monotonic()-begun<POLICY['sample_seconds'],'census deadline')
 return {'logical_bytes':logical,'allocated_bytes':allocated,'members':len(rows),'seconds':time.monotonic()-begun,'regular_extent_changes':extent_changes,'measurement':'complete sampled namespace; maximum of two regular extent observations'}


def census(root,owned_fetch_objects=None):
 begun=time.monotonic();last=None
 for attempt in range(3):
  try:
   result=_sample(root,owned_fetch_objects=owned_fetch_objects)
   require(time.monotonic()-begun<POLICY['sample_seconds'],'complete sampled census deadline')
   result['complete_attempts']=attempt+1
   return result
  except (ChangingTree,FileNotFoundError) as error:
   last=error
   require(time.monotonic()-begun<POLICY['sample_seconds'],'changing census deadline')
   if attempt<2:
    # Fixed scheduling deviation: at most two 100ms waits, inside the same
    # five-second whole-census deadline. No partial attempt is accepted.
    require(time.monotonic()-begun+.1<POLICY['sample_seconds'],'changing census retry delay budget')
    time.sleep(.1)
    require(time.monotonic()-begun<POLICY['sample_seconds'],'changing census retry delay deadline')
 raise ValueError('no complete census in three bounded attempts') from last
