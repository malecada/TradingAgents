"""Finite stdlib and isolated synthetic Git fixture; no Main Git mutation."""
import ast,builtins,hashlib,importlib.util,json,os,resource,signal,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_CPU,(30,30))
resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
signal.alarm(60)
assert os.sched_getaffinity(0)=={3}
start=time.perf_counter_ns();checks=[];measurements={}
def ok(name,value=True):
    assert value,name
    checks.append(name)
old_import=builtins.__import__
def safe_import(name,*a,**kw):
    assert name.split('.')[0] not in {'numpy','scipy','torch'},name
    return old_import(name,*a,**kw)
builtins.__import__=safe_import
def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old=load('baseline_verify');new=load('verify')
repo=HERE/'tiny-repository02';repo.mkdir(exist_ok=False)
env={**os.environ,'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_TERMINAL_PROMPT':'0'}
def git(*args):
    return subprocess.check_output(['git','-c','core.hooksPath=/dev/null','-c','commit.gpgsign=false','-c','user.name=Synthetic Fixture','-c','user.email=synthetic@example.invalid',*args],cwd=repo,env=env,stderr=subprocess.PIPE,timeout=5)
git('init','--quiet','--template=')
large=b'synthetic source line\n'*12000
small=b'other source\n'*40
for name,body in [('a.py',large),('b.py',large),('small.py',small),('medium.py',b'x'*1024),('line\nname',small),('carriage\rname',small),('nonutf\udcff',small)]:
    (repo/name).write_bytes(body)
git('add','--all');git('commit','--quiet','-m','synthetic source fixture')
first=git('rev-parse','HEAD').decode().strip()
(repo/'new.py').write_bytes(b'changed commit only\n');git('add','new.py');git('commit','--quiet','-m','synthetic second tree')
second=git('rev-parse','HEAD').decode().strip()
def digest(body):return hashlib.sha256(body).hexdigest()
def outcome(call):
    try:call();return ('OK','')
    except BaseException as e:return(type(e).__name__,str(e))
def measured(module,pinned,commits):
    actual=module._git_transport;calls=[]
    def spy(root,requests,expression=None,**kw):
        raw=actual(root,requests,expression,**kw)
        calls.append({'kind':'metadata' if kw.get('_source_check') else ('argv' if expression is not None else 'bodies'),'requests':requests.count(b'\n'),'bytes':len(raw),'shared_deadline':kw.get('_source_deadline')})
        return raw
    module._git_transport=spy
    at=time.perf_counter_ns()
    try:result=outcome(lambda:module._verify_sources(repo,pinned,commits))
    finally:module._git_transport=actual
    return {'outcome':result,'calls':calls,'response_bytes':sum(c['bytes'] for c in calls),'elapsed_ns':time.perf_counter_ns()-at}
for name,pinned,commits in [
    ('duplicate',{'a.py':digest(large),'b.py':digest(large)},[first,second]),
    ('unique',{'a.py':digest(large),'small.py':digest(small)},[first]),
    ('wrong_hash_first',{'a.py':'0'*64,'b.py':digest(large)},[first,second]),
    ('missing_later',{'a.py':'0'*64,'missing':'1'*64},[first]),
    ('missing_only',{'missing':'1'*64,'a.py':digest(large)},[first]),
    ('nonblob_later',{'a.py':'0'*64,'.':'1'*64},[first]),
    ('secret_later',{'a.py':'0'*64,'keys/no':'1'*64},[first]),
    ('newline',{'line\nname':digest(small)},[first,second]),
    ('carriage',{'carriage\rname':digest(small)},[first,second]),
    ('nonutf8',{'nonutf\udcff':digest(small)},[first,second]),
]:
    a=measured(old,pinned,commits);b=measured(new,pinned,commits)
    ok('differential '+name,a['outcome']==b['outcome'])
    measurements[name]={'old':a,'candidate':b}
