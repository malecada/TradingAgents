import datetime,hashlib,json,os,shutil,sys
from pathlib import Path
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');B=M/'research/onchain-paper-replication-2026-09-24/full_sources';H=B/'financial-genuine-wrapper-root-claimedrun-witness-tooling-capture01-2026-10-04'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(H/'capture_tooling01.py')=='85368444d94a93df1aa4ba8b0f657d2725bc3d4717e9a07beecc3fa59033a167'
assert sha(B/'financial-genuine-wrapper-claimedrun-witness-tooling-capture-review01-2026-10-04/MANIFEST01.json')=='d3a12fdeb484ca3b4feccb2c9e84048fc341c97937694444bbd311ec1c952a2f'
assert not any(os.path.lexists(H/n)for n in ['INTENT01.json','union-bytes01','archives','TOOLING_AUTHENTICATION01.json'])
assert shutil.disk_usage(H).free>=10*1024**3
pid=os.getpid();ticks=int(Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19])
r={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_root_pid':pid,'actual_start_ticks':ticks,'actual_pgid':os.getpgid(pid),'actual_sid':os.getsid(pid),'free_before':shutil.disk_usage(H).free,'source':sha(H/'capture_tooling01.py'),'qualification':'ONE fresh actual bounded opaque capture of two frozen tooling source/review roots. No financial/native/numerical job, claim, admission, Owner or ResearchRun.'}
with(H/'INTENT01.json').open('x')as f:json.dump(r,f,sort_keys=True,indent=2);f.write('\n')
os.execv(sys.executable,[sys.executable,'-B',str(H/'capture_tooling01.py')])
