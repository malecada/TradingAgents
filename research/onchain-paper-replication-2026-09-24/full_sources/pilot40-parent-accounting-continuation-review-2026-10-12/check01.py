from pathlib import Path
import os,resource
os.sched_setaffinity(0,{2,3});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
import runpy,json,copy
C=Path('research/onchain-paper-replication-2026-09-24/full_sources/pilot40-parent-accounting-continuation-candidate-2026-10-12');ns=runpy.run_path(str(C/'check02.py'));h=ns['Checks']();results=[]
for label,mutation in [
 ('counter',lambda d:d[0]['spent_counters'].update(completed_operations=995818906)),
 ('trace',lambda d:d[4].__setitem__('traceback',d[4]['traceback'].replace(b'stale interval cannot refresh',b'different failure'))),
 ('parent',lambda d:d[1].update(parent_experiment='other')),
 ('source',lambda d:d[5].__setitem__(next(iter(d[5])),b'pass\n')),
 ('recovery',lambda d:d[4].__setitem__('return_review',b'{}')),
 ('tail',lambda d:d[0]['retained_partial_work'].update(completed_operations=1)),
 ('mode',lambda d:d[1].update(parent_accounting_mode='unknown')),
 ('truncated',lambda d:d[1]['batches'].pop()),
 ('bool_zero',lambda d:d[0]['retained_partial_work'].update(checkpoint_attempts=False))]:
 d=h.fixture();mutation(d)
 try:h.call(d)
 except (ValueError,KeyError,TypeError):results.append({'control':label,'refused':True})
 else:results.append({'control':label,'refused':False})
print(json.dumps(results,indent=2))
assert all(r['refused'] for r in results)
