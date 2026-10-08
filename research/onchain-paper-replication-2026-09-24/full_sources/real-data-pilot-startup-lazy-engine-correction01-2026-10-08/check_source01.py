"""Exact AST/import-only delta and reversible byte reconstruction."""
import ast,hashlib,json,subprocess,tempfile
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[3]
files={'tradingagents/research/onchain_replication/matching_pair.py':'matching_pair.py','tradingagents/research/onchain_replication/compact_matcher.py':'compact_matcher.py','tests/research/onchain_replication/test_matching_pair_checkpoints.py':'test_matching_pair_checkpoints.py','tests/research/onchain_replication/test_compact_matcher.py':'test_compact_matcher.py'}
class Normalize(ast.NodeTransformer):
 def visit_ImportFrom(self,n):
  if any(a.name=='matching_checkpoint' and a.asname=='engine' for a in n.names):
   assert len(n.names)==1;return None
  return n
 def visit_Assign(self,n):
  if len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='engine' and isinstance(n.value,ast.Attribute) and isinstance(n.value.value,ast.Name) and n.value.value.id=='pair' and n.value.attr=='engine':return None
  return self.generic_visit(n)
 def visit_Attribute(self,n):
  if n.attr=='engine' and isinstance(n.value,ast.Name) and n.value.id in ('m','pair'):return ast.copy_location(ast.Name(id='engine',ctx=n.ctx),n)
  return self.generic_visit(n)
rows=[]
for path,name in files.items():
 a=(H/('baseline_'+name)).read_bytes();b=(H/name).read_bytes()
 assert (R/path).read_bytes()==a,'live source differs: '+path
 assert ast.dump(Normalize().visit(ast.parse(a)))==ast.dump(Normalize().visit(ast.parse(b))),name
 compile(b,str(H/name),'exec')
 rows.append({'target':path,'candidate':name,'before_sha256':hashlib.sha256(a).hexdigest(),'after_sha256':hashlib.sha256(b).hexdigest(),'normalized_ast_equal':True,'live_unchanged':True})
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp)
 for path,name in files.items():
  p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((H/('baseline_'+name)).read_bytes())
 for patch,prefix in [('FORWARD01.patch',''),('INVERSE01.patch','baseline_')]:
  result=subprocess.run(['patch','--batch','-p1','-i',str(H/patch)],cwd=root,capture_output=True,text=True,timeout=10)
  assert result.returncode==0,result.stderr
  for path,name in files.items():assert (root/path).read_bytes()==(H/(prefix+name)).read_bytes()
print(json.dumps({'files':rows,'forward_inverse_exact':True},indent=2))
