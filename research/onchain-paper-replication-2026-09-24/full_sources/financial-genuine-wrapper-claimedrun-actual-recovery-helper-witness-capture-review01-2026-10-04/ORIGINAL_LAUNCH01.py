import datetime,hashlib,json,os,shutil,sys
from pathlib import Path
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');B=M/'research/onchain-paper-replication-2026-09-24/full_sources';H=B/'financial-genuine-wrapper-root-claimedrun-recovery-helper-witness-capture01-2026-10-04'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(H/'capture_helpers01.py')=='06f1a923e4b1d77d019276117a55d34f5942990c7e19f631783a62116224d4da'
assert sha(B/'financial-genuine-wrapper-claimedrun-recovery-helper-witness-capture-review01-2026-10-04/MANIFEST01.json')=='128cffb0c122368ba8731be9f849f49dab148beef61cd2447cf5c36936e8657c'
assert not any(os.path.lexists(H/n)for n in ['INTENT01.json','union-bytes01','UNION_AUTHENTICATION01.json'])
assert shutil.disk_usage(H).free>=10*1024**3
pid=os.getpid();ticks=int(Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19])
r={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_root_pid':pid,'actual_start_ticks':ticks,'actual_pgid':os.getpgid(pid),'actual_sid':os.getsid(pid),'free_before':shutil.disk_usage(H).free,'source':sha(H/'capture_helpers01.py'),'qualification':'ONE fresh actual bounded completeSIXhelper source/review bytecapture. Originalclosedcapturenamespaces untouched. No native/NUM/research claim/admission/Binding/Owner/Run.'}
with(H/'INTENT01.json').open('x')as f:json.dump(r,f,sort_keys=True,indent=2);f.write('\n')
os.execv(sys.executable,[sys.executable,'-B',str(H/'capture_helpers01.py')])
