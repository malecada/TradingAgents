from pathlib import Path
import os,sys,time,json
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import recover01 as R
n=0;events=[];owned=D/'adversarial04';owned.mkdir();R.HERE=owned
for exception in (ValueError('watch breach'),KeyboardInterrupt('watch fatal'),MemoryError('watch memory')):
 original=R.W.census;count=0
 def sample(root):
  global count
  count+=1
  if count>=2:raise exception
  return original(root)
 R.W.census=sample;begun=time.monotonic()
 try:
  try:R.git(['-c','alias.pause=!sleep 5','pause'])
  except BaseException as e:assert (e is exception) if not isinstance(exception,ValueError) else (isinstance(e,RuntimeError) and e.__cause__ is exception);n+=1
  else:raise AssertionError('watch failure accepted')
 finally:R.W.census=original
 call=R.CALLS[-1];assert time.monotonic()-begun<3 and call['pid'] is not None and not Path('/proc',str(call['pid'])).exists();n+=1
 try:os.killpg(call['pid'],0)
 except ProcessLookupError:n+=1
 else:raise AssertionError('group retained')
 events.append(call)
# Exhausted sampled census cannot silently return partial counters.
original=R.W._sample
for exception in (R.W.ChangingTree('publication'),FileNotFoundError('temporary'),KeyboardInterrupt('fatal')):
 count=0
 def changing(root):
  global count
  count+=1;raise exception
 R.W._sample=changing
 try:
  try:R.W.census(owned)
  except BaseException as e:
   if isinstance(exception,KeyboardInterrupt):assert e is exception and count==1
   else:assert isinstance(e,ValueError) and count==3
   n+=1
  else:raise AssertionError('incomplete returned')
 finally:R.W._sample=original
# Actual directory iterator closes its real FD before secondary error; first fatal preserved.
oldscan=R.W.os.scandir
class Broken:
 def __init__(self,path):self.it=oldscan(path)
 def __iter__(self):return self
 def __next__(self):raise KeyboardInterrupt('iterator primary')
 def close(self):self.it.close();raise OSError('close secondary')
R.W.os.scandir=Broken
try:
 try:R.W.census(owned)
 except KeyboardInterrupt as e:assert str(e)=='iterator primary';n+=1
 else:raise AssertionError('first fatal masked')
finally:R.W.os.scandir=oldscan
(D/'ADVERSARIAL03.json').write_text(json.dumps({'checks':n,'actual_child_failure_calls':events,'no_network':True,'no_actual_entry':True},indent=2)+'\n');print(n)
