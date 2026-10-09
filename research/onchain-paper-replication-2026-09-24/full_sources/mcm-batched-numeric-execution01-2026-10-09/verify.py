import hashlib,importlib,json,os,sys,types
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[3]));fixtures=P/'fixtures';fixtures.mkdir()
package=types.ModuleType('numeric_execution_fixture');package.__path__=[str(P),str(fixtures)];sys.modules[package.__name__]=package
source=P.parent/'matching-exact-numeric-reuse03-2026-10-09'
for original,name in [('numeric_reuse.py','batched_numeric_reuse.py'),('batched_pair_executor.py','batched_pair_executor.py')]: (fixtures/name).write_bytes((source/original).read_bytes())
m=importlib.import_module('numeric_execution_fixture.numeric_execution');memo=importlib.import_module('numeric_execution_fixture.batched_numeric_reuse')
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph
c=dict(beta0=.2,beta_final=.5,beta_rate=.1,max_iterations=3,alpha=.7,max_pair_entries=10000,normalization_iterations=1,solver='algorithm1_literal')
p=dict(max_state_bytes=65536,normalization_chunk_entries=8,hardening_chunk_entries=8,hardening_buffer_bytes=65536,max_score_buffer_bytes=65536,chunk_edges=8,max_checkpoint_bytes=262144,max_publications=100,total_checkpoint_bytes=1048576)
s=dict(max_checkpoints=100,calls_per_checkpoint=2,operations_per_call=10000,max_total_checkpoints=1000,max_total_checkpoint_bytes=500000000)
def graph(names):return AttributedGraph(names,np.array([[0.],[1.]]),np.array([[0,1],[1,0]],dtype=np.int64),np.array([[.2],[.3]]),'a'*64,names[0])
a,b=graph(('a','b')),graph(('x','y'));checks=[]
def ck(n,v):assert v,n;checks.append(n)
def root(name):r=fixtures/name;r.mkdir();return r
def make(r,**kw):return m.NumericExecution(r,c,p,s,lambda *args:None,**(dict(cells=4,batch_cells=2,max_origin_bytes=36,max_summary_bytes=16384,max_entries=8,max_retained_bytes=16384,max_key_bytes=4096)|kw))
def fds():return len(list(Path('/proc/self/fd').iterdir()))
def refusal(fn):
    try:fn()
    except (ValueError,OSError):return True
    return False
r=root('complete');x=make(r);out=[]
for i in range(4):out.append(x(a,b,hashlib.sha256(str(i).encode()).hexdigest()))
binding=x.finish();ck('two_actual_guarded_batches',x.memo.counters['source_guard_calls']==5 and binding['computed']==1 and binding['reused']==3 and binding['batches']==2)
ck('unchanged_actual_result',all(v==out[0] for v in out));ck('exact9byte_origins',list(m.RECORD.iter_unpack((r/'numeric-origins.bin').read_bytes()))==[(0,0),(1,0),(1,0),(1,0)])
ck('read_only_full_verification',m.verify(r,binding)['cells']==4);x.close();ck('cache_closed',x.memo.closed and x.memo.count==0)
(P/'BINDING01.json').write_text(json.dumps(binding,indent=2)+'\n')
ck('duplicate_namespace_refused',refusal(lambda:make(r)))
# Exact finite range close cannot publish successful partial batch.
rp=root('partial');y=make(rp);y(a,b,'1'*64);guard=y.memo.counters['source_guard_calls'];y.close();ck('partial_close_no_attest_credit',y.memo.poisoned and y.memo.counters['source_guard_calls']==guard and (rp/'numeric-origins.bin').stat().st_size==0 and not list((rp/'numeric-batches').iterdir()))
# Final guard fails after a hit, before any batch output.
rg=root('guard');y=make(rg);y(a,b,'1'*64);saved=memo.immutable_session.__file__;wrong=fixtures/'wrong.txt';wrong.write_text('wrong body');memo.immutable_session.__file__=str(wrong)
try:ck('end_guard_before_disk_credit',refusal(lambda:y(a,b,'2'*64)) and y.poisoned and (rg/'numeric-origins.bin').stat().st_size==0 and not list((rg/'numeric-batches').iterdir()))
finally:memo.immutable_session.__file__=saved;y.close()
# Constructor failure after descriptor acquisition closes all owned handles.
n=fds();rc=root('constructor');memo.immutable_session.__file__=str(wrong)
try:ck('constructor_guard_refusal',refusal(lambda:make(rc)))
finally:memo.immutable_session.__file__=saved
ck('constructor_no_fd_leak',fds()==n)
# Partial physical origin write preserved, no summary accepted.
rw=root('partial-write');y=make(rw);y(a,b,'1'*64);write=os.write;calls=0
failure=OSError('synthetic write failure')
def badwrite(fd,body):
    global calls
    if fd==y.origins_fd:
        calls+=1
        if calls==1:return write(fd,body[:5])
        raise failure
    return write(fd,body)
os.write=badwrite
try:
    try:y(a,b,'2'*64)
    except OSError as e:ck('partial_write_primary_and_no_credit',e is failure and y.poisoned and (rw/'numeric-origins.bin').stat().st_size==5 and not list((rw/'numeric-batches').iterdir()))
    else:raise AssertionError('write failure accepted')
finally:os.write=write;y.close()
# Readback corruption and cumulative summary reservation reject before summary credit.
rr=root('readback');y=make(rr);y(a,b,'1'*64);pread=os.pread
os.pread=lambda fd,count,offset:b'X'*count if fd==y.origins_fd else pread(fd,count,offset)
try:ck('origin_readback_refuses',refusal(lambda:y(a,b,'2'*64)) and y.poisoned and not list((rr/'numeric-batches').iterdir()))
finally:os.pread=pread;y.close()
rl=root('summary-cap');y=make(rl,max_summary_bytes=1);y(a,b,'1'*64);ck('summary_cap_before_origin_write',refusal(lambda:y(a,b,'2'*64)) and (rl/'numeric-origins.bin').stat().st_size==0);y.close()
ck('origin_reservation_constructor_refuses',refusal(lambda:make(root('origin-cap'),max_origin_bytes=35)))
# All cleanup actions attempted and primary caller exception preserved.
rf=root('cleanup');y=make(rf);original_close=os.close;target=y.origins_fd;clean_error=OSError('synthetic close after close');primary=RuntimeError('primary caller failure');before=fds()
def badclose(fd):
    original_close(fd)
    if fd==target:raise clean_error
os.close=badclose
try:
    try:
        with y:raise primary
    except RuntimeError as e:ck('cleanup_preserves_primary',e is primary and bool(e.__notes__))
finally:os.close=original_close
ck('cleanup_attempts_all',fds()==before-3 and y.closed)
# A new namespace child and changed bytes cannot retain final closure credit.
(r/'numeric-batches'/'extra').write_text('unexpected');ck('extra_summary_refuses',refusal(lambda:m.verify(r,binding)))
rs=root('tamper');z=make(rs,cells=2,max_origin_bytes=18);z(a,b,'1'*64);z(a,b,'2'*64);zb=z.finish();z.close();(rs/'numeric-origins.bin').write_bytes(b'\x01'+b'\0'*17);ck('origin_tamper_refuses',refusal(lambda:m.verify(rs,zb)))
result={'status':'PASS','checks':checks,'affinity':sorted(os.sched_getaffinity(0)),'actual_tiny_session_memo':True,'owner_run_authority':False,'origin_bytes_per_cell':m.RECORD.size,'full_cells':415968128,'full_origin_bytes':9*415968128,'binding_summary_bytes':binding['summary_bytes']}
(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
