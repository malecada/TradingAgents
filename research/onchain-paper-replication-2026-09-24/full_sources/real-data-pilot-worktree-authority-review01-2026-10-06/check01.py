import ast,hashlib,json,os,subprocess,sys,types
from pathlib import Path
H=Path(__file__).resolve().parent
M=H.parents[3]
C=H.parent/'real-data-pilot-worktree-authority-seam01-2026-10-06'
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((C/'MANIFEST01.json').read_bytes())
assert sha((C/'MANIFEST01.json').read_bytes())=='3e3a8c07cff455834804c074e8e08d399aa4f53009c6e7436c71893c927c7aa0'
for p,r in manifest['files'].items():
 b=(C/p).read_bytes();assert sha(b)==r['sha256'] and len(b)==r['bytes']
pins=json.loads((C/'SOURCE_PINS01.json').read_bytes())
for p,r in pins.items():
 b=(M/p).read_bytes();assert sha(b)==r['sha256'] and len(b)==r['bytes'],p
change=json.loads((C/'CHANGE01.json').read_bytes());text=(C/'real_pilot_import_caller.py').read_text()
assert sha(text.encode())==change['after_sha256']
for edit in reversed(change['literal_edits']):
 assert text.count(edit['after'])==1;text=text.replace(edit['after'],edit['before'])
assert sha(text.encode())==change['before_sha256']
sys.path.insert(0,str(M))
from tradingagents.research import admission

def extract(p,names,ns):
 nodes=[n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names]
 assert len(nodes)==len(names)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),ns)
job=types.ModuleType('tradingagents.research.onchain_replication.job');job.Path=Path;job.subprocess=subprocess
extract(M/'tradingagents/research/onchain_replication/job.py',{'workspace_binding'},job.__dict__)
sys.modules[job.__name__]=job

def require(v,m):
 if not v:raise ValueError(m)
ns=dict(__package__='tradingagents.research.onchain_replication',Path=Path,require=require,hashlib=hashlib,json=json,FILE_MAX=4*1024**2)
extract(C/'real_pilot_import_caller.py',{'_read','_source_authority_root'},ns)
check=ns['_source_authority_root'];results=[]
env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
env.update(GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1',GIT_TERMINAL_PROMPT='0')
# All actual Git mutations remain in this owned empty-fixture directory.
os.environ.update(env)
for k in list(os.environ):
 if k.startswith('GIT_') and k not in env:del os.environ[k]
area=H/'fixtures02';area.mkdir();repo=area/'repo';repo.mkdir();wt=area/'worktree'
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,env=env,stderr=subprocess.PIPE)
git(repo,'init','--quiet','--template=')
git(repo,'-c','user.name=Review Fixture','-c','user.email=review@example.invalid','commit','--quiet','--allow-empty','--no-gpg-sign','-m','Empty fixture')
git(repo,'worktree','add','--quiet','--detach',str(wt),'HEAD')
assert git(repo,'ls-tree','HEAD')==b''
layout=job.workspace_binding(wt)
def ad(root=wt,value=None):
 raw=json.dumps(layout if value is None else value,sort_keys=True).encode();p=root/'layout.json';p.write_bytes(raw)
 return types.SimpleNamespace(root=root,inputs={'execution_workspace':{'path':p.name,'sha256':sha(raw)}})
def refused(name,f):
 try:f()
 except (ValueError,OSError):results.append(name);return
 raise AssertionError(name+' accepted')
assert check(types.SimpleNamespace(root=repo,inputs={}))
assert check(ad());results+=['legacy directory accepted','real linked worktree accepted']
for field in ('root','ledger','artifacts','git_common'):
 refused('wrong '+field,lambda field=field:check(ad(value=layout|{field:str(repo)})))
a=ad();(wt/'layout.json').write_bytes(b'{}');refused('changed authenticated body',lambda:check(a))
refused('missing registered role',lambda:check(types.SimpleNamespace(root=wt,inputs={})))
alias=area/'alias';alias.symlink_to(wt,target_is_directory=True);refused('symlink root alias',lambda:check(ad(root=alias)))
sub=wt/'sub';sub.mkdir();(sub/'.git').write_bytes((wt/'.git').read_bytes());refused('copied marker with original registered mapping',lambda:check(ad(root=sub)));assert check(ad(root=sub,value=job.workspace_binding(sub)));results.append('explicitly rebound copied marker accepted: backlink identity not claimed')
redirect=area/'redirect';redirect.mkdir();(redirect/'.git').symlink_to(wt/'.git');refused('symlink file marker',lambda:check(ad(root=redirect)))
a=ad();common_marker=repo/'.git/worktrees/worktree/commondir';old=common_marker.read_bytes();common_marker.write_text('../../../outside\n');refused('redirected common directory after binding',lambda:check(a));common_marker.write_bytes(old)
assert not {'numpy','torch','networkx','scipy'} & sys.modules.keys()
record={'decision':'passed','checks':results,'candidate_sha256':change['after_sha256'],'baseline_sha256':change['before_sha256'],'manifest_members':len(manifest['files']),'dependency_pins':pins,'exact_inverse':True,'empty_git_tree':True,'scope':'Only extracted topology/read predicates and actual empty Git fixtures; no genuine Admission/Run/Binding/Owner or runtime activation.'}
(H/'CHECK01.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'decision':'passed','checks':len(results),'manifest_members':len(manifest['files']),'dependency_pins':len(pins)}))
