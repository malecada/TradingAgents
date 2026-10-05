from pathlib import Path
import ast,hashlib,json,os,shutil,stat,datetime
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=Path(__file__).parent;R=F/'financial-wrapper-serialized-prediction-source-remote01-2026-10-05';B=F/'financial-wrapper-serialized-continuation-outcome-remote-lane03-2026-10-05'
sha=lambda b:hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes())}
old=(B/'recover01.py').read_text();new=(R/'recover01.py').read_text();assert sha(old.encode())=='29b2202cfff0b3046447f5053c7e8d8fdf02281bf50078d3b2f53d6d9984b38b';assert sha(new.encode())=='577172243f895972f8691538e1e6d975bd68c71c616ffea55a5b937b3bde9c8b'
tree=ast.parse(new);assigns=[n for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='REQUIRED'];assert len(assigns)==2;required=ast.literal_eval(assigns[-1].value)
lines=new.splitlines(True);del lines[assigns[-1].lineno-1:assigns[-1].end_lineno];inverse=''.join(lines).replace('FINAL_POPULATION_COUNT = 11','FINAL_POPULATION_COUNT = 12').replace('fresh-serialized-prediction-source01.git','fresh-serialized-continuation-outcome-lane03.git').replace('fresh-actual-serialized-prediction-source01-recovered','fresh-actual-serialized-continuation-outcome-lane03-recovered')
def qualification(t):
 return next(ast.literal_eval(v) for n in ast.walk(ast.parse(t)) if isinstance(n,ast.Dict) for k,v in zip(n.keys,n.values) if isinstance(k,ast.Constant) and k.value=='qualification')
inverse=inverse.replace(repr(qualification(new)),repr(qualification(old)));assert inverse==old
for n,p in [('watch01.py','121a443011f6a95f6e5ec84fedd6a06c51e328d1d317cdf445b77ef192b20795'),('utilities/owned_io.py','09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb')]:assert (R/n).read_bytes()==(B/n).read_bytes() and sha((R/n).read_bytes())==p
raw=(R/'SELECTED_BODIES01.json').read_bytes();assert sha(raw)=='edf64fee98876ce93bfce6f102434b64b522912465db083f54d8e21b0989d3e0';s=json.loads(raw);assert len(s['rows'])==len(required)==11 and sum(r['bytes'] for r in s['rows'])==831068
assert {r['path']:{k:v for k,v in r.items() if k!='path'} for r in s['rows']}==required
for row in s['rows']:
 b=(M/row['path']).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256'] and len(b)<=4194304
confirmation=F/'heartbeat-root-checkpoint10-2026-10-04/REMOTE_CONFIRMATION77.json';c=json.loads(confirmation.read_bytes());assert c['actual_remote_HEAD']==c['commit']==s['remote_commit']=='5642fcb3842cfb38bfa82927b5dd532d2340ecee' and c['push_actual_exit']==c['read_actual_exit']==0
absent=['fresh-serialized-prediction-source01.git','selected','REMOTE_RECOVERY01.json','FAILED01.json','ACTUAL_ROOT_EXIT01.json'];assert all(not os.path.lexists(R/n) for n in absent)
active=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  args=(p/'cmdline').read_bytes().split(b'\0')
  if any(x.endswith(b'/recover01.py') and b'financial-wrapper-' in x for x in args):active.append(int(p.name))
 except (FileNotFoundError,PermissionError,ProcessLookupError):pass
assert not active
free=shutil.disk_usage(R).free;assert free>=10737418240
check={'schema_version':1,'decision':'accepted-exact-source-retrieval-source-and-selection','source':ref(R/'recover01.py'),'baseline':ref(B/'recover01.py'),'selection':ref(R/'SELECTED_BODIES01.json'),'literal_inverse_exact':True,'population':11,'bytes':831068,'expected_operations':43,'qualification':'Five new nonnull inputs embedded in actual selected bound draft. Two new policy proofs excluded. No complete current capsule or final release recovery claim.','unchanged_watch':ref(R/'watch01.py'),'unchanged_owned_io':ref(R/'utilities/owned_io.py'),'original_obsolete_REQUIRED_literal':'Retained baseline assignment is overwritten before main; exact effective REQUIRED independently joined to selected11.'}
with (D/'SOURCE_REMOTE_SOURCE_CHECK01.json').open('x') as h:h.write(json.dumps(check,sort_keys=True,indent=2)+'\n')
release={'schema_version':1,'decision':'ACCEPTED_EXACT_ONCE_PREDICTION_SOURCE_RETRIEVAL','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cwd':str(M),'argv':[str(M/'.venv/bin/python'),'-B',str(R/'recover01.py'),'--selection-sha256',sha(raw)],'owned_root':str(R),'source_sha256':sha(new.encode()),'selection_sha256':sha(raw),'commit':s['remote_commit'],'population':11,'bytes':831068,'expected_operations':43,'actual_confirmation':ref(confirmation),'source_check':ref(D/'SOURCE_REMOTE_SOURCE_CHECK01.json'),'free_disk_bytes':free,'fresh_namespaces_absent':absent,'active_receiver_pids':active,'unchanged_limits':{'whole_seconds':600,'Git_seconds':60,'logical':67108864,'allocated':100663296,'per_file':4194304,'floor':10737418240},'numerical_authority':False,'qualification':'Root may run this exact receiver once. Failure retained; no namespace reuse. Actual receipt and recovered bytes must be reviewed before any source recovery proof. No Admission/native/financial/current-capsule release.'}
with (D/'SOURCE_REMOTE_ENTRY_RELEASE01.json').open('x') as h:h.write(json.dumps(release,sort_keys=True,separators=(',',':'))+'\n')
print(json.dumps({'sourcecheck':ref(D/'SOURCE_REMOTE_SOURCE_CHECK01.json'),'entry':ref(D/'SOURCE_REMOTE_ENTRY_RELEASE01.json'),'free':free}))
