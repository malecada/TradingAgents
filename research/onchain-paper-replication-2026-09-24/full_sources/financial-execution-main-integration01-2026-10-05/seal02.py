"""Authenticate copied source origins and freeze a finite seven-module integration."""
import ast,difflib,hashlib,json,stat,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[3];REL=Path('tradingagents/research/onchain_replication')
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 if not isinstance(b,(bytes,str)):b=json.dumps(b,sort_keys=True,indent=2)+'\n'
 with (H/n).open('xb') as f:f.write(b.encode() if isinstance(b,str) else b)
def info(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b),'mode':stat.S_IMODE(p.stat().st_mode)}
def git(root,*args):
 r=subprocess.run(['git','-C',str(root),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=True);assert len(r.stdout)<=4*1024**2;return r.stdout
heads={'Main':git(ROOT,'rev-parse','HEAD').decode().strip(),'CAP':git(CAP,'rev-parse','HEAD').decode().strip()}
assert heads['CAP']=='d4c81c0961342bfe4c5771aabbef1d46a14cffb8'
names=sorted(p.name for p in (H/'candidate').glob('*.py'));assert len(names)==7
origins={};inverses={};patch=[]
for n in names:
 new=(H/'candidate'/n).read_text();row={'candidate':info(H/'candidate'/n)};inverses[n]={}
 for label,root in [('Main',ROOT),('CAP',CAP)]:
  p=H/'origins'/label/n
  if not p.exists():
   assert label=='Main' and n=='financial_execution.py' and not (root/REL/n).exists()
   row[label]={'path':str(root/REL/n),'absent':True};old=''
  else:
   old=p.read_text();assert (root/REL/n).read_bytes()==p.read_bytes(),'source changed during preparation'
   committed=git(root,'show','HEAD:'+str(REL/n));assert committed==p.read_bytes(),'origin not exact current Git body'
   row[label]={**info(root/REL/n),'commit':heads[label],'git_blob':hashlib.sha1(b'blob '+str(len(committed)).encode()+b'\0'+committed).hexdigest()}
  segments=[];inverse=[]
  for tag,a,b,c,d in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
   if tag=='equal':inverse.append(new[c:d])
   else:segments.append({'original_offsets':[a,b],'candidate_offsets':[c,d],'original':old[a:b],'candidate':new[c:d]});inverse.append(old[a:b])
  reconstructed=''.join(inverse);assert reconstructed==old
  assert ast.dump(ast.parse(reconstructed))==ast.dump(ast.parse(old))
  inverses[n][label]={'literal_segments':segments,'full_byte_inverse':True,'full_AST_inverse':True,'original_sha256':sha(old.encode()),'candidate_sha256':sha(new.encode())}
  if label=='Main':patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='/dev/null' if not p.exists() else 'a/'+str(REL/n),tofile='b/'+str(REL/n)))
 origins[n]=row
unchanged={}
for n in ('model.py','streamed_gat.py','gat.py','pooling.py','temporal.py','feature_residency.py','training_batch_observer.py','treatment_admission.py'):
 p=ROOT/REL/n;unchanged[n]={'Main':info(p)}
 if (CAP/REL/n).exists():unchanged[n]['CAP']=info(CAP/REL/n)
for n in ('model.json','training.json'):
 p=Path('research/onchain-paper-replication-2026-09-24/config')/n
 cp=CAP/'fixture_inputs/financial_wrapper_compatibility01'/n
 unchanged[str(p)]={'Main':info(ROOT/p),'CAP':info(cp)}
 assert (ROOT/p).read_bytes()==cp.read_bytes()
