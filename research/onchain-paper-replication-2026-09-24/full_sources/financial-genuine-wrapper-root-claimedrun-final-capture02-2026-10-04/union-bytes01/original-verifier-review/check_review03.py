"""Independent exact-source scalar predicates; no actual receipts or OS/native run."""
import ast,copy,hashlib,itertools,json,os,stat,sys
from pathlib import Path
D=Path(__file__).resolve().parent;S=D/'source';P=D.parent/'financial-genuine-wrapper-first-outcome-verifier-preparation03-2026-10-04';checks=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ok(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def require(v,n):
 if not v:raise ValueError(n)
def defs(path,names,ns):
 tree=ast.parse(path.read_bytes());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns);return ns
ok('candidate source',sha(S/'verifier01.py')=='f6626d0a66dba46e6b4a314c4806a0452844fda886375f5e99e99186b2ceaa56')
ok('candidate manifest',sha(P/'MANIFEST03.json')=='72e5dd2e292d69fb1aa0e7e7d7f4a65b938e57015559435a539f1b36840d414c')
m=json.loads((P/'MANIFEST03.json').read_text());ok('complete author inventory',{p.relative_to(P).as_posix() for p in P.rglob('*') if p!=P/'MANIFEST03.json'}=={r['path'] for r in m['members']})
for r in m['members']:
 p=P/r['path'];q=S/r['path'];st=p.lstat();valid=stat.S_IMODE(st.st_mode)==r['mode']==stat.S_IMODE(q.lstat().st_mode)
 if r['kind']=='file':valid=valid and stat.S_ISREG(st.st_mode) and st.st_size==r['bytes'] and sha(p)==sha(q)==r['sha256']
 else:valid=valid and stat.S_ISDIR(st.st_mode) and q.is_dir()
 ok('manifest '+r['path'],valid)
old=D.parent/'financial-genuine-wrapper-first-outcome-verifier-preparation02-2026-10-04'
ok('preserved original verifier02',sha(S/'original_verifier02.py')==sha(old/'verifier01.py')=='bbbf3606274b5cb0f33c03ad2f87b4d8f71442e32974620471d1bd5ea81eaf20')
for n in ('REQUEST_FINAL03.json','owned_io.py','bounded_git01.py','recovery04.py'):ok('unchanged helper '+n,(S/n).read_bytes()==(old/n).read_bytes())
s=(S/'verifier01.py').read_text();edits=json.loads((S/'INVERSE03.json').read_text())['edits'];ok('five explicit inverse edits',len(edits)==5)
for i,e in enumerate(reversed(edits)):ok('unique inverse '+str(i),s.count(e['new'])==1);s=s.replace(e['new'],e['old'])
ok('full byte inverse',s==(S/'original_verifier02.py').read_text());ok('full AST inverse',ast.dump(ast.parse(s))==ast.dump(ast.parse((S/'original_verifier02.py').read_text())))
q=json.loads((S/'REQUEST_FINAL03.json').read_text());ok('old fixed QHASH',sha(S/'REQUEST_FINAL03.json')=='dc80a4dff93fbf3261bdf151076c1420630ed38926ab7094d60eb1902bde25bc');ok('actual original resources source pin',sha(D/'original_resources.py')==q['source_files']['tradingagents/research/onchain_replication/resources.py'])
rt=ast.parse((D/'original_resources.py').read_bytes());fn=next(x for x in rt.body if isinstance(x,ast.FunctionDef) and x.name=='verify_cpu_tree');original=defs(D/'original_resources.py',{'verify_cpu_tree'},{'Path':Path,'os':os})
owned=D/'owned-empty';owned.mkdir();(owned/'cgroup.procs').write_bytes(b'');empty=original['verify_cpu_tree'](owned,[3,7]);ok('actual extracted original empty owned procs census',empty=={})
predicate=next(x for x in ast.walk(fn) if isinstance(x,ast.If) and any(isinstance(z,ast.Constant) and z.value=='thread widened CPU affinity beyond registered two CPUs' for z in ast.walk(x)));origpred=compile(ast.Expression(predicate.test),'<original subset rule>','eval')
names={'final_cpu_census','early_cpu_evidence','planned_failure_route','classify'};reason='prospective engineering failed-parent fixture after one real update; no fit completion';v=defs(S/'verifier01.py',names,{'require':require,'REASON':reason})
oldtree=ast.parse((S/'original_verifier02.py').read_bytes());of=next(x for x in oldtree.body if isinstance(x,ast.FunctionDef) and x.name=='planned_failure_route');oldpred=next(x for x in of.body if isinstance(x,ast.Expr) and any(isinstance(y,ast.Constant) and y.value=='CPU thread readback differs/missing' for y in ast.walk(x)));oldcode=compile(ast.Module(body=[oldpred],type_ignores=[]),'<old VF2>','exec')
for census in (empty,{'817':[3]},{'817':[7]},{'817':[3],'821':[7]}):
 errors=[];exec(oldcode,{'cpus':[3,7],'readback':census,'need':lambda yes,msg:None if yes else errors.append(msg)});ok('old RED '+str(census),bool(errors));ok('new GREEN '+str(census),v['final_cpu_census']([3,7],census))
