import ast,hashlib,json,os,resource,signal,struct,time,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SRC=ROOT/'tradingagents/research/onchain_replication'
os.sched_setaffinity(0,{3});os.nice(10)
for key,val in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,60),(resource.RLIMIT_FSIZE,4*1024**2)]:resource.setrlimit(key,(val,val))
signal.alarm(60);start=time.monotonic_ns()
receipt={'pid':os.getpid(),'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'alarm_seconds':60}
(HERE/'LIMITER01.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert receipt['affinity']==[3]
checks=[]
def passed(s):checks.append(s)
def refuse(f,fragment):
 try:f()
 except ValueError as e:
  assert fragment in str(e),(fragment,str(e));return str(e)
 raise AssertionError('expected refusal')
def extracted(path):
 tree=ast.parse(path.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'require','_root','_capture','_rejoin'} or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'TOKEN','SUFFIXES'} for t in n.targets)]
 ns={'hashlib':hashlib,'struct':struct};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns);return ns
old=extracted(SRC/'batched_driver.py');new=extracted(HERE/'batched_driver.py')
a=(SRC/'batched_driver.py').read_text();b=(HERE/'batched_driver.py').read_text();assert b.replace('    return bytes(tokens)\n','    return tokens\n')==a;passed('exact one-line inverse')
jns={'__name__':'synthetic_actual_journal'};exec(compile((SRC/'batched_journal.py').read_text(),str(SRC/'batched_journal.py'),'exec'),jns);Journal=jns['BatchJournal']
tree=ast.parse((SRC/'compact_mcm_batched.py').read_text());posts=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='post_batch' and any(isinstance(x,ast.Constant) and x.value=='ordered grouped batch/token differs' for x in ast.walk(n))];assert len(posts)==1
# Actual nested consumer body with inert boundaries; no Owner or transport created.
factory=ast.parse('def factory():\n next_batch=0\n pending=[]\n def flush_group(j):\n  raise AssertionError("not reached")\n return post_batch,pending\n').body[0];factory.body.insert(-1,posts[0]);ns={'boundary':lambda:None,'require':new['require'],'modules':{'journal':types.SimpleNamespace(BatchJournal=Journal)},'batch_total':2};exec(compile(ast.fix_missing_locations(ast.Module(body=[factory],type_ignores=[])),'actual_grouped_post_batch','exec'),ns)
j=Journal(HERE/'journal',batch_cells=2,max_cells=4,max_bytes=20000,max_body_bytes=1024,boundary=lambda:None)
fd=j.fd
try:
 original=(str(j.root),tuple(j.pin));rows=[];tokens=[]
 for batch in range(2):
  result=j.run_batch_stream(2,iter([({'ordinal':batch*2+i},None,None) for i in range(2)]),lambda a,b,p:(0.5,1,'temperature_complete'),{'synthetic':True});rows.append(result)
  raw=old['_capture'](j,batch,result,original);token=new['_capture'](j,batch,result,original)
  assert type(raw)is bytearray and type(token)is bytes and bytes(raw)==token and len(token)==168
  new['_rejoin'](j,batch,token,original);tokens.append(token)
 passed('two real completed batches preserve all 168 bytes and rejoin')
 post,pending=ns['factory']();red=refuse(lambda:post(j,0,bytearray(tokens[0]),original),'ordered grouped');assert not pending;passed('baseline mutable token RED at actual grouped consumer')
 refuse(lambda:post(j,1,tokens[1],original),'ordered grouped');refuse(lambda:post(j,0,tokens[0][:-1],original),'ordered grouped')
 post(j,0,tokens[0],original);post(j,1,tokens[1],original);assert pending==list(enumerate(tokens));passed('candidate GREEN sequential grouped append; wrong order/short/mutable refused')
 refuse(lambda:new['_rejoin'](j,0,tokens[0][:-1],original),'extent')
 changed=bytearray(tokens[0]);changed[-1]^=1;refuse(lambda:new['_rejoin'](j,0,bytes(changed),original),'changed after consumer');passed('corrupt digest and short rejoin refused')
 refuse(lambda:new['_capture'](j,0,[],original),'record mismatch');passed('closure record mismatch remains refused')
 (j.root/'00000000.records.bin').write_bytes(b'corrupt')
 refuse(lambda:new['_rejoin'](j,0,tokens[0],original),'changed after consumer');passed('actual file corruption remains refused')
finally:j.close()
try:os.fstat(fd)
except OSError:passed('journal descriptor closed')
else:raise AssertionError('fd leaked')
result={'decision':'PASS','checks':checks,'baseline_refusal':red,'elapsed_ns':time.monotonic_ns()-start,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'scope':'synthetic routing/byte closure only; no numerical or authority proof'}
(HERE/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
