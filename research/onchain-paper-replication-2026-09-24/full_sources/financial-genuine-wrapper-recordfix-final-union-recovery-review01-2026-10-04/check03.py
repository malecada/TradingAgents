import ast,hashlib,importlib.util,json,os,sys,types
from pathlib import Path
O=Path(__file__).resolve().parent;P=O.parent/'financial-genuine-wrapper-recordfix-final-union-recovery-preparation01-2026-10-04'
sys.path.insert(0,str(P));sp=importlib.util.spec_from_file_location('candidate02',P/'restore_union01.py');M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M)
tree=ast.parse((P/'restore_union01.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='reserve');results=[]
for i,A in enumerate((MemoryError,KeyboardInterrupt,SystemExit,ValueError)):
 first=A('original-reservation-failure');later=ValueError('descriptor-close-failure');closed=[]
 def fail_sync(fd):raise first
 def close_then_fail(fd):
  os.close(fd);closed.append(fd);raise later
 proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os) if not n.startswith('__')});proxy.fsync=fail_sync;proxy.close=close_then_fail
 ns=dict(M.__dict__,os=proxy);exec(compile(ast.Module(body=[node],type_ignores=[]),str(P/'restore_union01.py'),'exec'),ns)
 observed=None
 try:ns['reserve'](O/('owned-reserve-qualified-'+str(i)))
 except BaseException as e:observed=e
 assert (observed is first if A is not ValueError else type(observed).__name__=='CleanupFailure' and observed.failures==(first,later)) and len(closed)==1
 try:os.fstat(closed[0]);raise AssertionError('descriptor not closed')
 except OSError:pass
 results.append({'original_type':A.__name__,'observed_type':type(observed).__name__,'original_identity_preserved':observed is first,'cleanup_failure_retains_original':any(x is first for x in getattr(observed,'failures',())),'real_descriptor_closed':True,'partial_created_directory_retained':True})
out={'schema_version':1,'decision':'RESERVE_IMPLICIT_ACTIVE_PRIMARY_VERIFIED','helper_sha256':hashlib.sha256((P/'restore_union01.py').read_bytes()).hexdigest(),'exact_extracted_function':'reserve','cases':results,'numerical_or_network_execution':False}
(O/'RESERVE_READBACK03.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out,sort_keys=True))
