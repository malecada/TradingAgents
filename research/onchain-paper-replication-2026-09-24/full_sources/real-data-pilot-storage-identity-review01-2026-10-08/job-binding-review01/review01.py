import ast,hashlib,json
from pathlib import Path
from types import SimpleNamespace as N
H=Path(__file__).resolve().parent;C=H.parent.parent/'real-data-pilot-storage-job-binding01-2026-10-08';R=H.parents[4]
b=(C/'baseline_job.py').read_text();c=(C/'job.py').read_text();checks=[]
def check(n,v):
 assert v,n
 checks.append(n)
check('candidate_hash',hashlib.sha256(c.encode()).hexdigest()=='2f0f33fe858dfcd2b5f1d76f8aaefe3ba87a333992cf89183f0fa254d17380f0')
edits=[("from .real_pilot_storage import validate,EXPERIMENT\n            if ad.experiment_id!=EXPERIMENT:raise ValueError('fixed real-pilot identity required')\n            validate(budget,Path(root))","from .real_pilot_storage import validate\n            validate(budget,Path(root),experiment=ad.experiment_id)"),("validate(budget,Path(args.root));return residual_check(Path(args.root))","validate(budget,Path(args.root),experiment=args.experiment);return residual_check(Path(args.root),experiment=args.experiment)"),("_,job=_admitted(args)","ad,job=_admitted(args)"),("prepare_environment(Path(args.root),budget,env)","prepare_environment(Path(args.root),budget,env,experiment=ad.experiment_id)"),("_, job = _admitted(args)","ad, job = _admitted(args)"),("        if 'native_unit_limits' in job['resources']:\n            guard_policy=", "        budget=job['resources'].get('storage_budget')\n        identity_join={'experiment':ad.experiment_id} if type(budget) is dict and budget.get('schema_version')==2 else {}\n        if 'native_unit_limits' in job['resources']:\n            guard_policy="),("native_unit_limits=job['resources']['native_unit_limits'], **guard_policy)","native_unit_limits=job['resources']['native_unit_limits'], **identity_join, **guard_policy)"),("owner_identity=owner, **job['resources'])","owner_identity=owner, **identity_join, **job['resources'])")]
x=c
for old,new in edits:
 check('unique_edit_'+str(len(checks)),x.count(new)==1);x=x.replace(new,old,1)
check('full_literal_inverse',x==b)
t=ast.parse(c);oldtree=ast.parse(b)
changed={'resource_policy','_pilot_residual_tail','launch','monitor'}
for n in oldtree.body:
 if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name not in changed:
  other=next(v for v in t.body if isinstance(v,type(n)) and v.name==n.name)
  check('unchanged_AST_'+n.name,ast.dump(other)==ast.dump(n))
class Strip(ast.NodeTransformer):
 def visit_ImportFrom(self,n):return None
def execute(nodes,ns):exec(compile(ast.fix_missing_locations(Strip().visit(ast.Module(nodes,type_ignores=[]))),'isolated_actual_seam','exec'),ns)
monitor=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='monitor')
assigns={n.targets[0].id:n for n in ast.walk(monitor) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)}
guard=next(n for n in ast.walk(monitor) if isinstance(n,ast.If) and ast.unparse(n.test)=="'native_unit_limits' in job['resources']")
for budget in [None,{'root':'legacy','limits':{}},{'schema_version':2}]:
 for native in [False,True]:
  resources={'storage_budget':budget,'wall_seconds':7}
  if native:resources['native_unit_limits']={'x':1}
  calls=[];ns=dict(job={'resources':resources},ad=N(experiment_id='fresh-admitted'),args=N(root='/metadata'),Path=Path,base=Path('/receipt'),owner={'experiment':'fresh-admitted'},_command=lambda a,role:['metadata',role],resources=N(guarded_run=lambda *a,**k:calls.append((a,k))))
  execute([assigns['budget'],assigns['identity_join'],guard],ns)
  check('single_metadata_call_'+str((budget,native)),len(calls)==1)
  kw=calls[0][1];expected={**resources,'cwd':'/metadata','receipt_dir':Path('/receipt/guard'),'memory_swap_max_bytes':0,'owner_identity':ns['owner']}
  if budget and budget.get('schema_version')==2:expected['experiment']='fresh-admitted'
  check('exact_kwargs_'+str((budget,native)),kw==expected)
res=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_pilot_residual_tail')
for budget in [None,{'root':'legacy'},{'schema_version':2}]:
 calls=[]
 def validate(b,r,*,experiment):calls.append(('validate',experiment));assert experiment=='fresh-args'
 def residual(r,*,experiment):calls.append(('residual',experiment));return 'observed'
 ns=dict(Path=Path,validate=validate,residual_check=residual);execute([res],ns)
 out=ns['_pilot_residual_tail'](N(root='/metadata',experiment='fresh-args'),{'resources':{'storage_budget':budget}})
 check('residual_exact_'+str(budget),calls==([('validate','fresh-args'),('residual','fresh-args')] if budget and budget.get('schema_version')==2 else []))
# Actual new validation call uses genuine admitted identity already established by unchanged predicates.
rp=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='resource_policy')
call=next(n for n in ast.walk(rp) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='validate')
seen=[];execute([ast.Expr(call)],dict(validate=lambda *a,**kw:seen.append((a,kw)),budget={'experiment':'fresh'},Path=Path,root='/metadata',ad=N(experiment_id='fresh')))
check('resource_policy_explicit_admitted_identity',seen==[(({'experiment':'fresh'},Path('/metadata')),{'experiment':'fresh'})])
result={'decision':'accepted-source-only-not-entry-release','source':{'candidate_sha256':hashlib.sha256(c.encode()).hexdigest(),'baseline_sha256':hashlib.sha256(b.encode()).hexdigest()},'checks':checks,'reused_storage_review_sha256':'3cb5b6f578f5d9467e8c6397bc5d5b726f3344deb1422562d76d9ed05f9ba696','scope':'Exact eight-edit full inverse. Unchanged genuine Admission/root/job/selection/plan/amended-reserve predicates retained. Actual extracted metadata assignments and calls tested using call recorders; no guard, Admission, Owner, claims, arrays or empirical execution. Legacy nonunion argument sets exact. Residual helper supplies args identity but grants no standalone authority.','pending':'Future RootIO/preflight/metadata controls still require explicit same admitted experiment and separately reviewed registration/binding/release. No Main/Git/live mutation.'}
(H/'SOURCE_REVIEW01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'decision':result['decision'],'checks':len(checks),'sha256':hashlib.sha256((H/'SOURCE_REVIEW01.json').read_bytes()).hexdigest()}))
