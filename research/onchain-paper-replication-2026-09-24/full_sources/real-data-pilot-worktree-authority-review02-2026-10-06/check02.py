import ast,copy,hashlib,json,os,subprocess,sys,types
from pathlib import Path
H=Path(__file__).resolve().parent;M=H.parents[3];F=H.parent
C=F/'real-data-pilot-worktree-authority-seam02-2026-10-06';O=F/'real-data-pilot-worktree-authority-seam01-2026-10-06'
sha=lambda b:hashlib.sha256(b).hexdigest()
change=json.loads((C/'CHANGE02.json').read_bytes());text=(C/'real_pilot_import_caller.py').read_text()
assert sha(text.encode())==change['after_sha256'];assert text.count(change['after'])==1
assert text.replace(change['after'],change['before'])==(O/'real_pilot_import_caller.py').read_text()
sys.path.insert(0,str(M))
from tradingagents.research import admission
from tradingagents.research.onchain_replication import owned_io

def require(v,m):
 if not v:raise ValueError(m)
def extracted(path,names,ns):
 nodes=[n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names]
 assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns);return nodes
job=types.ModuleType('tradingagents.research.onchain_replication.job');job.Path=Path;job.subprocess=subprocess
extracted(M/'tradingagents/research/onchain_replication/job.py',{'workspace_binding'},job.__dict__);sys.modules[job.__name__]=job
base=dict(__package__='tradingagents.research.onchain_replication',Path=Path,require=require,hashlib=hashlib,json=json,FILE_MAX=4*1024**2)
new=dict(base);nodes=extracted(C/'real_pilot_import_caller.py',{'_read','_source_authority_root'},new)
old=dict(base);extracted(O/'real_pilot_import_caller.py',{'_read','_source_authority_root'},old)
# Actual prior witness metadata is read unchanged; no old fixture mutations.
wt=F/'real-data-pilot-worktree-authority-review01-2026-10-06/fixtures02/worktree'
def obj(root):
 p=root/'layout.json';return types.SimpleNamespace(root=root,inputs={'execution_workspace':{'path':p.name,'sha256':sha(p.read_bytes())}})
witness=obj(wt/'sub');assert old['_source_authority_root'](witness)
results=[]
def refuses(label,call):
 try:call()
 except (ValueError,OSError):results.append(label);return
 raise AssertionError(label)
refuses('original copied-marker RED becomes GREEN refusal',lambda:new['_source_authority_root'](witness))
assert new['_source_authority_root'](obj(wt));results.append('original official linked fixture accepted')
# Execute only exact added backlink statements against Main: does not assert a registered role or Admission.
node=copy.deepcopy(next(n for n in nodes if n.name=='_source_authority_root'))
start=next(i for i,n in enumerate(node.body) if isinstance(n,ast.Import) and [a.name for a in n.names]==['os','stat'])
node.body=node.body[start:];node.name='backlink_only'
ns=dict(base,_git=admission._git,marker=M/'.git')
exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(C/'real_pilot_import_caller.py'),'exec'),ns)
assert ns['backlink_only'](types.SimpleNamespace(root=M));results.append('actual Main backlink-only read accepted')
# Fresh isolated metadata/Git fixtures test only new backlink predicates.
area=H/'fixtures';area.mkdir();repo=area/'repo';repo.mkdir();tree=area/'tree'
env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};env.update(GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1',GIT_TERMINAL_PROMPT='0')
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,env=env,stderr=subprocess.PIPE)
git(repo,'init','--quiet','--template=');git(repo,'-c','user.name=Review','-c','user.email=review@example.invalid','commit','--quiet','--allow-empty','--no-gpg-sign','-m','Empty review fixture');git(repo,'worktree','add','--quiet','--detach',str(tree),'HEAD')
p=tree/'layout.json';p.write_text(json.dumps(job.workspace_binding(tree)));ad=obj(tree)
admin=Path(git(tree,'rev-parse','--absolute-git-dir').decode().strip());b=admin/'gitdir';raw=b.read_bytes()
assert new['_source_authority_root'](ad)
b.write_bytes(b'x'*8193);refuses('oversized backlink refused',lambda:new['_source_authority_root'](ad));b.write_bytes(raw)
b.write_bytes(raw+b'\n');refuses('multiline backlink refused',lambda:new['_source_authority_root'](ad));b.write_bytes(raw)
original=admin/'gitdir-original';b.rename(original);b.symlink_to(original)
refuses('symlink backlink refused',lambda:new['_source_authority_root'](ad));b.unlink();original.rename(b)
b.write_text(os.path.relpath(tree/'.git',admin)+'\n');assert new['_source_authority_root'](ad);results.append('relative backlink resolved against actual admin');b.write_bytes(raw)
assert not {'numpy','torch','networkx','scipy'} & sys.modules.keys()
record={'decision':'passed','checks':results,'candidate_sha256':change['after_sha256'],'exact_predecessor_inverse':True,'owned_io_sha256':sha(Path(owned_io.__file__).read_bytes()),'main_test_scope':'Exact backlink fragment only; no execution_workspace registration or real Admission/Owner/Run was constructed.','original_witness_retained':True}
(H/'CHECK02.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'decision':'passed','checks':len(results),'candidate_sha256':change['after_sha256']}))
