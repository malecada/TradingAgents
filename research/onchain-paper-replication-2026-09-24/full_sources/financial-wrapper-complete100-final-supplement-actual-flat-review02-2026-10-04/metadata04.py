from pathlib import Path
import hashlib,json,os,stat,subprocess
D=Path(__file__).resolve().parent;F=D.parent;Q=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-final-contract-20261004-01/REQUEST_RELEASED01.json');q=json.loads(Q.read_bytes());C=Path(q['capsule_root']);P=Path(q['parent_root']);sha=lambda b:hashlib.sha256(b).hexdigest();n=0
p=subprocess.run(['git','--no-replace-objects','-C',str(C),'ls-tree','-r','-z',q['source']],env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL=''),stdin=subprocess.DEVNULL,capture_output=True,timeout=10);assert p.returncode==0 and not p.stderr;rows=p.stdout.rstrip(b'\0').split(b'\0');assert len(rows)==339;n+=2;tracked=[]
for r in rows:
 a,name=r.split(b'\t');mode,kind,oid=a.decode().split();name=name.decode();b=(C/name).read_bytes();s=(C/name).lstat();assert kind=='blob' and stat.S_ISREG(s.st_mode) and mode==('100755' if s.st_mode&0o111 else '100644') and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid;n+=1;tracked.append(name)
assert set(tracked)==set(q['source_files'])|{q['registration']};n+=1
reg=json.loads((C/q['registration']).read_bytes());e=reg['experiments'][q['identity']];family=reg['families'][e['family']];extension=json.loads((C/e['cumulative_budget_extension']['extension']['path']).read_bytes());assert family['attempt_budget']==18 and family['prior_attempts']==0 and extension['cumulative_ceiling']==19 and extension['consumed_before']==1;n+=1
claims=[json.loads(x.read_bytes()) for x in (C/'research_runs').glob('*/claim.json')];assert len(claims)==2 and sorted(x['effective_attempt_budget'] for x in claims)==[18,19];n+=1
base=F/'financial-wrapper-complete100-baseline-remote01-2026-10-04';pm=json.loads((base/'flat-parent01/body-metadata.json').read_bytes());assert stat.S_IMODE(P.stat().st_mode)==pm['manifest']['root_mode'];n+=1
for r in pm['manifest']['members']:
 s=(P/r['path']).lstat();assert stat.S_IMODE(s.st_mode)==r['mode'] and stat.S_ISREG(s.st_mode);n+=1
result={'checks':n,'current_tracked339':True,'current_gate_plus338pins_exact':True,'both_failed_spent':2,'highest_actual_allowance':19,'base18_prior0_unchanged':True,'Parent_original_literal_modes_unchanged':True,'native_or_new_claim':False};(D/'METADATA04.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
