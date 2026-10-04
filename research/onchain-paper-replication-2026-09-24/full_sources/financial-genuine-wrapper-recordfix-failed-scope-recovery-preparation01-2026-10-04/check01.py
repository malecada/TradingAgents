import copy,json,sys
from pathlib import Path
import restore01 as M
R=M.R;H=Path(__file__).resolve().parent;checks=[]
def ok(n,v):assert v,n;checks.append(n)
def refuse(n,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,FileExistsError):ok(n,True)
 else:raise AssertionError(n)
q={'schema_version':1,'remote_root':None,'remote_receipt_sha256':None,'capture_review_manifest':None,'review':None,'release':None,'output_root':None};(H/'REQUEST_TEMPLATE01.json').write_bytes(R.encode(q));refuse('unreleased draft',lambda:M.request(q))
b=H.parent/'financial-genuine-wrapper-root-recordfix-failed-scope-capture01-2026-10-04';bodies={n:R.read(b,n) for n in M.EXPECTED}
for n,pin in M.EXPECTED.items():ok('actual capture body '+n,len(bodies[n])==pin['bytes'] and R.digest(bodies[n])==pin['sha256'])
c,ms=M.joins(bodies);ok('actual whole1049/763',sum(len(m['members']) for m in ms.values())==1049 and sum(sum(r['kind']=='file' for r in m['members']) for m in ms.values())==763)
for n in M.EXPECTED:
 if n.endswith('.tar.gz'):continue
 z=dict(bodies);z[n]=b'{}';refuse('changed metadata '+n,lambda:M.joins(z))
for n,pin in M.PINS.items():ok('unchanged primitive '+n,R.digest(R.read(H,n))==pin)
# Real tiny three-role ordinary recovery only, not actual failed-tree restoration.
o=H/'owned01';o.mkdir();results={}
for role in M.COUNTS:
 src=o/(role+'-source');src.mkdir();(src/'ordinary').write_bytes((role+' opaque').encode());m=R.scan(src);info=R.pack(src,m,o/(role+'.tar.gz'));dest=o/('flat-'+role);M.reserve(dest);result=R.restore(o/(role+'.tar.gz'),info,m,dest);meta=M.recovered_metadata(dest,result,m);ok('real opaque '+role,R.read(dest,meta['flat_members']['ordinary'])==(src/'ordinary').read_bytes());refuse('one-use '+role,lambda:M.reserve(dest));results[role]=result
 wrong=dict(info,sha256='0'*64);refuse('wrong archive pin '+role,lambda:R.restore(o/(role+'.tar.gz'),wrong,m,dest))
for first in [ValueError('ordinary'),MemoryError('memory'),KeyboardInterrupt('interrupt')]:
 for later in [OSError('ordinary'),MemoryError('memory'),KeyboardInterrupt('interrupt')]:
  seen=[]
  def fail():seen.append(1);raise later
  def last():seen.append(2)
  actual=None
  try:R._cleanup((fail,last),primary=first)
  except BaseException as e:actual=e
  fatal=lambda e:not isinstance(e,Exception) or isinstance(e,MemoryError)
  valid=actual is None if fatal(first) else actual is later if fatal(later) else type(actual).__name__=='CleanupFailure' and actual.failures==(first,later)
  ok('firstfatal '+type(first).__name__+type(later).__name__,valid);ok('allclose '+type(first).__name__+type(later).__name__,seen==[1,2])
ok('no numeric imports',all(n not in sys.modules for n in ['numpy','torch','pandas','scipy']))
(H/'CHECKS01.json').write_bytes(R.encode({'checks':checks,'count':len(checks),'actual_failed_scope_restores':0,'new_claims':0,'network':0}));print('PASS',len(checks))
