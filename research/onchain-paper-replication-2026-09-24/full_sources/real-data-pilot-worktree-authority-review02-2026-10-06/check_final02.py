import ast,hashlib,json,os,sys,types
from pathlib import Path
H=Path(__file__).resolve().parent;M=H.parents[3];C=H.parent/'real-data-pilot-worktree-authority-seam02-2026-10-06'
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((C/'MANIFEST02.json').read_bytes());assert sha((C/'MANIFEST02.json').read_bytes())=='87bfcc2b946d452fde11a94b076b951175edbf09426ad48939521a4b8e1cc808'
for p,r in manifest['files'].items():
 b=(C/p).read_bytes();assert sha(b)==r['sha256'] and len(b)==r['bytes']
for p,r in json.loads((C/'SOURCE_PINS02.json').read_bytes()).items():assert sha((M/p).read_bytes())==r['sha256']
text=(C/'real_pilot_import_caller.py').read_text();assert sha(text.encode())=='0b5f11bdf09750f2c6d0d2fd7b330a74eb13c7b78a35cb50c6cf975ae4f97266'
# Exact final predicate-only inverse to independently tested intermediate e77021cc.
old="    require((admin / target).resolve(strict=True) == marker,"
new="    require(target.is_absolute(), 'absolute worktree backlink required by pinned Git runtime')\n    require(target == marker and target.resolve(strict=True) == marker,"
assert text.count(new)==1;assert sha(text.replace(new,old).encode())=='e77021cc763e76a7db9c470213211512ded049f941ee1bad960f8adf97521657'
sys.path.insert(0,str(M));from tradingagents.research import admission

def require(v,m):
 if not v:raise ValueError(m)
node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='_source_authority_root')
i=next(i for i,n in enumerate(node.body) if isinstance(n,ast.Import) and [a.name for a in n.names]==['os','stat']);node.body=node.body[i:]
ns=dict(__package__='tradingagents.research.onchain_replication',Path=Path,require=require,_git=admission._git,marker=M/'.git')
exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(C/'real_pilot_import_caller.py'),'exec'),ns)
check=ns['_source_authority_root'];assert check(types.SimpleNamespace(root=M))
root=H/'fixtures/tree';b=H/'fixtures/repo/.git/worktrees/tree/gitdir';raw=b.read_bytes();ns['marker']=root/'.git';assert check(types.SimpleNamespace(root=root))
b.write_text(os.path.relpath(root/'.git',b.parent)+'\n')
try:
 try:check(types.SimpleNamespace(root=root))
 except ValueError as e:assert 'absolute worktree backlink' in str(e)
 else:raise AssertionError('relative accepted')
finally:b.write_bytes(raw)
# The original copied marker points to official admin; its backlink must refuse.
sub=H.parent/'real-data-pilot-worktree-authority-review01-2026-10-06/fixtures02/worktree/sub';ns['marker']=sub/'.git'
try:check(types.SimpleNamespace(root=sub))
except ValueError as e:assert 'backlink differs' in str(e)
else:raise AssertionError('copied marker accepted')
assert not {'numpy','torch','scipy','networkx'} & sys.modules.keys()
r={'decision':'passed','manifest_sha256':sha((C/'MANIFEST02.json').read_bytes()),'manifest_members':len(manifest['files']),'source_sha256':sha(text.encode()),'predicate_inverse_to_tested_e77021cc':True,'checks':['actual Main absolute backlink fragment','official local absolute backlink','relative backlink refusal','original copied marker backlink refusal'],'scope':'Topology fragment only, no registered Admission/Run/Owner.'}
(H/'FINAL_CHECK02.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
