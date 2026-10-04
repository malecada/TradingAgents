"""Independent source/metadata inspection. Only extracted assembly predicates execute.
No public preview, proof validator, accepted authority body, Admission or Run is constructed.
"""
from pathlib import Path
import ast,copy,hashlib,json,os,stat,subprocess
D=Path(__file__).resolve().parent;F=D.parent;ROOT=F.parents[2];C=F/'heartbeat-root-checkpoint10-2026-10-04';P=F/'financial-wrapper-compatibility-registration-preparation01-2026-10-04';CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');SRC=C/'root_compatibility_gate_preview01.py';NEW='fixture_inputs/financial_wrapper_compatibility01';OLD='fixture_inputs/financial_wrapper_claimedrun01/gates.json';sha=lambda b:hashlib.sha256(b).hexdigest();encode=lambda o:(json.dumps(o,sort_keys=True,indent=2,allow_nan=False)+'\n').encode();J=lambda p:json.loads(p.read_bytes())
raw=SRC.read_bytes();assert sha(raw)=='845e744580b45228e9bcb19925dd9d4ed851ea6912e246287b6e447c6c620de6';(D/'AUTHOR_SOURCE01.py').write_bytes(raw);tree=ast.parse(raw);controls=[]
def check(v,n):
 assert v,n
 controls.append({'name':n,'passed':True})
def git(*args):
 q=subprocess.run(['git','--no-replace-objects',*args],cwd=CAP,capture_output=True,timeout=10,env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL=''));assert q.returncode==0 and len(q.stdout)<=4194304;return q.stdout
check(git('rev-parse','HEAD').decode().strip()=='7b056a574e3e7b3c7ba209a39ee6a615e649d60c','current exact CAP source')
check(git('status','--porcelain','--untracked-files=no')==b'','current tracked source clean')
names=[n.decode() for n in git('ls-files','-z').split(b'\0') if n];check(len(names)==len(set(names))==340,'exact340 distinct current tracked paths')
base={n:sha((CAP/n).read_bytes()) for n in names};gate=J(CAP/OLD);check(sha((CAP/OLD).read_bytes())=='752c34dfad4df2ca36b5dc4dcb999846f8de01bd1a61c5356092c4e55fbd678c','old gate pin');check(len(gate['experiments'])==12,'twelve historical definitions');draft=J(P/'EXPERIMENT_DRAFT_NOT_REGISTRATION01.json');files={NEW+'/'+p.name:p.read_bytes() for p in (P/NEW).iterdir()};policy=J(P/NEW/'policy.json');ident=draft['identity'];check(len(files)==13 and len(draft['experiment']['inputs'])==10,'actual13prepared bodies/10roles')
for role,ref in draft['experiment']['inputs'].items():check(sha(files[ref['path']])==ref['sha256'],'actual role '+role)
check(len(policy['target']['installed'])==195 and all(base[n]==v for n,v in policy['target']['installed'].items()),'all195 actual target source bodies')
check(not os.path.lexists(CAP/NEW) and not os.path.lexists(CAP/'research_runs'/ident),'new actual gate namespace and run absent')
check(ident==policy['consumers']['complete100']['experiment'] and draft['experiment']['parent'] is None and draft['experiment']['cells']==[policy['consumers']['complete100']['cell_id']],'fixed complete100 topology')
claims=[]
for p in sorted((CAP/'research_runs').glob('*/claim.json')):
 q=J(p);f=p.parent/'failed.json';check(f.is_file() and not (p.parent/'complete.json').exists(),'actual FAILED '+p.parent.name);claims.append({'identity':p.parent.name,'claim_sha256':sha(p.read_bytes()),'failed_sha256':sha(f.read_bytes()),'budget':q.get('effective_attempt_budget',q['family']['attempt_budget'])})
check(len(claims)==3 and max(x['budget'] for x in claims)==19,'actual three spent/highest19')
check(gate['families']['synthetic-financial-wrapper']['attempt_budget']==18 and gate['families']['synthetic-financial-wrapper']['prior_attempts']==0,'base18/prior0 unchanged')
# Canonical encoding is extracted as a pure function; no dependency imports or entry points.
def purefunc(body,name):
 t=ast.parse(body);f=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==name);ns={'json':json};exec(compile(ast.Module(body=[f],type_ignores=[]),'<pure canonical>','exec'),ns);return ns[name]
