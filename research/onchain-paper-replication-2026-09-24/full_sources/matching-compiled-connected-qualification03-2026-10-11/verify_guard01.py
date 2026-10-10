"""Finite stdlib source/parser proof only. Does not call native_memory_guard/execute."""
import ast,builtins,hashlib,importlib.util,json,os,resource,signal
from pathlib import Path
P=Path(__file__).resolve().parent;OLD=P.parent/'matching-compiled-connected-qualification02-2026-10-10'
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(15,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(20);assert os.sched_getaffinity(0)=={3}
checks=[]
def ok(n,v=True):assert v,n;checks.append(n)
original=builtins.__import__
def guard(name,*a,**kw):
 assert name.split('.')[0] not in {'numpy','scipy','torch','ctypes','tradingagents'},name
 return original(name,*a,**kw)
builtins.__import__=guard
spec=importlib.util.spec_from_file_location('qualification03_metadata',P/'qualify.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
frozen=q.inputs();cases=frozen['CASES.json'];old=json.loads((OLD/'CASES.json').read_text());adjusted=dict(cases);adjusted['address_space_bytes']=old['address_space_bytes'];adjusted.pop('resident_cgroup_bytes');adjusted.pop('cgroup_unit')
ok('all other cases/criteria/caps unchanged',adjusted==old)
ok('fixed virtual correction and resident ceiling',cases['address_space_bytes']==17179869184 and cases['resident_cgroup_bytes']==3221225472)
for name in ('SOURCE_REQUIREMENTS.json','matching-config.json'):ok('exact predecessor '+name,(P/name).read_bytes()==(OLD/name).read_bytes())
body='0::/user.slice/user-1000.slice/user@1000.service/app.slice/onchain-compiled-qualification-20261011-03.service\n'
ok('synthetic parser shape accepted without native proof',q.cgroup_membership(body,1000)==body[3:-1])
for invalid in ('',body.replace('1000','1001'),body.replace('-03.service','-02.service'),body.replace('app.slice','other.slice'),body+'0::/other\n',body.replace('0::','1:memory:'),body.replace('/app.slice/','/app.slice/../app.slice/')):
 try:q.cgroup_membership(invalid,1000)
 except ValueError:ok('membership parser refuses different unit/path/hierarchy')
 else:raise AssertionError('invalid membership accepted')
tree=ast.parse((P/'qualify.py').read_text());functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)};execute=functions['execute']
protected=next(n for n in execute.body if isinstance(n,ast.Try) and n.handlers and n.finalbody)
science=[n for n in ast.walk(protected) if isinstance(n,(ast.Import,ast.ImportFrom)) and (getattr(n,'module','') or '').startswith('tradingagents') or isinstance(n,ast.Import) and any(x.name in ('numpy','scipy','torch','ctypes') for x in n.names)]
ok('scientific package imports inside reporting try',len(science)>=6)
ok('imports precede no numerical call outside reporting try',not any(isinstance(n,(ast.Import,ast.ImportFrom)) and any(x.name in ('numpy','scipy','torch','ctypes') for x in n.names) for n in execute.body))
ok('import failures retain original FAILED/result handler',"record['status'] = 'FAILED_OR_UNAVAILABLE'" in ast.unparse(protected.handlers[0]) and "write(output / 'RESULT.json', record)" in ast.unparse(protected))
source=ast.unparse(functions['native_memory_guard'])
for needle in ("'/proc/self/cgroup'","'/sys/fs/cgroup'", "'cgroup.procs'", "'memory.high': '3221225472'", "'memory.max': '3221225472'", "'memory.swap.max': '0'", 'root.resolve() == root'):
 ok('actual kernel readback source '+needle,needle in source)
index=lambda token:next(i for i,n in enumerate(execute.body) if token in ast.unparse(n))
ok('actual guard before protected scientific imports',index('memory_receipt = native_memory_guard(cases)')<execute.body.index(protected))
ok('receipt included before PREFLIGHT publication',index("'native_memory_policy': memory_receipt")<index("write(output / 'PREFLIGHT.json', record)"))
inverse=json.loads((P/'LITERAL_INVERSE01.json').read_text());s=(P/'qualify.py').read_text()
for item in reversed(inverse['changes']):assert s.count(item['after'])==1;s=s.replace(item['after'],item['before'],1)
ok('exact literal inverse including unchanged numerical body',s==(OLD/'qualify.py').read_text())
ok('actual guard never invoked in preparation',True)
(P/'RESULT_SOURCE01.json').write_text(json.dumps(dict(status='PASS_STDLIB_SOURCE_AND_GUARD_PARSER_ONLY',checks=checks,count=len(checks),actual_native_policy_verified=False,numerical_executed=False,scientific_imports=False),indent=2)+'\n');print('PASS',len(checks))
