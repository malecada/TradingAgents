from pathlib import Path
import warnings
OLD=Path(__file__).parent.parent/'real-data-pilot-exact-annealing-acceleration01-2026-10-08'
exec(compile((OLD/'verify.py').read_text().split('for name,a,b in fixtures:')[0],__file__,'exec'))
results=[]
class PolicyFailure(Exception):pass
class Logger:
    def write(self,*args):raise PolicyFailure('log')
def callback(*args):raise PolicyFailure('call')
def compare(label,a,b,setup,policy,warning_error=False):
    seed=B.create(a,b,config,max_state_bytes=1000000,max_chunk_entries=32)
    B.advance(seed,a,b,config,max_operations=len(a.node_ids)*len(b.node_ids)+1)
    setup(seed)
    states=[];errors=[];used=[]
    for mod in [B,C]:
        state=copy.deepcopy(seed)
        with warnings.catch_warnings(),np.errstate(**policy):
            if warning_error:warnings.simplefilter('error',RuntimeWarning)
            try:used.append(mod.advance(state,a,b,config,max_operations=9));errors.append(None)
            except BaseException as err:errors.append(type(err).__name__);used.append(None)
        states.append(state)
    assert errors[0]==errors[1] and used[0]==used[1],(label,errors,used)
    equal(*states);results.append({'case':label,'exception':errors[0],'cursor':states[0]['cursor'],'safe':states[0]['safe']})
a=graph(2,[(0,1)],True);b=graph(10,[(0,j) for j in range(1,10)],True)
def tiny(s):s['M'][:]=1.;s['M'][1,4]=np.exp(-745.)
oldcall=np.geterrcall()
try:
    for mode in ['raise','call','log','warn','print','ignore']:
        np.seterrcall(Logger() if mode=='log' else callback)
        compare('under-'+mode,a,b,tiny,{'under':mode},mode=='warn')
finally:np.seterrcall(oldcall)
def overflow(s):s['M'][:]=np.finfo(float).max;s['Q'][:]=np.finfo(float).max
compare('overflow-warning-error',a,b,overflow,{'under':'ignore','over':'warn'},True)
compare('overflow-raise',a,b,overflow,{'under':'ignore','over':'raise'})
# Normal bounded inputs remain eligible with RuntimeWarning promoted to exception.
compare('bounded-warning-error',a,b,lambda s:None,{'under':'ignore','over':'warn','invalid':'warn'},True)
# Large but finite M and Q must take scalar fallback even without raised errors.
compare('large-finite-fallback',a,b,lambda s:s['M'].fill(1e100),{'under':'ignore'})
# Original agreement fails after three products and must publish that prefix.
bad=graph(10,[(0,j) for j in range(1,10)],True)
f=bad.edge_features.copy();f[3,0]=1e308;object.__setattr__(bad,'edge_features',f)
compare('agreement-overflow-prefix',a,bad,lambda s:None,{'under':'ignore'})
for name,a,b in fixtures[:3]:
    x=B.create(a,b,config,max_state_bytes=1000000,max_chunk_entries=32);y=C.create(a,b,config,max_state_bytes=1000000,max_chunk_entries=32)
    idx=0
    while x['phase']!='done':
        budget=[1,8,9,17,1024][idx%5];idx+=1
        assert B.advance(x,a,b,config,max_operations=budget)==C.advance(y,a,b,config,max_operations=budget);equal(x,y)
    assert B.result(x,a,b,config).score.hex()==C.result(y,a,b,config).score.hex()
    h=C.save(y,P/('candidate-checkpoint-'+name),a,b,config,max_checkpoint_bytes=1000000)
    equal(y,B.load(P/('candidate-checkpoint-'+name),a,b,config,expected_sha256=h,max_state_bytes=1000000,max_chunk_entries=32))
    h=B.save(x,P/('baseline-checkpoint-'+name),a,b,config,max_checkpoint_bytes=1000000)
    equal(x,C.load(P/('baseline-checkpoint-'+name),a,b,config,expected_sha256=h,max_state_bytes=1000000,max_chunk_entries=32))
# Instrument only to establish the eligible domain is exercised.
a,b=fixtures[-1][1:];seed=B.create(a,b,config,max_state_bytes=1000000,max_chunk_entries=32);B.advance(seed,a,b,config,max_operations=97)
times={}
for label,mod in [('baseline',B),('candidate',C)]:
    samples=[]
    for _ in range(5):
        state=copy.deepcopy(seed);t=time.perf_counter();mod._advance_checked(state,a,b,config,max_operations=7392);samples.append(time.perf_counter()-t)
    times[label]=samples
receipt={'status':'PASS','boundary_checks':checks,'cases':results,'timing_seconds':times,'median_synthetic_edge_speedup':float(np.median(times['baseline'])/np.median(times['candidate']))}
(P/'RESULT01.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
