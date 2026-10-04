"""Prepare exact gate bytes after genuine accepted composed recovery.

This writes a new review directory only. It never adopts a gate, creates an
Admission/Owner/ResearchRun, starts numerical work or changes a historical file.
"""
from pathlib import Path
import argparse, copy, datetime, hashlib, json, os, stat, subprocess

ROOT=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
FS=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
PREP=FS/'financial-wrapper-compatibility-registration-preparation01-2026-10-04'
DEST=FS/'financial-wrapper-compatibility-gate-preview01-2026-10-04'
NEW='fixture_inputs/financial_wrapper_compatibility01'
OLD='fixture_inputs/financial_wrapper_claimedrun01/gates.json'
POLICY='ae8fbdc9d13e75fc453b70b5ee633c89fb4577e9b68a35b4147cf1bbd58c6887'
OLD_GATE='752c34dfad4df2ca36b5dc4dcb999846f8de01bd1a61c5356092c4e55fbd678c'
CURRENT='7b056a574e3e7b3c7ba209a39ee6a615e649d60c'
HELPER='d0d770b45def89e8e00e81fa1bbb35416034eaace5ecab0f15193fd43b7a32d8'
def sha(b):return hashlib.sha256(b).hexdigest()
def encode(v):return (json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def read(p):
    p=Path(p);s=p.lstat()
    assert p.is_absolute() and p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304
    before=tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
    raw=p.read_bytes();after=p.lstat()
    assert tuple(getattr(after,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))==before
    return raw
def protected(name):
    return any(p.lower() in ('keys','apis','.env','.ssh','hf_token.txt','.venv','node_modules') or p.lower().endswith(('.pem','.key')) for p in Path(name).parts)

args=argparse.ArgumentParser()
for name in ('recovery-proof','recovery-machine','recovery-manifest','recovery-report'):args.add_argument('--'+name,required=True)
a=args.parse_args(); paths={k:Path(getattr(a,k.replace('-','_'))).absolute() for k in ('recovery-proof','recovery-machine','recovery-manifest','recovery-report')}
raw={k:read(p) for k,p in paths.items()};proof=json.loads(raw['recovery-proof']);machine=json.loads(raw['recovery-machine']);manifest=json.loads(raw['recovery-manifest'])
policy_raw=read(PREP/NEW/'policy.json');assert sha(policy_raw)==POLICY;policy=json.loads(policy_raw)
expected={'schema_version':1,'kind':'operational_source_compatibility_recovery','policy_sha256':POLICY,'checker_sha256':HELPER,'historical_map_sha256':sha(canonical(policy['historical']['installed'])),'target_map_sha256':sha(canonical(policy['target']['installed'])),'decision':'accepted'}
assert proof==expected and machine['decision']=='ACCEPTED_ACTUAL_OPERATIONAL_SOURCE_POLICY_BYTE_RECOVERY'
assert machine['recovery_proof_sha256']==sha(raw['recovery-proof']) and machine['report_sha256']==sha(raw['recovery-report'])
for k in ('schema_version','policy_sha256','checker_sha256','historical_map_sha256','target_map_sha256'):assert machine[k]==expected[k]
for name,p in paths.items():
    if name=='recovery-manifest':continue
    assert p.parent==paths['recovery-manifest'].parent
    assert any(x.get('kind')=='file' and x.get('path')==p.name and x.get('sha256')==sha(raw[name]) and x.get('bytes')==len(raw[name]) for x in manifest['members'])
receipts=machine['recovery_receipts'];assert isinstance(receipts,list) and receipts and len({json.dumps(x,sort_keys=True) for x in receipts})==len(receipts)
for ref in receipts:
    assert set(ref)=={'path','sha256'} and sha(read(Path(ref['path'])))==ref['sha256']
    rel=Path(ref['path']).relative_to(paths['recovery-manifest'].parent).as_posix()
    assert any(x.get('path')==rel and x.get('sha256')==ref['sha256'] and x.get('kind')=='file' for x in manifest['members'])
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=CAP,text=True).strip()==CURRENT
assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=CAP)
gate_raw=read(CAP/OLD);assert sha(gate_raw)==OLD_GATE
gate=json.loads(gate_raw);draft=json.loads(read(PREP/'EXPERIMENT_DRAFT_NOT_REGISTRATION01.json'))
assert draft['status']=='DRAFT_NOT_REGISTRATION_NOT_ADMITTED_NOT_NUMERICALLY_RELEASED'
identity=draft['identity'];assert identity==policy['consumers']['complete100']['experiment'] and identity not in gate['experiments']
assert not os.path.lexists(CAP/'research_runs'/identity) and not os.path.lexists(CAP/NEW) and not os.path.lexists(DEST)
files={}
for p in sorted((PREP/NEW).iterdir()):
    assert p.is_file();files[NEW+'/'+p.name]=read(p)
