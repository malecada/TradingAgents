import ast,copy,difflib,json,hashlib,os,resource,signal,types
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10);resource.setrlimit(resource.RLIMIT_CPU,(9,9));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(10)
P=Path(__file__).resolve().parent;O=P.parent/'matching-compiled-two-attribute-qualification02-2026-10-11';checks=[]
def ck(ok,name):assert ok,name;checks.append(name)
old=(O/'fixture02.py').read_text();new=(P/'fixture03.py').read_text()
class Target:
 def __init__(self,error):self.error=error
 def __truediv__(self,name):return self
 def open(self,mode):
  assert mode=='x'
  if self.error:raise self.error
  return self
 def __enter__(self):return self
 def __exit__(self,*args):return False
class BadText(ValueError):
 def __str__(self):raise MemoryError('format failed')
def exercise(source,error=None,trace_error=None,result_error=None):
 tree=ast.parse(source);node=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.Try)))
 node.body=ast.parse('raise injected' if error else 'pass').body
 records=[]
 def result(path,value):
  if result_error:raise result_error
  records.append(value)
 ns=dict(injected=error,ATTEMPT=Target(trace_error),failure=None,failed=False,primary=None,secondary=[],checks=[],start=0,time=types.SimpleNamespace(monotonic=lambda:1),traceback=types.SimpleNamespace(print_exc=lambda **kwargs:None),write_result=result)
 escaped=None
 try:exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'actual-except-finally','exec'),ns)
 except BaseException as caught:escaped=caught
 return records,escaped,ns
original=ValueError('numerical failure');reporting=OSError('traceback storage failure')
records,escaped,ns=exercise(old,original,reporting)
ck(records[0]['status']=='PASS_FINITE_SYNTHETIC' and records[0]['failure'] is None and escaped is reporting,'02 RED actual handler writes false PASS and masks original')
records,escaped,ns=exercise(new,original,reporting)
ck(records[0]['status']=='FAILED' and escaped is original and ns['secondary']==[reporting],'03 GREEN traceback error keeps FAILED and original identity')
ck(records[0]['reporting_errors']==['OSError'] and any('traceback storage failure' in x for x in original.__notes__),'secondary traceback failure retained in result and original note')
for error,trace_error,result_error in ((ValueError('ordinary'),None,None),(BadText(),None,None),(KeyboardInterrupt('fatal'),reporting,OSError('result storage failure'))):
 records,escaped,ns=exercise(new,error,trace_error,result_error)
 ck(escaped is error and ns['failed'] is True,'primary retained '+type(error).__name__)
 ck(all(r['status']=='FAILED' for r in records),'no false PASS '+type(error).__name__)
 if isinstance(error,BadText):ck(records[0]['failure'] is None and records[0]['reporting_errors']==['MemoryError'],'failed formatting cannot emit PASS')
 if result_error:ck(ns['secondary']==[trace_error,result_error] and not records,'both reporting failures secondary, no fabricated result')
records,escaped,ns=exercise(new)
ck(escaped is None and records[0]['status']=='PASS_FINITE_SYNTHETIC','unchanged successful disposition')
result_error=OSError('success result unavailable');records,escaped,ns=exercise(new,result_error=result_error)
ck(escaped is result_error and ns['failed'] and not records,'success storage failure escapes without result')
a='    filler=make_filler(native,np,agreement)';b='except BaseException as e:'
ck(new[new.index(a):new.rindex(b)]==old[old.index(a):old.rindex(b)],'complete numerical criteria byte-identical')
ck(new[:new.index('start=time.monotonic()')]==old[:old.index('start=time.monotonic()')],'reservation references and exclusive raw setup unchanged')
ck((P/'REFERENCES01.json').read_bytes()==(O/'REFERENCES01.json').read_bytes(),'immutable reference manifest unchanged')
for a,b,name in ((old,new,'FORWARD.patch'),(new,old,'INVERSE.patch')):ck(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='fixture.py',tofile='fixture.py'))==(P/name).read_text(),'exact '+name)
ck(not (P/'attempt01').exists(),'actual attempt remains absent')
(P/'SOURCE_RESULT01.json').write_text(json.dumps({'status':'PASS_SOURCE_ONLY_RED_TO_GREEN','checks':checks,'native_load':False,'scientific_imports':False,'numeric_execution':False},indent=2)+'\n');print(len(checks),'checks')
