import ast,copy,hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;P=B/'financial-genuine-wrapper-claimedrun-outcome-binding-preparation02-2026-10-04';O=B/'financial-genuine-wrapper-claimedrun-outcome-binding-preparation01-2026-10-04';W=B/'financial-genuine-wrapper-claimedrun-claim-window-review01-2026-10-04';checks=[];refusals=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def load(p):return json.loads(p.read_bytes())
def refuse(f,n):
 try:f()
 except (ValueError,TypeError,KeyError,FileNotFoundError) as e:refusals.append({'case':n,'type':type(e).__name__,'reason':str(e)});check(True,'refusal '+n)
 else:raise AssertionError('not refused '+n)
m=load(P/'MANIFEST02.json');check(sha((P/'MANIFEST02.json').read_bytes())=='2241ec9be76510da07c06b8cea389d6f2782e25c1fc6fbeec0237b69e41ac80c','exact frozen manifest');actual=[]
def scan(p):
 for q in p.iterdir():
  actual.append(q.relative_to(P).as_posix())
  if stat.S_ISDIR(q.lstat().st_mode):scan(q)
scan(P);check(set(actual)=={r['path'] for r in m['members']}|{'MANIFEST02.json'},'complete full author tree')
for r in m['members']:
 p=P/r['path'];s=p.lstat();check(oct(stat.S_IMODE(s.st_mode))==r['mode'],'mode '+r['path'])
 if r['kind']=='file':check(stat.S_ISREG(s.st_mode) and len(p.read_bytes())==r['bytes'] and sha(p.read_bytes())==r['sha256'],'body '+r['path'])
 elif r['kind']=='symlink':check(stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'],'literal symlink')
 else:check(stat.S_ISDIR(s.st_mode),'directory')
raw=(P/'bind01.py').read_bytes();check(sha(raw)=='b5af0ffe3688144ab6f5f691ad92f188441d90dd620090fca34be5485c60fd4f','exact binder');inverse=load(P/'INVERSE02.json');back=raw.decode().replace(inverse['new'],inverse['old']);check(raw.decode().count(inverse['new'])==1 and back==(O/'bind01.py').read_text(),'exact one added accounting rewrite byte inverse');check(ast.dump(ast.parse(back))==ast.dump(ast.parse((O/'bind01.py').read_bytes())),'full binder AST inverse')
sys.path.insert(0,str(P));spec=importlib.util.spec_from_file_location('binder_review_only',P/'bind01.py');S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S);parent=S.prepared();check(sha((P/'accepted_parent01.py').read_bytes())==S.PARENT_HASH=='5d5cbdae455c62c3e66b53208b0f79e6e5bbc7ce05d3ded77126da5e0692deda','genuine pinned Parent validator');q=load(P/'ACTUAL_PARENT_DRAFT01.json');check(sha((P/'ACTUAL_PARENT_DRAFT01.json').read_bytes())=='b1087b980a44fcc4cd920cdcbd472f092ba17223d0a329cbc74b52a8e0236c98','exact real draft');refuse(lambda:S.fixed(q),'genuine draft cannot bind');refuse(lambda:parent.validate_release(q),'genuine Parent validator refuses draft');check(q['final_review'] is None and q['proofs']['full_recovery'] is None,'future final/fullrecovery null')
# Actual known Source/gate/input/root mappings, no admission or execution.
N=Path(S.CAP);gate=load(N/q['registration']);exp=gate['experiments'][S.IDENTITY];check(q['source']==q['design_source']==S.SOURCE=='0a2e7639b42b9423b90743feadcda4078aa21816' and q['source_files']==exp['source_files'] and len(q['source_files'])==338,'actual source339/338');check(q['input_hashes']=={k:r['sha256'] for k,r in exp['inputs'].items()} and len(q['input_hashes'])==8,'actual8 roles');check(sha((N/q['registration']).read_bytes())==q['registration_sha256']=='3a20293832fa7ecc5e2821fb27dc940d1a997ab7f2ad373bc28f73e893e8781a','actual gate');check(q['source_files']['tradingagents/research/onchain_replication/financial_wrapper_fixture.py']=='f4ea651b4677c83f8e16c316d17f704d44d9ec86ff78a4bf7c4b895e92e1a16e','actualf4ea');check(q['runtime_mapping']==load(N/exp['inputs']['runtime_mapping']['path']) and len(q['runtime_mapping']['distribution_records'])==251,'actual251 metadata');check(q['caller_sha256']==S.PARENT_HASH and q['capsule_root']==S.CAP and q['parent_root']==S.PARENT,'exact new Parent/root');
for n,pin in q['helper_hashes'].items():check(sha((P/n).read_bytes())==pin,'exact6 helper '+n)
# Pure rewrite uses a labeled test-only hash in memory. No request or verifier emitted.
original=(P/'original-verifier03.py').read_bytes();testhash=sha(b'opaque independent source transformation control only');rewritten,edits=S.rewrite(original,testhash,'REQUEST_FINAL77.json');check(len(edits)==7,'exact3binding+3accounting+1window rewrite');unbound=rewritten.decode()
for edit in reversed(edits):check(unbound.count(edit['new'])==1,'unique full verifier inverse');unbound=unbound.replace(edit['new'],edit['old'])
check(unbound.encode()==original and ast.dump(ast.parse(unbound))==ast.dump(ast.parse(original)),'full generated source byte/AST inverse');check(not (P/'generated-claimedrun01').exists(),'author no emitted verifier')
for h in (None,'',True,'0'*63,'Z'*64,S.OLD_QHASH):refuse(lambda h=h:S.rewrite(original,h,'REQUEST_FINAL77.json'),'bad/old request hash '+str(h))
for name in ('../REQUEST_FINAL77.json','REQUEST_FINAL7.json','other.json'):refuse(lambda name=name:S.rewrite(original,testhash,name),'bad basename '+name)
# Extract only exact new window assignments/guards, execute with genuine old claim.
claim=load(W/'actual-old-claim.json');oldgate=load(W/'actual-old-gate.json');oldexp=oldgate['experiments'][claim['experiment_id']];snippet=ast.parse(inverse['verifier_new'].replace('\n  ','\n'));oldsnippet=ast.parse(inverse['verifier_old']);
def require(v,m):
 if not v:raise ValueError(m)
