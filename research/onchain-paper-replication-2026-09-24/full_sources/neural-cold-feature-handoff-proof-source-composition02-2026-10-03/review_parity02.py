import ast,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def tree(p):return ast.parse(p.read_bytes())
def producer(t):return next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_produce_locked')
def handler(t):return next(n for n in producer(t).body if isinstance(n,ast.Try)).handlers
selected=tree(HERE/'source-bodies/tradingagents/research/onchain_replication/compact_mcm.py')
metadata=tree(HERE.parent/'imported-source-metadata-correction02-2026-10-03/compact_mcm.py')
cleanup=tree(HERE.parent/'original-import-native-refusal-candidate03-2026-10-03/compact_mcm.py')
assert ast.dump(ast.Module(body=handler(selected),type_ignores=[]))==ast.dump(ast.Module(body=handler(cleanup),type_ignores=[]))
next(n for n in producer(selected).body if isinstance(n,ast.Try)).handlers=handler(metadata)
assert ast.dump(selected)==ast.dump(metadata)
assert 'resource_refusal' not in (HERE/'source-bodies/tradingagents/research/onchain_replication/compact_mcm.py').read_text()
deps=json.loads((HERE/'DEPENDENCY_READBACK02.json').read_bytes())['dependencies']
for r in deps:
 b=(ROOT/r['path']).read_bytes();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
print(json.dumps({'status':'passed-source-only','whole_module_restored_parity':True,'cleanup_handler_parity':True,'resource_refusal_hooks':False,'dependency_body_pins':len(deps)}))
