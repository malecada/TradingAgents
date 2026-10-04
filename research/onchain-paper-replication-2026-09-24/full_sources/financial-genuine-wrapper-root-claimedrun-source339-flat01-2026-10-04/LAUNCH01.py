import datetime,hashlib,json,os,shutil,sys
from pathlib import Path
B=Path.cwd()/'research/onchain-paper-replication-2026-09-24/full_sources';H=B/'financial-genuine-wrapper-root-claimedrun-source339-flat01-2026-10-04';F=B/'financial-genuine-wrapper-claimedrun-source339-flat-20261004-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert len(sys.argv)==2 and sha(H/'REQUEST_FINAL03.json')==sys.argv[1]
assert sha(F/'restore01.py')=='9e21e92ca69fad038dc77324b8fcc9f7600380293e55a90b7c0fd5b8ae95c1fc'
q=json.loads((H/'REQUEST_FINAL03.json').read_bytes());r=q['release'];assert sha(Path(r['path']))==r['sha256']=='62606a555380daf83d89cc420d7f4d9ae3371bb8f419924cc5014ac34f2fa167'
assert not any((F/n).exists()for n in['INTENT01.json','flat-source01','RECOVERY01.json','FAILED01.json'])
assert not(H/'PARENT_OBSERVATION01.json').exists();free=shutil.disk_usage(H).free;assert free>=10*1024**3
pid=os.getpid();ticks=int(Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19])
ob={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_parent_pid':pid,'actual_start_ticks':ticks,'actual_pgid':os.getpgid(pid),'actual_sid':os.getsid(pid),'free_before':free,'final_request_sha256':sys.argv[1],'helper_sha256':sha(F/'restore01.py'),'release_sha256':r['sha256'],'qualification':'ONE original strict03 genuine source-only747-body restore from actual authenticated external195 selection. No Git network, NumPy/Torch/SciPy/Pandas, Admission, Run, Binding, Owner or native numerical launch. Original helper own intent remains separately authentic.'}
with(H/'PARENT_OBSERVATION01.json').open('x')as f:json.dump(ob,f,sort_keys=True,indent=2);f.write('\n')
os.execv(sys.executable,[sys.executable,'-B',str(F/'restore01.py'),'--request',str(H/'REQUEST_FINAL03.json'),'--sha256',sys.argv[1]])