a=measurements['duplicate']['old'];b=measurements['duplicate']['candidate']
ok('RED original transfers four duplicate bodies',len(a['calls'])==1 and a['calls'][0]['requests']==4)
ok('GREEN candidate fresh four refs then one body',[(x['kind'],x['requests']) for x in b['calls']]==[('metadata',4),('bodies',1)])
ok('GREEN duplicate physical response reduced',b['response_bytes']<a['response_bytes'])
ok('same deadline for both transport phases',len({c['shared_deadline'] for c in b['calls']})==1)
ok('unique domain uses original body route',[(x['kind'],x['requests']) for x in measurements['unique']['candidate']['calls']]==[('metadata',2),('bodies',2)])
ok('unique startup overhead retained as cost',measurements['unique']['candidate']['response_bytes']>measurements['unique']['old']['response_bytes'])
ok('nonUTF8 literal baseline batch preserved',all(c['kind']=='bodies' for c in measurements['nonutf8']['candidate']['calls']))
# Same call repeated must freshly resolve all refs again; no retained authority.
repeat=measured(new,{'a.py':digest(large),'b.py':digest(large)},[first,second])
ok('no cross-call reuse',[(x['kind'],x['requests']) for x in repeat['calls']]==[('metadata',4),('bodies',1)])
# Original caps are scaled down only inside this isolated unit fixture.
for name,body_limit,parts,pinned in [
    ('oversize_later_wronghash_first',600,128,{'small.py':'0'*64,'medium.py':digest(b'x'*1024)}),
    ('oversize_first',600,128,{'medium.py':digest(b'x'*1024),'small.py':digest(small)}),
    ('aggregate_before_wronghash',600,2,{'small.py':'0'*64}),
]:
    results=[]
    for module in (old,new):
        saved=module._GIT_BODY,module._GIT_PARTS
        module._GIT_BODY,module._GIT_PARTS=body_limit,parts
        try:results.append(measured(module,pinned,[first,second]))
        finally:module._GIT_BODY,module._GIT_PARTS=saved
    ok('differential '+name,results[0]['outcome']==results[1]['outcome'])
    measurements[name]={'old':results[0],'candidate':results[1]}
ok('earlier hash precedes later per-body oversize',measurements['oversize_later_wronghash_first']['candidate']['outcome'][1]=='registered source/charter/selection hash mismatch')
ok('first oversize uses old per-body refusal',measurements['oversize_first']['candidate']['outcome'][1]=='Git blob body ceiling exceeded')
ok('aggregate refusal precedes first hash',measurements['aggregate_before_wronghash']['candidate']['outcome'][1]=='Git aggregate output ceiling exceeded')
# Faulted new metadata/body paths must not mask earlier original hash errors.
for mode in ('metadata_malformed','metadata_missing','metadata_nonblob','metadata_extra','metadata_oversized_header','metadata_error','body_wrong_oid','body_short','body_trailing','body_error'):
    actual=new._git_transport;events=[]
    def injected(root,requests,expression=None,**kw):
        events.append(kw.get('_source_check',False))
        if kw.get('_source_check'):
            raw=actual(root,requests,expression,**kw)
            if mode=='metadata_malformed':return b'garbage\n'
            if mode=='metadata_missing':return b'missing\n'
            if mode=='metadata_nonblob':return raw.replace(b' blob ',b' tree ',1)
            if mode=='metadata_extra':return raw+b'extra\n'
            if mode=='metadata_oversized_header':return b'0'*129+b'\n'
            if mode=='metadata_error':raise ValueError('new metadata failure')
            return raw
        # OID request denotes new unique body phase; commit:path is old route.
        if b':' not in requests:
            raw=actual(root,requests,expression,**kw)
            if mode=='body_wrong_oid':return b'0'*40+raw[40:]
            if mode=='body_short':return raw[:-2]
            if mode=='body_trailing':return raw+b'extra'
            if mode=='body_error':raise ValueError('new body failure')
            return raw
        return actual(root,requests,expression,**kw)
    new._git_transport=injected
    try:result=outcome(lambda:new._verify_sources(repo,{'a.py':'0'*64,'b.py':digest(large)},[first,second]))
    finally:new._git_transport=actual
    ok('fault routes through original hash order '+mode,result==('ValueError','registered source/charter/selection hash mismatch'))
# Fatal and uncertain cleanup are never swallowed/retried by optimization.
for error in (MemoryError('fixture'),KeyboardInterrupt('fixture'),new._GitCleanupFailure('fixture')):
    actual=new._git_transport;count=[0]
    def fatal(*a,**kw):count[0]+=1;raise error
    new._git_transport=fatal
    try:
        try:new._verify_sources(repo,{'a.py':digest(large)},[first,second])
        except BaseException as caught:ok('fatal identity/no retry '+type(error).__name__,caught is error and count[0]==1)
        else:raise AssertionError('fatal absent')
    finally:new._git_transport=actual