for mask in ([],[3],[7],[3,7],[8],[3,8]):ok('original/new subset parity '+str(mask),v['final_cpu_census']([3,7],{'817':mask})==(not eval(origpred,{'mask':set(mask),'allowed':{3,7}})))
bad=(None,[],False,0,'unknown',{'817':[]},{'817':[True]},{'817':[3.,7]},{'817':[7,3]},{'817':[3,3]},{'0':[3]},{'-1':[3]},{'pid':[3]},{817:[3]},{'٨':[3]})
for item in bad:ok('malformed census '+repr(item),not v['final_cpu_census']([3,7],item))
for cpus in (None,[],[3],[3,3],[True,7],[3.,7],[-1,7],(3,7)):
 ok('invalid CPU choice '+repr(cpus),not v['final_cpu_census'](cpus,{}))
# Minimal scalar field projections only. These are never serialized as receipts.
props={'ActiveState':'failed','Result':'exit-code'};snapshot={'memory_events':{'oom':0,'oom_kill':0},'memory_current_bytes':64}
t={'reason':'PlannedInterruption: '+reason,'status':'failed'}
g={'phase':'failed','child_exit_code':1,'elapsed_time_kill':False,'retry':False,'cleanup_verified':True,'unit_properties':props,'limit_reason':'RuntimeError: child or unit failed: '+str(props),'terminal_memory_snapshot':snapshot,'memory_events':{'oom':0,'oom_kill':0},'memory_current_bytes':64,'cpus':[3,7],'cpu_thread_readback':{},'native_unit_limits':{'file_size_bytes':4194304},'native_environment':{'opaque':'projection'},'kernel_controls':{'memory.max':'3221225472','memory.high':'3221225472','memory.swap.max':'0'},'initial_memory_events':{'oom':0,'oom_kill':0}}
c={'exit_code':1,'reason':'workload exited','snapshot_error':None,'workload_pid':912,'terminal_memory_snapshot':snapshot}
p={'actual_child_exit':1,'actual_parent_exit':None,'planned_interrupt_requested':True,'outcome_semantics_accepted':False,'primary_exception_observed':False,'error_type':None,'supervisor_result':{'exit_code':1},'cleanup':{'original_parent_exit':1,'joined_unit_stopped':True,'cgroup_absent':True}}
ready={'pid':817,'cpus':[3,7],'native_unit_limits':{'file_size_bytes':4194304},'file_size_limit':[4194304,4194304],'native_environment':g['native_environment']};release={'kernel_controls_verified':True}
def route(**changes):
 args={'terminal':t,'guard':g,'child':c,'parent':p,'actual_exit':1,'cpu_ready':ready,'release':release};args.update(changes);return v['planned_failure_route'](**args)
