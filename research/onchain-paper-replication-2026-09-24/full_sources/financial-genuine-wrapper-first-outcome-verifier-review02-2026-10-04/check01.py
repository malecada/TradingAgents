"""Independent frozen source and scalar semantics only; no outcome fabrication."""
import ast,copy,hashlib,importlib.util,itertools,json,os,stat,sys
from pathlib import Path
D=Path(__file__).resolve().parent;S=D/'source';P=D.parent/'financial-genuine-wrapper-first-outcome-verifier-preparation02-2026-10-04';T=D/'owned01';T.mkdir();sys.path.insert(0,str(S))
def load(n,f):
 spec=importlib.util.spec_from_file_location(n,S/f);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
V=load('new_verifier','verifier01.py');O=load('old_verifier','original_verifier01.py');checks=[];witness=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ok(n,v,detail=None):
 if not v:raise AssertionError(n)
 checks.append({'name':n,'detail':detail})
def dump(n,o):(D/n).write_text(json.dumps(o,sort_keys=True,indent=2)+'\n')
ok('exact source pin',sha(S/'verifier01.py')=='bbbf3606274b5cb0f33c03ad2f87b4d8f71442e32974620471d1bd5ea81eaf20');ok('exact manifest',sha(P/'MANIFEST02.json')=='798c56dc36b4c06a621a14cc947b1d1a2e34e5588c75021e196cd89b7f05a852')
m=json.loads((P/'MANIFEST02.json').read_text());rows=m.get('entries',m.get('members'));ok('complete manifest membership',{p.relative_to(P).as_posix() for p in P.rglob('*') if p!=P/'MANIFEST02.json'}=={r['path'] for r in rows})
for r in rows:
 p=P/r['path'];s=p.lstat();kind=r.get('type',r.get('kind'));good=stat.S_IMODE(s.st_mode)==r['mode']
 if kind=='file':good=good and stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and sha(p)==r['sha256'] and ('nlink' not in r or s.st_nlink==r['nlink'])
 elif kind=='directory':good=good and stat.S_ISDIR(s.st_mode)
 else:good=False
 ok('manifest '+r['path'],good)
q=json.loads((S/'REQUEST_FINAL03.json').read_bytes());cap=Path(q['capsule_root']);ok('unchanged request',sha(S/'REQUEST_FINAL03.json')==V.QHASH==O.QHASH)
for local,rel in [('original-resources.py','tradingagents/research/onchain_replication/resources.py'),('original-job.py','tradingagents/research/onchain_replication/job.py'),('original-lifecycle.py','tradingagents/research/lifecycle.py')]:ok('actual original source '+local,sha(S/local)==q['source_files'][rel]==sha(cap/rel))
ok('actual original Parent',sha(S/'original-parent01.py')==q['caller_sha256']==sha(Path(q['parent_root'])/'parent01.py'))
ok('original failed review body join',sha(S/'original_verifier01.py')==json.loads((D/'prior-REVIEW01.json').read_text())['candidate_source_sha256'])
s=(S/'verifier01.py').read_text()
for e in reversed(json.loads((S/'INVERSE01.json').read_text())['edits']):ok('unique inverse seam '+str(len(checks)),s.count(e['new'])==1);s=s.replace(e['new'],e['old'])
ok('full exact byte inverse',s==(S/'original_verifier01.py').read_text());ok('full exact AST inverse',ast.dump(ast.parse(s))==ast.dump(ast.parse((S/'original_verifier01.py').read_text())))
# Minimal scalar projections using actual original field names, never receipts.
props={'ActiveState':'failed','SubState':'failed','Result':'exit-code'};snapshot={'memory_events':{'oom':0,'oom_kill':0},'memory_current_bytes':47}
t={'reason':'PlannedInterruption: '+V.REASON,'status':'failed'}
g={'child_exit_code':1,'phase':'failed','retry':False,'elapsed_time_kill':False,'cleanup_verified':True,'unit_properties':props,'limit_reason':'RuntimeError: child or unit failed: '+repr(props),'terminal_memory_snapshot':snapshot,'memory_events':{'oom':0,'oom_kill':0},'memory_current_bytes':47,'cpus':[3,7],'cpu_thread_readback':{'opaque-thread':[3,7]}}
c={'exit_code':1,'reason':'workload exited','snapshot_error':None,'workload_pid':17,'terminal_memory_snapshot':snapshot}
p={'actual_child_exit':1,'actual_parent_exit':None,'planned_interrupt_requested':True,'outcome_semantics_accepted':False,'primary_exception_observed':False,'error_type':None,'supervisor_result':{'exit_code':1},'cleanup':{'original_parent_exit':1,'joined_unit_stopped':True,'cgroup_absent':True}}
def route(tt=t,gg=g,cc=c,pp=p,actual=1,late=False):return V.planned_failure_route(tt,gg,cc,pp,actual,late)
ok('consistent failed child1 projection',route()['eligible'])
prior=json.loads((D/'prior-VF1_WITNESSES01.json').read_text())
for row in prior:
 if 'mutated_original_resource_field' not in row:continue
 field=row['mutated_original_resource_field'];mut=copy.deepcopy(g);mut[field]=row['value'];r=route(gg=mut);ok('preserved VF1 old RED '+field,O.classify(claim_present=True,planned_bytes=True,cleanup_proved=True,predispatch_proved=False)==row['disposition']);ok('VF1 successor GREEN '+field,not r['eligible']);witness.append({'case':'VF1 '+field,'successor':r,'original':row['disposition']})
