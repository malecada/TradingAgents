from pathlib import Path
import ast,hashlib,json,os,stat,types
D=Path(__file__).resolve().parent;P=D.parent/'financial-wrapper-compatibility-baseline-root-remote02-2026-10-05';S=P/'caller02.py';t=ast.parse(S.read_bytes());nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('sig','raw','read')];records=[]
for name,primary,secondary in [('fatal-ordinary',KeyboardInterrupt('original'),ValueError('close')),('ordinary-fatal',ValueError('read'),SystemExit('close')),('first-fatal',KeyboardInterrupt('first'),MemoryError('later')),('healthy',None,None),('growth',None,None)]:
 p=D/('caller02-opaque-'+name);p.write_bytes(b'opaque');proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});closed=[];requested=[];grown=[]
 def read(fd,n):
  requested.append(n)
  if primary is not None:raise primary
  if name=='growth' and not grown:p.write_bytes(b'x'*65);grown.append(True)
  return os.read(fd,n)
 def close(fd):
  os.close(fd);closed.append(fd)
  if secondary is not None:raise secondary
 proxy.read=read;proxy.close=close;env={'os':proxy,'stat':stat,'hashlib':hashlib,'FILE':64,'pins':{}};exec(compile(ast.Module(body=nodes,type_ignores=[]),'exact-caller02-read','exec'),env)
 actual=None
 try:out=env['read'](p,hashlib.sha256(b'opaque').hexdigest())
 except BaseException as e:actual=e
 assert len(closed)==1 and max(requested)<=65
 try:os.fstat(closed[0])
 except OSError:pass
 else:raise AssertionError('descriptor remains open')
 if name=='healthy':assert actual is None and out==b'opaque'
 elif name=='growth':assert isinstance(actual,AssertionError) and str(actual)=='metadata file bound exceeded'
 elif name=='ordinary-fatal':assert actual is secondary and actual.__cause__ is primary
 else:assert actual is primary and actual.__cause__ is secondary
 records.append({'name':name,'selected_exception':None if actual is None else type(actual).__name__,'actual_close_once':True,'requested_max':max(requested),'original_fatal_precedence_passed':True,'scaled_growth_limit':64})
old=(P/'caller01.py').read_bytes();new=S.read_bytes();cor=json.loads((P/'ROOT_CALLER_CORRECTION02.json').read_bytes());inverse=new.decode()
for e in reversed(cor['edits']):assert inverse.count(e['new'])==1;inverse=inverse.replace(e['new'],e['old'])
assert inverse.encode()==old
assert "FILE=4194304" in new.decode() and "RLIMIT_FSIZE,(FILE,FILE)" in new.decode()
result={'caller_sha256':hashlib.sha256(new).hexdigest(),'literal_inverse_matches_original':True,'actual_configured_file_limit':4194304,'bounded_growth_predicate_exercised_at64':True,'controls':records,'public_main_invoked':False,'child_launched':False};(D/'CALLER02_CONTROLS01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