ok('empty final plus original early fields eligible',route()['eligible'])
for census in ({'817':[3]},{'817':[7]},{'817':[3,7]}):ok('subset route '+str(census),route(guard=dict(g,cpu_thread_readback=census))['eligible'])
for label,body in (('guard',g),('cpu_ready',ready),('release',release)):
 for key in body:
  modified=copy.deepcopy(body);modified.pop(key);ok('missing required '+label+'/'+key,not route(**{label:modified})['eligible'])
for key,value in [('cpus',[7,3]),('pid',True),('file_size_limit',[4194304,4194305]),('native_environment',{}),('native_unit_limits',{})]:ok('early ready contradicts '+key,not route(cpu_ready=dict(ready,**{key:value}))['eligible'])
for value in (None,False,{},[],{'kernel_controls_verified':1},{'kernel_controls_verified':False},{'kernel_controls_verified':True,'extra':0}):ok('release rejects '+repr(value),not route(release=value)['eligible'])
for key,value in [('elapsed_time_kill',True),('retry',True),('storage_breach',{}),('storage_last_error','fail'),('cleanup_error','fail'),('cpu_limit_reached',True),('cpu_kill',True),('child_log_limit_reached',True),('child_exit_code',137),('phase','complete'),('memory_events',{'oom':1,'oom_kill':0}),('initial_memory_events',{'oom':0,'oom_kill':1}),('limit_reason','RuntimeError: deadline'),('kernel_controls',{}),('cleanup_verified',False)]:ok('VF1 guard contradiction retained '+key,not route(guard=dict(g,**{key:value}))['eligible'])
for rootexit,childexit in itertools.product((None,0,1,True,137),(0,1,137)):
 result=route(actual_exit=rootexit,child=dict(c,exit_code=childexit));ok('independent exit grid '+repr((rootexit,childexit)),result['eligible']==(type(rootexit)is int and rootexit==childexit==1))
for change in ({'actual_parent_exit':1},{'actual_child_exit':137},{'primary_exception_observed':True},{'error_type':'MemoryError'},{'cleanup':None},{'supervisor_result':{'exit_code':137}}):ok('Parent contradiction '+repr(change),not route(parent=dict(p,**change))['eligible'])
ok('late native marker remains uncertain',route(late_native_failure=True)['cleanup_uncertain'] and not route(late_native_failure=True)['eligible'])
for claim,cleanup,predispatch,planned in itertools.product((False,True),repeat=4):
 expected='CLEANUP_UNCERTAIN' if not cleanup else ('NO_CLAIM_PREDISPATCH_REFUSAL' if predispatch else 'UNEXPECTED_FAILURE_NO_CLAIM') if not claim else 'PLANNED_FAILED_SPENT_INTERRUPT1_BYTES' if planned else 'UNEXPECTED_FAILURE_SPENT'
 ok('disposition grid '+repr((claim,cleanup,predispatch,planned)),v['classify'](claim_present=claim,planned_bytes=planned,cleanup_proved=cleanup,predispatch_proved=predispatch)==expected)
# AST verifies additional evidence is read on the genuine claim branch and passed.
verify=next(n for n in ast.parse((S/'verifier01.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='verify');calls=[n for n in ast.walk(verify) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
ok('both original early evidence paths read',all(any(n.func.id=='observed' and any(isinstance(k,ast.Constant) and k.value==suffix for k in ast.walk(n)) for n in calls) for suffix in ('/guard/cpu_ready.json','/guard/release.json')))
call=next(n for n in calls if n.func.id=='planned_failure_route');ok('early fields supplied to actual route',ast.unparse(call).endswith('cpu_ready, native_release)'))
ok('no numerical imports',not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')))
result={'verdict':'ACCEPTED_SOURCE_ONLY_VF2_CORRECTION','count':len(checks),'checks':checks,'actual_outcomes_inspected':False,'actual_outcomes_reclassified':False,'native_executions':0,'actual_admit_or_start_calls':0,'authority':None,'qualification':'Scalar projections and an owned empty procs-shaped file, not genuine receipts or OS cgroup observations. Original source proves ordering; final census is not historical complete task evidence.'}
(D/'CHECKS03.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'verdict':result['verdict'],'count':len(checks)}))
