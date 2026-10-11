"""QUEUED: Root only after active native job closes; scientific/native imports.
No Owner/Admission. Finite synthetic differential, not universal equivalence.
"""
import ast,hashlib,importlib.util,json,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
start=time.monotonic();checks=[];failure=None
try:
    baseline=ROOT/'tradingagents/research/onchain_replication/matching_annealing.py'
    assert hashlib.sha256(baseline.read_bytes()).hexdigest()==json.loads((P/'BASELINE.json').read_text())['sha256']
    built=json.loads((P/'BUILD01.json').read_text());lib=P/built['library']
    assert built['returncode']==0 and hashlib.sha256(lib.read_bytes()).hexdigest()==built['sha256']
    spec=importlib.util.spec_from_file_location('_edge_chunk',lib);native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
    import numpy as np
    from tradingagents.research.onchain_replication import matching_annealing as ann
    from tradingagents.research.onchain_replication.contracts import AttributedGraph
    from adapter import make_filler
    filler=make_filler(native,np,ann.agreement)
    tree=ast.parse((P/'matching_annealing.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_advance_checked')
    env=dict(vars(ann));exec(compile(ast.Module(body=[node],type_ignores=[]),str(P/'matching_annealing.py'),'exec'),env)
    advance=env['_advance_checked']
    config=dict(alpha=1.,beta0=1.,beta_final=30.,beta_rate=.075,max_iterations=50,normalization_iterations=1,solver='algorithm1_literal',max_pair_entries=1024)
    def graph(bad=False):
        features=np.arange(18,dtype=np.float64).reshape(9,2)/32
        if bad:features[5,0]=1e200
        return AttributedGraph(('a','b','c'),np.zeros((3,2)),np.array([(i,j) for i in range(3) for j in range(3)],dtype=np.int64).T,features,'0'*64,'a')
    def eq(a,b):
        assert set(a)==set(b)
        for k in a:
            if type(a[k]) is np.ndarray:assert a[k].dtype==b[k].dtype and a[k].shape==b[k].shape and a[k].tobytes()==b[k].tobytes(),k
            else:assert a[k]==b[k],k
    # Complete actual annealing under small logical budgets; uncached81-edge-product chunks.
    a,b=graph(),graph();x=ann.create(a,b,config,max_state_bytes=4096);y=ann.create(a,b,config,max_state_bytes=4096)
    native_calls=[0]
    def counted(*args):
        value=filler(*args)
        if value:native_calls[0]+=1
        return value
    for i in range(512):
        ann.check(x,a,b,config);ann.check(y,a,b,config)
        u=ann._advance_checked(x,a,b,config,max_operations=32)
        v=advance(y,a,b,config,max_operations=32,edge_chunk_fill=counted)
        assert u==v;eq(x,y)
        if x['phase']=='done':break
    else:raise AssertionError('fixed512-advance bound exhausted')
    assert native_calls[0]>0
    left=ann.harden(x['M']);right=ann.harden(y['M']);assert np.array_equal(left,right)
    assert ann.score_assignment(a,b,left,config)==ann.score_assignment(a,b,right,config)
    checks.append({'complete_boundaries':i+1,'native_chunks':native_calls[0],'state_assignment_score_equal':True})
    # Original late agreement OverflowError and prefix cursor/Q equality.
    a,b=graph(),graph(True);x=ann.create(a,b,config,max_state_bytes=4096);y=ann.create(a,b,config,max_state_bytes=4096)
    ann._advance_checked(x,a,b,config,max_operations=10);ann._advance_checked(y,a,b,config,max_operations=10)
    errors=[]
    for state,fn,kw in [(x,ann._advance_checked,{}),(y,advance,{'edge_chunk_fill':filler})]:
        try:fn(state,a,b,config,max_operations=32,**kw)
        except BaseException as e:errors.append((type(e).__name__,str(e)))
    assert len(errors)==2 and errors[0]==errors[1] and errors[0][0]=='OverflowError';eq(x,y)
    checks.append({'late_original_error':errors[0],'prefix_cursor':x['cursor'],'prefix_equal':True})
    # Adapter refuses unsupported writable features before writes.
    w=np.full(8,-7.);idx=np.arange(8,dtype=np.int64);progress=[None]
    assert filler(w,np.zeros((8,2)),np.zeros((8,2)),idx,idx,8,ann.agreement,progress) is False
    assert np.all(w==-7.) and progress==[None];checks.append({'unsupported_no_write':True})
except BaseException as e:
    failure={'type':type(e).__name__,'message':str(e)}
finally:
    (P/'NUMERIC_RESULT01.json').write_text(json.dumps({'status':'FAILED' if failure else 'PASS_FINITE_SYNTHETIC','checks':checks,'failure':failure,'elapsed_seconds':time.monotonic()-start},indent=2)+'\n')
if failure:raise SystemExit(1)
