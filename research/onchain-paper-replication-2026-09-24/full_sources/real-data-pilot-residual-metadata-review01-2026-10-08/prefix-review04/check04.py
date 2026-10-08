import ast,copy,hashlib,json,types,difflib
from pathlib import Path
R=Path.cwd(); F=R/'research/onchain-paper-replication-2026-09-24/full_sources'; P=F/'real-data-pilot-fixed20-metadata-successor01-2026-10-08'; H=Path(__file__).resolve().parent
checks=[]; hashes={}
def pin(p,h=None):
 b=p.read_bytes();v=hashlib.sha256(b).hexdigest();assert h is None or v==h,(p,v);hashes[str(p.relative_to(R))]=v;return b.decode()
def check(n,v):
 assert v,n
 checks.append(n)
def mod(p):
 m=types.ModuleType('review');m.__file__=str(p);exec(compile(pin(p),str(p),'exec'),m.__dict__);return m
a=json.loads(pin(P/'DEPENDENCIES03.json'));b=json.loads(pin(P/'DEPENDENCIES04.json'))
reservation=json.loads(pin(P/'PREFIX_RESERVATION04.json'))
pin(P/'successor04.py','65f34aecd8f7b4e2505fb28586c10196c731e3ed51a95f3edca7b8761997e267')
check('loader_only_dependency_filename',pin(P/'successor04.py').replace('DEPENDENCIES04.json','DEPENDENCIES03.json')==pin(P/'successor03.py'))
check('only_four_dependencies_changed',{k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}=={'builder','controls','handoff','residuals'})
for k,v in a.items():pin(R/v['path'],v['sha256'])
for k,v in b.items():pin(R/v['path'],v['sha256'])
for k,v in reservation['source_changes'].items():check('reservation_pin_'+k,v==b[k])
v=reservation['source_stop_proof']; evidence=json.loads(pin(R/v['path'],v['sha256']))
for name,h in evidence['reviewed_sources'].items():pin(R/'tradingagents/research/onchain_replication'/name,h)
for k in ('builder','controls','handoff','residuals'):
 old=(R/a[k]['path']).read_text();new=(R/b[k]['path']).read_text();(H/(k+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=a[k]['path'],tofile=b[k]['path'])))
old=mod(P/'successor03.py');new=mod(P/'successor04.py')
stage=json.loads((F/'real-data-pilot-capacity-selection03-2026-10-08/compact_policy.json').read_text())['stage_policy']
kwargs=dict(native_file_bytes=1073741824,training_checkpoint_bytes=4194304,runtime_reservation=dict(logical_bytes=1048576,regular_files=16,directories=13,max_file_bytes=1048576))
def norm(v):
 v=copy.deepcopy(v)
 for d in v['residual_domains'].values():d.pop('evidence_sha256')
 return v
r3=old.load('residuals');r4=new.load('residuals');full=norm(r4.resolve(stage,**kwargs));prior=norm(r3.resolve(stage,**kwargs));check('actual_default_residual_equal',full==prior)
prefix=norm(r4.resolve(stage,**kwargs,matching_stages=1));c=prefix['residual_domains']['checkpoint_retention'];f=full['residual_domains']['checkpoint_retention']
check('one_stage_counts',all(c[k]*7==f[k] for k in ('logical_bytes','regular_files','directories')))
for k in ('logical_bytes','regular_files','directories','bound_basis'):c[k]=f[k]
prefix['source_bounds']['matching_stages']=7
check('residual_all_other_fields_unchanged',prefix==full)
for bad in (True,1.0,0,2,6,8,'1',None):
 try:r4.resolve(stage,**kwargs,matching_stages=bad)
 except ValueError:checks.append('stage_refused_'+repr(bad))
 else:raise AssertionError(bad)
# Execute exact changed source guard statements in isolation, without metadata IO.
diag={'schema_version':1,'max_completed_pairs':1024,'checkpoint_every_pairs':64,'checkpoint_relative':'scoring-diagnostic/progress.json'}
for key,var,graphs in [('builder','p','g'),('handoff','pilot','graphs')]:
 tree=ast.parse((R/b[key]['path']).read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==('build' if key=='builder' else 'prepare'))
 start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prefix' for t in n.targets))
 code=compile(ast.Module(body=fn.body[start:start+2],type_ignores=[]),'<exact guard>','exec')
 def run(d,rows=33):
  env={var:{'scoring_diagnostic':d},graphs:{str(i):{'rows':rows} for i in range(7)},'need':r4.need};exec(code,env)
 run(diag);checks.append(key+'_exact_guard_accepts')
 bads=[None,[],{},diag|{'extra':1},diag|{'max_completed_pairs':1025},diag|{'schema_version':True},diag|{'max_completed_pairs':1024.0},diag|{'checkpoint_every_pairs':64.0},diag|{'checkpoint_relative':'other'}]
 for d in bads:
  try:run(d)
  except ValueError:pass
  else:raise AssertionError((key,d))
 checks.append(key+'_count_type_membership_refusals')
 try:run(diag,32)
 except ValueError:checks.append(key+'_first_graph_boundary_refused')
 else:raise AssertionError('boundary')
controls=new.load('controls');tree=ast.parse((R/b['controls']['path']).read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='calculate');code=compile(ast.Module(body=fn.body[:4],type_ignores=[]),'<controls guard>','exec')
fields={'schema_version','graphs','chunk_cells','typed_control_bytes','archive','stage','transport','residual_domains','filesystem','baseline','storage_budget'}
def cr(d):exec(code,{'s':dict.fromkeys(fields)|{'diagnostic':d},'need':r4.need})
d=reservation['diagnostic'];cr(d);checks.append('controls_exact_guard_accepts')
for v in (None,[],{},d|{'extra':1},d|{'max_completed_pairs':1025},d|{'retained_matrix_files':True},d|{'active_matching_stages':1.0},d|{'retained_matrix_files':7}):
 try:cr(v)
 except ValueError:pass
 else:raise AssertionError(v)
checks.append('controls_count_type_membership_refusals')
(H/'CHECKS04.json').write_text(json.dumps({'status':'NARROW_SOURCE_CHECKS_PASS','checks':checks,'source_sha256':hashes},indent=2,sort_keys=True)+'\n')
print(json.dumps({'checks':len(checks),'status':'PASS'}))
