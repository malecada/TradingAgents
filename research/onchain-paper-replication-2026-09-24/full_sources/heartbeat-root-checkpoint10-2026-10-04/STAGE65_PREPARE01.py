import hashlib,json,stat,subprocess
from pathlib import Path
root=Path.cwd();s=root/'research/onchain-paper-replication-2026-09-24';f=s/'full_sources';c=f/'heartbeat-root-checkpoint10-2026-10-04'
paths={s/'STATE.md',f/'parallel-execution-2026-10-02/COORDINATION.md'}
for name in ('financial-wrapper-continuation-outcome-review01-2026-10-05','financial-wrapper-continuation-refused-outcome-remote01-2026-10-05','financial-wrapper-continuation-refused-outcome-flat01-2026-10-05'):
 d=f/name
 for p in d.rglob('*'):
  rel=p.relative_to(d)
  if any(x=='selected' or x=='flat' or x.endswith('.git') for x in rel.parts):continue
  if p.is_file() and not p.is_symlink():paths.add(p)
for name in ('REMOTE_CONFIRMATION64.json','CANONICAL_CONTINUATION_REFUSAL_FLAT01.py','CANONICAL_CONTINUATION_REFUSAL_FLAT02.py','CANONICAL_CONTINUATION_REFUSAL_FLAT02.stdout','CANONICAL_CONTINUATION_REFUSAL_FLAT02.stderr','OVERHEAD_PRIORITY_AUTOMATION_UPDATE02.json','RESTART_CHECKPOINT01.py','RESTART_OBSERVATION01.json','STATE_TOP96_SNAPSHOT01.md','COORDINATION_PRE_RESTART01.md','STAGE65_PREPARE01.py'):
 p=c/name;assert p.is_file(),name;paths.add(p)
rows=[]
for p in sorted(paths):
 st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_size<=4*1024**2
 raw=p.read_bytes();rows.append({'path':p.relative_to(root).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
assert sum(r['bytes'] for r in rows)<4*1024**2
manifest=c/'STAGE65_SELECTED_SCOPE01.json';spec=c/'STAGE65_PATHSPEC01.nul'
with manifest.open('x') as w:json.dump({'schema_version':1,'prior_head':'b94682059c2d7a739d18db0d299d8c3a0a5019be','files':rows,'bytes':sum(r['bytes'] for r in rows),'qualification':'selected changed outcome/recovery/restart records; original bare, selected and flat recovered bodies remain preserved outside this commit'},w,sort_keys=True,indent=2);w.write('\n')
with spec.open('xb') as w:w.write(b''.join((r['path'].encode()+b'\0') for r in rows)+str(manifest.relative_to(root)).encode()+b'\0')
subprocess.run(['git','add','--pathspec-from-file='+str(spec),'--pathspec-file-nul'],check=True)
check=subprocess.run(['git','diff','--cached','--check'],capture_output=True,text=True);assert check.returncode==0,check.stdout+check.stderr
print(json.dumps({'selected_files':len(rows),'selected_bytes':sum(r['bytes'] for r in rows),'staged_paths':subprocess.run(['git','diff','--cached','--name-only'],capture_output=True,text=True,check=True).stdout.count('\n')}))
