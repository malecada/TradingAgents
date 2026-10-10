"""Independent bounded deduplication seam review; synthetic sources only."""
import ast,builtins,copy,difflib,hashlib,importlib.util,json,os,re,resource,signal,subprocess,sys,time,types
from pathlib import Path
P=Path(__file__).resolve().parent;C=P.with_name('claim-source-dedup-candidate01-2026-10-10');R=P.parents[3]
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));signal.alarm(45)
assert os.sched_getaffinity(0)=={3}
started=time.perf_counter_ns();checks=[];evidence={};observations={}
def digest(x):return hashlib.sha256(x).hexdigest()
def record(p):
 b=p.read_bytes();evidence[str(p.relative_to(R))]={'bytes':len(b),'sha256':digest(b)};return b
def ok(name,condition=True):
 assert condition,name
 checks.append(name)
def outcome(f):
 try:f();return ('OK','')
 except BaseException as e:return (type(e).__name__,str(e))
original_import=builtins.__import__
def no_numeric(name,*a,**kw):
 assert name.split('.')[0] not in {'numpy','scipy','torch','ctypes'},name
 return original_import(name,*a,**kw)
builtins.__import__=no_numeric
manifest=record(C/'MANIFEST01.json');ok('frozen manifest',digest(manifest)=='ceb57a7e16f963f0b4638f48523e6a45b2e1831b5dbf3dab9756b9b43a98e53a')
for name,ref in json.loads(manifest)['artifacts'].items():
 b=record(C/name);ok('manifest '+name,len(b)==ref['bytes'] and digest(b)==ref['sha256'])
base=record(C/'baseline_verify.py');candidate=record(C/'verify.py');installed=record(R/'tradingagents/research/verify.py')
ok('installed baseline byte identity',base==installed)
ok('candidate frozen digest',digest(candidate)=='7f710a8e0393c4d929b47173400bf6a0530681fa2987c678fd0a8fcf6af08cd0')
for reverse in (False,True):
 a,b,fa,fb=(candidate,base,'verify.py','baseline_verify.py') if reverse else (base,candidate,'baseline_verify.py','verify.py')
 expected=''.join(difflib.unified_diff(a.decode().splitlines(True),b.decode().splitlines(True),fromfile=fa,tofile=fb)).encode()
 ok('exact '+('inverse' if reverse else 'forward')+' patch',expected==(C/('verify.inverse.patch' if reverse else 'verify.patch')).read_bytes())
bt=ast.parse(base);ct=ast.parse(candidate)
def function(tree,name):return next(n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name)
changed={'_git_transport','_verify_sources','_verify_source_flush'}
ok('all unrelated AST identical',[ast.dump(n) for n in bt.body if getattr(n,'name',None) not in changed]==[ast.dump(n) for n in ct.body if getattr(n,'name',None) not in changed])
# Independently remove precisely the advertised additions from the actual AST.
inverse=copy.deepcopy(ct);inverse.body=[n for n in inverse.body if getattr(n,'name',None)!='_verify_source_flush']
t=function(inverse,'_git_transport');t.args.kwonlyargs=[];t.args.kw_defaults=[]
t.body=[n for n in t.body if not (isinstance(n,ast.If) and ast.unparse(n.test) in ('_source_check','_source_deadline is not None'))]
s=function(inverse,'_verify_sources');inner=next(n for n in s.body if isinstance(n,ast.FunctionDef));body=inner.body[0].body
body[0]=copy.deepcopy(next(n for n in function(bt,'_verify_sources').body if isinstance(n,ast.FunctionDef)).body[0].body[0])
ok('whole module independent AST inverse',ast.dump(inverse)==ast.dump(bt))
def source_segment(raw,tree,name):return ast.get_source_segment(raw.decode(),function(tree,name))
for name in ('_registration_pair','_blob','_verify_batch','_source_request','_git_cleanup','_git_fatal','verify_claim','verify_run'):
 ok('literal original function '+name,source_segment(base,bt,name)==source_segment(candidate,ct,name))
