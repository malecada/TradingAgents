# Reuses the author tiny fixture definitions, not its execution or assertions.
import ast
from pathlib import Path
P=Path(__file__).resolve().parent
source=(P/'verify02.py').read_text();exec(compile(source.split("a=graph();b=graph();ex=executor();")[0],str(P/'verify02.py'),'exec'))
a,b=graph(),graph();x=executor(entries=1);x(a,b,'1'*64);x(graph(features=np.array([[.1],[1.]])),b,'2'*64);x(a,b,'3'*64);ck('one_entry_actual_eviction',x.computed==3 and x.count==1 and x.retained_bytes<=x.max_retained_bytes)
x=executor();x(a,b,'4'*64);x(a,graph(features=np.array([[.2],[1.]])),'5'*64);ck('ordered_right_graph_bytes_miss',x.last_receipt['mode']=='computed')
x=executor();x(a,b,'6'*64);pins=m.SOURCE_PINS;m.SOURCE_PINS={**pins,next(iter(pins)):'0'*64}
try:
 try:x(a,b,'7'*64)
 except ValueError:ck('source_digest_refuses_cache_hit',x.poisoned and x.count==0)
 else:raise AssertionError('source mismatch hit')
finally:m.SOURCE_PINS=pins
states=[];primary=RuntimeError('callback-stop')
def checkpoint(key,ordinal,state,*args):states.append(state);raise primary
x=m.NumericReuseExecutor(c,policy,schedule,checkpoint,max_entries=2,max_retained_bytes=16384,max_key_bytes=4096)
try:x(a,b,'8'*64)
except RuntimeError as e:ck('failed_engine_actual_cleanup',e is primary and len(states)==1 and states[0]['annealing'] is None and x.count==0)
class Purpose(str):pass
x=executor()
try:x(a,b,Purpose('9'*64))
except ValueError:ck('purpose_subclass_refused',x.poisoned)
else:raise AssertionError('purpose subclass accepted')
(P/'RESULT03.json').write_text(json.dumps({'status':'PASS','checks':checks},indent=2)+'\n');print(json.dumps(checks))
