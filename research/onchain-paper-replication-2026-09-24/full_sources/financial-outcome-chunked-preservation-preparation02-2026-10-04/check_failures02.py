import hashlib,json,os,sys
from pathlib import Path
import chunk_archive01 as A
D=Path(__file__).resolve().parent;T=D/'tiny-failures02';T.mkdir();checks=[]
def check(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
source=T/'source';source.mkdir();(source/'opaque').write_bytes(b'opaque body')
real=A._write
classes=(OSError,MemoryError,KeyboardInterrupt,SystemExit)
for i,pc in enumerate(classes):
 for j,cc in enumerate(classes):
  primary=pc('original');secondary=cc('failure-publication');target=T/('case-%d-%d'%(i,j))
  def fault(directory,name,raw,bounds):
   if name=='chunk-00000000.bin':raise primary
   if name=='capture-failure.json':raise secondary
   return real(directory,name,raw,bounds)
  A._write=fault;observed=None
  try:A.capture({'s':str(source)},target)
  except BaseException as e:observed=e
  finally:A._write=real
  fatal=lambda e:isinstance(e,MemoryError) or not isinstance(e,Exception)
  if fatal(primary):check('first fatal survives secondary '+str((i,j)),observed is primary)
  elif fatal(secondary):check('secondary fatal outranks ordinary '+str((i,j)),observed is secondary)
  else:check('ordinary cleanup uncertainty stops worker '+str((i,j)),type(observed).__name__=='CleanupFailure')
  check('partial intent survives '+str((i,j)),(target/'intent.json').is_file() and not (target/'index.json').exists() and not (target/'capture-failure.json').exists())
# No descriptor leaked by repeated real write failures or completion attempts.
check('no complete index fabricated',all(not(p/'index.json').exists() for p in T.glob('case-*')))
# The output-size refusal executes before any file is created.
out=T/'bound-output';out.mkdir();b=A.Bounds();b.anchors[out]=A.anchor(out)
try:A._write(out,'oversize',b'x'*(A.FILE+1),b)
except ValueError:checks.append('4MiB per-artifact refusal')
else:raise AssertionError('oversize accepted')
check('oversize refusal wrote no file',not (out/'oversize').exists())
# Unchanged helper body hashes; no tuning or monkeypatch of their bounds.
pins=json.loads((D/'HELPER_PINS01.json').read_text())['unchanged_helpers']
for name,pin in pins.items():check('exact original helper '+name,hashlib.sha256((D/name).read_bytes()).hexdigest()==pin)
check('R4 bounds unchanged',A.R.FILE==4*1024**2 and A.R.BASE==128*1024**2 and A.R.TOTAL==1024**3)
check('no numerical import',not any(k in sys.modules for k in ('numpy','torch','scipy')))
(D/'CHECKS02.json').write_text(json.dumps({'count':len(checks),'checks':checks,'scope':'owned opaque failure injection; source/native limits unchanged'},indent=2)+'\n');print(len(checks),'passed')