prior=P.with_name('claim-source-git-batch-review01-2026-10-03');prior_manifest=json.loads(record(prior/'REVIEW_MANIFEST01.json'))
for name in ('REVIEW_BATCH01.md','review_batch01.py','review_batch01.log'):
 ref=next(x for x in prior_manifest['files'] if x['path']==name);b=record(prior/name);ok('accepted cleanup evidence '+name,len(b)==ref['bytes'] and digest(b)==ref['sha256'])
old_source=record(P.with_name('claim-source-git-batch-candidate01-2026-10-03')/'candidate01.py');old_tree=ast.parse(old_source)
for name in ('_GitCleanupFailure','_git_fatal','_git_cleanup'):
 ok('prior accepted cleanup AST '+name,ast.dump(function(bt,name))==ast.dump(function(old_tree,name)))
ok('prior accepted transport body literal',source_segment(base,bt,'_git_transport')==source_segment(old_source,old_tree,'_git_transport'))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old=load('baseline_for_review',C/'baseline_verify.py');new=load('candidate_for_review',C/'verify.py')
ok('fixed original limits',(new._GIT_PARTS,new._GIT_BODY,new._GIT_REQUEST,new._GIT_SECONDS)==(128,8388608,65536,10))
# Synthetic isolated Git; no actual claim or Main Git writes.
os.environ.update({'GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_COUNT':'2','GIT_CONFIG_KEY_0':'protocol.allow','GIT_CONFIG_VALUE_0':'never','GIT_CONFIG_KEY_1':'core.hooksPath','GIT_CONFIG_VALUE_1':'/dev/null'})
G=P/'synthetic-git01';G.mkdir()
def git(*args):return subprocess.check_output(['git','-c','user.name=Source Review','-c','user.email=review@example.invalid','-c','commit.gpgsign=false',*args],cwd=G,stderr=subprocess.PIPE,timeout=5)
git('init','-q','--template=')
A=b'alpha\x00\xff\n'*91;B=b'beta body\n'*17
files={'a':A,'b':B,'c':A,'empty':b'','line\npath':B,'cr\rpath':B,'byte\udcfe':B}
files.update({f'alias{i:03}':A for i in range(67)})
for name,body in files.items():(G/name).write_bytes(body)
git('add','--all');git('commit','-qm','synthetic source one');one=git('rev-parse','HEAD').decode().strip()
(G/'unrelated').write_bytes(b'next commit');git('add','unrelated');git('commit','-qm','synthetic source two');two=git('rev-parse','HEAD').decode().strip()
def measured(m,pins,commits):
 actual=m._git_transport;events=[]
 def spy(root,requests,expression=None,**kw):
  e={'phase':'metadata' if kw.get('_source_check') else ('argv' if expression is not None else 'body'),'request_bytes':len(requests),'rows':requests.count(b'\n'),'deadline':kw.get('_source_deadline')};events.append(e)
  raw=actual(root,requests,expression,**kw);e['response_bytes']=len(raw);return raw
 m._git_transport=spy
 try:result=outcome(lambda:m._verify_sources(G,pins,commits))
 finally:m._git_transport=actual
 return dict(outcome=result,events=events,response_bytes=sum(e.get('response_bytes',0) for e in events))
pins={name:digest(files[name]) for name in ('a','b','c')}
for name,values,commits in [('mixed',pins,[one,two]),('last_duplicate_hash_wrong',dict(pins,c='0'*64),[one,two]),('empty_duplicate',{'empty':digest(b'')},[one,two]),('badpath_after_hash',{'a':'0'*64,'../bad':'0'*64},[one]),('missing_after_hash',{'a':'0'*64,'missing':'0'*64},[one]),('tree_after_hash',{'a':'0'*64,'.':'0'*64},[one]),('oddpaths',{n:digest(files[n]) for n in ('line\npath','cr\rpath','byte\udcfe')},[one,two])]:
 a=measured(old,values,commits);b=measured(new,values,commits);observations[name]={'baseline':a,'candidate':b};ok('actual Git differential '+name,a['outcome']==b['outcome'])
