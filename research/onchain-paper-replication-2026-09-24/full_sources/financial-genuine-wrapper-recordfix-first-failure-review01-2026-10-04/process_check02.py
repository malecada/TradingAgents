import datetime,json,os
from pathlib import Path
HERE=Path(__file__).resolve().parent;rows=[];gone=[];denied=[];scanned=0;begin=datetime.datetime.now(datetime.timezone.utc).isoformat();mod='tradingagents.research.onchain_replication.job';prefix='/home/malecada/master_thesis/onchain-financial-isolation/'
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  scanned+=1;argv=[b.decode(errors='replace') for b in (p/'cmdline').read_bytes().split(b'\0') if b];cg=(p/'cgroup').read_text();exact=any(argv[i]=='-m' and argv[i+1]==mod for i in range(max(0,len(argv)-1)));parent=any(a.startswith(prefix) and Path(a).name in ('parent01.py','supervisor01.py') for a in argv[1:3]);native='onchain-replication-' in cg
  if exact or parent or native:rows.append({'pid':int(p.name),'exact_module':exact,'selected_parent':parent,'native_cgroup':native,'cgroup':cg,'argv':argv if exact or parent else None})
 except (FileNotFoundError,ProcessLookupError):gone.append(int(p.name))
 except PermissionError:denied.append(int(p.name))
assert not rows and not denied
out={'begin':begin,'end':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scanned':scanned,'selected_matches':rows,'vanished_races':gone,'permission_denied':denied,'qualification':'Observable selected argv/cgroup snapshot; not complete historical descendants or whole-system continuous census','checks':2}
with (HERE/'PROCESS_CHECK02.json').open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps(out))
