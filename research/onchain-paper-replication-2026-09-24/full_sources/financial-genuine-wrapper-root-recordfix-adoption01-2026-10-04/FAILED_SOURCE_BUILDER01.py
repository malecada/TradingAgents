import ast,copy,datetime,hashlib,json,os,shutil,stat,subprocess
from pathlib import Path
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');B=M/'research/onchain-paper-replication-2026-09-24/full_sources';OLD=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source');NEW=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source');D=B/'financial-genuine-wrapper-root-recordfix-adoption01-2026-10-04';P=B/'financial-genuine-wrapper-recordfix-registration-preparation02-2026-10-04';REV=B/'financial-genuine-wrapper-recordfix-registration-review02-2026-10-04';REC=B/'financial-genuine-wrapper-first-attempt-actual-recovery-review01-2026-10-04';COR=B/'financial-genuine-wrapper-runtime-record-correction01-2026-10-04';PREFIX='fixture_inputs/financial_wrapper_recordfix01';ID='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01';FAILED='financial-wrapper-classification-eager-interrupt1-20261003-01';PATH='tradingagents/research/onchain_replication/financial_wrapper_fixture.py';GATE=PREFIX+'/gates.json';FILE=4*1024**2

def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<=FILE and p.resolve()==p,(p,s.st_size);return p.read_bytes()
def enc(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def put(p,v):
 with p.open('xb') as f:f.write(enc(v))
def git(root,args,limit=FILE):
 q=subprocess.run(['git','-c','core.hooksPath=/dev/null',*args],cwd=root,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60);assert q.returncode==0,(args,q.stderr.decode());assert len(q.stdout)<=limit;return q.stdout
assert not os.path.lexists(D) and not os.path.lexists(NEW.parent);assert shutil.disk_usage(M).free>=10*1024**3
assert sha(read(P/'MANIFEST02.json'))=='08af38d682eaf9af0a79be8ed6347be4516d6d87f47ecaa8213ffba6bc4fdafb'
assert sha(read(REV/'MANIFEST02.json'))=='cb2bf34865ee6ca7cf5f8729e01277fe10658792c3ce5ce8aa970a6db75681aa'
assert json.loads(read(REV/'REVIEW02.json'))['verdict']=='ACCEPTED_SOURCE_ONLY_DRAFT_OPERATIONAL_ACCOUNTING'
assert sha(read(REC/'MANIFEST02.json'))=='ca360ddc266f4a81740707a1c3d957758554d2d53f2ae339236ba333185265ee'
r=json.loads(read(REC/'FLAT_READBACK02.json'));assert r['decision']=='FAILED_SCOPE_BYTE_UNION_ACCEPTED' and r['flat_receipt_sha256']=='2eb6546ab3e3953847610d328c301129441d38afa9f0fb8eeca056a192264f49'
assert sha(read(B/'financial-genuine-wrapper-runtime-record-review01-2026-10-04/MANIFEST01.json'))=='0f831ce02ebd367337a1d33078b6b781cc70379641494416906388c8fd2f93a7'
assert git(OLD,['rev-parse','HEAD'],128).decode().strip()=='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0'
assert not git(OLD,['status','--porcelain'])
original_names=git(OLD,['ls-files','-z']).decode().split('\0')[:-1];assert len(original_names)==290
original={n:sha(read(OLD/n)) for n in original_names};original_gate='fixture_inputs/financial_wrapper_registration01/gates.json';assert original[original_gate]=='6818dfdc48879fde8bf149bd1dae252885c6460a209e31af5a17a66012247691'
assert not os.path.lexists(OLD/'research_runs') and not os.path.lexists(OLD/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID)
# Only selected job module argv are inspected; no general process or credential content is printed.
active=[]
for child in Path('/proc').iterdir():
 if child.name.isdecimal():
  try:argv=(child/'cmdline').read_bytes().split(b'\0')
  except (PermissionError,ProcessLookupError,FileNotFoundError):continue
  if b'tradingagents.research.onchain_replication.job' in argv and any(str(p).encode() in argv for p in (OLD,NEW)):active.append(int(child.name))
assert not active
D.mkdir(mode=0o700);put(D/'INTENT01.json',{'one_use':True,'kind':'ordinary-isolated-source-and-operational-registration-adoption','time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'old_source':'d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0','old_permanently_reserved_identity':FAILED,'fresh_identity':ID,'target':str(NEW),'failed_scope_acceptance_manifest_sha256':'ca360ddc266f4a81740707a1c3d957758554d2d53f2ae339236ba333185265ee','actual_numerical_claims_before':0,'actual_numerical_ceiling':18,'native_or_claim_started':False})
NEW.parent.mkdir(mode=0o700)
clone=subprocess.run(['git','-c','core.hooksPath=/dev/null','clone','--no-hardlinks','--quiet',str(OLD),str(NEW)],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60);(D/'CLONE01.out').write_bytes(clone.stdout);(D/'CLONE01.err').write_bytes(clone.stderr);assert clone.returncode==0
assert git(NEW,['rev-parse','HEAD'],128).decode().strip()=='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0'
assert all(sha(read(NEW/n))==pin for n,pin in original.items())
correction=read(COR/'candidate.py');assert sha(correction)=='e2d9208ac51fd5876b63b6a72f734fc4fedd28fa42ac9c7fa1014346feb8404c';ast.parse(correction.decode());(NEW/PATH).write_bytes(correction)
prep=json.loads(read(P/'generated01/PREPARATION01.json'));roles=prep['role_body_pins'];assert len(roles)==8 and prep['release'] is False
for n,pin in sorted(roles.items()):
 raw=read(P/'generated01/bodies'/n);assert sha(raw)==pin;p=NEW/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw)
 os.chmod(p,0o644)
root=NEW/PREFIX
supports={
 'registration-review':(REV,['REVIEW02.json','REVIEW02.md','MANIFEST02.json','CHECKS01.json','DAG01.json']),
 'runtime-review':(B/'financial-genuine-wrapper-runtime-record-review01-2026-10-04',['REVIEW01.json','REVIEW01.md','MANIFEST01.json','ACTUAL_REVIEW01.json']),
 'operational-investigation':(B/'financial-genuine-wrapper-zero-claim-extension-investigation01-2026-10-04',['REPORT01.md','READBACK01.json','MANIFEST01.json']),
 'failed-recovery-review':(REC,['REMOTE_READBACK01.json','REMOTE_REVIEW01.md','MANIFEST01.json','FLAT_READBACK02.json','FLAT_REVIEW02.md','MANIFEST02.json']),
 'failed-remote':(B/'financial-genuine-wrapper-root-remote-recovery04-2026-10-04',['REMOTE_RECOVERY01.json','ACTUAL_TERMINAL01.json']),
 'failed-flat':(B/'financial-genuine-wrapper-root-flat-recovery04-2026-10-04',['RECOVERY01.json','ACTUAL_TERMINAL01.json'])}
copied=[]
for label,(base,names) in supports.items():
 for n in names:
  raw=read(base/n);target=root/label/n;target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as f:f.write(raw)
  os.chmod(target,0o644);copied.append({'path':target.relative_to(NEW).as_posix(),'original_path':str(base/n),'sha256':sha(raw),'bytes':len(raw),'body_scope':'Exact review/receipt metadata only; original full witness trees remain preserved in Main.'})
for n in ('DEPENDENT_REBINDINGS_DRAFT.json','ORIGINAL_PHASES_PRESERVED.json'):
 with (root/n).open('xb') as f:f.write(read(P/'generated01'/n))
 os.chmod(root/n,0o644)
amend=json.loads(read(P/'generated01/OPERATIONAL_AMENDMENT_DRAFT.json'))
amend.update(status='FROZEN_OPERATIONAL_SOURCE_CORRECTION_WITHOUT_NUMERICAL_RELEASE',actual_adoption={'kind':'source-and-metadata-only','time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'implementation_body_sha256':sha(correction),'original_source':'d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0','new_source_design_binding':'genuine committed current/design source must be independently verified; no self-referential commit field'},independent_amendment_review={'path':PREFIX+'/registration-review/REVIEW02.json','sha256':sha(read(REV/'REVIEW02.json'))},original_failed_scope_acceptance={'path':PREFIX+'/failed-recovery-review/FLAT_READBACK02.json','sha256':sha(read(REC/'FLAT_READBACK02.json'))},original_failed_scope_full_recovery={'remote':{'path':PREFIX+'/failed-remote/REMOTE_RECOVERY01.json','sha256':sha(read(B/'financial-genuine-wrapper-root-remote-recovery04-2026-10-04/REMOTE_RECOVERY01.json'))},'flat':{'path':PREFIX+'/failed-flat/RECOVERY01.json','sha256':sha(read(B/'financial-genuine-wrapper-root-flat-recovery04-2026-10-04/RECOVERY01.json'))}})
assert amend['numerical_attempt_budget']==18 and amend['numerical_claims_before']==0 and amend['defined_identity_count']==19 and amend['prospective_numerical_phase_count']==18
put(root/'OPERATIONAL_AMENDMENT01.json',amend)
charter=copy.deepcopy(json.loads(read(OLD/'fixture_inputs/financial_wrapper_registration01/CHARTER02.json')))
charter['operational_source_correction']={'amendment':{'path':PREFIX+'/OPERATIONAL_AMENDMENT01.json','sha256':sha(read(root/'OPERATIONAL_AMENDMENT01.json'))},'original_charter_sha256':original['fixture_inputs/financial_wrapper_registration01/CHARTER02.json'],'permanently_reserved_unavailable_outer_identity':FAILED,'fresh_fixed_initial_identity':ID,'numerical_attempt_budget_unchanged':18,'genuine_numerical_claims_before':0,'operational_identity_definitions':19,'prospective_numerical_phases':18,'source_body_change':{'path':PATH,'sha256':sha(correction)},'no_spent_claim_refund_or_transfer':True,'old_gate_entries_are_historical_not_currently_executable':True,'runtime_metadata_assumption':'Pinned CPython3.13.13 PathDistribution._path installed-origin selection; vendored RECORD inventory is not top-level distribution origin. All251 original pins remain unchanged.','full_witness_tree_location':'Original closed author/reviewer witness trees are preserved in Main; this source installs exact metadata bodies only. No runtime bodies or empirical stores were recovered.'}
assert charter['base_attempt_budget']==18 and charter['prior_attempts']==0
put(root/'CHARTER01.json',charter)
# Exact finite staged file scope. New gate alone is excluded from its own map.
existing=git(NEW,['ls-files','-z']).decode().split('\0')[:-1];added=[str(p.relative_to(NEW)) for p in root.rglob('*') if p.is_file()];names=sorted(set(existing+added));assert GATE not in names
pins={n:sha(read(NEW/n)) for n in names}
gate=json.loads(read(P/'generated01/GATE_DRAFT.json'));orig_gate=json.loads(read(OLD/original_gate));assert all(gate['experiments'][n]==v for n,v in orig_gate['experiments'].items()) and gate['families']==orig_gate['families']
exp=gate['experiments'][ID];exp['charter']={'path':PREFIX+'/CHARTER01.json','sha256':sha(read(root/'CHARTER01.json'))};exp['source_files']=pins;assert 'cumulative_budget_extension' not in exp and len(gate['experiments'])==11
put(NEW/GATE,gate)
for n in names+[GATE]:assert len(read(NEW/n))<=FILE
for start in range(0,len(names)+1,96):git(NEW,['add','-f','--',*(names+[GATE])[start:start+96]])
git(NEW,['diff','--cached','--check','--',PATH]);git(NEW,['commit','-q','-m','fix(research): bind unique installed runtime RECORD without resetting wrapper budget'])
head=git(NEW,['rev-parse','HEAD'],128).decode().strip();assert head!='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0' and not git(NEW,['status','--porcelain'])
tracked=git(NEW,['ls-files','-z']).decode().split('\0')[:-1];assert set(tracked)==set(names+[GATE])
assert len([n for n in original_names if sha(read(NEW/n))!=original[n]])==1 and sha(read(NEW/PATH))==sha(correction)
for n,pin in original.items():assert sha(read(OLD/n))==pin
assert git(OLD,['rev-parse','HEAD'],128).decode().strip()=='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0' and not git(OLD,['status','--porcelain'])
assert not os.path.lexists(NEW/'research_runs') and not os.path.lexists(NEW/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID)
put(D/'SOURCE_ADOPTION01.json',{'status':'ACTUAL_SOURCE_AND_OPERATIONAL_REGISTRATION_FROZEN_NOT_NUMERICALLY_RELEASED','source':head,'design_source':head,'root':str(NEW),'original_source':'d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0','tracked':len(tracked),'source_pins':len(pins),'implementation':194,'package':149,'implementation_changed':1,'implementation_unchanged':193,'original290_paths_preserved':True,'original_gate_entries_preserved':10,'new_gate_entries':11,'registration':GATE,'registration_sha256':sha(read(NEW/GATE)),'source_files':pins,'role_hashes':roles,'copied_metadata_support':copied,'numerical_attempt_budget':18,'prior_attempts':0,'actual_numerical_claims':0,'operational_identity_definitions':19,'prospective_numerical_phases':18,'old_permanently_reserved_identity':FAILED,'fresh_identity':ID,'new_caller':None,'independent_actual_source_admission_review':None,'actual_external_recovery':None,'native_or_claim_started':False,'qualified_mode_mapping':'Portable new role/support files installed0644/Git100644; original bodies remain unchanged. Clone local origin is provenance, not an external backup. Full review witness trees, installed runtime bodies and empirical stores are not inside this capsule.'})
print(json.dumps({'source':head,'tracked':len(tracked),'pins':len(pins),'gate_sha256':sha(read(NEW/GATE)),'actual_claims':0,'target':str(NEW)}))
