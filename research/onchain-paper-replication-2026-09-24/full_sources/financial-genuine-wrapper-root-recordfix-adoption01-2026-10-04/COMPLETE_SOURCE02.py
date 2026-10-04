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

assert shutil.disk_usage(M).free>=10*1024**3
original_names=git(OLD,['ls-files','-z']).decode().split('\0')[:-1];assert len(original_names)==290
original={n:sha(read(OLD/n)) for n in original_names};original_gate='fixture_inputs/financial_wrapper_registration01/gates.json'
assert original[original_gate]=='6818dfdc48879fde8bf149bd1dae252885c6460a209e31af5a17a66012247691'
correction=read(COR/'candidate.py');assert sha(correction)=='e2d9208ac51fd5876b63b6a72f734fc4fedd28fa42ac9c7fa1014346feb8404c'
prep=json.loads(read(P/'generated01/PREPARATION01.json'));roles=prep['role_body_pins'];root=NEW/PREFIX
for n,pin in roles.items():assert sha(read(NEW/n))==pin
assert json.loads(read(REC/'FLAT_READBACK02.json'))['decision']=='FAILED_SCOPE_BYTE_UNION_ACCEPTED'
partial=json.loads(read(D/'PARTIAL_SOURCE_OBSERVATION02.json'))
for row in partial['exact33_prefix_files']:assert sha(read(NEW/row['path']))==row['sha256']
assert git(NEW,['rev-parse','HEAD'],128).decode().strip()=='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0' and not git(NEW,['diff','--cached','--name-only'])
assert not os.path.lexists(NEW/'research_runs') and not os.path.lexists(root/'CHARTER01.json') and not os.path.lexists(NEW/GATE)
copied=json.loads(read(D/'SUPPORT_SCOPE02.json'))['copied_metadata_support']
charter=copy.deepcopy(json.loads(read(OLD/'fixture_inputs/financial_wrapper_registration01/CHARTER02.json')))
charter['operational_source_correction']={'amendment':{'path':PREFIX+'/OPERATIONAL_AMENDMENT01.json','sha256':sha(read(root/'OPERATIONAL_AMENDMENT01.json'))},'original_charter_sha256':original['fixture_inputs/financial_wrapper_registration01/CHARTER02.json'],'permanently_reserved_unavailable_outer_identity':FAILED,'fresh_fixed_initial_identity':ID,'numerical_attempt_budget_unchanged':18,'genuine_numerical_claims_before':0,'operational_identity_definitions':19,'prospective_numerical_phases':18,'source_body_change':{'path':PATH,'sha256':sha(correction)},'no_spent_claim_refund_or_transfer':True,'old_gate_entries_are_historical_not_currently_executable':True,'runtime_metadata_assumption':'Pinned CPython3.13.13 PathDistribution._path installed-origin selection; vendored RECORD inventory is not top-level distribution origin. All251 original pins remain unchanged.','full_witness_tree_location':'Original closed author/reviewer witness trees are preserved in Main; this source installs exact metadata bodies only. No runtime bodies or empirical stores were recovered.'}
put(D/'COMPLETION_INTENT02.json',{'kind':'separate bounded completion of authenticated uncommitted Root-owned source assembly','original_builder_closed':True,'clone_or_assembly_repeated':False,'native_or_claim_started':False,'fixed_charter_field':'prior_same_mechanism_attempts'})
assert charter['base_attempt_budget']==18 and charter['prior_same_mechanism_attempts']==0
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
