"""QUEUED Root-only after active pilot terminal; imports native/NumPy when run."""
import hashlib,importlib.util,json,sys,time,math
from pathlib import Path
P=Path(__file__).resolve().parent
start=time.monotonic();checks=[];failure=None
try:
    built=json.loads((P/'BUILD01.json').read_text());lib=P/built['library']
    assert built['returncode']==0 and hashlib.sha256(lib.read_bytes()).hexdigest()==built['sha256']
    spec=importlib.util.spec_from_file_location('_edge_chunk',lib);native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
    import numpy as np
    from tradingagents.research.onchain_replication.matching_reference import agreement
    from edge_chunk_adapter import make_filler
    filler=make_filler(native,np,agreement)
    def frozen(rows):return np.frombuffer(np.asarray(rows,dtype=np.float64).tobytes(),dtype=np.float64).reshape(-1,2)
    cases=[('normal',[[0.,0.],[1.,-2.],[2**-24,2**-25]],[[0.,-0.],[2.,-1.],[0.,0.]]),('extreme',[[1e100,-1e100],[math.inf,0.],[math.nan,1.]],[[0.,0.],[math.inf,0.],[0.,0.]]),('late_overflow',[[0.,0.],[1e200,1.]],[[0.,0.],[0.,0.]])]
    for name,rows,other in cases:
        a,b=frozen(rows),frozen(other);n=len(a);idx=np.arange(n,dtype=np.int64)
        expected=np.full(n,-7.);actual=expected.copy();errors=[];finished=0
        try:
            for i in range(n):expected[i]=.5*agreement(a[i],b[i]);finished+=1
        except BaseException as e:errors.append((type(e).__name__,str(e)))
        progress=[None];native_error=None
        try:assert filler(actual,a,b,idx,idx,n,agreement,progress) is True
        except BaseException as e:native_error=(type(e).__name__,str(e))
        assert native_error==(errors[0] if errors else None)
        assert expected.tobytes()==actual.tobytes(),name
        assert progress[0]==(finished if errors else n-1),name
        checks.append({'case':name,'byte_equal':True,'progress':progress[0],'error':native_error,'eligible_readonly_two_attribute':True})
    # Original callback is used by caller after False; unsupported never touches state.
    a=frozen([[1.,2.]]);idx=np.array([0],dtype=np.int64)
    for unsupported in (a.copy(),np.frombuffer(bytes(24),dtype=np.float64).reshape(1,3)):
        w=np.array([-7.]);progress=[None]
        assert filler(w,unsupported,unsupported,idx,idx,1,agreement,progress) is False
        assert w.tobytes()==np.array([-7.]).tobytes() and progress==[None]
    checks.append({'unsupported_no_write':True})
    # Same-function changed-code and mutable math-global refusal before writes.
    def refusal(call):
        try:call()
        except ValueError:return
        raise AssertionError('expected currentness refusal')
    original_code=agreement.__code__
    try:
        agreement.__code__=(lambda a,b:1.).__code__
        w=np.array([-7.]);progress=[None];refusal(lambda:filler(w,a,a,idx,idx,1,agreement,progress));assert progress==[None]
    finally:agreement.__code__=original_code
    original_exp=math.exp
    try:
        math.exp=lambda x:1.
        refusal(lambda:filler(w,a,a,idx,idx,1,agreement,progress));assert progress==[None]
    finally:math.exp=original_exp
    checks.append({'function_and_global_mutation_refused':True})
except BaseException as e:failure={'type':type(e).__name__,'message':str(e)}
finally:
    (P/'NUMERIC_RESULT01.json').write_text(json.dumps({'status':'FAILED' if failure else 'PASS_FINITE_SYNTHETIC','checks':checks,'failure':failure,'elapsed_seconds':time.monotonic()-start},indent=2)+'\n')
if failure:raise SystemExit(1)
