"""Root-only post-transfer measurement; no Git command or allowance creation."""
import json,os,stat,time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def census():
 root=HERE/'fresh-complete100-failed-outcome02-01.git'
 if root.resolve()!=root or not root.is_dir():raise ValueError('genuine fresh Git root unavailable')
 start=time.monotonic();rows=[];logical=allocated=0
 for parent,dirs,files in os.walk(root,followlinks=False):
  for name in sorted(dirs+files):
   p=Path(parent)/name;s=p.lstat()
   if time.monotonic()-start>=30 or len(rows)>=32768 or p.resolve()!=p or not (stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode)):raise ValueError('bounded canonical Git physical census')
   logical+=s.st_size if stat.S_ISREG(s.st_mode) else 0;allocated+=s.st_blocks*512
   if logical>64*1024**2 or allocated>64*1024**2:raise ValueError('64MiB observed Git extent ceiling; retain tree for review')
   rows.append({'path':p.relative_to(root).as_posix(),'kind':'file' if stat.S_ISREG(s.st_mode) else 'directory','bytes':s.st_size,'allocated_bytes':s.st_blocks*512,'mode':stat.S_IMODE(s.st_mode)})
 large=[r for r in rows if r['kind']=='file' and r['bytes']>4*1024**2]
 return {'status':'MEASURED_ONLY_REQUIRES_INDEPENDENT_PHYSICAL_POLICY' if large else 'OBSERVED_GIT_FILES_WITHIN_4M_NOT_CONTINUOUS_PROOF','members':rows,'logical_bytes':logical,'allocated_bytes':allocated,'above_4MiB':large,'universal_4MiB_claim':False,'new_authority':False}
if __name__=='__main__':print(json.dumps(census(),sort_keys=True))
