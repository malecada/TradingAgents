"""Read-only bounded metadata inventory; never opens source file bodies."""
import os,stat,json,datetime,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3]
F=P.parent
contract=json.loads((F/'xsect-posix-recovery-entry01-2026-10-09/CONTRACT_FINAL01.json').read_text())
roots=[Path(contract['original_root']),Path(contract['target_root'])]
result={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'trees':[]}
for root in roots:
 out={'path':str(root),'files':0,'directories':0,'logical_bytes':0,'allocated_bytes':0,'nonregular':[],'multiply_linked_files':0,'device':root.stat().st_dev}
 todo=[root]
 while todo:
  path=todo.pop();s=path.lstat();out['allocated_bytes']+=s.st_blocks*512
  if stat.S_ISDIR(s.st_mode):
   out['directories']+=1;todo.extend(path.iterdir())
  elif stat.S_ISREG(s.st_mode):
   out['files']+=1;out['logical_bytes']+=s.st_size;out['multiply_linked_files']+=int(s.st_nlink!=1)
  else:out['nonregular'].append(str(path))
  assert out['files']+out['directories']<10000
 result['trees'].append(out)
result['disk_free_bytes']=shutil.disk_usage(ROOT).free
prep=json.loads((F/'real-data-pilot-final23-2026-10-09/PREPARATION_RESULT02.json').read_text())
growth=prep['builder03_result']['capacity_lower_bounds']['declared_allocated_growth_bytes'];floor=prep['inventory']['local_free_floor_bytes']
result['draft23']={'growth_bytes':growth,'floor_bytes':floor,'required_free_bytes':growth+floor}
for name,reclaimed in [('keep_both',0),('retire_original_keep_recovered',result['trees'][0]['allocated_bytes']),('retire_both',sum(x['allocated_bytes'] for x in result['trees']))]:
 projected=result['disk_free_bytes']+reclaimed
 result['draft23'][name]={'conditional_reclaimed_bytes':reclaimed,'conditional_free_bytes':projected,'margin_bytes':projected-growth-floor}
# One bounded /proc metadata pass. No environments, command lines, memory or bodies.
proc={'processes_seen':0,'fd_links_read':0,'denied':0,'races':0,'matches':[],'limit_reached':False}
for d in Path('/proc').iterdir():
 if not d.name.isdigit():continue
 proc['processes_seen']+=1
 try:entries=[d/'cwd',d/'root']+list((d/'fd').iterdir())
 except PermissionError:proc['denied']+=1;continue
 except FileNotFoundError:proc['races']+=1;continue
 for entry in entries:
  if proc['fd_links_read']>=32768:proc['limit_reached']=True;break
  try:target=os.readlink(entry);proc['fd_links_read']+=1
  except PermissionError:proc['denied']+=1;continue
  except FileNotFoundError:proc['races']+=1;continue
  if any(target==str(r) or target.startswith(str(r)+'/') for r in roots):proc['matches'].append({'pid':int(d.name),'slot':entry.name,'target':target})
 if proc['limit_reached']:break
result['process_observation']=proc
result['qualification']='Metadata only, no writer exclusion; st_blocks potential reclaim is conditional on final-link removal, no open references/shared extents and concurrent filesystem changes. No retirement performed or authorized by this observation.'
(P/'INVENTORY01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
