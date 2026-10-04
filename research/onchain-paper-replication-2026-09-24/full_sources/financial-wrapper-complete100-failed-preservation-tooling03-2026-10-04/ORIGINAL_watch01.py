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
def _sample(root):
 root=Path(root);require(root.is_absolute() and root.resolve()==root,'canonical owned root');begun=time.monotonic();rows=[];logical=allocated=0;saved={};device=root.stat().st_dev
 def visit(p,depth):
  nonlocal logical,allocated
  require(depth<=POLICY['depth'] and time.monotonic()-begun<POLICY['sample_seconds'],'finite complete census');s=p.lstat();require(p.resolve()==p and s.st_dev==device and (stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode)),'owned tree type/path/device');require(len(rows)<POLICY['members'],'whole member cap');saved[p]=signature(s);allocated+=s.st_blocks*512
  if stat.S_ISREG(s.st_mode):
   require(s.st_nlink==1 and s.st_size<=POLICY['file'],'owned per-file/hardlink bound');logical+=s.st_size
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
 for p,s in saved.items():
  require(p.resolve()==p,'changed canonical path')
  if signature(p.lstat())!=s:raise ChangingTree('incomplete/changing census refused')
 require(time.monotonic()-begun<POLICY['sample_seconds'],'census deadline')
 return {'logical_bytes':logical,'allocated_bytes':allocated,'members':len(rows),'seconds':time.monotonic()-begun}


def census(root):
 begun=time.monotonic();last=None
 for attempt in range(3):
  try:
   result=_sample(root)
   require(time.monotonic()-begun<POLICY['sample_seconds'],'complete sampled census deadline')
   result['complete_attempts']=attempt+1
   return result
  except (ChangingTree,FileNotFoundError) as error:
   last=error
   require(time.monotonic()-begun<POLICY['sample_seconds'],'changing census deadline')
 raise ValueError('no complete census in three bounded attempts') from last
