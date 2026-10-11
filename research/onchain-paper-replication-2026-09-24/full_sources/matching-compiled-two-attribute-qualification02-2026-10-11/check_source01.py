"""Only stdlib reservation/result helpers and source checks; never imports fixture."""
import ast,difflib,hashlib,json,os,resource,signal
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10);resource.setrlimit(resource.RLIMIT_CPU,(9,9));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(10)
P=Path(__file__).resolve().parent;O=P.parent/'matching-compiled-two-attribute-agreement01-2026-10-11';source=(P/'fixture02.py').read_text();tree=ast.parse(source);old=(O/'fixture01.py').read_text();checks=[]
def ck(v,name):assert v,name;checks.append(name)
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('reserve_attempt','write_result')];ns={'json':json}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'reservation-result-only','exec'),ns)
scratch=P/'synthetic-reservation01';scratch.mkdir(exist_ok=False)
a=ns['reserve_attempt'](scratch/'spent');ck(a.is_dir(),'exclusive first reservation')
try:ns['reserve_attempt'](a)
except FileExistsError:ck(True,'second invocation refuses before workload')
else:ck(False,'duplicate reservation accepted')
ck(not (a/'NUMERIC_RESULT01.json').exists(),'interrupted reservation has no invented result')
ns['write_result'](a,{'synthetic':True});before=(a/'NUMERIC_RESULT01.json').read_bytes()
try:ns['write_result'](a,{'overwritten':True})
except FileExistsError:ck((a/'NUMERIC_RESULT01.json').read_bytes()==before,'exclusive result preserves original')
else:ck(False,'result overwrite accepted')
ck(source.index('ATTEMPT=reserve_attempt')<source.index('spec.loader.exec_module(native)')<source.index('import numpy'),'reservation precedes native and science loads')
ck('os.O_WRONLY|os.O_CREAT|os.O_EXCL' in source and "(ATTEMPT/'failure.txt').open('x')" in source,'raw logs and traceback are exclusive')
start='    filler=make_filler(native,np,agreement)';end="except BaseException as e:"
ck(source[source.index(start):source.rindex(end)]==old[old.index(start):old.rindex(end)],'entire numerical cases and criteria byte-identical')
for a,b,name in ((old,source,'FORWARD.patch'),(source,old,'INVERSE.patch')):ck(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='fixture.py',tofile='fixture.py'))==(P/name).read_text(),'literal '+name)
refs=json.loads((P/'REFERENCES01.json').read_text())
for name,row in refs.items():
 body=(O/name).read_bytes();ck(len(body)==row['bytes'] and hashlib.sha256(body).hexdigest()==row['sha256'],'immutable reference '+name)
ck(not (P/'attempt01').exists(),'actual numerical attempt remains unreserved and unexecuted')
(P/'SOURCE_RESULT01.json').write_text(json.dumps({'status':'PASS_SOURCE_ONLY','checks':checks,'numerical_execution':False,'native_load':False,'scientific_imports':False},indent=2)+'\n');print(len(checks),'checks')
