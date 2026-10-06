"""Actual native helper AST plus stdlib owned-IO fatal selection, no native calls."""
from pathlib import Path
import ast,json,types,os
H=Path(__file__).resolve().parent;F=H.parent.parent;ROOT=F.parents[2];C=F/'real-data-pilot-residual-enforcement-candidate01-2026-10-06'
io=types.ModuleType('owned_io');p=ROOT/'tradingagents/research/onchain_replication/owned_io.py';exec(compile(p.read_bytes(),str(p),'exec'),vars(io))
tree=ast.parse((C/'resources.py').read_text());names={'_native_select','_native_reason','_native_finalize','_native_write'}
ns={'json':json,'os':os};exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'actual-resources-helpers','exec'),ns)
primary=MemoryError('original primary fatal');events=[]
class NoBirth:
 def _opened(self,*a):raise AssertionError('oversize must refuse before birth')
def oversize():
 events.append('oversize');ns['_native_write'](Path('not-created'),{'reason':'long value'},NoBirth(),max_bytes=1)
def cleanup():events.append('cleanup')
def sync():events.append('sync')
state={};selected,failed=ns['_native_finalize'](state,primary,[('receipt',oversize),('cleanup',cleanup),('sync',sync)],io)
assert selected is primary and failed and events==['oversize','cleanup','sync'] and state['phase']=='failed'
state={};selected,failed=ns['_native_finalize'](state,None,[('receipt',oversize),('cleanup',cleanup)],io)
assert isinstance(selected,ValueError) and failed and state['phase']=='failed'
r={'status':'PASS_FOCUSED_NATIVE_FAILURE_COMPOSITION','original_fatal_identity_preserved':True,'oversize_before_birth':True,'cleanup_and_sync_attempted_after_receipt_failure':True,'new_oversize_failure_remains_failed':True,'native_or_numerical_execution':False}
(H/'FAILURE_CHECK01.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');print(json.dumps(r))
