"""Source-extracted fresh() ambiguity witness, metadata only; no child process."""
import ast,json,types,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[3];p=R/'tradingagents/research/onchain_replication/resources.py';tree=ast.parse(p.read_text());child=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_child_legacy');fn=next(x for x in child.body if isinstance(x,ast.FunctionDef) and x.name=='fresh');receipt=H/'tiny';receipt.mkdir();ns={'receipt':receipt,'json':json,'time':types.SimpleNamespace(monotonic=lambda:100.),'lease_seconds':15.};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(p),'exec'),ns)
results={}
for label,body in [('valid',{'monotonic_seconds':99.}),('stale',{'monotonic_seconds':84.}),('future',{'monotonic_seconds':101.}),('missing_key',{})]:
 (receipt/'live.json').write_text(json.dumps(body));results[label]=ns['fresh']()
(receipt/'live.json').write_text('{');results['malformed_json']=ns['fresh']();(receipt/'live.json').unlink();results['absent_file']=ns['fresh']()
assert results=={'valid':True,'stale':False,'future':False,'missing_key':False,'malformed_json':False,'absent_file':False}
(H/'CHECK01.json').write_text(json.dumps({'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'results':results,'meaning':'Distinct causes collapse to identical False; does not identify actual May30 cause','native_or_workload_executed':False},indent=2)+'\n');print(json.dumps(results))
