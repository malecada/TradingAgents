"""Exact source preservation checks; no claim or Git execution."""
import ast,copy,difflib,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];C=P.parent/'pilot-admission-claims-parallel-candidate-2026-10-12'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((C/'SOURCE_MANIFEST01.json').read_text());assert sha(C/'SOURCE_MANIFEST01.json')=='347715cffbb7d35be6673bfb361c1c9b30e8b2c486b5b5eb89d39accf2784ef3'
for ref in [m['original_admission'],m['unchanged_verify'],m['unchanged_lifecycle']]+m['files']:
 p=R/ref['path'];assert p.is_file() and not p.is_symlink() and sha(p)==ref['sha256'] and p.stat().st_size==ref['bytes']
a=(R/m['original_admission']['path']).read_text();b=(C/'admission.py').read_text();ta=ast.parse(a);tb=ast.parse(b)
afunc={n.name:n for n in ta.body if isinstance(n,ast.FunctionDef)};bfunc={n.name:n for n in tb.body if isinstance(n,ast.FunctionDef)}
for name in afunc:
 if name not in ('claims','admit'):assert ast.dump(afunc[name])==ast.dump(bfunc[name]),name
oldloop=next(n for n in afunc['claims'].body if isinstance(n,ast.For));newloop=next(n for n in bfunc['claims'].body if isinstance(n,ast.For));assert ast.dump(oldloop)==ast.dump(newloop)
proof=bfunc['_verify_claim_child'];assert [ast.dump(n) for n in oldloop.body[1:-1]]==[ast.dump(n) for n in proof.body[:-1]];assert ast.dump(proof.body[-1])==ast.dump(ast.Return(ast.Name('claim',ast.Load())))
# Remove only the selector assignment and restore the old claims invocation.
admit=copy.deepcopy(bfunc['admit']);admit.body=[n for n in admit.body if not (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='claim_workers' for t in n.targets))]
oldprior=next(n for n in afunc['admit'].body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prior' for t in n.targets))
for i,n in enumerate(admit.body):
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prior' for t in n.targets):admit.body[i]=oldprior
assert ast.dump(admit)==ast.dump(afunc['admit'])
for name,x,y in [('LITERAL_PATCH01.diff',a,b),('LITERAL_INVERSE01.diff',b,a)]:assert (C/name).read_text().splitlines(True)[2:]==list(difflib.unified_diff(x.splitlines(True),y.splitlines(True)))[2:]
parallel=ast.get_source_segment(b,bfunc['_parallel_claims'])
assert "ThreadPoolExecutor(max_workers=2" in parallel and "len(pending) < 2" in parallel
assert "done = {future for future in pending if future.done()}" in parallel and "if errors:" in parallel
assert "return [values[index] for index in range(len(children))]" in parallel
assert "executor.shutdown(wait=True)" in parallel and "raise cleanup_error" in parallel and "except BaseException as probe_error" in parallel
print(json.dumps({'status':'STATIC_SOURCE_PASS','manifest_sha256':sha(C/'SOURCE_MANIFEST01.json'),'admission_sha256':sha(C/'admission.py'),'full_per_child_operation_AST_identical':True,'literal_default_loop_identical':True,'admit_inverse_AST_identical':True,'all_original_other_functions_unchanged':True,'verify_lifecycle_hashes_unchanged':True,'literal_patch_inverse_exact':True,'executor_inflight_limit':2,'no_runtime_claim_git_execution':True},indent=2))
