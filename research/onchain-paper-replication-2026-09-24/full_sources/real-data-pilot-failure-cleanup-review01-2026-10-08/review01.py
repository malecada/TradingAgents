import ast, difflib, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
PACKAGE=HERE.parent/'real-data-pilot-failure-cleanup-investigation01-2026-10-08'
manifest=json.loads((PACKAGE/'MANIFEST01.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
for name,pin in manifest['files'].items():
    raw=(PACKAGE/name).read_bytes()
    assert len(raw)==pin['bytes'] and sha(raw)==pin['sha256'],name
old=(ROOT/manifest['source']['path']).read_bytes()
new=(ROOT/manifest['candidate']['path']).read_bytes()
assert sha(old)==manifest['source']['sha256']
assert sha(new)==manifest['candidate']['sha256']
a,b=old.decode().splitlines(True),new.decode().splitlines(True)
assert ''.join(difflib.unified_diff(a,b,fromfile='a/compact_mcm.py',tofile='b/compact_mcm.py'))==(PACKAGE/'FORWARD01.patch').read_text()
assert ''.join(difflib.unified_diff(b,a,fromfile='a/compact_mcm.py',tofile='b/compact_mcm.py'))==(PACKAGE/'INVERSE01.patch').read_text()
x,y=ast.parse(old),ast.parse(new)
f=lambda t:next(n for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name=='compute')
original,candidate=f(x),f(y)
assert len(candidate.body)==2 and isinstance(candidate.body[0],ast.Nonlocal)
t=candidate.body[1]
assert isinstance(t,ast.Try) and not t.finalbody and not t.orelse and len(t.handlers)==1
expected=ast.parse("try:\n pass\nexcept BaseException as primary:\n if stream is not None and not stream.closed:\n  io._close_after_failure(stream.close,primary)\n raise").body[0].handlers[0]
assert ast.dump(t.handlers[0])==ast.dump(expected)
candidate.body=candidate.body[:1]+t.body
assert ast.dump(x)==ast.dump(y)
compile(new,'candidate/compact_mcm.py','exec')
result={'decision':'ACCEPT narrow source correction','source_sha256':sha(old),'candidate_sha256':sha(new),'author_manifest_sha256':sha((PACKAGE/'MANIFEST01.json').read_bytes()),'checks':['all retained manifest bytes/hashes match','forward and inverse patches exactly regenerated from full source bytes','AST normalization removes only the precisely asserted exception wrapper; entire original module identical','candidate compiles without executing imports'],'retained_functional_results':'CHECKS01.json independently inspected against check01.py; reused, not rerun','scope':'stdlib-only source/hash/AST verification; no native process, numerical import, data or authority execution'}
(HERE/'SOURCE_REVIEW01.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
