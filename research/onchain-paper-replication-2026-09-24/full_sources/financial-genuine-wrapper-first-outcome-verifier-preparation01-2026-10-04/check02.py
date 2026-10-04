"""Pure metadata predicates and actual FD cleanup; no Owner/Run objects."""
import itertools,json,os
from pathlib import Path
import verifier01 as V
root=Path(__file__).resolve().parent;out=root/'opaque_controls02';out.mkdir();checks=0
def ok(v):
 global checks
 assert v;checks+=1
def refused(f):
 global checks
 try:f()
 except (ValueError,KeyError,TypeError):checks+=1
 else:raise AssertionError('mutation accepted')
originals=[{'pid':41,'ticks':'101'},{'pid':42,'ticks':'102'}]
valid=[{'pid':41,'original_ticks':'101','current_ticks':None},{'pid':42,'original_ticks':'102','current_ticks':'900'}]
ok(V.pid_observations(originals,valid))
for rows in ([],valid[:1],valid+valid[:1],list(reversed(valid)),[{**valid[0],'current_ticks':'101'},valid[1]],[{**valid[0],'current_ticks':101},valid[1]],[{**valid[0],'pid':True},valid[1]],[{**valid[0],'original_ticks':'bad'},valid[1]]):refused(lambda:V.pid_observations(originals,rows))
# All actual FD callbacks run, and first genuine fatal identity survives.
for first,second in itertools.product((None,ValueError,KeyboardInterrupt,MemoryError,SystemExit),repeat=2):
 calls=[];a=None if first is None else first('body');b=None if second is None else second('close');path=out/('fd-'+str(checks));path.write_bytes(b'opaque');fd=os.open(path,os.O_RDONLY)
 def cleanup():
  calls.append('close');os.close(fd)
  if b is not None:raise b
 caught=None
 try:
  try:
   if a is not None:raise a
  finally:V.R._cleanup((cleanup,lambda:calls.append('last')))
 except BaseException as e:caught=e
 ok(calls==['close','last'])
 try:os.fstat(fd)
 except OSError:ok(True)
 else:raise AssertionError('leaked fd')
 fatal=lambda x:x is not None and (isinstance(x,MemoryError) or not isinstance(x,Exception))
 if fatal(a):ok(caught is a)
 elif fatal(b):ok(caught is b)
 elif b is None:ok(caught is a)
 else:ok(caught is not None)
print(json.dumps({'checks':checks,'scope':'scalar metadata and genuine owned file descriptors only'}))
