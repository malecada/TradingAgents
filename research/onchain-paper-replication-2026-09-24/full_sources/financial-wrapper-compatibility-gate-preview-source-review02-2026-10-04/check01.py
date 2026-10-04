from pathlib import Path
import ast,copy,hashlib,json,os,stat,subprocess
H=Path(__file__).resolve().parent;B=H.parent;C=B/'heartbeat-root-checkpoint10-2026-10-04';P=B/'financial-wrapper-compatibility-registration-preparation01-2026-10-04';CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');NEW='fixture_inputs/financial_wrapper_compatibility01';OLD='fixture_inputs/financial_wrapper_claimedrun01/gates.json';checks=[];cases=[];sha=lambda b:hashlib.sha256(b).hexdigest();enc=lambda x:(json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
old=(C/'root_compatibility_gate_preview01.py').read_bytes();new=(C/'root_compatibility_gate_preview02.py').read_bytes();ok(sha(new)=='8edbfb20abba29cea941203ad40b720730de89b643954f0730cea2a2127bd208','exact successor');ok(sha(old)=='845e744580b45228e9bcb19925dd9d4ed851ea6912e246287b6e447c6c620de6','exact original')
inv=json.loads((C/'ROOT_GATE_PREVIEW02_SOURCE_INVERSE01.json').read_bytes());text=new.decode()
for x in reversed(inv['replacement_segments']):ok(text[x['new_start']:x['new_end']]==x['new'],'literal inverse span');text=text[:x['new_start']]+x['old']+text[x['new_end']:]
ok(text.encode()==old and ast.dump(ast.parse(text))==ast.dump(ast.parse(old)),'full literal AST inverse')
t=ast.parse(new);oldtree=ast.parse(old);funcs=[n for n in t.body if isinstance(n,ast.FunctionDef)];ns={'Path':Path,'os':os,'stat':stat,'hashlib':hashlib,'json':json};exec(compile(ast.Module(body=funcs,type_ignores=[]),'actual exact pure functions','exec'),ns)
for name in ['PREP_DRAFT_PIN','PREP_BINDING_PIN','PREPARED_PINS','HISTORY_PINS','CURRENT']:
 node=next(n for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id==name for x in n.targets));ns[name]=ast.literal_eval(node.value)
start=next(i for i,n in enumerate(t.body) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='draft_raw' for x in n.targets));end=next(i for i,n in enumerate(t.body) if isinstance(n,ast.Assert) and ast.unparse(n.test)=='actual_highest == 19 and len(history) == 3');subset=t.body[start:end+1];code=compile(ast.Module(body=subset,type_ignores=[]),'exact02 pin/history block only','exec')
prepared={p.name:p.read_bytes() for p in (P/NEW).iterdir()};draft=json.loads((P/'EXPERIMENT_DRAFT_NOT_REGISTRATION01.json').read_bytes());binding=(P/'PREPARATION_BINDING01.json').read_bytes();policy=json.loads(prepared['policy.json']);actualns=dict(ns,PREP=P,CAP=CAP,NEW=NEW,policy=policy);exec(code,actualns);ok(actualns['actual_highest']==19 and len(actualns['history'])==3,'actual current history genuine3/highest19')
for n,pin in ns['PREPARED_PINS'].items():ok(sha(prepared[n])==pin,'actual exact13 body '+n)
allclaim={name:{leaf:(CAP/'research_runs'/name/leaf).read_bytes() for leaf in pins} for name,pins in ns['HISTORY_PINS'].items()}
def fixture(label,dr=None,files=None,history_edit=None,bind=None,extra=None):
 root=H/label;root.mkdir(mode=0o700);prep=root/'prep';(prep/NEW).mkdir(parents=True);cap=root/'cap';(cap/'research_runs').mkdir(parents=True);(cap/'research_runs/.lock').write_bytes(b'')
 for n,b in (prepared if files is None else files).items():(prep/NEW/n).write_bytes(b)
 (prep/'EXPERIMENT_DRAFT_NOT_REGISTRATION01.json').write_bytes((P/'EXPERIMENT_DRAFT_NOT_REGISTRATION01.json').read_bytes() if dr is None else enc(dr));(prep/'PREPARATION_BINDING01.json').write_bytes(binding if bind is None else bind)
 hist=copy.deepcopy(allclaim)
 if history_edit:history_edit(hist)
 for name,leaves in hist.items():
  p=cap/'research_runs'/name;p.mkdir()
  for leaf,b in leaves.items():(p/leaf).write_bytes(b)
 if extra:(cap/'research_runs'/extra).mkdir()
 return dict(ns,PREP=prep,CAP=cap,NEW=NEW,policy=policy)
