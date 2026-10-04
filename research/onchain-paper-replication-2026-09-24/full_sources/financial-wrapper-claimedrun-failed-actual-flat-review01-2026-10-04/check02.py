from pathlib import Path
import json,hashlib,os
D=Path(__file__).resolve().parent;F=D.parent;T=F/'financial-wrapper-claimedrun-failed-remote01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((T/'flat-capsule01/body-metadata.json').read_bytes());mapping=m['flat_members'];checks=[]
def read(n):return (T/'flat-capsule01'/mapping[n]).read_bytes()
def ok(v,n):assert v,n;checks.append(n)
id='financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01';c=json.loads(read('research_runs/'+id+'/claim.json'));ok(len(c['experiment']['source_files'])==338,'genuine338sourcepins')
for n,pin in c['experiment']['source_files'].items():ok(sha(read(n))==pin,'recovered registered source '+n)
for n,pin in c['experiment']['runtime_hashes'].items():
 choices=[p for p in mapping if p.endswith('/'+n)and sha(read(p))==pin];ok(len(choices)==1,'genuine runtime API code '+n)
ok(c['inputs']==c['experiment']['inputs']and len(c['inputs'])==8,'exact genuine eight input roles')
for n,r in c['inputs'].items():ok(sha(read(r['path']))==r['sha256'],'genuine claimed input '+n)
runtime=json.loads(read(c['inputs']['runtime_mapping']['path']));records=runtime['distribution_records'];ok(len(records)==251 and len({r['record']for r in records})==251,'preserved251 runtime RECORD metadata pins')
for r in records:ok(type(r['record_sha256'])is str and len(r['record_sha256'])==64 and r['record'].endswith('/RECORD'),'opaque RECORD metadata schema '+r['name'])
claims=[(p,json.loads(read(p)))for p in mapping if p.startswith('research_runs/')and p.endswith('/claim.json')];ok(len(claims)==2 and max(c['effective_attempt_budget']for p,c in claims)==19,'two genuine retained claims highest19')
for p,c0 in claims:
 failed=p[:-len('claim.json')]+'failed.json';ok(failed in mapping and p[:-len('claim.json')]+'complete.json'not in mapping,'retained FAILED no COMPLETE '+p)
 f=json.loads(read(failed));ok(f['status']=='failed'and f['claim_sha256']==sha(read(p)),'actual failed-claim binding '+p)
pmeta=json.loads((T/'flat-parent01/body-metadata.json').read_bytes());pm=pmeta['flat_members'];term=json.loads((T/'flat-parent01'/pm['attempt/parent-terminal.json']).read_bytes());pids=set();groups=set()
for n,f in pm.items():
 if n.endswith('owned-tree-cleanup.json'):
  j=json.loads((T/'flat-parent01'/f).read_bytes());ok(j['remaining_original_identities']==[],'recovered empty remaining original identities '+n)
  for r in j['owned_pid_start_records']:pids.add(r['pid']);groups.add(r['pgrp'])
for pid in pids:ok(not Path('/proc',str(pid)).exists(),'recorded original parent PID nowabsent '+str(pid))
for group in groups:
 try:os.killpg(group,0)
 except ProcessLookupError:checks.append('recorded original group nowabsent '+str(group))
 else:raise AssertionError('group present')
ok(not Path(term['cleanup']['cgroup']).exists(),'original native cgroup nowabsent')
(D/'READBACK02.json').write_text(json.dumps({'checks':len(checks),'checks_detail':checks,'runtime_RECORD_bodies_recovered':False,'runtime_distribution_bodies_validated':False,'runtime_metadata_pins_preserved':251,'genuine_source_pins':338,'runtime_API_sources':7,'inputs':8,'genuine_claims':2,'highest_actual_allowance':19,'native_checkpoint_decoded':False},sort_keys=True,indent=2)+'\n');print(json.dumps({'checks':len(checks)}))