for group,origin in [('terminal',t),('guard',g),('child',c),('parent',p)]:
 for field in origin:
  args=[copy.deepcopy(t),copy.deepcopy(g),copy.deepcopy(c),copy.deepcopy(p),1];index=['terminal','guard','child','parent'].index(group);args[index].pop(field);ok('required missing '+group+'/'+field,not V.planned_failure_route(*args)['eligible'])
 for value in (None,[],False,'absent'):
  args=[t,g,c,p,1];args[['terminal','guard','child','parent'].index(group)]=value;r=V.planned_failure_route(*args);ok('missing body '+group+repr(value),not r['eligible'] and r['cleanup_uncertain'])
for value in (None,0,137,-9,True,'1'):ok('Root exit contradiction '+repr(value),not route(actual=value)['eligible'])
for group,field,value in [('parent','actual_parent_exit',1),('parent','primary_exception_observed',True),('parent','error_type','MemoryError'),('child','exit_code',137),('child','reason','monitor lease lost during workload'),('child','snapshot_error','OSError'),('guard','phase','complete'),('terminal','reason','MemoryError: unexpected'),('guard','memory_events',{'oom':0,'oom_kill':1})]:
 args=[copy.deepcopy(t),copy.deepcopy(g),copy.deepcopy(c),copy.deepcopy(p),1];args[['terminal','guard','child','parent'].index(group)][field]=value;ok('contradiction '+group+'/'+field,not V.planned_failure_route(*args)['eligible'])
for text in (None,'RuntimeError: child or unit failed: __import__("os")','RuntimeError: child or unit failed: '+repr({'Result':'other'}),'RuntimeError: child or unit failed: '+('x'*8193)):
 ok('bounded reason '+repr(text)[:60],not route(gg={**g,'limit_reason':text})['eligible'])
r=route(late=True);ok('late native marker stops cleanup',not r['eligible'] and r['cleanup_uncertain'])
# Exact final exit join including no-dispatch key; absent claim not manufactured.
fn=next(x for x in ast.parse((S/'verifier01.py').read_text()).body if isinstance(x,ast.FunctionDef) and x.name=='verify');join=next(x for x in fn.body if isinstance(x,ast.If) and any(isinstance(y,ast.Name) and y.id=='joined' for y in ast.walk(x)));code=compile(ast.Module(body=[join],type_ignores=[]),'<actual-exit-join>','exec')
for native,rootexit,childexit,supexit,cleanup_exit in itertools.product((False,True),(None,0,1,137),(0,1),(0,1),(0,1)):
 clean={'original_parent_exit':cleanup_exit} if native else {'source_bound_no_dispatch':True,'supervisor_exit':cleanup_exit};projection={'actual_child_exit':childexit,'supervisor_result':{'exit_code':supexit},'cleanup':clean};ns={'parent':projection,'context':{'actual_parent_exit':rootexit},'cleanup':True,'missing':[]};exec(code,ns);expected=rootexit==childexit==supexit==cleanup_exit==1;ok('source exit join '+repr((native,rootexit,childexit,supexit,cleanup_exit)),ns['cleanup']==expected)
