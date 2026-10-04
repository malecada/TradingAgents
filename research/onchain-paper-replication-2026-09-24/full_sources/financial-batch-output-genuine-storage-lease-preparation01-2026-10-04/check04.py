import ast,difflib,hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import storage_lease01 as L
old=(H/'storage_lease01.draft02.py').read_text();new=(H/'storage_lease01.py').read_text()
a="owner=target.owner\n        require(type(target) is module(PKG+'imported_mcm_identity').Target and type(owner)"
b="require(type(target) is module(PKG+'imported_mcm_identity').Target,'actual original Target before attribute access')\n        owner=target.owner\n        require(type(owner)"
assert old.count(a)==1 and new.count(b)==1 and new.replace(b,a)==old
assert ast.dump(ast.parse(new.replace(b,a)),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False)
# No fake Target constructed: exact wrong-type branch uses a real built-in object;
# genuine module availability is itself required and stays absent in this harness.
try:L.GenuineLease(object(),object())
except ValueError as e:assert 'genuine loaded module' in str(e)
else:raise AssertionError('unavailable context accepted')
# Test independently extracted pure ordering guard, not simulated authority.
node=next(n for n in ast.walk(ast.parse(new)) if isinstance(n,ast.FunctionDef) and n.name=='_set')
text=ast.unparse(node);assert text.index('type(target)')<text.index('owner = target.owner')
(H/'DRAFT02_FINAL.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='storage_lease01.draft02.py',tofile='storage_lease01.py')))
old1=(H/'storage_lease01.draft01.py').read_text();(H/'DRAFT01_02.patch').write_text(''.join(difflib.unified_diff(old1.splitlines(True),old.splitlines(True),fromfile='storage_lease01.draft01.py',tofile='storage_lease01.draft02.py')))
result={'checks':5,'full_byte_inverse':True,'full_AST_inverse':True,'absent_real_modules_refused':True,'before_attribute_type_guard':True,'no_genuine_handles_constructed':True,'source_sha256':hashlib.sha256(new.encode()).hexdigest()}
(H/'CHECKS04.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result))
