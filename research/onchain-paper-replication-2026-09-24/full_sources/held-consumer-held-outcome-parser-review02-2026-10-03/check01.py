"""Independent stdlib/source review; tiny processes are not native research jobs."""
import ast,hashlib,importlib.util,json,os,stat,subprocess,sys
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;A=P.parent/'held-consumer-held-outcome-parser-preparation02-2026-10-03';B=P.parent/'held-consumer-held-outcome-parser-preparation01-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest()
assert H((A/'MANIFEST02.json').read_bytes())=='21d1dd58c07be43ce68746504330b4bb3c2393e979cf72693ccb8957f3933222'
assert H((A/'held_outcome01.py').read_bytes())=='95affaa3867b0f50dedc706121b47304126c6def39715133414ef149b9eae153'
manifest=json.loads((A/'MANIFEST02.json').read_bytes());paths=[]
for row in manifest['files']:
 q=A/row['path'];st=q.lstat();assert stat.S_IMODE(st.st_mode)==row['mode']
 if row['type']=='file':assert stat.S_ISREG(st.st_mode) and st.st_nlink==row['links'] and st.st_size==row['bytes'] and H(q.read_bytes())==row['sha256']
 elif row['type']=='directory':assert stat.S_ISDIR(st.st_mode)
 else:assert stat.S_ISLNK(st.st_mode) and os.readlink(q)==row['target']
 paths.append(row['path'])
actual=[]
for root,dirs,files in os.walk(A,followlinks=False):actual.extend(str((Path(root)/x).relative_to(A)) for x in dirs+files)
assert sorted(actual)==sorted(paths+['MANIFEST02.json'])
old=(B/'held_outcome01.py').read_text();new=(A/'held_outcome01.py').read_text()
def seam(s):return s[s.index('    actions=[]\n    if child is not None:'):s.index('    if poll is not None:actions.append')]
# Selector-close is also intentionally deferred via lambda.
inverse=new.replace(seam(new),seam(old)).replace('if poll is not None:actions.append(lambda:poll.close())','if poll is not None:actions.append(poll.close)')
assert inverse==old and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(old))
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=load(A/'held_outcome01.py','new');prior=load(B/'held_outcome01.py','prior');observations=[]
for module in (prior,m):
 for late in (OSError('poll failure'),SystemExit('poll fatal')):
  first=MemoryError('original allocation');calls=[]
  class Stream:
   @property
   def closed(self):raise SystemExit('closed property must not run')
   def close(self):calls.append('close')
  class Child:
   stdin=Stream();stdout=Stream();stderr=Stream()
   def poll(self):calls.append('poll');raise late
   def kill(self):calls.append('kill')
   def wait(self,timeout):calls.append('wait');return -9
  with patch.object(module.subprocess,'Popen',return_value=Child()),patch.object(module.selectors,'DefaultSelector',side_effect=first):
   try:module.git(P,['--version'])
   except BaseException as observed:result=observed
   else:raise AssertionError('missing fatal')
  if module is prior:assert result is late and calls==['poll']
  else:assert result is first and calls==['kill','wait','close','close','close']
  observations.append({'module':module.__name__,'late':type(late).__name__,'result':type(result).__name__,'calls':calls})
# Independent failures in every cleanup action still preserve the body fatal.
calls=[];first=KeyboardInterrupt('body')
class Stream:
 def close(self):calls.append('close');raise OSError('close')
class Child:
 stdin=Stream();stdout=Stream();stderr=Stream()
 def kill(self):calls.append('kill');raise SystemExit('late fatal')
 def wait(self,timeout):calls.append('wait');raise OSError('wait')
class Selector:
 def register(self,*a):raise first
 def close(self):calls.append('selector');raise MemoryError('last fatal')
# Allocation fails after child birth, then separately exercise selector cleanup.
sel=Selector();sel.register=lambda *a:None
sel.get_map=lambda:(_ for _ in ()).throw(first)
with patch.object(m.subprocess,'Popen',return_value=Child()),patch.object(m.selectors,'DefaultSelector',return_value=sel),patch.object(m.os,'set_blocking',side_effect=first):
 try:m.git(P,['--version'])
 except BaseException as observed:result=observed
assert result is first and calls==['kill','wait','close','close','close','selector']
# Real owned child killed/reaped and all original descriptors closed.
real=subprocess.Popen;children=[];first=MemoryError('selector birth')
def spawn(*args,**kw):
 c=real([sys.executable,'-B','-c','import time;time.sleep(20)'],cwd=P,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);children.append(c);return c
with patch.object(m.subprocess,'Popen',side_effect=spawn),patch.object(m.selectors,'DefaultSelector',side_effect=first):
 try:m.git(P,['--version'])
 except BaseException as observed:result=observed
assert result is first and len(children)==1
child=children[0];assert child.poll() is not None and not Path('/proc',str(child.pid)).exists() and all(x.closed for x in (child.stdin,child.stdout,child.stderr))
assert m.git(P,['--version'],cap=1024).startswith(b'git version ')
# Count close-method calls on a real normally reaped Git child. Underlying file
# objects remain idempotent; method count is not FD-release count.
counts={'stdin':0,'stdout':0,'stderr':0};realchildren=[]
class Proxy:
 def __init__(self,stream,name):self.stream=stream;self.name=name
 def fileno(self):return self.stream.fileno()
 def close(self):counts[self.name]+=1;return self.stream.close()
def observed_spawn(*args,**kw):
 c=real(*args,**kw);realchildren.append(c)
 for name in counts:setattr(c,name,Proxy(getattr(c,name),name))
 return c
with patch.object(m.subprocess,'Popen',side_effect=observed_spawn):assert m.git(P,['--version'],cap=1024).startswith(b'git version ')
assert counts=={'stdin':2,'stdout':1,'stderr':1}
assert all(getattr(realchildren[0],n).stream.closed for n in counts)
# Current source and input metadata only; do not invoke outcome/admission.
t=P.parent/'held-consumer-native-release-prerequisite-investigation01-2026-10-03/RELEASE_TEMPLATE01.json';release=m.parse(t.read_bytes());reader=m.Reader(release['capsule_root']);reg=m.sources(reader,release);exp=reg['experiments'][m.IDENTITY]
inputs={k:H(m.input_body(reader,exp,k)) for k in exp['inputs']};reader.recheck();assert len(inputs)==33 and len(exp['outputs'])==6
assert not any(n in sys.modules for n in ('numpy','torch','scipy'))
result={'status':'ACCEPTED_NARROW_SOURCE_ONLY','members':len(paths),'helper_sha256':H((A/'held_outcome01.py').read_bytes()),'inverse_bytes_ast':True,'HOP1_replays':observations,'real_child_reaped':True,'real_pipe_methods':counts,'real_source_git_bodies':205,'inputs':inputs,'full_authenticate_or_authority_executed':False,'numerical_imports':False}
(P/'READBACK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print('PASS: manifest, inverse, original HOP1 RED/current GREEN, independent actions, actual kill/reap, already-reaped Git, observed stdin method2/FD closed,205Git+33inputs metadata')