def evaluate(c,g=oldgate,e=oldexp):
 ns={'claim':c,'gate':g,'e':e,'require':require};exec(compile(snippet,'<exact new scalar windows>','exec'),ns);return ns['expected_windows'],ns['expected_exposures']
refuse(lambda:exec(compile(oldsnippet,'<exact old guard>','exec'),{'claim':claim,'e':oldexp,'require':require}),'actualold4c54 RED');ew,ee=evaluate(claim);check(ew==claim['windows'] and ee==claim['prior_exposures'],'actualold4c54 GREEN');check(ew[0]['availability']=='existing','availability preserved')
for field in ('windows','prior_exposures'):
 for key in claim[field][0]:
  c=copy.deepcopy(claim);c[field][0][key]='bad';refuse(lambda c=c:evaluate(c),'changed '+field+'.'+key)
  c=copy.deepcopy(claim);del c[field][0][key];refuse(lambda c=c:evaluate(c),'missing '+field+'.'+key)
 for kind in ('empty','extra','duplicate'):
  c=copy.deepcopy(claim)
  if kind=='empty':c[field]=[]
  elif kind=='extra':c[field][0]['unexpected']=True
  else:c[field]+=copy.deepcopy(c[field])
  refuse(lambda c=c:evaluate(c),kind+' '+field)
for k,v in [('schema_version',2),('bindings','bad'),('bindings_sha256','0'*64)]:
 c=copy.deepcopy(claim);c[k]=v;refuse(lambda c=c:evaluate(c),'schema/binding preserved '+k)
# Ordering needs two distinct metadata rows, not invented actual claims.
# Evaluate expected assignments alone and exact comparison predicate on lists.
assigns=[n for n in snippet.body if isinstance(n,ast.Assign)];g=copy.deepcopy(oldgate);e=copy.deepcopy(oldexp);e['windows']+=dict(e['windows'][0],start='2026-10-03T00:00:02Z',end='2026-10-03T00:00:03Z'),;g['datasets']['other']=dict(g['datasets']['synthetic'],identity='opaque-other');ns={'gate':g,'e':e};exec(compile(ast.Module(body=assigns,type_ignores=[]),'<pure expected ordering>','exec'),ns);check(ns['expected_windows']!=list(reversed(ns['expected_windows'])) and ns['expected_exposures']!=list(reversed(ns['expected_exposures'])),'ordered multi-window/exposure preserves order')
# Accounting remains exact projected scalar conditions, no fabricated claim object.
check(S.ACCOUNTING_EDITS[0]==("claim['effective_attempt_budget']==18","claim['effective_attempt_budget']==19"),'onlyeffective budget19');check("claim['family']['prior_attempts']==0" in rewritten.decode(),'prior0 retained');check("len(relevant)==2" in rewritten.decode() and "{identity,'financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01'}" in rewritten.decode(),'exact twoidentity count');check("4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128" in rewritten.decode() and "35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450" in rewritten.decode() and "original failed claim cannot become complete" in rewritten.decode(),'immutable original failed pins/refusal')
# All outcome/native/cleanup functions outside verify unchanged exactly by AST.
def defs(raw):return {n.name:ast.dump(n) for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a=defs(original);b=defs(rewritten);check(set(a)==set(b),'same function/class set')
for n in a:
 if n!='verify':check(a[n]==b[n],'unchanged outcome/native/cleanup '+n)
check(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')),'no numericimports');check(not (H/'generated-claimedrun01').exists(),'no emitted verifier in review');out={'decision':'ACCEPTED_SOURCE_ONLY_BINDER_AND_WINDOW_CORRECTION','checks':len(checks),'check_names':checks,'refusals':refusals,'pure_rewrite_only':True,'test_request_hash_not_authority':testhash,'actual_generated_verifier':None,'actual_final_request':None,'actual_full_recovery':None,'actual_outcome_classified':False,'no_fake_claims_Run_Owner':True};(H/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('check_names','refusals')}))
