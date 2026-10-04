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
def route(tt=t,gg=g,cc=c,pp=p,x=1,late=False):return V.planned_failure_route(tt,gg,cc,pp,x,late)
check('source-derived failed child1 route accepted',route()['eligible'])
oldns={};old=ast.parse((R/'original_verifier01.py').read_bytes());defs=[x for x in old.body if isinstance(x,ast.FunctionDef)and x.name=='classify'];exec(compile(ast.Module(body=defs,type_ignores=[]),'<exact-af95-classifier>','exec'),{'require':V.require},oldns)
mutations={'elapsed_time_kill':True,'storage_breach':{'entries':99999},'storage_last_error':'OSError','cleanup_error':'close failed','child_log_limit_reached':True,'cpu_kill':True,'child_exit_code':137,'limit_reason':'RuntimeError: deadline','memory_events':{'oom':1,'oom_kill':1},'phase':'complete','cleanup_verified':False,'retry':True,'cpu_thread_readback':{},'terminal_memory_snapshot':None}
for key,value in mutations.items():
 bad=copy.deepcopy(g);bad[key]=value
 check('RED old preserved '+key,oldns['classify'](claim_present=True,planned_bytes=True,cleanup_proved=True,predispatch_proved=False)=='PLANNED_FAILED_SPENT_INTERRUPT1_BYTES')
 check('GREEN new refuses '+key,not route(gg=bad)['eligible'])
for name,origin,index in [('terminal',t,0),('guard',g,1),('child',c,2),('parent',p,3)]:
 for key in origin:
  args=[t,g,c,p,1];bad=copy.deepcopy(origin);bad.pop(key);args[index]=bad;result=V.planned_failure_route(*args);check('missing '+name+'/'+key,not result['eligible'])
 for wrong in (None,[],False,'unknown'):
  args=[t,g,c,p,1];args[index]=wrong;check('missing body '+name+str(wrong),V.planned_failure_route(*args)['cleanup_uncertain'])
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
# Exact full byte and AST inverse; all original functions outside declared seams.
s=(R/'verifier01.py').read_text()
for change in reversed(json.loads((R/'INVERSE01.json').read_bytes())['edits']):check('unique inverse '+str(len(checks)),s.count(change['new'])==1);s=s.replace(change['new'],change['old'])
check('complete byte inverse',s==(R/'original_verifier01.py').read_text());check('complete AST inverse',ast.dump(ast.parse(s),include_attributes=False)==ast.dump(old,include_attributes=False))
# Static genuine original source/input route, no claim/Owner fabricated.
prior=R.parent/'financial-genuine-wrapper-first-outcome-verifier-preparation01-2026-10-04';cap=prior/'baseline/capsule';par=prior/'opaque_controls03/static_parent';ct=V.Tree(cap);pt=V.Tree(par);q=V.decoded((R/'REQUEST_FINAL03.json').read_bytes());context={'schema_version':1,'kind':'root-financial-first-outcome-observation-v1','identity':q['identity'],'capsule_inventory_sha256':V.sha(V.canonical(ct.inventory)),'parent_inventory_sha256':V.sha(V.canonical(pt.inventory)),'actual_parent_exit':None,'process_observation':None,'source_claim_review':None};raw=V.canonical(context);out=V.verify(cap,par,raw,V.sha(raw));check('static absent no-claim still cleanup uncertain',out['disposition']=='CLEANUP_UNCERTAIN' and out['claim_present'] is False and out['paper_financial_fit_credit']==0);(R/'STATIC_RESULT01.json').write_bytes(V.R.encode(out));(R/'CHECKS01.json').write_bytes(V.R.encode({'count':len(checks),'names':checks,'kind':'pure metadata projections; no actual outcome or authority','no_numerical_imports':True}));print(len(checks))