assert len(files)==13
files[NEW+'/policy-recovery.json']=raw['recovery-proof']
assert len(files)==14
names=subprocess.check_output(['git','ls-files','-z'],cwd=CAP).split(b'\0');names=[n.decode() for n in names if n];assert len(names)==340
assert all(not protected(n) for n in names)
source_files={name:sha(read(CAP/name)) for name in names}
source_files.update({name:sha(body) for name,body in files.items()});assert len(source_files)==354
experiment=copy.deepcopy(draft['experiment']);experiment['source_files']=source_files
for role,ref in experiment['inputs'].items():
    assert ref['path'] in files and sha(files[ref['path']])==ref['sha256']
experiment['inputs']['operational_source_compatibility_recovery']={'dataset':'synthetic','path':NEW+'/policy-recovery.json','sha256':sha(raw['recovery-proof'])}
assert len(experiment['inputs'])==11 and experiment['parent'] is None
assert experiment['cells']==[policy['consumers']['complete100']['cell_id']]
for path,pin in policy['target']['installed'].items():assert source_files[path]==pin
assert json.loads(files[NEW+'/wrapper_plan.json'])['experiment']==identity
old_exp=copy.deepcopy(gate['experiments']);gate['experiments'][identity]=experiment
assert all(gate['experiments'][k]==v for k,v in old_exp.items()) and len(old_exp)==12
assert gate['families']['synthetic-financial-wrapper']['attempt_budget']==18 and gate['families']['synthetic-financial-wrapper']['prior_attempts']==0
assert sha(files[NEW+'/extension20.json'])=='07100b23f9a8c2dfcae98a8647f9f1eeb019f4093192cd4b2576c6a13bf9840e'
assert sha(files[NEW+'/allocation20.json'])=='461df69895a0a5e70b23882c759790a4c000eb33d1662629cacd322b7d3b0116'
assert sha(files[NEW+'/extension-review20.json'])=='b5ac7652631ba25296003580774e29b9f0e555a3ed4ef5d2323576099c39f389'
files[NEW+'/gates.json']=encode(gate)
assert len(files)==15
DEST.mkdir(mode=0o700)
for name,body in files.items():
    p=DEST/name;p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    with p.open('xb') as f:f.write(body)
with (DEST/'PREVIEW01.json').open('x') as out:
    json.dump({'schema_version':1,'status':'CONCRETE_GATE_PREVIEW_NOT_ADOPTED','time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_before':CURRENT,'root':str(CAP),'old_gate_sha256':OLD_GATE,'new_gate_path':NEW+'/gates.json','new_gate_sha256':sha(files[NEW+'/gates.json']),'identity':identity,'parent':None,'roles':11,'existing_tracked':340,'new_files':15,'prospective_tracked':355,'source_pins':354,'old_experiments_preserved':12,'actual_highest':19,'prospective_amendment':20,'actual_recovery_refs':{k:{'path':str(paths[k]),'sha256':sha(v)} for k,v in raw.items()},'new_file_pins':{k:sha(v) for k,v in files.items()},'genuine_Admission_or_Owner_or_Run_created':False,'gate_or_budget_adopted':False,'paper_budget_changed':False},out,indent=2,sort_keys=True);out.write('\n')
print(json.dumps({'status':'CONCRETE_GATE_PREVIEW_NOT_ADOPTED','identity':identity,'new_files':15,'source_pins':354}))
