"""Actual child control flow with mocked OS launch/affinity; real tiny receipts."""
import ast,hashlib,json,os,signal,sys,types
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[3];v=json.loads((H/'INVERSE01.json').read_text());old=(R/v['baseline']).read_text();new=(H/'resources.py').read_text()
s=old
for e in v['edits']:assert s.count(e['before'])==1;s=s.replace(e['before'],e['after'])
assert s==new
class OS:
 def __getattr__(self,k):return getattr(os,k)
 def sched_setaffinity(self,*a):pass
 def sched_getaffinity(self,*a):return {0,1}
 def getpid(self):return 42

def run(source,label,body,clock_values,workload_running=False):
 receipt=H/label;receipt.mkdir()
 if body is not None:(receipt/'live.json').write_text(body)
 (receipt/'release.json').write_text('{}')
 calls=[];clock=iter(clock_values)
 def now():calls.append('clock');return next(clock)
 def popen(*a,**kw):calls.append('mock_popen');return types.SimpleNamespace(pid=73,returncode=0,poll=lambda:None if workload_running else 0)
 ns={'os':OS(),'json':json,'sys':sys,'Path':Path,'time':types.SimpleNamespace(monotonic=now,sleep=lambda _:None),'signal':types.SimpleNamespace(SIGTERM=signal.SIGTERM,SIGINT=signal.SIGINT,signal=lambda *a:None),'subprocess':types.SimpleNamespace(Popen=popen),'_snapshot':lambda p:{'mock_metadata':True},'_own_cgroup':lambda:None}
 tree=ast.parse(source);nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ('_atomic','_child_legacy')];exec(compile(ast.Module(body=nodes,type_ignores=[]),label,'exec'),ns)
 code=ns['_child_legacy'](receipt,[0,1],15.,['never-launched'])
 return code,json.loads((receipt/'child_exit.json').read_text()),calls
cases={'valid':('{"monotonic_seconds":99}',[100.],None),'stale':('{"monotonic_seconds":84}',[100.],'expired_age'),'future':('{"monotonic_seconds":101}',[100.],'negative_age'),'missing_key':('{}',[100.],'missing_timestamp'),'malformed':('{',[],'value_error'),'absent':(None,[],'read_error')}
results={}
for name,(body,times,category) in cases.items():
 a=run(old,'old-'+name,body,times);b=run(new,'new-'+name,body,times)
 assert a[0]==b[0] and a[2]==b[2]
 stripped=dict(b[1]);detail=stripped.pop('lease_rejection',None);assert stripped==a[1]
 if category is None:assert detail is None and a[0]==0
 else:
  assert detail['category']==category and b[0]==125
  assert detail['sampled_monotonic_seconds']==(100. if times else None)
  if name=='absent':assert detail['read_or_value_error']['type']=='FileNotFoundError'
  if name=='malformed':assert detail['read_or_value_error']['type']=='JSONDecodeError'
 results[name]={'code':b[0],'detail':detail}
a=run(old,'old-workload','{"monotonic_seconds":99}',[100.,116.],True);b=run(new,'new-workload','{"monotonic_seconds":99}',[100.,116.],True)
assert a[0]==b[0]==125 and a[2]==b[2] and b[1]['reason']=='monitor lease lost during workload'
assert b[1]['lease_rejection']['observed_age_seconds']==17.
assert 'numpy' not in sys.modules
(H/'CHECK01.json').write_text(json.dumps({'decision':'pass','cases':results,'actual_child_exit_receipt_path_tested':True,'during_workload_rejection_retained':True,'original_codes_reasons_clock_calls_equal':True,'literal_inverse':True,'native_processes_started':0},indent=2)+'\n');print('PASS five refusal classes + valid parity; actual child finally receipt; during-workload path; unchanged clock/launch decisions; inverse')
