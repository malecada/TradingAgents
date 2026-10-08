import ast,hashlib,json,re,tempfile,types
from pathlib import Path
H=Path(__file__).resolve().parent;C=H.parent/'real-data-pilot-storage-identity01-2026-10-08';R=H.parents[3];M=R/'tradingagents/research/onchain_replication'
checks=[]
def check(name,ok):
 assert ok,name
 checks.append(name)
def refuse(name,fn):
 try:fn()
 except (ValueError,RuntimeError):checks.append(name);return
 raise AssertionError(name)
def load(p,ns):
 t=ast.parse(p.read_text());t.body=[n for n in t.body if not isinstance(n,ast.ImportFrom) or not n.level];exec(compile(t,str(p),'exec'),ns)
s={};load(M/'workflow_storage.py',s);load(C/'real_pilot_storage.py',s)
o={};load(M/'workflow_storage.py',o);load(C/'baseline_real_pilot_storage.py',o)
pins=json.loads((C/'HASHES.json').read_text())
for n in ['real_pilot_storage.py','resources.py','real_pilot_import_caller.py']:check('hash_'+n,hashlib.sha256((C/n).read_bytes()).hexdigest()==pins[n])
for n in ['RESIDUAL_POLICY','NATIVE_METADATA_BYTES','FIELDS','COUNTS']:check('unchanged_'+n,s[n]==o[n])
old=s['EXPERIMENT'];new='eth-paper-real-data-end-to-end-resource-20261009-22'
for v in [None,True,1,'../x',new+'/../21',new+'\n',new.replace('-22','-022'),new.replace('-22','-0'),new.replace('-22','-1000000'),new.replace('20261009','２０２６１００９')]:refuse('name_'+repr(v),lambda v=v:s['experiment_name'](v))
# Extract only added metadata joins. No guard, Owner or Admission instantiated.
t=ast.parse((C/'resources.py').read_text())
f=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=='guarded_run')
block=next(x for x in f.body if isinstance(x,ast.If) and ast.unparse(x.test)=='storage_budget is not None').body[1].body
worker=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=='assert_guarded_worker')
wblock=next(x for x in worker.body if isinstance(x,ast.If) and ast.unparse(x.test)=="'native_unit_limits' in live").body[:2]
class Strip(ast.NodeTransformer):
 def visit_ImportFrom(self,n):return None
def snippet(body,values):
 tree=Strip().visit(ast.Module(body=body,type_ignores=[]));exec(compile(ast.fix_missing_locations(tree),'actual_metadata_seam','exec'),dict(s,**values))
with tempfile.TemporaryDirectory(dir=H) as td:
 root=Path(td);(root/'research_runs').mkdir();(root/'research_runs/.lock').touch();(root/'research_artifacts').mkdir()
 def budget(name):return {'schema_version':2,'kind':s['KIND'],'authority_root':str(root),'experiment':name,'roots':[str(root/'research_artifacts'),str(root/'research_runs'/name)],'shared_files':[str(root/'research_runs/.lock')],'limits':dict(max_allocated_bytes=10**8,max_logical_bytes=10**8,max_entries=10000,max_depth=64,max_scan_seconds=5)}
 check('legacy_validate_inverse',s['validate'](budget(old),root).identity==o['validate'](budget(old),root).identity)
 check('legacy_paths_inverse',s['residual_paths'](root)==o['residual_paths'](root))
 check('legacy_environment_inverse',s['environment'](root,{})==o['environment'](root,{}))
 refuse('fresh_default_refusal',lambda:s['validate'](budget(new),root))
 b=budget(new);s['validate'](b,root,experiment=new);checks.append('fresh_explicit')
 for field,val in [('authority_root',str(root/'wrong')),('shared_files',[]),('roots',budget(old)['roots']),('experiment',old)]:
  changed=dict(b);changed[field]=val;refuse('budget_'+field,lambda:s['validate'](changed,root,experiment=new))
 w=s['WritableUnion'](b,root,experiment=new);observed=w.check();check('residual_three_paths',all(Path(x['root']).name==new for x in observed['residual_domains']['training_and_lifecycle']['roots']))
 w.target.mkdir();w.check();w.target.rename(root/'research_runs/retired');refuse('birth_disappearance',w.check)
 def parent(budgetname,ownername,exp,native={}):snippet(block,dict(storage_budget=budget(budgetname),cwd=root,native_unit_limits=native,owner_identity={'experiment':ownername},experiment=exp))
 parent(old,old,None);parent(new,new,new);checks.append('parent_legacy_none_and_fresh')
 for args in [(new,new,None),(new,old,new),(old,new,new),(new,new,new,None)]:refuse('parent_mismatch_'+repr(args),lambda args=args:parent(*args))
 def child(budgetname,ownername,adname):snippet(wblock,dict(live={'storage_budget':budget(budgetname),'owner_identity':{'experiment':ownername}},pilot_context=None if adname is None else (types.SimpleNamespace(experiment_id=adname),{})))
 child(old,old,None);child(new,new,new);checks.append('worker_legacy_and_explicit')
 for args in [(new,new,None),(old,new,new),(new,old,new),(new,new,old)]:refuse('worker_mismatch_'+repr(args),lambda args=args:child(*args))
base=(C/'baseline_real_pilot_import_caller.py').read_text();check('caller_single_keyword', (C/'real_pilot_import_caller.py').read_text()==base.replace('watch=WritableUnion(budget,run.admission.root)','watch=WritableUnion(budget,run.admission.root,experiment=run.admission.experiment_id)',1))
result={'decision':'accepted-source-only-not-entry-release','candidate_hashes':{n:pins[n] for n in ('real_pilot_storage.py','resources.py','real_pilot_import_caller.py')},'checks':checks,'scope':'Actual validators/scanners and extracted actual parent/worker identity statements; metadata fixtures only, no actual guard, Owner, Admission, scientific imports or job. Canonical name is syntax, not calendar or admission authentication. Existing genuine callers must supply admitted identity. Environment route only validates budget/name/path shape, not authority.','required_future_seams':['job.py:242 prepare_environment(...,experiment=ad.experiment_id)','job.py native guarded_run call around307: experiment=ad.experiment_id (only the applicable fresh pilot route)','fresh preflight WritableUnion(...,experiment=EXPERIMENT)','fresh RootIO WritableUnion(...,experiment=EXPERIMENT)','metadata preparation storage.validate/WritableUnion/residual_check/prepare_environment when used for fresh identity; exact selected experiment required'],'preservation':'Residual limits/native cap/environment routes unchanged. Existing birth, volume, inode, lock and scanner code unchanged except routing chosen identity. None/default continues21. No Main/Git/live edits.'}
(H/'SOURCE_REVIEW01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'decision':result['decision'],'checks':len(checks)}))