# VF2 exact original CPU checker on an owned opaque empty-procs directory.
resource_tree=ast.parse((S/'original-resources.py').read_text());cpu=next(x for x in resource_tree.body if isinstance(x,ast.FunctionDef) and x.name=='verify_cpu_tree');ns={'os':os,'Path':Path};exec(compile(ast.Module(body=[cpu],type_ignores=[]),'<original-verify-cpu-tree>','exec'),ns);owned=T/'opaque-empty-group';owned.mkdir();(owned/'cgroup.procs').write_bytes(b'');empty=ns['verify_cpu_tree'](owned,[3,7]);ok('original exact empty final readback accepted',empty=={})
mut={**g,'cpu_thread_readback':empty};r=route(gg=mut);disposition=V.classify(claim_present=True,planned_bytes=r['eligible'],cleanup_proved=not r['cleanup_uncertain'],predispatch_proved=False);ok('VF2 successor rejects original valid empty readback',not r['eligible'] and not r['cleanup_uncertain'] and disposition=='UNEXPECTED_FAILURE_SPENT');witness.append({'finding':'VF2','case':'empty final CPU readback','original_checker_result':empty,'successor':r,'disposition':disposition,'qualification':'actual original pure filesystem function on owned empty-procs directory plus scalar projection; not an OS cgroup or real outcome'})
mask_pred=next(x for x in ast.walk(cpu) if isinstance(x,ast.If) and any(isinstance(y,ast.Constant) and y.value=='thread widened CPU affinity beyond registered two CPUs' for y in ast.walk(x)));maskcode=compile(ast.Module(body=[mask_pred],type_ignores=[]),'<exact-original-mask-predicate>','exec')
exec(maskcode,{'mask':{3},'allowed':{3,7}});r=route(gg={**g,'cpu_thread_readback':{'opaque-thread':[3]}});ok('VF2 original subset accepted but successor refused',not r['eligible']);witness.append({'finding':'VF2','case':'allowed strict subset CPU mask','original_mask_predicate':'accepted','successor':r,'qualification':'exact original scalar predicate; no affinity syscall or actual thread identity claim'})
# Verify actual loop placement: final CPU overwrite precedes unit failure test.
source=(S/'original-resources.py').read_text();loop=source.index('if cgroup.exists():state[\'cpu_thread_readback\']=verify_cpu_tree(cgroup,cpus)');terminal=source.index("if props.get('ActiveState') not in ('active', 'activating'):",loop);ok('original final overwrite precedes terminal branch',loop<terminal)
# Genuine frozen static inputs, no outcome records or claim construction.
priorprep=D.parent/'financial-genuine-wrapper-first-outcome-verifier-preparation01-2026-10-04';capcopy=priorprep/'baseline/capsule';parcopy=priorprep/'opaque_controls03/static_parent';ct=V.Tree(capcopy);pt=V.Tree(parcopy);context={'schema_version':1,'kind':'root-financial-first-outcome-observation-v1','identity':q['identity'],'capsule_inventory_sha256':V.sha(V.canonical(ct.inventory)),'parent_inventory_sha256':V.sha(V.canonical(pt.inventory)),'actual_parent_exit':None,'process_observation':None,'source_claim_review':None};raw=V.canonical(context);result=V.verify(capcopy,parcopy,raw,V.sha(raw));ok('actual static route no claim uncertain',result['disposition']=='CLEANUP_UNCERTAIN' and result['claim_present'] is False and result['release_authorized'] is False and result['planned_failure_route'] is None);dump('STATIC_INSPECTION01.json',result)
ok('no numerical imports',not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')))
dump('WITNESSES01.json',witness);dump('CHECKS01.json',{'checks':len(checks),'names':checks,'source_sha256':sha(S/'verifier01.py'),'verdict':'WITHHELD_VF2','VF1':'tested contradiction seams corrected','actual_outcomes_inspected':0,'claims_created':0,'native_executions':0,'scope':'exact source authentication/inverse, original owned empty CPU readback and scalar projections; no fake original receipts/Owner/claim','authority':None});print(json.dumps({'checks':len(checks),'verdict':'WITHHELD_VF2'}))
