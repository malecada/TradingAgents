from pathlib import Path
import ast,json,hashlib,difflib,types
R=Path(__file__).resolve().parents[4];F=R/'research/onchain-paper-replication-2026-09-24/full_sources';C=F/'pilot-edge-geometry-layout-candidate-2026-10-12';I=F/'pilot-post-cache-hotpath-integration-2026-10-12'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((C/'SOURCE_MANIFEST02.json').read_bytes());assert h(C/'SOURCE_MANIFEST02.json')=='0f1d6f91279bb0399eddf5b5ef9e3a70813077fdca65313a38abb742f87622bf'
for row in m['files']+[m['reused_harness']]:assert h(R/row['path'])==row['sha256']
a=(C/'BASELINE_matching_annealing.py').read_text();b=(C/'matching_annealing.py').read_text()
for x,y,name in ((a,b,'CANDIDATE01.diff'),(b,a,'INVERSE01.diff')):
 assert (C/name).read_text().splitlines(True)[2:]==list(difflib.unified_diff(x.splitlines(True),y.splitlines(True)))[2:]
t=ast.parse(b);branch=next(n for n in ast.walk(t) if isinstance(n,ast.If) and 'not a.edge_index.flags.writeable' in ast.unparse(n.test));signature=ast.dump(branch)
class Restore(ast.NodeTransformer):
 def visit_If(self,n):return n.orelse if ast.dump(n)==signature else self.generic_visit(n)
assert ast.dump(Restore().visit(ast.parse(b)))==ast.dump(ast.parse(a))
code=compile(ast.Module(body=[branch],type_ignores=[]),'actual-four-row-branch','exec')
class Arr:
 def __init__(self,rows=None,index=None,fail=None):self.rows=rows;self.index=index;self.fail=fail;self.flags=types.SimpleNamespace(writeable=False);self.calls=[]
 def __getitem__(self,key):
  row,idx=key;self.calls.append(row)
  if self.fail is not None and row==1:raise self.fail
  if isinstance(row,slice):return tuple([r[i] for i in idx.index] for r in self.rows)
  return [self.rows[row][i] for i in idx.index]
class Sub(Arr):pass
for mode in ('duplicate_negative_order','left_index_subclass','right_edge_subclass','row_allocation_fatal'):
 fatal=MemoryError('synthetic gather allocation');left=(Sub if mode=='left_index_subclass' else Arr)(index=[2,-1,0,2]);right=Arr(index=[1,0,1,-1])
 aa=Arr(rows=[[7,8,9],[9,7,8]],fail=fatal if mode=='row_allocation_fatal' else None);bb=(Sub if mode=='right_edge_subclass' else Arr)(rows=[[3,4,5],[5,3,4]])
 ns={'a':types.SimpleNamespace(edge_index=aa),'b':types.SimpleNamespace(edge_index=bb),'left':left,'right':right,'np':types.SimpleNamespace(ndarray=Arr),'state':{'Q':'original','cursor':19},'used':4}
 try:exec(code,ns)
 except MemoryError as caught:
  assert mode=='row_allocation_fatal' and caught is fatal and ns['state']=={'Q':'original','cursor':19} and ns['used']==4
 else:
  assert [ns[k] for k in ('u','v','i','j')]==[[9,9,7,9],[8,8,9,8],[4,3,4,5],[3,5,3,4]]
  fallback=mode in ('left_index_subclass','right_edge_subclass')
  assert len(aa.calls)==len(bb.calls)==(1 if fallback else 2)
pin=json.loads((I/'SOURCE_PIN_PATCH01.json').read_bytes());assert h(I/'SOURCE_PIN_PATCH01.json')=='694654fbf464f73edc164472ed1576991a8b0a9a490561d96f106f1e53ed345a'
old=(I/'BASELINE_batched_numeric_reuse.py').read_text();new=(I/'batched_numeric_reuse.py').read_text()
assert h(I/'BASELINE_batched_numeric_reuse.py')==pin['baseline_sha256'] and h(I/'batched_numeric_reuse.py')==pin['candidate_sha256']
assert old.count(pin['old_pin'])==new.count(pin['new_pin'])==1
assert old.replace(pin['old_pin'],pin['new_pin'])==new and new.replace(pin['new_pin'],pin['old_pin'])==old
assert pin['new_pin']==h(C/'matching_annealing.py')
hook=(C/'benchmark01.py').read_text();compile(hook,'geometry-hook','exec')
assert "h.solve(a,b,c,2,budget=budget)" in hook and 'budget=1000000' in hook
assert "struct.pack('!d',a.score)!=struct.pack('!d',b.score)" in hook and 'old[1]!=new[1]' in hook
assert 'finally:h.ann._advance_checked=baseline' in hook
print(json.dumps({'result':'PASS','exact_manifest_literal_AST_inverse':True,'independent_controls':['ordered duplicate and negative gathers','index subclass original fallback','edge subclass original fallback','gather allocation failure leaves Q/cursor/operation credit untouched'],'single_source_pin_inverse':True,'root_hook_scope':'four original48-temperature v2/v2 solver pairs plus optional focused1024 checkpoint; no actual Owner or live source mutation','numerical_imports':False},indent=2))
