"""Offline metadata/opaque-body mutation controls; no original modules imported."""
import copy,json,stat
from prepare01 import HERE,CAP,CASES,CHANGE,NEW,OLD,one_change,release,read,sha,encode
from rebind01 import rebind
checks=[]
def check(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
def refuses(name,fn):
 try:fn()
 except ValueError:checks.append(name)
 else:raise AssertionError(name)
inventory=json.loads(read(HERE/'generated01/SOURCE_MAP01.json'))
before={r['path']:r['baseline_sha256'] for r in inventory['entries']};after={r['path']:r['candidate_sha256'] for r in inventory['entries']}
one_change(before,after);check('exact199/148',len(before)==199 and sum(x.startswith('tradingagents/') for x in before)==148)
for r in inventory['entries']:
 for kind in ('baseline','candidate'):
  p=HERE/'generated01'/kind/r['path'];check(kind+' body '+r['path'],sha(read(p))==r[kind+'_sha256']);check(kind+' physical mode '+r['path'],stat.S_IMODE(p.stat().st_mode)==r['physical_mode'])
wrong=dict(after);wrong.pop(next(k for k in wrong if k!=CHANGE));refuses('missing source refused',lambda:one_change(before,wrong))
wrong=dict(after);wrong[next(k for k in wrong if k!=CHANGE)]='0'*64;refuses('second mutation refused',lambda:one_change(before,wrong))
wrong=dict(after);wrong[CHANGE]=OLD;refuses('unchanged dictionary refused',lambda:one_change(before,wrong))
wrong=dict(after);wrong[CHANGE]='0'*64;refuses('unreviewed replacement refused',lambda:one_change(before,wrong))
for case in CASES:
 d,b=rebind(case);check(case+' unresolved root',d['capsule_root'] is None);check(case+' fresh identity null',d['fresh_identity'] is None and d['case_contract']['experiment_id'] is None)
 check(case+' no inherited budget',d['experiment']['cumulative_budget_extension'] is None and d['cumulative_allocation'] is None)
 check(case+' exact33/15/6',len(d['experiment']['inputs'])==33 and len(d['roles'])==15 and len(d['experiment']['outputs'])==6)
 for role,reference in d['case_contract']['additional_inputs'].items():
  ref=reference['reference'];raw=b.get(ref['path'])
  if raw is None:raw=read(HERE/'generated01/input-baseline'/ref['path'])
  check(case+' contract input '+role,sha(raw)==ref['sha256']==d['experiment']['inputs'][role]['sha256'] and len(raw)==ref['bytes'])
 fresh='/nonexistent-root-owned-candidate/source';bound,bodies=rebind(case,fresh)
 job=json.loads(bodies[d['experiment']['inputs']['execution_job']['path']]);check(case+' new root resource paths',job['resources']['disk_paths']==[fresh] and job['resources']['storage_budget']['root']==fresh)
 check(case+' unchanged limits',job['resources']['memory_max_bytes']==3*1024**3 and job['resources']['memory_high_bytes']==3*1024**3 and job['resources']['disk_floor_bytes']==10*1024**3 and job['resources']['wall_seconds']==1800)
 refuses(case+' old root refused',lambda:rebind(case,str(CAP)));refuses(case+' relative root refused',lambda:rebind(case,'relative'))
 refuses(case+' release refused',lambda:release(bound))
check('original26source',len(json.loads(read(HERE/'generated01/ORIGINAL_PROVENANCE01.json'))['source_objects'])==26)
with (HERE/'CHECKS01.json').open('xb') as f:f.write(encode({'count':len(checks),'checks':checks,'native_execution':False,'numerical_imports':False,'payload_decoding':False,'paper_fits':0}))
print(len(checks),'passed')