put('SOURCE_ORIGINS01.json',{'schema_version':1,'heads':heads,'modules':origins,'untouched_dependencies':unchanged})
put('SOURCE_INVERSE01.json',{'schema_version':1,'modules':inverses,'qualification':'Literal inverse authenticates the entire original body, including all unrelated Main and CAP differences; only the seven candidate bodies are proposed.'})
put('MAIN_INTEGRATION01.patch',''.join(patch))
checks=json.loads((H/'CHECK02.stdout').read_bytes());assert checks['passed']==68
put('REPORT01.md','''# Main financial execution integration candidate

Seven complete candidate modules connect the accepted optional financial execution backend to Main fitting, checkpointing, replay and batch evaluation. Four are byte-identical to the genuine committed CAP d4c81c0: financial_execution.py, model_registry.py, checkpoints.py and replay.py. The new module authenticates the fixed streamed source/policy and retains private constructor/model contract pins. Selected execution metadata is validated and persisted through checkpoint/replay paths. Legacy absent/None execution remains the default.

Training copies CAP's exact fit function while retaining Main's complete original _reserve and predict_cell. The two inserted model guards are the only training-loop AST differences from Main; optimizer, loss, gradients, clipping, chronology, batch size, seed, epoch/update/cursor and checkpoint scheduling are unchanged. The unrelated operational_source_compatibility branch is deliberately excluded because it is a separate CAP protocol and its helper is absent in Main.

run.py ports CAP's schema2 selection and admitted source checks, then supplies execution to evaluation. evaluation.py is the necessary seventh seam: it joins execution to provenance, selected construction, fitted/completed model validation and checkpoint-state validation. Main's mandatory treatment admission, common population masks, feature binding, detached feature residency, batch observer and newer storage handling are retained. Its entire batch_factory and feature_hash functions are AST-identical. Model/GAT/pooling/temporal sources, scientific model/training configuration and all live sources remain untouched.

SOURCE_ORIGINS01 pins actual Main/CAP committed source bodies and unchanged dependencies. SOURCE_INVERSE01 supplies complete reversible literal segments and AST inverses to both originals. MAIN_INTEGRATION01.patch is the exact seven-file adoption patch; candidate/ contains full bodies. The Main HEAD and source hashes must still match before Root applies it. No fixture, gate, budget, Owner, Run, runtime package, empirical store or launcher is added or changed.

68 bounded controls passed: all source compilation, exact CAP copies, full training scientific AST preservation, Main treatment/observer/detached-function preservation, execution identity/policy/schema/arm refusals, checkpoint execution/contract presence, legacy None construction dispatch and keyword joins. The helper was actually imported alone with stdlib dependencies; no NumPy/Torch/SciPy/Pandas import occurred. The first harness stopped at a NameError in its diagnostic label; CHECK01 and check01.py are preserved, and check02 changes only those two labels.

Not tested: genuine framework model construction/private-pin mutation defenses, forward/backward/all-gradient numerical agreement, Adam/RNG equality, real save/load/replay, real continuation or prediction, full native fitting and whole-population capacity. Those require the separately admitted numerical workflow. The existing accepted CAP implementation is reused, but its synthetic/backend evidence is not a fresh Main scientific outcome. Actual public admission, frozen source closure, caller/native limits and complete recovery remain Root responsibilities. No currentness, writer exclusion, saving, runtime capacity or paper-fit credit is inferred.
''')
machine={'schema_version':1,'decision':'IMPLEMENTED_SOURCE_CANDIDATE_PENDING_INDEPENDENT_REVIEW','author':'combined_worker_review','heads':heads,'candidate_files':{n:info(H/'candidate'/n) for n in names},'exact_CAP_modules':['financial_execution.py','model_registry.py','checkpoints.py','replay.py'],'Main_reserve_preserved':True,'Main_observer_treatment_detached_preserved':True,'numerical_training_AST_unchanged_except_two_guards':True,'tests_passed':68,'failed_harness_preserved':['check01.py','CHECK01.stdout','CHECK01.stderr'],'source_origins':info(H/'SOURCE_ORIGINS01.json'),'inverse':info(H/'SOURCE_INVERSE01.json'),'patch':info(H/'MAIN_INTEGRATION01.patch'),'report':info(H/'REPORT01.md'),'live_installation':False,'numerical_execution':False,'scientific_authority':False}
put('MACHINE01.json',machine)
rows=[]
for p in sorted(H.rglob('*')):
 s=p.lstat();r={'path':p.relative_to(H).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):r['kind']='directory'
 elif stat.S_ISREG(s.st_mode):
  b=p.read_bytes();assert len(b)<=4*1024**2;r.update(kind='file',bytes=len(b),sha256=sha(b))
 else:raise ValueError('unexpected evidence member')
 rows.append(r)
put('MANIFEST01.json',{'schema_version':1,'root_mode':stat.S_IMODE(H.stat().st_mode),'members':rows,'scope':'complete source candidate and all raw preparation/control evidence; self excluded','numerical_authority':False})
print(json.dumps({n:info(H/n) for n in ('MANIFEST01.json','MACHINE01.json','MAIN_INTEGRATION01.patch')},sort_keys=True))
