from pathlib import Path
import json,hashlib,datetime,os,subprocess,time,stat
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'financial-wrapper-compatibility-operational-delta-root-remote02-2026-10-04';V=F/'financial-wrapper-compatibility-operational-delta-entry-review02-2026-10-04'
def h(b):return hashlib.sha256(b).hexdigest()
def put(n,o):
 with (D/n).open('x') as f:json.dump(o,f,indent=2,sort_keys=True);f.write('\n')
assert h((V/'MACHINE01.json').read_bytes())=='215436fdab9b44d071079a723416cabd164afd126526ceb4245ab52b069837ac'
v=json.loads((V/'MACHINE01.json').read_bytes());assert not (D/'ROOT_REMOTE02_INTENT01.json').exists();s=json.loads((D/'ROOT_INSTALLATION_DRAFT01.json').read_bytes())
for n,row in s['helpers_and_selection'].items():assert h((D/n).read_bytes())==row['sha256']
for n in ['fresh-operational-source-policy01.git','selected','flat-operational-delta01','REMOTE_RECOVERY01.json','FAILED01.json','ROOT_REMOTE02.stdout','ROOT_REMOTE02.stderr']:assert not os.path.lexists(D/n)
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
 try:argv=(proc/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,ProcessLookupError,PermissionError):continue
 assert str(D/'recover01.py').encode() not in argv and str(D/'restore01.py').encode() not in argv
pin=h((D/'SELECTED_BODIES01.json').read_bytes());assert pin=='55532ac9b8ea0d92f8a75f202a6733b43124cb9367dccca2c4fabfd175b7f791';cmd=[str(R/'.venv/bin/python'),'-B',str(D/'recover01.py'),'--selection-sha256',pin];begun=time.monotonic()
put('ROOT_REMOTE02_INTENT01.json',{'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':cmd,'cwd':str(R),'entry_review_sha256':h((V/'MACHINE01.json').read_bytes()),'selection_sha256':pin,'parent_pid':os.getpid(),'claim_or_native':False})
with (D/'ROOT_REMOTE02.stdout').open('xb') as out,(D/'ROOT_REMOTE02.stderr').open('xb') as err:
 child=subprocess.Popen(cmd,cwd=R,stdout=out,stderr=err,start_new_session=True);put('ROOT_REMOTE02_SPAWN01.json',{'pid':child.pid,'parent_pid':os.getpid(),'argv':cmd,'time':datetime.datetime.now(datetime.timezone.utc).isoformat()});code=child.wait(timeout=650)
put('ROOT_REMOTE02_EXIT01.json',{'schema_version':1,'actual_outer_exit':code,'actual_child_pid':child.pid,'elapsed_seconds':time.monotonic()-begun,'stdout_bytes':(D/'ROOT_REMOTE02.stdout').stat().st_size,'stdout_sha256':h((D/'ROOT_REMOTE02.stdout').read_bytes()),'stderr_bytes':(D/'ROOT_REMOTE02.stderr').stat().st_size,'stderr_sha256':h((D/'ROOT_REMOTE02.stderr').read_bytes()),'claim_or_native':False})
print(code,time.monotonic()-begun)
raise SystemExit(code)
