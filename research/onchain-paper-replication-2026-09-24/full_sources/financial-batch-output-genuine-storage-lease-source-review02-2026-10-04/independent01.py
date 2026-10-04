from pathlib import Path
import os,json,time
import storage_lease01 as L
H=Path(__file__).resolve().parent;rows=[]
def fresh(name,callback=lambda:None):
 p=H/name;p.mkdir(mode=0o700);roles={r:r for r in L.ROLES}
 for v in roles.values():(p/v).mkdir(mode=0o700)
 return p,L.OwnedLease(p,'lease',roles,64*L.MIB,64*L.MIB,callback)
# Mutations at actual statvfs return boundary, after measured census.
for kind in ('extra','mode','growth'):
 root,x=fresh('query-'+kind);x.reserve('codec',[('codec/a','file',3)]);p=root/'codec/a';p.write_bytes(b'abc');x.check();saved=(x.logical_reserved,x.allocated_reserved);old=os.fstatvfs;events=[]
 def query(fd):
  value=old(fd)
  if fd==x.fd and not events:
   events.append(fd)
   if kind=='extra':(root/'diagnostic/unreserved').write_bytes(b'x')
   elif kind=='mode':p.chmod(0o640)
   else:
    with p.open('ab') as f:f.write(b'x')
  return value
 error=None
 os.fstatvfs=query
 try:x.check()
 except ValueError as e:error=str(e)
 finally:os.fstatvfs=old
 assert error and x.failed and x.fd is None and saved==(x.logical_reserved,x.allocated_reserved)
 rows.append({'case':'late-resource-'+kind,'error':error,'events':len(events),'no_refund':True})
# Actual close-failure pairs preserve a final rejoin primary fatal and drain both.
for P in (KeyboardInterrupt,MemoryError,SystemExit):
 for Q in (OSError,MemoryError,SystemExit):
  root,x=fresh('fatal-'+P.__name__+'-'+Q.__name__);fds=(x.fd,x.ledger_fd);primary=P('first');later=Q('close');realjoin=L._rejoin;realclose=os.close;events=[]
  def fail(*a,**k):raise primary
  def close(fd):
   realclose(fd)
   if fd in fds:events.append(fd);raise later
  error=None;L._rejoin=fail;os.close=close
  try:x.check()
  except BaseException as e:error=e
  finally:L._rejoin=realjoin;os.close=realclose
  assert error is primary and set(events)==set(fds) and x.failed
  for fd in fds:
   try:os.fstat(fd)
   except OSError:pass
   else:raise AssertionError('fd leak')
  rows.append({'case':P.__name__+'/'+Q.__name__,'primary_preserved':True,'both_actual_closed':True})
(H/'INDEPENDENT01.json').write_text(json.dumps({'cases':rows,'count':len(rows),'genuine_handles':False},indent=2)+'\n');print(len(rows))
