from pathlib import Path
import argparse,json,hashlib,datetime,os,subprocess,time
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04';V=F/'financial-wrapper-compatibility-operational-delta-entry-review03-2026-10-04';HEAD='4d0dbef40c978788ec9ddd9a5e4f4c2d18c52714'
def h(b):return hashlib.sha256(b).hexdigest()
def put(n,o):
 with (D/n).open('x') as f:json.dump(o,f,indent=2,sort_keys=True);f.write('\n')
a=argparse.ArgumentParser();a.add_argument('--entry-review-sha256',required=True);args=a.parse_args();raw=(V/'MACHINE01.json').read_bytes();assert h(raw)==args.entry_review_sha256;v=json.loads(raw)
assert v['decision']=='ACCEPTED_EXACT_ONE_USE_FORENSIC_REMOTE_ENTRY_ONLY';assert v['owned_root']==str(D) and v['commit']==HEAD and v['root_outer_caller_sha256']==h(Path(__file__).read_bytes())
assert v['selection_sha256']=='d2f64f4a7175ab13de9f40bcb7c700dc615197c61e65c39456233a21617bb23b' and v['installation_draft_sha256']=='4ac66420883fe2605db005152c4492e0597aaab1593ebc9976d1857b0ff6a96d'
assert v['remote_helper_sha256']=='ada3dafc7250452cb6db2eb33cdd5b5ecddb776511e247efcbc858dbb446aabf' and v['expected_operations']==55 and v['flat_execution_released'] is False and v['numerical_authority'] is False
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==HEAD
assert not (D/'ROOT_REMOTE03_INTENT01.json').exists();s=json.loads((D/'ROOT_INSTALLATION_DRAFT01.json').read_bytes())
for n,row in s['helpers_and_selection'].items():assert h((D/n).read_bytes())==row['sha256']
for n in ['fresh-operational-source-policy02.git','selected','flat-operational-delta01','flat-failed-remote02-01','REMOTE_RECOVERY01.json','FAILED01.json','ROOT_REMOTE03.stdout','ROOT_REMOTE03.stderr']:assert not os.path.lexists(D/n)
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
 try:argv=(proc/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,ProcessLookupError,PermissionError):continue
 assert str(D/'recover01.py').encode() not in argv and str(D/'restore01.py').encode() not in argv
pin=h((D/'SELECTED_BODIES01.json').read_bytes());assert pin==v['selection_sha256'];cmd=[str(R/'.venv/bin/python'),'-B',str(D/'recover01.py'),'--selection-sha256',pin];begun=time.monotonic()
put('ROOT_REMOTE03_INTENT01.json',{'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':cmd,'cwd':str(R),'entry_review_sha256':h(raw),'selection_sha256':pin,'parent_pid':os.getpid(),'outer_caller_sha256':h(Path(__file__).read_bytes()),'claim_or_native':False})
with (D/'ROOT_REMOTE03.stdout').open('xb') as out,(D/'ROOT_REMOTE03.stderr').open('xb') as err:
 child=subprocess.Popen(cmd,cwd=R,stdout=out,stderr=err,start_new_session=True);put('ROOT_REMOTE03_SPAWN01.json',{'pid':child.pid,'parent_pid':os.getpid(),'argv':cmd,'time':datetime.datetime.now(datetime.timezone.utc).isoformat()});code=child.wait(timeout=650)
put('ROOT_REMOTE03_EXIT01.json',{'schema_version':1,'actual_outer_exit':code,'actual_child_pid':child.pid,'elapsed_seconds':time.monotonic()-begun,'stdout_bytes':(D/'ROOT_REMOTE03.stdout').stat().st_size,'stdout_sha256':h((D/'ROOT_REMOTE03.stdout').read_bytes()),'stderr_bytes':(D/'ROOT_REMOTE03.stderr').stat().st_size,'stderr_sha256':h((D/'ROOT_REMOTE03.stderr').read_bytes()),'claim_or_native':False})
print(code,time.monotonic()-begun);raise SystemExit(code)
