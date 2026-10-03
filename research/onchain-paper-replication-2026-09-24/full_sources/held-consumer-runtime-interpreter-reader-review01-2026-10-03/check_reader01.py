import ast,hashlib,json,os,runpy,sys,tempfile
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parent;P=H.parent/'held-consumer-runtime-interpreter-reader-preparation01-2026-10-03';S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-05/source');sha=lambda b:hashlib.sha256(b).hexdigest()
mraw=(P/'MANIFEST01.json').read_bytes();assert sha(mraw)=='aedff0f28cf4d360703d944a0d134ff967d0509ab4c912d4259e505566192a91';m=json.loads(mraw)
for row in m['files']:
 b=(P/row['path']).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
assert len(m['files'])==13 and sum(r['bytes'] for r in m['files'])==146025
old=(P/'capsule_builder01.py.baseline05.txt').read_text();new=(P/'capsule_builder01.py').read_text();assert old==(S/'fixture_tools/capsule_builder01.py').read_text()
n=next(n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef) and n.name=='_held_interpreter');ls=new.splitlines(True);del ls[n.lineno-1:n.end_lineno+1];inverse=''.join(ls).replace("    _held_interpreter(root,executable,expected['executable_sha256'],expected['executable_bytes'])","    read(executable.parent,executable.name,expected['executable_sha256'],executable.stat().st_size)",1);assert inverse==old and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(old))
B=runpy.run_path(str(P/'capsule_builder01.py'));O=runpy.run_path(str(S/'fixture_tools/capsule_builder01.py'));expected=json.loads((S/'fixture_inputs/held/runtime-role01.json').read_bytes());assert expected['executable_bytes']==31510904
try:O['held_runtime_metadata'](S,expected)
except ValueError as err:assert str(err)=='source type/link/extent differs';red=str(err)
else:raise AssertionError('original runtime unexpectedly passed')
result=B['held_runtime_metadata'](S,expected);assert result['record_count']==251 and result['record_bytes']==5033917 and not result['native_controls_verified'] and not result['execution_admitted'] and not result['all_installed_package_bodies_rehashed']
actual=Path(expected['resolved_executable']);read=os.read;cl=os.close;sizes=[]
def bounded(fd,size):
 if os.readlink('/proc/self/fd/'+str(fd))==str(actual):sizes.append(size)
 return read(fd,size)
with patch.object(os,'read',side_effect=bounded):v=B['_held_interpreter'](S,actual,expected['executable_sha256'],expected['executable_bytes'])
assert v=={'bytes':31510904,'sha256':expected['executable_sha256']} and max(sizes)<=65536
cases=[]
with tempfile.TemporaryDirectory(dir=H,prefix='synthetic-') as temp:
 base=Path(temp)
 for mode in ['body-memory','body-keyboard','ordinary-later-fatal','two-close-fatal','open-fatal','replacement','parent-redirect','hardlink','source-cap']:
  parent=base/mode;parent.mkdir();p=parent/'exe';p.write_bytes(b'abc');bodyfatal=MemoryError('body') if mode=='body-memory' else KeyboardInterrupt('body');late=SystemExit('later');second=MemoryError('second');closed=[];once=[False]
  def selected_read(fd,size):
   if os.readlink('/proc/self/fd/'+str(fd))==str(p) and not once[0]:
    once[0]=True
    if mode.startswith('body-'):raise bodyfatal
    if mode=='ordinary-later-fatal':raise OSError('ordinary body')
    if mode=='replacement':p.rename(parent/'old');p.write_bytes(b'abc')
    if mode=='parent-redirect':parent.rename(base/(mode+'-moved'));parent.symlink_to(mode+'-moved')
   return read(fd,size)
  def selected_close(fd):
   target=os.readlink('/proc/self/fd/'+str(fd));cl(fd)
   if target in (str(p),str(parent)):
    closed.append(target)
    if mode.startswith('body-'):raise OSError('later ordinary')
    if mode=='ordinary-later-fatal':raise late
    if mode=='two-close-fatal':raise late if len(closed)==1 else second
  if mode=='hardlink':os.link(p,parent/'alias')
  if mode=='source-cap':
   os.truncate(p,4194305)
   try:B['read'](parent,'exe','0'*64,4194305)
   except ValueError:cases.append(mode);continue
   raise AssertionError('source cap weakened')
  op=os.open
  def selected_open(path,*args,**kwargs):
   if mode=='open-fatal' and path=='exe' and 'dir_fd' in kwargs:raise bodyfatal
   return op(path,*args,**kwargs)
  try:
   with patch.object(os,'read',side_effect=selected_read),patch.object(os,'close',side_effect=selected_close),patch.object(os,'open',side_effect=selected_open):B['_held_interpreter'](S,p,sha(b'abc'),3)
  except BaseException as err:
   if mode.startswith('body-') or mode=='open-fatal':assert err is bodyfatal
   elif mode in ('ordinary-later-fatal','two-close-fatal'):assert err is late
   else:assert isinstance(err,ValueError)
  else:raise AssertionError('expected refusal '+mode)
  if mode in ('body-memory','body-keyboard','ordinary-later-fatal','two-close-fatal'):assert closed==[str(p),str(parent)]
  if mode=='open-fatal':assert closed==[str(parent)]
  cases.append(mode)
assert not any(x.split('.')[0] in ('numpy','torch','scipy') for x in sys.modules)
assert (S/'fixture_tools/capsule_builder01.py').read_text()==old
out={'schema_version':1,'candidate_sha256':sha(new.encode()),'baseline_sha256':sha(old.encode()),'members_verified':13,'whole_inverse_bytes_ast':True,'actual_old_runtime_refusal':red,'actual_candidate_runtime':result,'interpreter_bytes':31510904,'max_observed_interpreter_read_bytes':max(sizes),'independent_tiny_cases':cases,'numerical_imports':False,'installed_source05_unchanged':True,'candidate_installed':False}
(H/'READBACK01.json').write_text(json.dumps(out,indent=2)+'\n');print('PASS13bodies/fullinverse; actualSource05RED→candidate251RECORDsGREEN;31510904Bstream<=65536;9independentFD/fatal/mutation/sourcecapcases;noNum/authority')
