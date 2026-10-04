"""Independent source-only Parent review. Never calls admission, preflight or launch."""
import ast,hashlib,importlib.util,itertools,json,os,re,stat,sys,time
from pathlib import Path
from types import SimpleNamespace
D=Path(__file__).resolve().parent;S=D/'source';P=D.parent/'financial-genuine-wrapper-recordfix-parent-preparation01-2026-10-04';checks=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ok(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def refuse(n,f):
 try:f()
 except (ValueError,TypeError,KeyError,OSError):ok(n,True);return
 raise AssertionError('accepted '+n)
def require(v,n):
 if not v:raise ValueError(n)
ok('candidate hash',sha(S/'parent01.py')=='82d79e1a99cff7be02fcd402661034f18eda749de870b6aa3a51f4994df4f578');ok('manifest hash',sha(P/'MANIFEST01.json')=='b6b951e4d11311ae75b77e85d587836ddf4cf8f8a70f1f420b008dd21af4c377')
m=json.loads((P/'MANIFEST01.json').read_text());ok('complete inventory',{p.relative_to(P).as_posix() for p in P.rglob('*') if p!=P/'MANIFEST01.json'}=={r['path'] for r in m['members']})
for row in m['members']:
 p=P/row['path'];q=S/row['path'];st=p.lstat();valid=stat.S_IMODE(st.st_mode)==row['mode']==stat.S_IMODE(q.lstat().st_mode)
 if row['kind']=='file':valid=valid and stat.S_ISREG(st.st_mode) and st.st_size==row['bytes'] and sha(p)==sha(q)==row['sha256']
 else:valid=valid and p.is_dir() and q.is_dir()
 ok('manifest '+row['path'],valid)
old=D.parent/'financial-genuine-wrapper-parent-preparation03-2026-10-04';ok('actual accepted predecessor',sha(S/'original-parent01.py')==sha(old/'parent01.py')=='3546fadac261bf1853b0139466c296c351e568b3842658d2984ac0aa5bdb8843')
for n in ('supervisor01.py','descendants01.py','owned_io.py','recovery04.py','bounded_git01.py','PROTOCOL_PINS01.json'):ok('unchanged helper '+n,(S/n).read_bytes()==(old/n).read_bytes())
raw=(S/'parent01.py').read_text();inverse=raw
for i,e in enumerate(reversed(json.loads((S/'INVERSE01.json').read_text())['edits'])):ok('unique inverse '+str(i),inverse.count(e['new'])==1);inverse=inverse.replace(e['new'],e['old'])
ok('full byte inverse',inverse==(S/'original-parent01.py').read_text());ok('full AST inverse',ast.dump(ast.parse(inverse))==ast.dump(ast.parse((S/'original-parent01.py').read_text())))
tree=ast.parse(raw);f={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)};oldf={n.name:n for n in ast.parse(inverse).body if isinstance(n,ast.FunctionDef)}
for name in ('child_cleanup','launch','stream_hash','memory','main'):ok('exact inherited function '+name,ast.dump(f[name])==ast.dump(oldf[name]))
literal={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and isinstance(n.value,ast.Constant)}
template=json.loads((S/'REQUEST_TEMPLATE01.json').read_text());CAP=Path(template['capsule_root']);PARENT=Path(template['parent_root'])
ok('fixed fresh root and identity',str(CAP)=='/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source' and literal['IDENTITY']==template['identity']=='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01')
# Authenticate copied original APIs against both preserved original request and current API bodies only.
q=json.loads((D.parent/'financial-genuine-wrapper-first-outcome-verifier-preparation03-2026-10-04/REQUEST_FINAL03.json').read_text())
api={}
for local,path in [('original-admission.py','tradingagents/research/admission.py'),('original-job.py','tradingagents/research/onchain_replication/job.py'),('original-resources.py','tradingagents/research/onchain_replication/resources.py')]:
 ok('actual API bytes '+local,sha(S/local)==q['source_files'][path]==sha(CAP/path));api[path]=sha(S/local)
wrapper=CAP/'tradingagents/research/onchain_replication/financial_wrapper_fixture.py';ok('current exact corrected wrapper bytes',sha(wrapper)=='e2d9208ac51fd5876b63b6a72f734fc4fedd28fa42ac9c7fa1014346feb8404c');(D/'corrected_wrapper.py').write_bytes(wrapper.read_bytes())
ad=ast.parse((S/'original-admission.py').read_text());klass=next(n for n in ad.body if isinstance(n,ast.ClassDef) and n.name=='Admission');fields={n.target.id for n in klass.body if isinstance(n,ast.AnnAssign)};used={n.attr for n in ast.walk(f['preflight']) if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=='admitted'};ok('all accessed genuine Admission fields',used<=fields and used=={'root','experiment_id','experiment','effective_attempt_budget'})
jtree=ast.parse((S/'original-job.py').read_text());jf={n.name:n for n in jtree.body if isinstance(n,ast.FunctionDef)};jtext=ast.get_source_segment((S/'original-job.py').read_text(),jf['_admitted']);ok('actual admission call chain', 'admitted = admit(' in jtext and 'financial_wrapper_fixture.admitted(admitted,job)' in jtext and 'return admitted, job' in jtext)
wf=next(n for n in ast.parse(wrapper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='admitted');ok('corrected runtime invoked from wrapper admission',any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='runtime_check' for n in ast.walk(wf)))
for label,node in [('job_admitted',jf['_admitted']),('wrapper_admitted',wf)]:
 calls=[ast.unparse(n.func) for n in ast.walk(node) if isinstance(n,ast.Call)];ok('no claim/start/write calls '+label,not any(x.endswith(('.start','.mkdir','.write_bytes','.write_text')) or x=='Owner' for x in calls))
