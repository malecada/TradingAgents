import ast,datetime,hashlib,json,tempfile
from pathlib import Path
from types import SimpleNamespace as N
H=Path(__file__).resolve().parent;C=H.parent/'real-data-pilot-storage-root-binding01-2026-10-08';R=H.parents[3];B=H.parent/'real-data-pilot-final21-2026-10-08'
checks=[]
def ck(n,v):
 assert v,n
 checks.append(n)
manifest=json.loads((C/'CANDIDATE01.json').read_text())
for name,row in manifest['files'].items():
 for role,path in [('candidate',C/name),('baseline',B/name)]:ck(name+'_'+role+'_hash',hashlib.sha256(path.read_bytes()).hexdigest()==row[role]['sha256'])
# Independently enumerate the exact allowed changes, then invert all bytes.
b=(B/'root_io.py').read_text();c=(C/'root_io.py').read_text()
x=c.replace("PREFIX = 'research_artifacts/", "EXPERIMENT = 'eth-paper-real-data-end-to-end-resource-20261008-21'\nPREFIX = 'research_artifacts/",1)
x=x.replace("if not io['outer_log_handles_closed']", "if args.experiment != EXPERIMENT or not io['outer_log_handles_closed']",1).replace("base = root/PREFIX/'runs'/args.experiment","base = root/PREFIX/'runs'/EXPERIMENT",1).replace("launch['experiment'] != args.experiment:","launch['experiment'] != EXPERIMENT:",1).replace("WritableUnion(job['resources']['storage_budget'],root,experiment=args.experiment)","WritableUnion(job['resources']['storage_budget'],root)",1).replace("'experiment':args.experiment,'source':args.source","'experiment':EXPERIMENT,'source':args.source",1).replace("    admission, job = _admitted(args)\n    if args.experiment != admission.experiment_id:\n        raise ValueError('Root IO experiment differs from genuine admission')", "    if args.experiment != EXPERIMENT:\n        raise ValueError('This Root IO seam admits only the fixed unused pilot')\n    _, job = _admitted(args)",1).replace("logs = root/PREFIX/'pilot-parent'/admission.experiment_id","logs = root/PREFIX/'pilot-parent'/EXPERIMENT",1)
ck('root_eight_edit_full_inverse',x==b)
p=(C/'preflight01.py').read_text();ck('preflight_single_edit_inverse',p.replace('WritableUnion(budget,ROOT,experiment=admission.experiment_id)','WritableUnion(budget,ROOT)',1)==(B/'preflight01.py').read_text())
t=ast.parse(c);base=ast.parse(b)
ck('capture_AST_unchanged',ast.dump(next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='capture'))==ast.dump(next(n for n in base.body if isinstance(n,ast.FunctionDef) and n.name=='capture')))
class Strip(ast.NodeTransformer):
 def visit_ImportFrom(self,n):return None
def ex(nodes,ns):exec(compile(ast.fix_missing_locations(Strip().visit(ast.Module(nodes,type_ignores=[]))),'actual_metadata_seam','exec'),ns)
launch=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='launch_checked');prefix='research_artifacts/onchain-paper-replication-2026-09-24'
with tempfile.TemporaryDirectory(dir=H) as tmp:
 root=Path(tmp);(root/prefix/'pilot-parent').mkdir(parents=True)
 args=N(root=str(root),experiment='eth-paper-real-data-end-to-end-resource-20261009-22')
 events=[];ns=dict(Path=Path,PREFIX=prefix,_admitted=lambda a:(N(experiment_id='different'),{}),_command=lambda a,mode:['tiny-not-executed',mode],_immutable=lambda *a:events.append(('write',a)),capture=lambda *a:events.append(('capture',a)) or 'captured')
 ex([launch],ns)
 try:ns['launch_checked'](args,{'ready':'metadata'},H)
 except ValueError:checks.append('mismatch_refuses')
 else:raise AssertionError('mismatch accepted')
 ck('mismatch_before_immutable_and_capture',events==[])
 ns['_admitted']=lambda a:(N(experiment_id=args.experiment),{'resources':{}})
 ck('capture_return',ns['launch_checked'](args,{'ready':'metadata'},H)=='captured')
 ck('attempt_then_capture', [x[0] for x in events]==['write','capture'])
 capture=events[1][1];ck('capture_command_and_log_placement',capture[:3]==(['tiny-not-executed','launch'],root,root/prefix/'pilot-parent'/args.experiment))
final=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='final_storage')
# Only actual metadata assignments and identity predicate; no process/unit/filesystem query.
assign={n.targets[0].id:n for n in final.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)}
identity=next(n for n in final.body if isinstance(n,ast.If) and 'launch[\'supervisor_pid\']' in ast.unparse(n.test))
args=N(experiment='fresh-admitted',source='source',root='/metadata');io={'supervisor_pid':42};calls=[]
ns=dict(root=Path('/metadata'),PREFIX=prefix,args=args,io=io,launch={'supervisor_pid':42,'source_commit':'source','experiment':'fresh-admitted'},job={'resources':{'storage_budget':{'experiment':'fresh-admitted'}}},WritableUnion=lambda *a,**k:calls.append((a,k)) or N(check=lambda:'observed'))
ex([assign['base'],assign['paths'],identity,assign['observation']],ns)
ck('all_final_paths_selected',all(str(v).startswith('/metadata/'+prefix+'/runs/fresh-admitted/') for v in ns['paths'].values()))
ck('explicit_scan_identity',calls==[(({'experiment':'fresh-admitted'},Path('/metadata')),{'experiment':'fresh-admitted'})])
ns['launch']['experiment']='old'
try:ex([identity],ns)
except ValueError:checks.append('final_launch_identity_mismatch_refuses')
else:raise AssertionError('final mismatch accepted')
result={'decision':'accepted-source-only-not-fresh-entry-release','files':manifest['files'],'checks':checks,'reused_reviews':['storage identity3cb5b6f578f5d9467e8c6397bc5d5b726f3344deb1422562d76d9ed05f9ba696','job bindingcfd679f6c4a52193810c24b6a8e8cff008fbc513b692e63ca034d5f3c625586c'],'limitations':['Metadata-only AST doubles; no actual admission, Owner, launch, guard/unit query, subprocess or empirical input read.','Full inverse preserves existing capture/cleanup/unit/currentness logic; unchanged tests not rerun.','Fixed21 preflight gate/source/budget/allowance remains unchanged. Fresh metadata controls, source integration, registration/binding/release remain pending.','Generic RootIO assumes _admitted provides genuine validated identity. final_storage is terminal observation, not standalone authorization.']}
(H/'SOURCE_REVIEW01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'decision':result['decision'],'checks':len(checks),'sha256':hashlib.sha256((H/'SOURCE_REVIEW01.json').read_bytes()).hexdigest()}))
