import os,resource,signal,time,json,math,sys
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[3]))
import numpy as np
from tradingagents.research.onchain_replication.matching_numeric_kernel import fill_agreement

def frozen(a,dtype):
    a=np.asarray(a,dtype=dtype);return np.frombuffer(a.tobytes(),dtype=dtype).reshape(a.shape)
rows=[]
for width in (2,4):
    left=frozen([[(i*7+k*3)%17/8-1 for k in range(width)] for i in range(64)],np.float64)
    right=frozen([[(i*11-k*5)%19/8-1 for k in range(width)] for i in range(64)],np.float64)
    for count in (8,1024):
        i=frozen([k%64 for k in range(count)],np.int64);j=frozen([(k*13+1)%64 for k in range(count)],np.int64)
        a=np.zeros(count);b=np.zeros(count)
        def candidate():
            if not fill_agreement(left,right,i,j,a,0,count):raise AssertionError('declined')
        def scalar():
            for k in range(count):
                b[k]=math.exp(-math.fsum((float(x)-float(y))**2 for x,y in zip(left[i[k]],right[j[k]],strict=True))/width)
        candidate();scalar();np.testing.assert_allclose(a,b,rtol=1e-6,atol=1e-8)
        result={'width':width,'count':count,'loops_per_route':100,'max_absolute_difference':float(np.max(np.abs(a-b)))}
        # Alternating order reduces systematic first-route placement bias; no hidden warmup matrix.
        times={name:[0.,0.] for name in ('candidate','scalar')}
        for cycle in range(2):
            for name,fn in ((('candidate',candidate),('scalar',scalar)) if cycle==0 else (('scalar',scalar),('candidate',candidate))):
                wall=time.perf_counter();cpu=time.process_time()
                for _ in range(50):fn()
                times[name][0]+=time.perf_counter()-wall;times[name][1]+=time.process_time()-cpu
        result['seconds_wall_cpu']=times;result['scalar_over_candidate_wall']=times['scalar'][0]/times['candidate'][0];rows.append(result)
with (H/'TIMING01.json').open('x') as f:json.dump({'scope':'synthetic complete helper vs scalar output loop; not actual solver speed','numpy':np.__version__,'rows':rows},f,indent=2);f.write('\n')
print(json.dumps(rows))
