"""Independent changed-source/parser-only check. Never calls execute/native guard."""
import ast,datetime,hashlib,json,os,resource,signal,stat
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2]
C=F/'matching-compiled-connected-qualification03-2026-10-11';O=F/'matching-compiled-connected-qualification02-2026-10-10'
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(15,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(20)
checks=[];refs={};total=0
def ck(ok,name):
    assert ok,name
    checks.append(name)
def read(p):
    global total
    p=Path(p);s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<2*1024**2
    b=p.read_bytes();total+=len(b);assert total<8*1024**2
    refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return b
def sha(b):return hashlib.sha256(b).hexdigest()
def js(p):return json.loads(read(p))
mb=read(C/'MANIFEST01.json');ck(sha(mb)=='a7b67aa9933217ce187f290dbcffbb5d4cbc7fc9a2cd5a00fc5dccc779530e7e','external candidate manifest');m=json.loads(mb)
for name,row in m['files'].items():
    b=read(C/name);ck({'bytes':len(b),'sha256':sha(b)}==row,'frozen candidate '+name)
source=read(C/'qualify.py').decode();ck(sha(source.encode())=='e3add7dd56333c0117f1e8e02728607e8f01030f4b00a5722ec71a80db6d70de','external qualify source pin')
inverse=js(C/'LITERAL_INVERSE01.json');restored=source
for item in reversed(inverse['changes']):
    ck(restored.count(item['after'])==1,'unique literal inverse seam');restored=restored.replace(item['after'],item['before'],1)
old=read(O/'qualify.py');ck(restored.encode()==old and sha(old)=='07374bbcc71f81e1932d5a164e08f1bf6bd5d4a0a2235284e9f688659d7cd920','entire accepted02 numerical source restored')
ck(sha(read(O/'MANIFEST01.json'))==m['predecessor_manifest_sha256']=='b6eb54c3d8aa37b98b45a0f7bd1975d6f2e33821c489d25e098d4c4fb64d104b','accepted02 candidate anchor')
previous=js(F/'matching-compiled-connected-qualification-review02-2026-10-10/REVIEW01.json');ck(previous['disposition']=='ACCEPT_SOURCE_ENTRY_ONLY_UNEXECUTED' and previous['candidate_manifest_sha256']==m['predecessor_manifest_sha256'] and previous['qualify_sha256']==sha(old),'accepted02 independent review source join')
cases=js(C/'CASES.json');oldcases=js(O/'CASES.json');amended=dict(cases);amended['address_space_bytes']=oldcases['address_space_bytes'];del amended['resident_cgroup_bytes'];del amended['cgroup_unit']
ck(amended==oldcases,'all numerical cases criteria and remaining caps unchanged')
ck(cases['address_space_bytes']==16*1024**3 and cases['resident_cgroup_bytes']==3*1024**3 and cases['cgroup_unit']=='onchain-compiled-qualification-20261011-03.service','exact finite resource correction')
for name in ('SOURCE_REQUIREMENTS.json','matching-config.json'):ck(read(C/name)==read(O/name),'byte-identical predecessor '+name)
requirements=js(C/'SOURCE_REQUIREMENTS.json');ck(len(requirements['installed_module_sha256'])==8,'exact eight lower pins')
for name,h in requirements['installed_module_sha256'].items():ck(sha(read(R/'tradingagents/research/onchain_replication'/name))==h,'actual installed source '+name)
tree=ast.parse(source);functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
pins=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='INPUT_PINS' for t in n.targets))
for name,h in pins.items():ck(sha(read(C/name))==h,'actual frozen input pin '+name)
ns={};exec(compile(ast.Module(body=[functions['need'],functions['cgroup_membership']],type_ignores=[]),'<membership-parser-only>','exec'),ns)
body='0::/user.slice/user-1000.slice/user@1000.service/app.slice/onchain-compiled-qualification-20261011-03.service\n'
ck(ns['cgroup_membership'](body,1000)==body[3:-1],'synthetic exact local03 parser')
for bad in ['',body.rstrip(),body+'\n',body+'0::/other\n',body.replace('1000','1001'),body.replace('-03.service','-02.service'),body.replace('app.slice','other.slice'),body.replace('0::','1:memory:'),body.replace('/app.slice/','/app.slice/../app.slice/'),body.replace('.service\n','.scope\n')]:
    try:ns['cgroup_membership'](bad,1000)
    except ValueError:checks.append('rejects synthetic non-exact membership '+repr(bad))
    else:raise AssertionError('accepted wrong membership')
