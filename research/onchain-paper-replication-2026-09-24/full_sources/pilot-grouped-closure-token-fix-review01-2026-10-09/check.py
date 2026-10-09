import ast,struct,hashlib,types,json,os,signal,resource
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];C=D.parent/'pilot-grouped-closure-token-fix01-2026-10-09';S=R/'tradingagents/research/onchain_replication'
os.sched_setaffinity(0,{3});os.nice(10)
for k,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_FSIZE,4*1024**2),(resource.RLIMIT_CPU,30)]:resource.setrlimit(k,(v,v))
signal.setitimer(signal.ITIMER_REAL,30)
limits={'affinity':sorted(os.sched_getaffinity(0)),'as':resource.getrlimit(resource.RLIMIT_AS),'fsize':resource.getrlimit(resource.RLIMIT_FSIZE),'cpu':resource.getrlimit(resource.RLIMIT_CPU),'wall_remaining':signal.getitimer(signal.ITIMER_REAL)[0],'nice':os.getpriority(os.PRIO_PROCESS,0)}
assert limits['affinity']==[3] and limits['fsize']==(4194304,4194304)
(D/'LIMITER01.json').write_text(json.dumps(limits,indent=2)+'\n')
old=(S/'batched_driver.py').read_text();new=(C/'batched_driver.py').read_text();assert new.count('    return bytes(tokens)\n')==1 and new.replace('    return bytes(tokens)\n','    return tokens\n')==old

def extracted(text):
 tree=ast.parse(text);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('require','_root','_capture','_rejoin') or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('TOKEN','SUFFIXES') for t in n.targets)]
 ns={'struct':struct,'hashlib':hashlib};exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-driver','exec'),ns);return ns
oldns,newns=map(extracted,[old,new]);SUFFIXES=newns['SUFFIXES']
class FixtureJournal:
 root=Path('/synthetic-unused');pin=(17,19)
 def __init__(self):self.bodies={f'00000000{s}':(s.encode(),(17,30+i)) for i,s in enumerate(SUFFIXES)};self.reads=[]
 def _root(self):pass
 def _read(self,name,body=None,pin=None):
  actual,p=self.bodies[name];assert body is None or body==actual;assert pin is None or pin==p;self.reads.append((name,body,pin));return actual,p
 def read_complete(self,b):assert b==0;return [('synthetic-result',)]
j=FixtureJournal();root=(str(j.root),j.pin);records=j.read_complete(0)
a=oldns['_capture'](j,0,records,root);oldreads=list(j.reads);j.reads=[];b=newns['_capture'](j,0,records,root);assert oldreads==j.reads
assert type(a)is bytearray and type(b)is bytes and len(b)==168 and bytes(a)==b
for i,s in enumerate(SUFFIXES):
 assert newns['TOKEN'].unpack_from(b,i*56)==(17,30+i,len(s.encode()),hashlib.sha256(s.encode()).digest())
newns['_rejoin'](j,0,b,root)
tree=ast.parse((S/'grouped_offload_semantics.py').read_text());roster=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='roster');ns={'require':newns['require'],'MAX_BATCHES':16,'TOKEN':newns['TOKEN']};exec(compile(ast.Module(body=[roster],type_ignores=[]),'actual-roster','exec'),ns)
try:ns['roster'](((0,a),))
except ValueError as e:assert str(e)=='group batch/token shape'
else:raise AssertionError('baseline admitted')
assert ns['roster'](((0,b),))==((0,b),)
a[0]^=1;assert b[0]!=a[0]
mutable=bytearray(168);mutable[:]=b;assert bytes(mutable)==b # original retained token store still accepts immutable source
(D/'RESULT01.json').write_text(json.dumps({'decision':'PASS_STDLIB_ONLY','checks':['literal one-line inverse','same original capture reads/order','all168 bytes and every packed field unchanged','candidate rejoin succeeds','actual grouped roster rejects original bytearray and accepts bytes','returned bytes independent of mutable original','existing bytearray token-store assignment compatible'],'limitations':'Independent fixture uses explicit journal double; author eight connected actual-journal checks separately authenticated. No Owner or numerical runtime imported.','limits':limits},indent=2)+'\n');print('PASS: seven focused checks')
