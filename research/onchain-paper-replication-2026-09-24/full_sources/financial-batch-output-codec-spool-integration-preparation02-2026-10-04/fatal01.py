import json,os
from pathlib import Path
import router05 as A
P=Path(__file__).resolve().parent;src=P/'new-source';desc=A.C.parse(A.R.read(src,'start.json'))['descriptor'];pin=A.sha(A.R.read(src,'terminal.json'));inv=A.inspect(src,'b'*64,desc,pin);route=A.route((inv,),4);rows=[]
def mkdir(n):p=P/n;p.mkdir(mode=0o700);return p
for i,Primary in enumerate((MemoryError,KeyboardInterrupt,SystemExit)):
 for j,Secondary in enumerate((OSError,MemoryError,SystemExit)):
  label='fatal-%d-%d'%(i,j);ledger=A.Router(mkdir(label+'-ledger'),route,*A.estimate(route));spools=tuple(mkdir(label+'-spool-'+str(k)) for k in range(len(route.partitions)));rr=(mkdir(label+'-recovery'),)
  rid=(rr[0].stat().st_dev,rr[0].stat().st_ino);originalclose=os.close;originalinit=A.L.LocalStore.__init__;fdpin=[None];events=[];first=Primary('original callback fatal');later=Secondary('actual recovered close secondary')
  def init(store,*a,**kw):originalinit(store,*a,**kw);fdpin[0]=store.fd
  def close(fd):
   try:st=os.fstat(fd);chosen=(st.st_dev,st.st_ino)==rid
   except OSError:chosen=False
   originalclose(fd)
   if fd==fdpin[0] and chosen and not events:events.append(fd);raise later
  def send(*a):raise first
  error=None
  try:
   os.close=close;A.L.LocalStore.__init__=init;ledger.run(spools,rr,send,None)
  except BaseException as e:error=e
  finally:os.close=originalclose;A.L.LocalStore.__init__=originalinit
  assert error is first and len(events)==1 and ledger.failed and not ledger.finished and ledger.consumed==A.estimate(route)
  assert (ledger.root/'failed.json').exists() and not (ledger.root/'complete.json').exists()
  try:os.fstat(fdpin[0])
  except OSError:pass
  else:raise AssertionError('persistent recovery descriptor leaked')
  rows.append({'primary':Primary.__name__,'secondary':Secondary.__name__,'first_identity_retained':True,'real_close_count':len(events),'failed':True,'no_refund':True});ledger.close()
(P/'FATAL01.json').write_text(json.dumps(rows,sort_keys=True,indent=2)+'\n');print(len(rows),'real final-close fatal pairs passed')
