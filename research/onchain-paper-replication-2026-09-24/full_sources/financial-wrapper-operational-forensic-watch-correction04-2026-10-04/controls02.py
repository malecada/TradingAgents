"""Additional genuine endpoint/namespace controls; synthetic capacities only lowered."""
from pathlib import Path
import sys,os,time,json,traceback
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import watch01 as W;import recover01 as R
B=D/'owned02';B.mkdir();rows=[]
def rec(n,**kw):rows.append(dict(name=n,**kw));(D/'CONTROLS02.json').write_text(json.dumps(rows,indent=2)+'\n')
def req(v,m):
 if not v:raise AssertionError(m)
def trial(fn):
 try:return {'returned':fn()},None
 except BaseException as e:return {'error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()},e
for kind in ('continuous-publication','directory-mode','directory-replacement','regular-growth','regular-shrink','aggregate-growth'):
 root=B/kind;root.mkdir();(root/'a').write_bytes(b'x'*64);(root/'b').write_bytes(b'y'*64);orig=Path.lstat;calls={};changes=[];policy=dict(W.POLICY)
 if kind=='aggregate-growth':W.POLICY['logical']=192
 def hook(p,*a,**k):
  calls[p]=calls.get(p,0)+1
  if kind in ('continuous-publication','directory-mode','directory-replacement') and p==root and calls[p]%2==0:
   n=len(changes)
   if kind=='continuous-publication':(root/f'new-{n}').mkdir()
   if kind=='directory-mode':root.chmod(0o700 if n%2==0 else 0o750)
   if kind=='directory-replacement':root.rename(B/f'retained-original-{n}');root.mkdir();(root/'a').write_bytes(b'x'*64);(root/'b').write_bytes(b'y'*64)
   changes.append(n)
  if kind in ('regular-growth','regular-shrink','aggregate-growth') and p==root/'a' and calls[p]==2:
   size=128 if kind!='regular-shrink' else 1
   with p.open('wb') as f:f.write(b'z'*size);f.flush();os.fsync(f.fileno())
   if kind=='aggregate-growth':
    with (root/'b').open('wb') as f:f.write(b'z'*128);f.flush();os.fsync(f.fileno())
   changes.append(size)
  return orig(p,*a,**k)
 Path.lstat=hook;start=time.monotonic()
 try:result,e=trial(lambda:W.census(root))
 finally:Path.lstat=orig;W.POLICY.clear();W.POLICY.update(policy)
 if kind in ('continuous-publication','directory-mode','directory-replacement'):req(type(e)is ValueError and len(changes)==3 and calls[root]==6 and time.monotonic()-start>=.2,'unchanged identity/churn refuses after three complete attempts')
 elif kind=='aggregate-growth':req(type(e)is ValueError and result['error']=='whole rejoin logical/allocated cap','both endpoint aggregate retained')
 else:req(e is None and result['returned']['logical_bytes']==(192 if kind=='regular-growth' else 128) and result['returned']['regular_extent_changes']==1 and result['returned']['complete_attempts']==1,'both regular endpoints max unchanged')
 rec(kind,changes=changes,elapsed=time.monotonic()-start,**result)
for kind in ('vanish-after-enumeration','late-close-publication'):
 root=B/kind;root.mkdir();(root/'opaque').write_bytes(b'opaque');original=W.os.scandir;once=[];closed=[];before=len(os.listdir('/proc/self/fd'))
 class End:
  def __init__(self,p):self.p=Path(p);self.it=original(p)
  def __iter__(self):return self
  def __next__(self):return next(self.it)
  def close(self):
   self.it.close();closed.append(str(self.p))
   if self.p==root and not once:
    once.append(True)
    if kind=='vanish-after-enumeration':(root/'opaque').rename(B/'retained-vanished-body')
    else:(root/'late').mkdir()
 W.os.scandir=End;start=time.monotonic()
 try:result,e=trial(lambda:W.census(root))
 finally:W.os.scandir=original
 req(e is None and result['returned']['complete_attempts']==2 and result['returned']['members']==(1 if kind=='vanish-after-enumeration' else 3) and before==len(os.listdir('/proc/self/fd')),'complete rescan, no ignored missing or late names')
 rec(kind,closed=closed,fd_before=before,fd_after=len(os.listdir('/proc/self/fd')),elapsed=time.monotonic()-start,**result)
original=R.W.census;called=[];R.HERE=B;R.START=time.monotonic();R.WATCHES=[{}]*8192
R.W.census=lambda p:called.append(p)
try:result,e=trial(R.watch)
finally:R.W.census=original
req(type(e)is ValueError and not called,'8192 cap before sample')
rec('unchanged8192-sample-ceiling',**result)
rec('complete',rows_before_completion=len(rows),no_network=True,no_entry=True)
print(json.dumps({'rows':len(rows)}))