pre=ast.get_source_segment(raw,f['preflight']);launch=ast.get_source_segment(raw,f['launch']);ok('genuine admission before command',pre.index('job._admitted(args)')<pre.index("job._command(args,'launch')"));ok('preflight before attempt/intent/spawn',launch.index('preflight(q)')<launch.index('directory.mkdir')<launch.index("'intent.json'")<launch.index('result=supervise'))
ok('post-admission prefix reauthentication',pre.index('job._admitted(args)')<pre.index("'post-admission actual package prefix/hash'"));ok('post-admission numerical guard',pre.index('job._admitted(args)')<pre.index("'no preflight numerical import'"));ok('three lexical one-use roots',"CAP/'research_runs'/q['identity'],job._base(args),parent/'attempt'" in pre and 'not os.path.lexists(path)' in pre)
ok('preflight not own writer/spawner',not any(isinstance(n,ast.Call) and (ast.unparse(n.func) in ('supervise','Owner') or ast.unparse(n.func).endswith(('.start','.mkdir','.put'))) for n in ast.walk(f['preflight'])))
# Execute actual release validator only on unresolved templates; no references or authority are supplied.
ns={'Path':Path,'re':re,'require':require,'CAP':CAP,'PARENT':PARENT,'IDENTITY':literal['IDENTITY'],'PROOFS':{'cumulative','full_recovery','independent_source_input_runtime'}}
exec(compile(ast.Module(body=[f['validate_release']],type_ignores=[]),'<actual validate_release>','exec'),ns)
refuse('unmodified draft refused',lambda:ns['validate_release'](template))
for key in template:
 bad=dict(template);bad.pop(key);refuse('missing exact contract '+key,lambda bad=bad:ns['validate_release'](bad))
for key in ('source','design_source','registration','registration_sha256','source_files','input_hashes','runtime_mapping','caller_sha256','helper_hashes','proofs','final_review'):ok('authority remains null '+key,template[key] is None)
# Extract changed pure predicates only, not a fabricated Admission or released request.
familyexpr=next(n for n in ast.walk(f['preflight']) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and any(isinstance(z,ast.Constant) and z.value=='unchanged numerical18/prior0 without extension' for z in n.args));fc=compile(ast.Expression(familyexpr.args[0]),'<numerical predicate>','eval')
for budget,prior,ext in itertools.product((17,18,19,True),(0,1,False),(False,True)):
 expected=type(budget)is int and budget==18 and type(prior)is int and prior==0 and not ext;ok('strict numerical scalar '+repr((budget,prior,ext)),eval(fc,{'family':{'attempt_budget':budget,'prior_attempts':prior},'exp':{'cumulative_budget_extension':None} if ext else {}})==expected)
commandns={'sys':sys,'Path':Path,'MODULE':'tradingagents.research.onchain_replication.job'};exec(compile(ast.Module(body=[jf['_command']],type_ignores=[]),'<genuine command only>','exec'),commandns);args=SimpleNamespace(root=str(CAP),registration='UNRELEASED',experiment=literal['IDENTITY'],source='UNRESOLVED');cmd=commandns['_command'](args,'launch');ok('exact original command composition',cmd==[sys.executable,'-B','-m',commandns['MODULE'],'--mode','launch','--root',str(CAP),'--registration','UNRELEASED','--experiment',literal['IDENTITY'],'--source','UNRESOLVED'])
# Direct unchanged cleanup reducer with actual exception objects; no process or authority stand-in.
spec=importlib.util.spec_from_file_location('independent_owned_cleanup',S/'owned_io.py');io=importlib.util.module_from_spec(spec);spec.loader.exec_module(io)
types=(ValueError,MemoryError,KeyboardInterrupt,SystemExit)
for a,b in itertools.product(types,repeat=2):
 primary=a('first');secondary=b('second');trace=[]
 def bad():trace.append('cleanup');raise secondary
 def final():trace.append('final')
 observed=None
 try:
  try:raise primary
  finally:io._cleanup((bad,final),primary=primary)
 except BaseException as e:observed=e
 expected=primary if io._fatal(primary) else secondary if io._fatal(secondary) else None
 ok('first fatal/all cleanup '+a.__name__+'/'+b.__name__,trace==['cleanup','final'] and (observed is expected if expected is not None else isinstance(observed,io.CleanupFailure) and observed.failures==(primary,secondary)))
ok('legacy terminal null/acceptance flags',"'actual_parent_exit':None" in launch and "'outcome_semantics_accepted':False" in launch);ok('no numerical imports',not any(x in sys.modules for x in ('numpy','torch','scipy','pandas')))
result={'verdict':'ACCEPTED_SOURCE_ONLY_RECORDFIX_PARENT','count':len(checks),'checks':checks,'actual_api_body_pins':api,'actual_admission_calls':0,'native_executions':0,'source_adoption':False,'authority':None,'no_claim_qualification':'Source-chain and ordering inspection only; no live claim census or actual admit call; Root separate current admission review required.'};(D/'CHECKS01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'count':len(checks),'verdict':result['verdict']}))
