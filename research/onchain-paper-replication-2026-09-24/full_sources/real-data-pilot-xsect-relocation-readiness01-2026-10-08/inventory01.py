"""Bounded metadata-only exact xsect inventory; no payload open/read or following links."""
import os,stat,time,json
from pathlib import Path
ROOT=Path('/home/malecada/master_thesis/TradingAgents/data/xsect')
OUT=Path(__file__).resolve().parent
start=time.monotonic();entries=[];errors=[];stack=[ROOT];seen=set();complete=True
counts={k:0 for k in ('regular','directory','symlink','other','hardlinked_regular')}
logical=allocated=gain=0
while stack:
 if time.monotonic()-start>=60 or len(entries)>=100000:complete=False;break
 p=stack.pop()
 try:
  s=p.lstat();kind='regular' if stat.S_ISREG(s.st_mode) else 'directory' if stat.S_ISDIR(s.st_mode) else 'symlink' if stat.S_ISLNK(s.st_mode) else 'other'
  row={'relative_path':str(p.relative_to(ROOT)),'kind':kind,'mode':s.st_mode,'device':s.st_dev,'inode':s.st_ino,'nlink':s.st_nlink,'logical_bytes':s.st_size,'allocated_bytes':s.st_blocks*512,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns}
  entries.append(row);counts[kind]+=1
  if kind=='regular':
   logical+=s.st_size;allocated+=s.st_blocks*512
   if s.st_nlink>1:counts['hardlinked_regular']+=1
   elif (s.st_dev,s.st_ino) not in seen:gain+=s.st_blocks*512
  seen.add((s.st_dev,s.st_ino))
  if kind=='directory':
   with os.scandir(p) as it:
    for child in it:
     if time.monotonic()-start>=60 or len(entries)+len(stack)>=100000:complete=False;break
     stack.append(Path(child.path))
 except OSError as e:errors.append({'path':str(p.relative_to(ROOT)),'error':type(e).__name__});complete=False
 if not complete:break
result={'schema_version':1,'kind':'metadata-only-xsect-inventory','root':str(ROOT),'complete':complete and not errors and not stack,'max_seconds':60,'max_entries':100000,'elapsed_seconds':time.monotonic()-start,'counts':counts,'entries_including_root':len(entries),'regular_logical_bytes_path_sum':logical,'regular_allocated_bytes_path_sum':allocated,'all_entries_allocated_bytes_path_sum':sum(x['allocated_bytes'] for x in entries),'nonhardlinked_regular_gain_upper_bound_bytes':gain,'errors':errors,'qualification':'Sampled path metadata only; no file bodies read. No atomic writer exclusion, content hashes, backup verification or guaranteed free-space gain. Every multiply linked regular file excluded from gain.','entries':entries}
(OUT/'INVENTORY01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='entries'},sort_keys=True))