mixed=observations['mixed'];ok('mixed unique bodies only once',[(e['phase'],e['rows']) for e in mixed['candidate']['events']]==[('metadata',6),('body',2)] and mixed['candidate']['response_bytes']<mixed['baseline']['response_bytes'])
ok('later duplicate expected SHA still checked',observations['last_duplicate_hash_wrong']['candidate']['outcome']==('ValueError','registered source/charter/selection hash mismatch'))
ok('empty duplicate nonsaving fallback',[(e['phase'],e['rows']) for e in observations['empty_duplicate']['candidate']['events']]==[('metadata',2),('body',2)])
ok('LF CR argv and nonUTF8 original routing',[(e['phase'],e['rows']) for e in observations['oddpaths']['candidate']['events']]==[('argv',0)]*4+[('body',2)])
many=measured(new,{f'alias{i:03}':digest(A) for i in range(67)},[one,two]);observations['134_rows']=many
ok('actual 128-row boundary and fresh second flush',many['outcome'][0]=='OK' and [(e['phase'],e['rows']) for e in many['events']]==[('metadata',128),('body',1),('metadata',6),('body',1)])
repeat=measured(new,pins,[one,two]);ok('fresh next invocation',[(e['phase'],e['rows']) for e in repeat['events']]==[('metadata',6),('body',2)])
(G/'a').write_bytes(b'changed committed source');git('add','a');git('commit','-qm','synthetic changed source');three=git('rev-parse','HEAD').decode().strip()
stale=measured(new,pins,[one,three]);observations['changed_commit']=stale
ok('changed source refused after prior success',stale['outcome']==('ValueError','registered source/charter/selection hash mismatch'))
# Every expected hash executes, original order, on a duplicate/mixed fast flush.
bodyA=b'x'*193;bodyB=b'y'*79;oidA=b'a'*40;oidB=b'b'*40
header=lambda oid,n:oid+b' blob '+str(n).encode()+b'\n'
frame=lambda oid,b:header(oid,len(b))+b+b'\n'
requests=b'c:a\nc:b\nc:c\nc:d\n';rows=[('a','c',digest(bodyA)),('b','c',digest(bodyB)),('c','c',digest(bodyA)),('d','c',digest(bodyB))]
actual=new._git_transport;original_batch=new._verify_batch

def check_flush(name,transport,selected_rows=rows):
 events=[]
 def spy(root,req,expression=None,**kw):events.append({'request':req.decode('utf8','backslashreplace'),'source_check':bool(kw.get('_source_check')),'deadline':kw.get('_source_deadline')});return transport(req,kw)
 new._git_transport=spy
 try:result=outcome(lambda:new._verify_source_flush(None,requests,selected_rows))
 finally:new._git_transport=actual
 observations[name]={'outcome':result,'events':events};return result,events