ours=purefunc(raw,'canonical');helper=CAP/'tradingagents/research/onchain_replication/operational_source_compatibility.py';check(sha(helper.read_bytes())=='d0d770b45def89e8e00e81fa1bbb35416034eaace5ecab0f15193fd43b7a32d8','actual helperpin');canonical_helper=purefunc(helper.read_bytes(),'canonical')
preclaim=F/'financial-wrapper-compatibility-preclaim-source01-2026-10-04/preclaim01.py';canonical_preclaim=purefunc(preclaim.read_bytes(),'canonical')
for sample in [{'z':[1,False,None],'a':'opaque'},policy['historical']['installed'],policy['target']['installed']]:check(ours(sample)==canonical_helper(sample)==canonical_preclaim(sample),'canonical compact encoding agreement')
check(sha(ours(policy['historical']['installed']))=='ebb1727ccb55678aead9f0d5b5ee43ec81a46019c7fbb13c4b4f76144507bbca','exact old canonicalmap');check(sha(ours(policy['target']['installed']))=='2e281f7ca64a12be316424d8e93b0eab28ba0d121214e79ada7249c96930b040','exact target canonicalmap')
# Extract precisely lines66--83: post-authority metadata assembly and assertions only.
subset=[x for x in tree.body if 66<=x.lineno<=83];check(len(subset)>10 and all(not(isinstance(x,ast.Expr) and isinstance(x.value,ast.Call)) for x in subset),'extraction excludes public IO/entry/proof block')
code=compile(ast.Module(body=subset,type_ignores=[]),'<author exact assembly predicates lines66-83>','exec')
opaque=b'opaque engineering marker; not an accepted recovery proof'
def assemble(kind,edit=None,refuse=False):
 fs=copy.deepcopy(files);dr=copy.deepcopy(draft);gt=copy.deepcopy(gate)
 if edit:edit(fs,dr)
 fs[NEW+'/policy-recovery.json']=opaque
 ns={'CAP':CAP,'NEW':NEW,'sha':sha,'read':lambda p:p.read_bytes(),'names':names,'files':fs,'draft':dr,'copy':copy,'json':json,'raw':{'recovery-proof':opaque},'policy':policy,'identity':ident,'gate':gt,'encode':encode}
 try:exec(code,ns)
 except AssertionError:
  assert refuse,kind;return {'name':kind,'refused':True}
 assert not refuse,kind
 # No assembled gate bytes or pseudo proof body are written anywhere.
 return {'name':kind,'component_predicates_passed':True,'inputs':len(ns['experiment']['inputs']),'new_files':len(ns['files']),'source_pins':len(ns['source_files']),'historical12_equal':all(ns['gate']['experiments'][n]==v for n,v in gate['experiments'].items()),'changed_training_hash':sha(ns['files'][NEW+'/training.json']),'has_budget_extension':'cumulative_budget_extension' in ns['experiment']}
witness=[assemble('actual unchanged metadata with opaque skipped-authority marker')]
def mutate_json(name,field,value,coherent=True):
 def change(fs,dr):
  path=NEW+'/'+name;b=json.loads(fs[path]);b[field]=value;fs[path]=encode(b)
  if coherent:
   for ref in dr['experiment']['inputs'].values():
    if ref['path']==path:ref['sha256']=sha(fs[path])
 return change
for label,edit in [('training epochs100to99 coherent self-pin',mutate_json('training.json','epochs',99)),('recipe seed11to12 coherent self-pin',mutate_json('synthetic_recipe.json','seed',12)),('plan execution eager to selected coherent self-pin',mutate_json('wrapper_plan.json','execution','selected')),('drop cumulative extension while original files remain',lambda f,d:d['experiment'].pop('cumulative_budget_extension')),('alter family string',lambda f,d:d['experiment'].__setitem__('family','foreign-family'))]:witness.append(assemble(label,edit))
for label,edit in [('training changed without coherent draft hash',mutate_json('training.json','epochs',99,False)),('nonempty parent',lambda f,d:d['experiment'].__setitem__('parent','foreign')),('wrong cell',lambda f,d:d['experiment'].__setitem__('cells',['foreign'])),('extra role',lambda f,d:d['experiment']['inputs'].__setitem__('extra',copy.deepcopy(d['experiment']['inputs']['model']))),('changed extension bytes',lambda f,d:f.__setitem__(NEW+'/extension20.json',b'opaque changed extension'))]:witness.append(assemble(label,edit,True))
check(all(x.get('component_predicates_passed') for x in witness[:6]),'five coherent preparation mismatches demonstrably pass');check(all(x.get('refused') for x in witness[6:]),'five genuine inverse refusals')
# Verify names/counts independently without actual proof bytes or gate creation.
newnames=set(files)|{NEW+'/policy-recovery.json',NEW+'/gates.json'};check(len(newnames)==15 and not(newnames&set(names)),'15new paths disjoint from340');check(len(set(names)|newnames)==355 and len((set(names)|newnames)-{NEW+'/gates.json'})==354,'355 tracked/354sourcepins gate excluded')
check(not any('claim.json' in ast.unparse(n) or 'failed.json' in ast.unparse(n) for n in tree.body),'assembler does not rejoin current claims')
read_receipts=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='read'];check(all(not any(isinstance(x,ast.Constant) and x.value=='PREPARATION_BINDING01.json' for x in ast.walk(n)) for n in read_receipts),'preparation binding body not read')
(D/'WITNESSES01.json').write_text(json.dumps({'schema_version':1,'scope':'exact extracted assembly predicates only; proof block and public preview never executed','opaque_marker_is_not_recovery_proof':True,'cases':witness},indent=2)+'\n')
(D/'ACTUAL_SOURCE_METADATA01.json').write_text(json.dumps({'schema_version':1,'source_sha256':sha(raw),'current':git('rev-parse','HEAD').decode().strip(),'draft_sha256':sha((P/'EXPERIMENT_DRAFT_NOT_REGISTRATION01.json').read_bytes()),'prepared_file_pins':{n:sha(b) for n,b in files.items()},'actual_claims':claims,'actual_future_source_pins':354,'actual_prospective_tracked':355,'actual_gate_adopted':False,'public_preview_invoked':False,'actual_recovery_authority_constructed':False,'controls':controls},indent=2)+'\n')
print(json.dumps({'metadata_checks':len(controls),'extracted_cases':len(witness),'coherent_wrong_preparation_cases_accepted':5,'actual_preview_invoked':False}))
