import hashlib,json,os,resource,runpy,statistics,time
from pathlib import Path
os.sched_setaffinity(0,{2,3});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
P=Path(__file__).resolve().parent;ns=runpy.run_path(str(P/'check_candidate01.py'));g=ns['graph'](32769);expected=ns['original_hash'](g);env,calls=ns['helper']()
began=time.perf_counter();pin=env['WeeklyDigestPin'](g,original_digest=expected);construction=time.perf_counter()-began;assert pin._pin is not None
rows={'original_graph_hash_fresh_validation':[],'pin_rejoin_fresh_validation':[]}
for repeat in range(9):
 for name,fn in ((list(rows)[0],lambda:ns['original_hash'](g)),(list(rows)[1],lambda:pin.verify(g))):
  w=time.perf_counter();c=time.process_time();value=fn();rows[name].append({'wall':time.perf_counter()-w,'cpu':time.process_time()-c});assert value==expected
median={k:statistics.median(x['wall'] for x in v) for k,v in rows.items()};a,b=median.values()
out={'status':'SYNTHETIC_ONLY','source_sha256':hashlib.sha256((P/'weekly_graph_digest_pin.py').read_bytes()).hexdigest(),'affinity':sorted(os.sched_getaffinity(0)),'address_limit_bytes':1024**3,'cpu_limit_seconds':60,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'nodes':32769,'edges':32768,'repetitions':9,'initial_pin_construction_wall_seconds':construction,'original_digest':expected,'samples':rows,'median_wall_seconds':median,'baseline_over_pin':a/b,'wall_reduction_fraction':1-b/a,'helper_validation_calls':calls['validate'],'helper_hash_calls':calls['hash'],'qualification':'One moderate immutable exact-ndarray synthetic graph; original full graph validation remains on each call; no Owner/node-order/source-admission/pipeline measurement; no empirical gain claim.'}
with (P/'BENCHMARK01.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({k:out[k] for k in ('median_wall_seconds','baseline_over_pin','wall_reduction_fraction','peak_rss_kib','initial_pin_construction_wall_seconds')}))
