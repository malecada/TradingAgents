from pathlib import Path
import ast,hashlib,json
D=Path(__file__).resolve().parent;F=D.parent;A=F/'financial-wrapper-compatibility-composed-recovery-preparation01-2026-10-04';U=F/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04/utilities/owned_io.py';h=lambda b:hashlib.sha256(b).hexdigest()
old=(A/'verify01.py').read_bytes();dep=U.read_bytes();assert h(old)=='14145d47b0df54c4234c4c029a1108ce8b3e7a9d4638f92b9475d99eb3f7c52f';assert h(dep)=='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb';inputs=(A/'INPUTS01.json').read_bytes();assert h(inputs)=='f992329f1e0baf29bff17eaa1ba82d0f0fe73edf5f8845b9d30a7386f630f4af'
(D/'ORIGINAL01.py').write_bytes(old);(D/'owned_io.py').write_bytes(dep);(D/'INPUTS01.json').write_bytes(inputs)
s=old.decode();edits=[]
def replace(a,b):
 global s
 assert s.count(a)==1;edits.append({'old':a,'new':b});s=s.replace(a,b)
replace('import argparse,gzip,hashlib,io,json,os,re,stat,tarfile,time','import argparse,gzip,hashlib,io,json,os,re,stat,tarfile,time,types')
insert='''# Exact pinned owned_io dependency is embedded as immutable bytes to avoid introducing
# another filesystem/bootstrap cleanup path. The retained owned_io.py is byte-identical.
OWNED_IO_BYTES = '''+repr(dep)+'''
require(h(OWNED_IO_BYTES)=='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','owned IO dependency pin')
IO=types.ModuleType('_composed_pinned_owned_io')
exec(compile(OWNED_IO_BYTES,'<pinned owned_io09d1fbcc>','exec'),IO.__dict__)
def _retain(selected,errors):
 # Diagnostic retention is optional and cannot replace the already selected error.
 if selected is None:return
 try:
  namespace=BaseException.__dict__['__dict__'].__get__(selected)
  prior=namespace.get('composed_failures',())
  if not isinstance(prior,tuple):prior=(prior,)
  retained=list(prior)
  for error in errors:
   if error is not None and error is not selected and all(error is not e for e in retained):retained.append(error)
  if retained:namespace['composed_failures']=tuple(retained)
 except BaseException:pass
def _finish(actions,primary):
 failures=[];selected=primary
 def wrapped(action):
  def close():
   try:action()
   except BaseException as error:failures.append(error);raise
  return close
 try:IO._cleanup(tuple(wrapped(action) for action in actions),primary=primary)
 except BaseException as error:selected=error;raise
 finally:_retain(selected,([primary] if primary is not None else [])+failures)
'''
replace('class Reader:\n',insert+'class Reader:\n')
replace("   finally:\n    try:os.close(fd)\n    except BaseException as close:\n     if primary is None:raise\n     BaseException.__dict__['__dict__'].__get__(primary)['secondary_close_failure']=close", "   finally:_finish((lambda:os.close(fd),),primary)")
replace("   with os.scandir(p) as it:\n    for e in it:\n     self.tick();n=str(Path(e.path).relative_to(root))\n     if p==root and e.name in exclude:continue\n     safe(n);t=os.lstat(e.path);require(stat.S_ISREG(t.st_mode) or stat.S_ISDIR(t.st_mode),'tree special');require(len(found)<LIMIT,'tree members');found[n]=sig(t)\n     if stat.S_ISDIR(t.st_mode):pending.append(Path(e.path))", "   it=None;primary=None\n   try:\n    it=os.scandir(p)\n    for e in it:\n     self.tick();n=str(Path(e.path).relative_to(root))\n     if p==root and e.name in exclude:continue\n     safe(n);t=os.lstat(e.path);require(stat.S_ISREG(t.st_mode) or stat.S_ISDIR(t.st_mode),'tree special');require(len(found)<LIMIT,'tree members');found[n]=sig(t)\n     if stat.S_ISDIR(t.st_mode):pending.append(Path(e.path))\n   except BaseException as error:primary=error;raise\n   finally:_finish(() if it is None else (lambda:it.close(),),primary)")
replace("  print(json.dumps({'schema_version':1,'status':'REFUSED','exception_type':type(error).__name__,'reason':str(error),'recovery_proof':None,'numerical_authority':False},sort_keys=True));raise", "  _finish((lambda:print(json.dumps({'schema_version':1,'status':'REFUSED','exception_type':type(error).__name__,'reason':str(error),'recovery_proof':None,'numerical_authority':False},sort_keys=True)),),error);raise")
(D/'verify02.py').write_text(s);inverse=s
for row in reversed(edits):assert inverse.count(row['new'])==1;inverse=inverse.replace(row['new'],row['old'])
assert inverse.encode()==old and ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False)
# Explicit semantic boundary: all original top-level definitions except Reader unchanged;
# Reader init/tick/anchor/j/finish unchanged; run, maps, caps, byte/Git logic are exact AST.
a=ast.parse(old);b=ast.parse(s);aa={x.name:x for x in a.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))};bb={x.name:x for x in b.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))};unchanged=[]
for n,node in aa.items():
 if n!='Reader':assert ast.dump(node)==ast.dump(bb[n]);unchanged.append(n)
ar={x.name:x for x in aa['Reader'].body if isinstance(x,ast.FunctionDef)};br={x.name:x for x in bb['Reader'].body if isinstance(x,ast.FunctionDef)}
for n,node in ar.items():
 if n not in ('read','tree'):assert ast.dump(node)==ast.dump(br[n]);unchanged.append('Reader.'+n)
(D/'INVERSE01.json').write_text(json.dumps({'schema_version':1,'original_sha256':h(old),'successor_sha256':h(s.encode()),'owned_dependency_sha256':h(dep),'inputs_sha256':h(inputs),'literal_edits':edits,'full_literal_inverse_equals_original':True,'full_AST_inverse_equals_original':True,'unchanged_original_definitions':unchanged,'dependency_embedded_equals_literal_copied_file':True},indent=2)+'\n');print(h(s.encode()),len(edits))
