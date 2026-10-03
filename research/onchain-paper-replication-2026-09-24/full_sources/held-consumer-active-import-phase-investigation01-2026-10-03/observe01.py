import os,time,json,datetime,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent
C=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source')
ID='original-import-held-success-20261003-01'
def proc(pid):
 p=Path('/proc')/str(pid)
 try:
  raw=(p/'stat').read_text();v=raw[raw.rfind(')')+2:].split();status=(p/'status').read_text().splitlines()
  children=[]
  for t in sorted((p/'task').iterdir())[:32]:
   try:children+=list(map(int,(t/'children').read_text().split()))
   except FileNotFoundError:pass
  return dict(pid=pid,state=v[0],ppid=int(v[1]),utime_ticks=int(v[11]),stime_ticks=int(v[12]),cutime_ticks=int(v[13]),cstime_ticks=int(v[14]),start_ticks=int(v[19]),wchan=(p/'wchan').read_text(),status=[x for x in status if x.startswith(('Name:','Threads:','VmRSS:'))],argv=(p/'cmdline').read_bytes().decode(errors='replace').split('\0'),children=sorted(set(children)))
 except (FileNotFoundError,ProcessLookupError):return dict(pid=pid,absent=True)
rows=[]
for n in range(8):
 seeds=[4050318,4050527,4050749,4050790,4050843,4050847];seen=set();records=[]
 while seeds and len(seen)<32:
  pid=seeds.pop(0)
  if pid in seen:continue
  seen.add(pid);r=proc(pid);records.append(r);seeds.extend(r.get('children',[]))
 rows.append(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),processes=records))
 if n<7:time.sleep(.5)
markers=[]
for root in [C/'research_runs'/ID,C/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/ID,C/'research_artifacts/onchain_representations']:
 if not root.exists():markers.append(dict(path=str(root),exists=False));continue
 paths=[root]
 if root.name=='onchain_representations':
  paths+=list(root.glob('*'))+list(root.glob('*/*'))
 else:
  paths+=list(root.glob('*'))
 for p in paths[:100]:
  s=p.lstat();markers.append(dict(path=str(p),mode=s.st_mode,size=s.st_size,mtime_ns=s.st_mtime_ns))
claims=[]
for p in sorted((C/'research_runs').glob('*/claim.json')):
 b=p.read_bytes();x=json.loads(b);e=x['experiment'];pins=dict(e['source_files']);pins[e['charter']['path']]=e['charter']['sha256']
 claims.append(dict(path=str(p.relative_to(C)),sha256=hashlib.sha256(b).hexdigest(),id=x['experiment_id'],source=x['source'],design=x['design_source'],source_count=len(e['source_files']),pins_with_charter=len(pins),input_count=len(x['inputs']),terminal=[q.name for q in p.parent.glob('*.json') if q.name in ('failed.json','complete.json')],effective=x.get('effective_attempt_budget'),extension=bool(e.get('cumulative_budget_extension'))))
out=dict(clock_ticks=os.sysconf('SC_CLK_TCK'),samples=rows,markers=markers,claims=claims,scope='Read-only process metadata and registered control documents; no process environment, FD contents, arrays or module execution.')
(D/'OBSERVATION01.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
