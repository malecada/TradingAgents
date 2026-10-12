"""Actual36 metadata-only corrected reconstruction; never writes an observer."""
import ast,builtins,hashlib,json
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2]
source=F/'pilot38-observer-ledger-correction-2026-10-12/job.py'
digest=lambda b:hashlib.sha256(b).hexdigest()
file_hash=lambda p:digest(p.read_bytes())
ns={'Path':Path,'json':json,'digest':digest,'file_hash':file_hash}
tree=ast.parse((R/'tradingagents/research/admission.py').read_text())
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='local_path')
exec(compile(ast.Module(body=[node],type_ignores=[]),'actual local_path AST','exec'),ns)
def imports(name,globals=None,locals=None,fromlist=(),level=0):
 if name=='admission' and level==2:return SimpleNamespace(local_path=ns['local_path'])
 return builtins.__import__(name,globals,locals,fromlist,level)
ns['__builtins__']={**vars(builtins),'__import__':imports}
tree=ast.parse(source.read_text())
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_terminal','_resource_pilot_rows')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),ns)
run=R/'research_runs/eth-paper-real-data-end-to-end-resource-20261011-36'
native=R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/run.name
paths=[run/'claim.json',run/'failed.json',run/'outputs/cell-ledger.json',native/'postmortem-cells.json',native/'observer.json']
before={str(p.relative_to(R)):file_hash(p) for p in paths}
claim=json.loads((run/'claim.json').read_bytes())
rows=ns['_resource_pilot_rows'](R,claim,file_hash(run/'claim.json'))
assert list(rows.values())==json.loads((run/'outputs/cell-ledger.json').read_bytes())
assert list(rows.values())[0]['status']=='failed'
assert json.loads((native/'postmortem-cells.json').read_bytes())[0]['status']=='unavailable'
assert before=={str(p.relative_to(R)):file_hash(p) for p in paths}
(P/'OBSERVER_CHECK01.json').write_text(json.dumps({'status':'PASS_METADATA_ONLY_NO_OBSERVER_WRITE','source_sha256':file_hash(source),'reconstructed':rows,'original_postmortem_preserved':'unavailable','original_hashes_before_and_after':before},indent=2)+'\n')
print('PASS: authenticated original36 FAILED row recovered; original unavailable postmortem unchanged')
