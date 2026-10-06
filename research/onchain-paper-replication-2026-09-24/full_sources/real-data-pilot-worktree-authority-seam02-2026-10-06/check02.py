"""Focused copied-marker witness; empty disposable Git fixture only."""
import ast,hashlib,json,os,subprocess,sys,types
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT))
from tradingagents.research import admission

def require(value,message):
    if not value:raise ValueError(message)
def extract(path,names,ns):
    tree=ast.parse(path.read_text());nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in names];assert len(nodes)==len(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
job=types.ModuleType('tradingagents.research.onchain_replication.job');job.Path=Path;job.subprocess=subprocess
extract(ROOT/'tradingagents/research/onchain_replication/job.py',['workspace_binding'],job.__dict__);sys.modules[job.__name__]=job
ns={'__package__':'tradingagents.research.onchain_replication','Path':Path,'require':require,'hashlib':hashlib,'json':json,'FILE_MAX':4*1024**2}
extract(HERE/'real_pilot_import_caller.py',['_read','_source_authority_root'],ns)
area=HERE/'empty-git-fixture03';area.mkdir();repo=area/'repo';repo.mkdir();worktree=area/'worktree'
env=dict(os.environ,GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1',GIT_TERMINAL_PROMPT='0')
def git(*args):return subprocess.check_output(['git',*args],cwd=repo,env=env,stderr=subprocess.STDOUT,text=True)
git('init','--quiet','--template=');git('-c','user.name=Offline Fixture','-c','user.email=fixture@example.invalid','commit','--quiet','--allow-empty','--no-gpg-sign','-m','Empty topology fixture');git('worktree','add','--quiet','--detach',str(worktree),'HEAD');assert git('ls-tree','HEAD').strip()==''
def ad(root):
    value=job.workspace_binding(root);raw=json.dumps(value,sort_keys=True).encode();(root/'layout.json').write_bytes(raw)
    return types.SimpleNamespace(root=root,inputs={'execution_workspace':{'path':'layout.json','sha256':hashlib.sha256(raw).hexdigest()}})
check=ns['_source_authority_root'];assert check(ad(worktree))
copied=worktree/'sub';copied.mkdir();(copied/'.git').write_bytes((worktree/'.git').read_bytes());fake=ad(copied)
assert Path(admission._git(copied,'rev-parse','--show-toplevel').decode().strip())==copied
try:check(fake)
except ValueError as error:assert str(error)=='Git administration backlink differs from admitted worktree';refusal=str(error)
else:raise AssertionError('copied marker accepted')
# Verify the existing reader refuses a symlink to otherwise correct backlink bytes.
admin=Path(admission._git(worktree,'rev-parse','--absolute-git-dir').decode().strip());link=admin/'gitdir';saved=admin/'original-gitdir'
original=link.read_bytes()
try:
    link.write_text(os.path.relpath(worktree/'.git',admin)+'\n')
    try:check(ad(worktree))
    except ValueError as error:assert str(error)=='absolute worktree backlink required by pinned Git runtime'
    else:raise AssertionError('unsupported relative backlink accepted')
finally:link.write_bytes(original)
link.rename(saved);link.symlink_to(saved)
try:
    try:check(ad(worktree))
    except OSError:pass
    else:raise AssertionError('symlink backlink accepted')
finally:link.unlink();saved.rename(link)
change=json.loads((HERE/'CHANGE02.json').read_bytes());source=(HERE/'real_pilot_import_caller.py').read_text();assert source.count(change['after'])==1
assert hashlib.sha256(source.replace(change['after'],change['before']).encode()).hexdigest()==change['before_sha256']
assert 'numpy' not in sys.modules and 'torch' not in sys.modules
record={'official_worktree':'passed','copied_marker_matching_root_body':'refused','reason':refusal,'symlink_backlink':'refused','unsupported_relative_backlink':'refused','exact_inverse':'passed','scope':'empty topology fixture only; no Admission or ResearchRun authority instantiated'}
(HERE/'ACTUAL_CHECK02.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