metadata=header(oidA,len(bodyA))+header(oidB,len(bodyB))+header(oidA,len(bodyA))+header(oidB,len(bodyB));unique=frame(oidA,bodyA)+frame(oidB,bodyB)
full=frame(oidA,bodyA)+frame(oidB,bodyB)+frame(oidA,bodyA)+frame(oidB,bodyB)
seen=[];original_hash=new.hashlib
new.hashlib=types.SimpleNamespace(sha256=lambda b:seen.append(bytes(b)) or hashlib.sha256(b))
try:r,e=check_flush('hash_order',lambda req,k:metadata if k.get('_source_check') else unique)
finally:new.hashlib=original_hash
ok('all four expected SHA computations in row order',r[0]=='OK' and seen==[bodyA,bodyB,bodyA,bodyB])
# Distinct new fault cases: canonical-size failure, sameOID conflicting extent,
# unexpected terminator, short second header, out-of-order unique bodies.
faults={'metadata_leadingzero':metadata.replace(b' 193\n',b' 0193\n',1),'metadata_negative':metadata.replace(b' 193\n',b' -1\n',1),'metadata_cr':metadata.replace(b'\n',b'\r\n',1),'metadata_large':header(oidA,new._GIT_BODY+1)*4,'metadata_missing':b'c:a missing\n'*4,'metadata_tree':metadata.replace(b' blob ',b' tree ',1),'metadata_extra':metadata+b'x\n','metadata_129':b'a'*129+b'\n'}
wrongrows=copy.deepcopy(rows);wrongrows[0]=('a','c','0'*64)
for name,corrupt in faults.items():
 def stub(req,k,bad=corrupt):return bad if k.get('_source_check') else full
 r,e=check_flush(name,stub,wrongrows);ok('metadata fallback keeps earlier hash '+name,r==('ValueError','registered source/charter/selection hash mismatch') and len(e)==2 and e[-1]['request']==requests.decode())
for name,corrupt in [('body_reordered',frame(oidB,bodyB)+frame(oidA,bodyA)),('body_missing_second',frame(oidA,bodyA)),('body_terminator',unique[:-1]+b'x'),('body_trailing',unique+b'\n')]:
 def stub(req,k,bad=corrupt):return metadata if k.get('_source_check') else (full if req==requests else bad)
 r,e=check_flush(name,stub,wrongrows);ok('body fallback preserves original hash '+name,r==('ValueError','registered source/charter/selection hash mismatch') and len(e)==3 and e[-1]['request']==requests.decode())
# Fatal identity in both new phases, including uncertainty and SystemExit.
for phase in ('metadata','body'):
 for error in (MemoryError('injected'),KeyboardInterrupt('injected'),SystemExit(7),new._GitCleanupFailure('injected')):
  events=[]
  def fatal(root,req,expression=None,**kw):
   events.append(kw)
   if phase=='metadata' or not kw.get('_source_check'):raise error
   return metadata
  new._git_transport=fatal
  try:
   try:new._verify_source_flush(None,requests,rows)
   except BaseException as caught:ok('no fatal retry '+phase+' '+type(error).__name__,caught is error and len(events)==(1 if phase=='metadata' else 2))
   else:raise AssertionError('fatal suppressed')
  finally:new._git_transport=actual
# Real original cap values, synthetic in-memory source bytes; no large fixture file.
cap=new._GIT_BODY+128*new._GIT_PARTS
size=(cap-110)//2;large=b'z'*size;large_header=header(oidA,size)
assert 2*(len(large_header)+size+1)==cap
r,e=check_flush('exact_logical_cap',lambda req,k:large_header*2 if k.get('_source_check') else large_header+large+b'\n',[('a','c',digest(large))]*2)
ok('exact original logical cap accepted',r[0]=='OK' and len(e)==2)
for name,sz in [('duplicate_aggregate_over',size+1),('per_body_over',new._GIT_BODY+1)]:
 def stub(req,k,sz=sz):
  if k.get('_source_check'):return header(oidA,sz)*2
  if req==requests:raise ValueError('Git aggregate output ceiling exceeded')
  raise AssertionError('oversize optimization attempted')
 r,e=check_flush(name,stub,[('a','c','0'*64)]*2)
 ok('oversize duplicate uses original transport '+name,r==('ValueError','Git aggregate output ceiling exceeded') and len(e)==2)
