"""QUEUED Root-only after active pilot terminal; imports native/NumPy when run."""
import hashlib,importlib.util,json,sys,time,math,os,traceback
from pathlib import Path
P=Path(__file__).resolve().parent
CANDIDATE=P.parent/'matching-compiled-two-attribute-agreement01-2026-10-11'
REFERENCES={'MANIFEST01.json': {'sha256': '445cb2fb0d266a5c17243ad1d1fc9f29cc8a8b5e3fbe1b8472cc98513aa58152', 'bytes': 2179}, 'BUILD01.json': {'sha256': '6846409b718955144407171ab2872144cec7385f41b53098073e979c34e5c5b2', 'bytes': 867}, 'edge_chunk.c': {'sha256': '7218b75e9d2b1f4f832418e1057a7085eeeaa20120a3dfbdcc57e303542ce9f6', 'bytes': 4889}, 'edge_chunk_adapter.py': {'sha256': 'e93bc309b1e7a38dff37ba63fd12bb0a3dce3a6766f829d6583cb008361c4dc6', 'bytes': 3459}, '_edge_chunk.cpython-313-x86_64-linux-gnu.so': {'sha256': 'adead75d8f74f77b7d70164dab5465fef8a0e7ec06255b3dcd599f721745df97', 'bytes': 21920}, 'fixture01.py': {'sha256': '7a7fdebcf236b59a357bdc217ab1b6224e5018bbdc37f924b6adc7cb09de612b', 'bytes': 3527}}
def reserve_attempt(path):
    # Existing directory, including an interrupted attempt, is permanently spent.
    path.mkdir(mode=0o700,exist_ok=False)
    return path

def write_result(path,value):
    with (path/'NUMERIC_RESULT01.json').open('x') as stream:
        stream.write(json.dumps(value,indent=2)+'\n')

ATTEMPT=reserve_attempt(P/'attempt01')
# Preserve raw OS stdout/stderr including extension/runtime failures; no append/reuse.
for descriptor,name in ((1,'stdout.log'),(2,'stderr.log')):
    fd=os.open(ATTEMPT/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:os.dup2(fd,descriptor)
    finally:os.close(fd)
sys.path.insert(0,str(P.parents[3]))
start=time.monotonic();checks=[];failure=None;failed=False;primary=None;secondary=[]
try:
    for name,reference in REFERENCES.items():
        path=CANDIDATE/name
        with path.open('rb') as stream:body=stream.read(reference['bytes']+1)
        assert len(body)==reference['bytes'] and hashlib.sha256(body).hexdigest()==reference['sha256'],name
    built=json.loads((CANDIDATE/'BUILD01.json').read_text());lib=CANDIDATE/built['library']
    assert built['returncode']==0 and hashlib.sha256(lib.read_bytes()).hexdigest()==built['sha256']
    spec=importlib.util.spec_from_file_location('_edge_chunk',lib);native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
    import numpy as np
    from tradingagents.research.onchain_replication.matching_reference import agreement
    adapter_spec=importlib.util.spec_from_file_location('_qualified_two_attribute_adapter',CANDIDATE/'edge_chunk_adapter.py')
    adapter=importlib.util.module_from_spec(adapter_spec);adapter_spec.loader.exec_module(adapter)
    make_filler=adapter.make_filler
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
except BaseException as e:
    failed=True;primary=e
    try:failure={'type':type(e).__name__,'message':str(e)}
    except BaseException as reporting_error:secondary.append(reporting_error)
    try:
        with (ATTEMPT/'failure.txt').open('x') as stream:traceback.print_exc(file=stream)
    except BaseException as reporting_error:secondary.append(reporting_error)
finally:
    try:
        write_result(ATTEMPT,{'status':'FAILED' if failed else 'PASS_FINITE_SYNTHETIC','checks':checks,'failure':failure,'reporting_errors':[type(error).__name__ for error in secondary],'elapsed_seconds':time.monotonic()-start})
    except BaseException as reporting_error:
        if primary is None:failed=True;primary=reporting_error
        else:secondary.append(reporting_error)
    if primary is not None:
        for reporting_error in secondary:
            try:BaseException.add_note(primary,'qualification reporting failure: '+repr(reporting_error))
            except BaseException:pass
        raise primary