# Long argv path must keep the actual baseline fallback, no metadata phase.
for module in (old,new):
    actual=module._git_transport;calls=[]
    def argv_spy(root,requests,expression=None,**kw):calls.append((requests,expression,kw));return small
    module._git_transport=argv_spy
    try:module._verify_sources(repo,{'x'*65536:digest(small)},[first])
    finally:module._git_transport=actual
    ok('long path literal argv '+module.__name__,len(calls)==1 and calls[0][0]==b'' and calls[0][1]==first+':'+'x'*65536 and calls[0][2]=={})
# Multi-flush cardinality preserves 128 logical row boundary; real Git tiny bodies.
for module in (old,new):
    actual=module._git_transport;events=[]
    def spy(root,requests,expression=None,**kw):
        events.append((kw.get('_source_check',False),requests.count(b'\n')))
        return actual(root,requests,expression,**kw)
    module._git_transport=spy
    try:module._verify_sources(repo,{'small.py':digest(small)},[first]*129)
    finally:module._git_transport=actual
    ok('original128 flush boundary '+module.__name__,events==([(False,128),(False,1)] if module is old else [(True,128),(False,1),(False,1)]))
# Literal old request/argv limits reject identically before subprocess creation.
for requests,expression in ((b'x'*65537,None),(bytearray(),None),(b'','x'*131073)):
    ok('unchanged transport input bound '+str(len(checks)),outcome(lambda:old._git_transport(repo,requests,expression))==outcome(lambda:new._git_transport(repo,requests,expression)))
# Extracted real flush uses a single absolute deadline, including reconstruction.
import types
node=next(n for n in ast.parse((HERE/'verify.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_verify_source_flush')
clock=iter((0.,11.));fake_time=types.SimpleNamespace(monotonic=lambda:next(clock))
local_builtins=dict(vars(builtins))
local_builtins['__import__']=lambda name,*a,**k:fake_time if name=='time' else safe_import(name,*a,**k)
blob=b'z'*1024;oid=b'a'*40;header=oid+b' blob 1024\n';calls=[]
def transport(root,requests,**kw):
    calls.append(kw)
    return header*2 if kw.get('_source_check') else header+blob+b'\n'
namespace={'__builtins__':local_builtins,'_GIT_SECONDS':10,'_GIT_BODY':old._GIT_BODY,'_GIT_PARTS':128,'_git_transport':transport,'_verify_batch':old._verify_batch,'re':old.re,'subprocess':subprocess}
exec(compile(ast.Module(body=[node],type_ignores=[]),'deadline-fixture','exec'),namespace)
result=outcome(lambda:namespace['_verify_source_flush'](None,b'first\nsecond\n',[('p','c',digest(blob))]*2))
ok('shared deadline does not reset across phases',all(call['_source_deadline']==10. for call in calls) and len(calls)==2)
ok('expired final transport budget refuses before hashes',result[0]=='TimeoutExpired')
# All unrelated AST, registration transport calls, cleanup and parser untouched.
a=ast.parse((HERE/'baseline_verify.py').read_text());b=ast.parse((HERE/'verify.py').read_text())
changed={'_git_transport','_verify_sources','_verify_source_flush'}
ok('exact AST outside three changed scopes',[ast.dump(n,include_attributes=False) for n in a.body if getattr(n,'name',None) not in changed]==[ast.dump(n,include_attributes=False) for n in b.body if getattr(n,'name',None) not in changed])
# Inverse patch applies to byte-identical baseline without touching Main.
patched=subprocess.run(['patch','--batch','--silent','--output',str(HERE/'inverse_restored02.py'),str(HERE/'verify.py'),str(HERE/'verify.inverse.patch')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
ok('exact inverse',patched.returncode==0 and (HERE/'inverse_restored02.py').read_bytes()==(HERE/'baseline_verify.py').read_bytes())
result={'status':'PASS_SYNTHETIC_SOURCE_TRANSPORT_ONLY','checks':checks,'count':len(checks),'measurements':measurements,'elapsed_ns':time.perf_counter_ns()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'affinity':sorted(os.sched_getaffinity(0)),'numerical_imports':False,'main_git_changed':False,'actual_admission':False,'fixture_commits':[first,second]}
(HERE/'RESULT02.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'count':len(checks),'elapsed_ns':result['elapsed_ns'],'peak_rss_kib':result['peak_rss_kib'],'duplicate_response_bytes':{'old':measurements['duplicate']['old']['response_bytes'],'new':measurements['duplicate']['candidate']['response_bytes']},'unique_response_bytes':{'old':measurements['unique']['old']['response_bytes'],'new':measurements['unique']['candidate']['response_bytes']}}))
