import datetime,hashlib,json,os,shutil,sys
from pathlib import Path
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');B=M/'research/onchain-paper-replication-2026-09-24/full_sources'
args={'primary':('financial-genuine-wrapper-root-claimedrun-final-shards-remote01-2026-10-04','28f95d42e6f53c243d31ed9867724fedd89b04cb601b63de199ac2616c0f49c9'),'supplemental':('financial-genuine-wrapper-root-claimedrun-helper-raw-remote01-2026-10-04','c8dd51669514a49a1c75ad6e74572579d1a0590bad8c1da0d44d70245c54c4ea')}
name,pin=args[sys.argv[1]];H=B/name
assert hashlib.sha256((H/'recover01.py').read_bytes()).hexdigest()=='0b397ccd0a014f60a414ce79d67dfd53c58a0fb61ca616a6576cc43da4bbf0aa'
assert hashlib.sha256((H/'SELECTED_BODIES01.json').read_bytes()).hexdigest()==pin
assert hashlib.sha256((B/'financial-genuine-wrapper-claimedrun-final-committed-selections-review01-2026-10-04/MACHINE01.json').read_bytes()).hexdigest()=='3d3bfd78cff58862e733a68b3651ac3df35290500a0e08dfcf61a78f465160c8'
assert not any(os.path.lexists(H/n)for n in ['INTENT01.json','selected','fresh-recordfix-source325-01.git','REMOTE_RECOVERY01.json','FAILED01.json'])
assert shutil.disk_usage(H).free>=10*1024**3
pid=os.getpid();ticks=int(Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19])
with(H/'INTENT01.json').open('x')as f:
 json.dump({'actual_pid':pid,'actual_start_ticks':ticks,'actual_pgid':os.getpgid(pid),'actual_sid':os.getsid(pid),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selection_sha256':pin,'remote_commit':'a9b219042109be78498185cc6539c1454736e3eb','genuine_exact_scope_review_sha256':'3d3bfd78cff58862e733a68b3651ac3df35290500a0e08dfcf61a78f465160c8','actual_remote_confirmation':'REMOTE_CONFIRMATION28.json/29880/9993dc/5f0fd3/exit0','free_before':shutil.disk_usage(H).free,'qualification':'ONE fresh original ordinary external Git selected-byte recovery in this exclusive namespace. Independent batches share only6 mandatory read-only Source325 safety anchors. No paper job/claim/Owner/Binding/ResearchRun or budget transfer.'},f,sort_keys=True,indent=2);f.write('\n')
os.chdir(M);os.execv(sys.executable,[sys.executable,'-B',str(H/'recover01.py'),'--selection-sha256',pin])