guard=ast.unparse(functions['native_memory_guard'])
for fragment in ["'/proc/self/cgroup'",'cgroup_membership(membership, os.getuid())',"Path('/sys/fs/cgroup' + relative)",'root.is_dir() and root.resolve() == root',"'/sys/fs/cgroup/cgroup.controllers'","str(os.getpid()) in kernel_read(root / 'cgroup.procs', 65536).split()","'memory.high': '3221225472'","'memory.max': '3221225472'","'memory.swap.max': '0'",'stream.read(limit + 1)','len(body) <= limit']:
    ck(fragment in guard,'actual bounded readback guard '+fragment)
execute=functions['execute'];protected=next(n for n in execute.body if isinstance(n,ast.Try) and n.handlers and n.finalbody)
guardline=next(n.lineno for n in execute.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='native_memory_guard')
imports=[n for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and (n.module or '').split('.')[0] in {'numpy','scipy','torch','tradingagents'} or isinstance(n,ast.Import) and any(a.name.split('.')[0] in {'numpy','scipy','torch','ctypes','tradingagents'} for a in n.names)]
ck(len(imports)==8 and all(guardline<n.lineno and protected.lineno<n.lineno<protected.handlers[0].lineno for n in imports),'all eight scientific imports protected after actual guard')
handler=ast.unparse(protected.handlers[0]);ck("record['status'] = 'FAILED_OR_UNAVAILABLE'" in handler and 'raise' in handler,'original exception recorded and reraised')
final='\n'.join(ast.unparse(n) for n in protected.finalbody);ck("write(output / 'RESULT.json', record)" in final and "'/proc/self/status'" in final and "line.startswith('VmPeak:')" in final,'actual final result and bounded VmPeak')
before='\n'.join(ast.unparse(n) for n in execute.body[:execute.body.index(protected)])
for fragment in ['os.sched_setaffinity(0, {3})','os.nice(10)','resource.RLIMIT_AS','resource.RLIMIT_CPU','resource.RLIMIT_FSIZE','signal.alarm',"not output.exists()","memory_receipt = native_memory_guard(cases)","'native_memory_policy': memory_receipt","write(output / 'PREFLIGHT.json', record)"]:
    ck(fragment in before,'prescience protection '+fragment)
ck(before.index('memory_receipt = native_memory_guard(cases)')<before.index("write(output / 'PREFLIGHT.json', record)"),'native receipt before preflight publication')
output=F/'matching-compiled-connected-qualification03-execution01-2026-10-11';ck(not os.path.lexists(output),'fresh exact03 output absent')
prioroutput=F/'matching-compiled-connected-qualification02-execution01-2026-10-10'
ck((prioroutput/'PREFLIGHT.json').is_file() and not (prioroutput/'RESULT.json').exists() and (prioroutput/'ROOT_ACTUAL_EXIT01.json').is_file(),'original02 preflight and failed Root exit retained with missing result')
read(prioroutput/'PREFLIGHT.json');exit02=js(prioroutput/'ROOT_ACTUAL_EXIT01.json')
ck(not any(n.split('.')[0] in {'numpy','scipy','torch','ctypes','tradingagents'} for n in __import__('sys').modules),'no scientific imports executed')
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_SOURCE_AND_MEMBERSHIP_PARSER_ONLY','checks':checks,'references':refs,'read_bytes':total,'native_guard_called':False,'execute_called':False,'scientific_imports':False,'actual_source_eight_match':True,'output_absent_observation':str(output),'root02_exit_receipt':exit02,'limits':{'address_space_bytes':256*1024**2,'cpu_seconds':15,'alarm_seconds':20,'per_output_bytes':4*1024**2}}
with (P/'CHECKS01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'status':out['status'],'checks':len(checks),'read_bytes':total}))