def runfixture(label,**kwargs):
 n=fixture(label,**kwargs)
 try:exec(code,n)
 except (AssertionError,ValueError,OSError) as e:cases.append({'case':label,'refused':True,'type':type(e).__name__});return False
 cases.append({'case':label,'refused':False,'observed_spent':len(n['history']),'actual_highest':n['actual_highest']});return True
ok(runfixture('unchanged-real-byte-copies'),'unchanged exact copies pass')
# Reproduce original coherent assembly acceptance without public proof parser or authority output.
oldsub=[n for n in oldtree.body if 66<=n.lineno<=83];oldcode=compile(ast.Module(body=oldsub,type_ignores=[]),'exact original postauthority assembly only','exec')
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_ALLOW_PROTOCOL='')
def git(*a):
 p=subprocess.run(['git',*a],cwd=CAP,env=env,capture_output=True,timeout=10);ok(p.returncode==0 and len(p.stdout)<=4194304,'read-onlyGit '+a[0]);return p.stdout
ok(git('rev-parse','HEAD').decode().strip()==ns['CURRENT'] and git('status','--porcelain','--untracked-files=no')==b'','currentsourceclean');names=[x.decode() for x in git('ls-files','-z').split(b'\0') if x];ok(len(names)==340,'current340');gate=json.loads((CAP/OLD).read_bytes());ok(sha((CAP/OLD).read_bytes())=='752c34dfad4df2ca36b5dc4dcb999846f8de01bd1a61c5356092c4e55fbd678c','oldgate pin')
marker=b'opaque component marker; NOT an accepted recovery proof';identity=draft['identity']
for label,file,key,value in [('epochs','training.json','epochs',99),('seed','synthetic_recipe.json','seed',12),('execution','wrapper_plan.json','execution','selected'),('extension',None,None,None),('family',None,None,None)]:
 files=copy.deepcopy(prepared);dr=copy.deepcopy(draft)
 if file:
  o=json.loads(files[file]);o[key]=value;files[file]=enc(o)
  for ref in dr['experiment']['inputs'].values():
   if ref['path']==NEW+'/'+file:ref['sha256']=sha(files[file])
 elif label=='extension':dr['experiment'].pop('cumulative_budget_extension')
 else:dr['experiment']['family']='foreign-family'
 fs={NEW+'/'+n:b for n,b in files.items()};fs[NEW+'/policy-recovery.json']=marker
 oldns=dict(ns,CAP=CAP,NEW=NEW,names=names,files=fs,draft=dr,copy=copy,raw={'recovery-proof':marker},policy=policy,identity=identity,gate=copy.deepcopy(gate),encode=enc)
 exec(oldcode,oldns);ok(all(oldns['gate']['experiments'][n]==v for n,v in gate['experiments'].items()),'old drift retained12 '+label);cases.append({'case':'old-GP1-'+label,'original_component_accepted':True,'proof_parser_skipped':True,'no_gate_emitted':True})
 ok(not runfixture('new-GP1-'+label,dr=dr,files=files),'new frozenpins refuse coherent '+label)
