from pathlib import Path
import hashlib,sys,types,importlib,tempfile,json
D=Path(__file__).resolve().parent
P=D.parent/'real-data-pilot-imported-authority-lease01-2026-10-06/candidate/tradingagents/research/onchain_replication'
pkg=types.ModuleType('independent_lease');pkg.__path__=[str(P)];sys.modules[pkg.__name__]=pkg
m=importlib.import_module('independent_lease.imported_authority_lease')
with tempfile.TemporaryDirectory(dir=D) as tmp:
 root=Path(tmp);p=root/'fixture.py';raw=b'from contextlib import contextmanager\n@contextmanager\ndef held():\n    yield 1\n';p.write_bytes(raw)
 mod=types.ModuleType('independent_local_context');mod.__file__=str(p);sys.modules[mod.__name__]=mod;exec(compile(raw,str(p),'exec'),vars(mod))
 try:
  try:m._loaded(root,{'fixture.py':hashlib.sha256(raw).hexdigest()})
  except ValueError as e:
   assert str(e)=='import lease: loaded globals differ';reason=str(e)
  else:raise AssertionError('witness no longer reproduces; inspect correction')
 finally:sys.modules.pop(mod.__name__)
r={'source_sha256':hashlib.sha256((P/'imported_authority_lease.py').read_bytes()).hexdigest(),'original_pattern':'owned_io.py:60/65 and compact_owner.py:47/69 module-level @contextmanager','synthetic_authentication_refusal':reason,'scope':'stdlib contextmanager, no genuine authority or numerical imports'}
(D/'CHECK_CONTEXTMANAGER01.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');print(json.dumps(r))
