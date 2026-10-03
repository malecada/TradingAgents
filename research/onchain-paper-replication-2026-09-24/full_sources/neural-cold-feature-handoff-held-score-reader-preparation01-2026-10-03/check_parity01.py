import ast,hashlib
from pathlib import Path
b=Path(__file__).parent
old=(b/'mcm_score_stream.py.before').read_text();new=(b/'mcm_score_stream.py').read_text()
new=new[:new.index('\n\ndef _completion_identity(stream):')]
new=new.replace('import stat\n','').replace('from weakref import WeakKeyDictionary\n\n_COMPLETED = WeakKeyDictionary()\n','')
new=new.replace('            directory_pins = _directory_identity(self)\n','').replace('            _directory_rejoin(self,directory_pins)\n','')
new=new.replace('        _COMPLETED[self] = (_completion_identity(self), raw, result, directory_pins)\n','')
assert new==old
assert ast.dump(ast.parse(new))==ast.dump(ast.parse(old))
print('PASS entire inverse source bytes/AST. No changed constructor, numerical loop, original finish/history/close instructions.')
for name in ('exact_members02.py','owned_io.py'):
 source=b.parent/'batch-output-exact-member-reader-candidate02-2026-10-03'/name
 assert (b/name).read_bytes()==source.read_bytes()
 print('PASS unchanged',name,hashlib.sha256(source.read_bytes()).hexdigest())
