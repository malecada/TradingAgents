"""Scalar projections only: no Run, Owner or claim objects, no native evidence."""
import ast,copy,hashlib,importlib.util,itertools,json
from pathlib import Path
import verifier01 as V
R=Path(__file__).resolve().parent;checks=[]
def check(name,v):assert v,name;checks.append(name)
props={'ActiveState':'failed','Result':'exit-code','SubState':'failed'};snap={'memory_events':{'oom':0,'oom_kill':0},'memory_current_bytes':12}
t={'reason':'PlannedInterruption: '+V.REASON,'status':'failed'}
g={'phase':'failed','child_exit_code':1,'elapsed_time_kill':False,'retry':False,'cleanup_verified':True,'unit_properties':props,'limit_reason':'RuntimeError: child or unit failed: '+str(props),'terminal_memory_snapshot':snap,'memory_events':{'oom':0,'oom_kill':0},'memory_current_bytes':12,'cpus':[0,1],'cpu_thread_readback':{'42':[0,1]}}
c={'exit_code':1,'reason':'workload exited','snapshot_error':None,'workload_pid':42,'terminal_memory_snapshot':snap}
p={'actual_child_exit':1,'actual_parent_exit':None,'planned_interrupt_requested':True,'outcome_semantics_accepted':False,'primary_exception_observed':False,'error_type':None,'supervisor_result':{'exit_code':1},'cleanup':{'original_parent_exit':1,'joined_unit_stopped':True,'cgroup_absent':True}}
ready={'pid':42,'cpus':[0,1],'native_unit_limits':{'file_size_bytes':4194304},'file_size_limit':[4194304,4194304],'native_environment':{'opaque':'scalar projection'}}
release={'kernel_controls_verified':True}
g.update(native_unit_limits={'file_size_bytes':4194304},native_environment=ready['native_environment'],kernel_controls={'memory.max':'3221225472','memory.high':'3221225472','memory.swap.max':'0'},initial_memory_events={'oom':0,'oom_kill':0})
def route(tt=t,gg=g,cc=c,pp=p,x=1,late=False):return V.planned_failure_route(tt,gg,cc,pp,x,late,ready,release)
check('source-derived failed child1 route accepted',route()['eligible'])
oldns={};old=ast.parse((R/'original_verifier02.py').read_bytes());defs=[x for x in old.body if isinstance(x,ast.FunctionDef)and x.name=='classify'];exec(compile(ast.Module(body=defs,type_ignores=[]),'<exact-af95-classifier>','exec'),{'require':V.require},oldns)
mutations={'elapsed_time_kill':True,'storage_breach':{'entries':99999},'storage_last_error':'OSError','cleanup_error':'close failed','child_log_limit_reached':True,'cpu_kill':True,'child_exit_code':137,'limit_reason':'RuntimeError: deadline','memory_events':{'oom':1,'oom_kill':1},'phase':'complete','cleanup_verified':False,'retry':True,'terminal_memory_snapshot':None}
for key,value in mutations.items():
 bad=copy.deepcopy(g);bad[key]=value
 check('RED old preserved '+key,oldns['classify'](claim_present=True,planned_bytes=True,cleanup_proved=True,predispatch_proved=False)=='PLANNED_FAILED_SPENT_INTERRUPT1_BYTES')
 check('GREEN new refuses '+key,not route(gg=bad)['eligible'])
for name,origin,index in [('terminal',t,0),('guard',g,1),('child',c,2),('parent',p,3)]:
 for key in origin:
  args=[t,g,c,p,1];bad=copy.deepcopy(origin);bad.pop(key);args[index]=bad;result=V.planned_failure_route(*args,cpu_ready=ready,release=release);check('missing '+name+'/'+key,not result['eligible'])
 for wrong in (None,[],False,'unknown'):
  args=[t,g,c,p,1];args[index]=wrong;check('missing body '+name+str(wrong),V.planned_failure_route(*args,cpu_ready=ready,release=release)['cleanup_uncertain'])
for x in (None,0,2,137,-9,True,'1'):check('external exit '+str(x),not route(x=x)['eligible'])
for key,value in [('actual_child_exit',0),('actual_child_exit',137),('primary_exception_observed',True),('error_type','MemoryError'),('actual_parent_exit',1),('supervisor_result',{'exit_code':137}),('cleanup',{'original_parent_exit':0,'joined_unit_stopped':True,'cgroup_absent':True})]:
 bad=copy.deepcopy(p);bad[key]=value;check('parent contradiction '+key+str(value),not route(pp=bad)['eligible'])
for text in ('unexpected exception','context exited without completion','PlannedInterruption: wrong'):
 bad=dict(t,reason=text);check('lifecycle reason '+text,not route(tt=bad)['eligible'])
for text in (None,'RuntimeError: child or unit failed: __import__("os")','RuntimeError: child or unit failed: {}','RuntimeError: child or unit failed: '+('x'*8193)):
 check('literal reason refusal '+str(text)[:60],not route(gg=dict(g,limit_reason=text))['eligible'])
check('late native marker cleanup uncertain',route(late=True)['cleanup_uncertain'] and not route(late=True)['eligible'])
for parent_exit,child_exit in itertools.product((0,1,137),(0,1,137)):
 bad=dict(p,actual_child_exit=child_exit);check('exit pair '+str((parent_exit,child_exit)),route(pp=bad,x=parent_exit)['eligible']==(parent_exit==child_exit==1))
for taint in ('cleanup_error','storage_last_error'):
 bad=dict(g);bad[taint]='uncertain';check('cleanup taint precedence '+taint,route(gg=bad)['cleanup_uncertain'])

(R/'INHERITED_VF1_CHECKS01.json').write_bytes(V.R.encode({'count':len(checks),'checks':checks,'scope':'inherited VF1 projections with explicit early evidence; old empty-census refusal removed as VF2'}));print(len(checks))