del large
# Request byte limit and long/odd argv preserve original _verify_sources routing.
for label,path,commits in [('request_boundary','x'*32720,[one,two,one]),('longargv','x'*65536,[one]),('longargv_reject','x'*131073,[one])]:
 events=[]
 def routing(root,req,expression=None,**kw):
  events.append({'len':len(req),'rows':req.count(b'\n'),'argv':expression is not None,'kwargs':list(kw)})
  if len(req)>65536:raise AssertionError('oversize request forwarded')
  if expression is not None:
   if len(os.fsencode(expression))>131072:raise ValueError('Git argv expression ceiling exceeded')
   return bodyA
  count=req.count(b'\n')
  if kw.get('_source_check'):return header(oidA,len(bodyA))*count
  return frame(oidA,bodyA)*count
 new._git_transport=routing
 try:result=outcome(lambda:new._verify_sources(None,{path:digest(bodyA)},commits))
 finally:new._git_transport=actual
 observations[label]={'events':events,'outcome':result}
 if label=='request_boundary':ok('65536 request flush boundary',result[0]=='OK' and events[0]['rows']==2 and events[-1]['rows']==1 and all(e['len']<=65536 for e in events))
 elif label=='longargv':ok('longpath literal argv bypass',result[0]=='OK' and len(events)==1 and events[0]['argv'] and events[0]['kwargs']==[])
 else:ok('longpath original argv ceiling',result==('ValueError','Git argv expression ceiling exceeded'))
for req,expr in [(b'x'*65537,None),(bytearray(),None),(b'','x'*131073)]:ok('real transport input refusal',outcome(lambda:new._git_transport(G,req,expr))==outcome(lambda:old._git_transport(G,req,expr)))
# Extract the helper with a clock that expires during reconstruction; same absolute
# deadline reaches all phases. Separately verify ordinary failure fallback shares it.
node=copy.deepcopy(function(ct,'_verify_source_flush'))
for expired,fallback in ((True,False),(False,True)):
 clock=iter([200.,211. if expired else 201.]);fake_time=types.SimpleNamespace(monotonic=lambda:next(clock));calls=[]
 def transport(root,req,**kw):
  calls.append(kw)
  if kw.get('_source_check'):
   if fallback:raise OSError('metadata ordinary error')
   return metadata
  return full if fallback else unique
 bi=dict(vars(builtins));bi['__import__']=lambda name,*a,**kw:fake_time if name=='time' else no_numeric(name,*a,**kw)
 ns={'__builtins__':bi,'_GIT_SECONDS':10,'_GIT_BODY':new._GIT_BODY,'_GIT_PARTS':128,'_git_transport':transport,'_verify_batch':old._verify_batch,'re':re,'subprocess':subprocess}
 exec(compile(ast.Module(body=[node],type_ignores=[]),'deadline-seam','exec'),ns)
 result=outcome(lambda:ns['_verify_source_flush'](None,requests,rows))
 ok('single absolute deadline '+str(fallback),len(calls)==2 and all(c['_source_deadline']==210. for c in calls))
 ok('deadline reconstruction/fallback result '+str(fallback),result[0]==('TimeoutExpired' if expired else 'OK'))
ok('no numerical/native imports',not {'numpy','scipy','torch','ctypes'}&set(sys.modules))
# Recheck frozen bodies after tests; no source/registration/Main mutation.
ok('installed baseline still unchanged',(R/'tradingagents/research/verify.py').read_bytes()==installed)
ok('candidate still frozen',(C/'verify.py').read_bytes()==candidate and (C/'MANIFEST01.json').read_bytes()==manifest)
result={'decision':'ACCEPT_SOURCE_ONLY_UNINSTALLED','check_count':len(checks),'checks':checks,'observations':observations,'evidence':evidence,'elapsed_ns':time.perf_counter_ns()-started,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'affinity':sorted(os.sched_getaffinity(0)),'synthetic_commits':[one,two,three],'numerical_imports':False,'actual_admission':False,'main_git_mutations':False,'production_acceptance':False}
(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'decision':result['decision'],'checks':len(checks),'elapsed_ns':result['elapsed_ns'],'peak_rss_kib':result['peak_rss_kib'],'mixed_response_bytes':{k:v['response_bytes'] for k,v in mixed.items()}}))
