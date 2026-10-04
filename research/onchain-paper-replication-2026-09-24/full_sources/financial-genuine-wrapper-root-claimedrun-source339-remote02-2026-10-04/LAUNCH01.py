import datetime,hashlib,json,os,shutil,sys
from pathlib import Path
M=Path.cwd();B=M/'research/onchain-paper-replication-2026-09-24/full_sources';H=B/'financial-genuine-wrapper-root-claimedrun-source339-remote02-2026-10-04'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(H/'recover01.py')=='0b397ccd0a014f60a414ce79d67dfd53c58a0fb61ca616a6576cc43da4bbf0aa'
assert sha(H/'SELECTED_BODIES01.json')=='38bc70a9c3cc684588e9cb8792587be08ff65a4cefc27e4d31057fb630650cce'
review=B/'financial-genuine-wrapper-claimedrun-source339-selection-review02-2026-10-04/MANIFEST01.json';assert review.is_file();assert len(sys.argv)==2 and sha(review)==sys.argv[1]
assert not any((H/n).exists()for n in ['INTENT01.json','REMOTE_RECOVERY01.json','FAILED01.json','selected','fresh-recordfix-source325-01.git'])
free=shutil.disk_usage(H).free;assert free>=10*1024**3
pid=os.getpid();ticks=int(Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19])
r={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_root_pid':pid,'actual_start_ticks':ticks,'actual_pgid':os.getpgid(pid),'actual_sid':os.getsid(pid),'free_before':free,'selection_sha256':sha(H/'SELECTED_BODIES01.json'),'accepted_selection_manifest':sha(review),'actual_main_remote_commit':'6514f20fc208e0d2f7ada31bc285b4e0b5c33ff8','qualification':'ONE fresh actual bounded external recovery of Source339 complete archive and selected correction/history/admission/recovery witnesses. Legacy six Source325 required bodies/status wording remain supplemental and immutable. No native job/ResearchRun/claims; final Parent/full caller witness recovery remains separate.'}
with(H/'INTENT01.json').open('x')as f:json.dump(r,f,sort_keys=True,indent=2);f.write('\n')
os.execv(sys.executable,[sys.executable,'-B',str(H/'recover01.py'),'--selection-sha256',r['selection_sha256']])
