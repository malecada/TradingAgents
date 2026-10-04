import datetime,hashlib,json,os,shutil,sys
from pathlib import Path
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
B=M/'research/onchain-paper-replication-2026-09-24/full_sources'
H=B/'financial-genuine-wrapper-root-claimedrun-sharded-witness-capture02-2026-10-04'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(H/'capture_witness02.py')=='b275af0c30a4f19227cff1cccbc19c01d7548b3b218e43f78a3be493bfe05ae6'
assert sha(H/'shards01.py')=='9c38c0893790c22e3b0142a8ab175dceb9b14dd0aeeb80edc206e5329ffcbbba'
assert sha(B/'financial-genuine-wrapper-claimedrun-sharded-witness-capture-review02-2026-10-04/MANIFEST01.json')=='d0bd935a4f693f56dd5b43a7a4b5f3f9463bdf7afee29995b61aa9ba44016c3f'
assert not any(os.path.lexists(H/n)for n in ['INTENT01.json','union-bytes01','shards','shard-trees','SHARD_INDEX01.json','UNION_AUTHENTICATION01.json'])
assert shutil.disk_usage(H).free>=10*1024**3
pid=os.getpid();ticks=int(Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19])
r={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_root_pid':pid,'actual_start_ticks':ticks,'actual_pgid':os.getpgid(pid),'actual_sid':os.getsid(pid),'free_before':shutil.disk_usage(H).free,'source':sha(H/'capture_witness02.py'),'planner':sha(H/'shards01.py'),'qualification':'ONE fresh actual bounded byte witness capture. Exact five closed original roots and sole direct rawbody are required together. No numerical/native job, claim, admission, Owner or ResearchRun.'}
with(H/'INTENT01.json').open('x')as f:json.dump(r,f,sort_keys=True,indent=2);f.write('\n')
os.execv(sys.executable,[sys.executable,'-B',str(H/'capture_witness02.py')])