# Coherent binding drift and independent body-only drift are both refused.
bd=json.loads(binding);bd['actual_spent_FAILED']=2;ok(not runfixture('binding-refund',bind=enc(bd)),'binding refundrefusal')
fs=copy.deepcopy(prepared);fs['training.json']=enc(dict(json.loads(fs['training.json']),epochs=99));ok(not runfixture('body-only-drift',files=fs),'body drift independent of draft')
# Actual original claim bytes copied into owned fixtures; corruption is never a new genuine claim.
first=sorted(allclaim)[0]
def alter(field,value,coherent=False):
 def f(hist):
  q=json.loads(hist[first]['claim.json']);q[field]=value;hist[first]['claim.json']=enc(q)
  if coherent:
   z=json.loads(hist[first]['failed.json']);z['claim_sha256']=sha(hist[first]['claim.json']);hist[first]['failed.json']=enc(z)
 return f
for label,edit in [('budget-refund',alter('effective_attempt_budget',18,True)),('wrong-identity',alter('experiment_id','foreign',True)),('wrong-program',alter('program_id','foreign',True)),('missing-failure',lambda h:h[first].pop('failed.json')),('complete-terminal',lambda h:h[first].__setitem__('complete.json',b'opaque contradictory presence'))]:ok(not runfixture('GP2-'+label,history_edit=edit),'history refusal '+label)
ok(not runfixture('GP2-extra-empty-identity',extra='unregistered-opaque-presence'),'additional identity presence refuse')
# Independently derive method and finite prospective accounting from pinned actual metadata.
training=json.loads(prepared['training.json']);recipe=json.loads(prepared['synthetic_recipe.json']);plan=json.loads(prepared['wrapper_plan.json']);alloc=json.loads(prepared['allocation20.json'])
ok(training['epochs']==100 and training['batch_size']==16 and recipe['seed']==11 and recipe['batch']==16 and recipe['lookback']==28 and recipe['empirical_inputs'] is False,'fixed original methodmetadata')
ok(plan['phase']=='complete100' and plan['execution']=='eager' and plan['prior_input'] is None and plan['reference_input'] is None and draft['experiment']['parent'] is None,'independent fresh reference topology')
ok(alloc['original_phases']==18 and alloc['fulfilled_original_phases']==1 and len(alloc['pending_original_phase_mapping'])==17 and alloc['actual_spent']==3 and alloc['actual_highest_allowance']==19 and 19-3==16 and 3+17==20,'unrefunded cumulative20 prospective arithmetic')
newnames={NEW+'/'+n for n in prepared}|{NEW+'/policy-recovery.json',NEW+'/gates.json'};ok(len(newnames)==15 and not(set(names)&newnames) and len(set(names)|newnames)==355 and len((set(names)|newnames)-{NEW+'/gates.json'})==354,'full354sourcepins355tracked cardinality')
ok(len(gate['experiments'])==12 and len(draft['experiment']['inputs'])==10 and len(draft['experiment']['inputs'])+1==11,'original12 and future11roles');ok(not os.path.lexists(CAP/NEW) and not os.path.lexists(CAP/'research_runs'/identity),'actual new sourceinput/run namespaces absent')
for n,v in policy['target']['installed'].items():ok(sha((CAP/n).read_bytes())==v,'all195sourceactual '+n)
ok(ns['canonical'](policy['historical']['installed'])==json.dumps(policy['historical']['installed'],sort_keys=True,separators=(',',':'),allow_nan=False).encode(),'actual canonical encode unchanged')
(H/'READBACK01.json').write_text(json.dumps({'decision':'PASS_SOURCE_ONLY_GP1_GP2_CORRECTION','assertions':len(checks),'checks':checks,'cases':cases,'actual_history':actualns['history'],'current340':True,'prospective_source_pins':354,'prospective_tracked':355,'new_files':15,'roles_after_genuine_proof':11,'original_phase_remaining':17,'currently_remaining_allowances':16,'prospective20_not_adopted':True,'public_preview_invoked':False,'proof_parser_exercised':False,'accepted_proof_constructed':False,'gate_or_claim_emitted':False},indent=2,sort_keys=True)+'\n');print(json.dumps({'status':'PASS','assertions':len(checks),'cases':len(cases)}))
