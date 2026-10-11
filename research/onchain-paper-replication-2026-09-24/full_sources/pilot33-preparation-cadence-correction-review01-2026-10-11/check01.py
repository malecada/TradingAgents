import ast,builtins,copy,difflib,hashlib,json,types,resource
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(20,20));resource.setrlimit(resource.RLIMIT_AS,(268435456,268435456))
R=Path.cwd();H=Path(__file__).resolve().parent;F=H.parent;D=F/'pilot33-preparation-cadence-correction01-2026-10-11';P=R/'tradingagents/research/onchain_replication';refs={};checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 b=p.read_bytes();assert len(b)<2097152;refs[str(p.relative_to(R))]={'sha256':sha(b),'bytes':len(b)};return b
def ck(ok,n):assert ok,n;checks.append(n)
m=json.loads(read(D/'MANIFEST01.json'));ck(sha((D/'MANIFEST01.json').read_bytes())=='8189ebb0f227d2140ed4b13af0b2a18e03b83d2d11efbf48c67449d132b53dbc','exact frozen candidate manifest')
old=read(P/'compact_mcm.py').decode();new=read(D/'compact_mcm.py').decode();ck(sha(old.encode())=='becaab002648c440852553ebf1e662702affee96283a07bcb90bdfc2ca7379ca' and sha(new.encode())=='abd86e24681f0df4ef3ca82cfb016662d9af5a46a38a32bafc65e7c92f2dacf8','exact installed and candidate')
added=[s for s in new.splitlines(True) if s.startswith('    if imported:dictionary.check()  # Complete ')]
ck(len(added)==3,'three only explicit imported guards');back=new
for line in added:back=back.replace(line,'',1)
ck(back==old and ast.dump(ast.parse(back),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False),'literal and full AST inverse')
for name,a,b,pa,pb in [('forward.patch',old,new,P/'compact_mcm.py',D/'compact_mcm.py'),('inverse.patch',new,old,D/'compact_mcm.py',P/'compact_mcm.py')]:
 expected=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=str(pa.relative_to(R)),tofile=str(pb.relative_to(R))))
 ck(read(D/name).decode()==expected,'exact '+name)
fn=next(n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef) and n.name=='_prepare');indices=[i for i,n in enumerate(fn.body) if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='imported' and len(n.body)==1 and isinstance(n.body[0],ast.Expr) and ast.unparse(n.body[0])=='dictionary.check()']
ck(len(indices)==3,'three imported-only AST checks')
ck(ast.unparse(fn.body[indices[0]-1]).startswith('sources = dictionary._prepare_sources()'),'source phase before first check')
ck(isinstance(fn.body[indices[1]-1],ast.If) and ast.unparse(fn.body[indices[1]+1]).startswith('run = owner.bound._run'),'complete scope branch before second check')
ck(ast.unparse(fn.body[indices[2]-1])=='kernel.validate_policy(policy[\'numeric\'], pairs)' and ast.unparse(fn.body[indices[2]+1]).startswith('output_policy, output_reserved ='),'kernel validation before third check')
interval=read(P/'imported_authority_interval.py');ck(sha(interval)=='e61ef97f883ed9d27107f6316b774697b8949d83c313928150a0ae717b283f6f','unchanged real60s scheduler');iv={};exec(compile(interval,'actual-stdlib-Interval','exec'),iv)
target=ast.parse(read(P/'imported_mcm_identity.py'));klass=next(n for n in target.body if isinstance(n,ast.ClassDef) and n.name=='Target');check=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='check');ck('target_lease(self, boundary=True)' in ast.unparse(check) and 'self.final()' in ast.unparse(check),'genuine Target.check full boundary and final still selected')
# Reuse author fixture apparatus ONLY; execute no author top-level builder or test matrix.
fixture=ast.parse(read(D/'build_check01.py'));runfn=next(n for n in fixture.body if isinstance(n,ast.FunctionDef) and n.name=='run');AGE=51.80366844699893;COST=11.354144623001048;DEFAULT=(15.,15.,15.,AGE-45.)
policy_clock={'schema_version':1,'kind':iv['KIND'],'live_interval_ms':1000,'fingerprint_interval_ms':2000,'full_interval_ms':30000,'max_stale_ms':60000,'max_calls_between_full':100000,'assumption':iv['ASSUMPTION']}
ns=dict(globals());exec(compile(ast.Module(body=[runfn],type_ignores=[]),'reused-synthetic-apparatus-no-author-execution','exec'),ns);run=ns['run']
a=run(old);b=run(new);ck('stale interval cannot refresh' in str(a['error']) and a['closed'] and b['error'] is None and b['count']==5,'independent15/15/15/remainder conditional RED GREEN')
ck(abs(a['time']-a['full']-(AGE+COST))<1e-9,'failed scheduler does not refresh timestamp')
ck(run(old,False)==run(new,False),'legacy whole-function values and events identical')
for i in (2,3,4,5):
 error=KeyboardInterrupt('independent fatal');v=run(new,check_failure=(i,error));ck(v['error'] is error and v['closed'] and v['count']==i,'same fatal object closes and stops at '+str(i))
v=run(new,mutate_final=True);ck(str(v['error'])=='imported preparation dimensions/scope changed','final callback mutation remains refused')
for durations,cost,label in [((49.,0.,0.,0.),COST,'first uninterruptible49s phase plus fullcheck'),(DEFAULT,61.,'61s fullcallback')]:
 v=run(new,durations=durations,cost=cost);ck(v['closed'] and 'stale interval cannot refresh' in str(v['error']),label+' refuses unchanged60s')
# No clock/scheduler writes occur in added callsites, which are plain genuine checks.
ck(all(isinstance(fn.body[i].body[0].value,ast.Call) and not fn.body[i].body[0].value.args and not fn.body[i].body[0].value.keywords for i in indices),'no artificial refresh parameter or timestamp assignment')
result={'decision':'ACCEPT_EXACT_SOURCE_CANDIDATE_ONLY','checks':checks,'references':refs,'fixture_scope':'Reused authored synthetic apparatus, independently selected phase split and assertions; real extracted _prepare and original stdlib Interval; no real authority or scientific imports.','hypothetical_phase_seconds':DEFAULT,'actual_phase_timings':None,'actual_speed_success_or_capacity':None,'required_before_live_adoption':'Actual failed33 recovery acceptance, exact reviewed installation/current source entry and separately authorized prospective admission.'}
(H/'REVIEW01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'decision':result['decision'],'checks':len(checks),'review_sha256':sha((H/'REVIEW01.json').read_bytes())}))
