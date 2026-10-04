import dataclasses as D,hashlib,io,json,os,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-batch-output-codec-spool-integration-preparation02-2026-10-04';sys.path.insert(0,str(A));import router05 as R
checks=0;observations=[]
def ok(v):
 global checks
 assert v;checks+=1
# Independently check every exact fresh successful fixture/recovered file, not
# just the author's return or compact result; source arrays are never decoded.
for label,dtype,rows,index in [('one','<f4',9,0),('two','<f8',1,1)]:
 source=H/('run04-source-'+label);dest=H/('run04-complete-recovered-%02d'%index)
 start=R.C.parse(R.R.read(source,'start.json'));desc=start['descriptor'];terminal=R.R.read(source,'terminal.json');tp=R.sha(terminal)
 ok(desc['dtype']==dtype and desc['shape']==[rows,32]);ok(sorted(p.name for p in source.iterdir())==sorted(p.name for p in dest.iterdir()))
 for p in sorted(source.iterdir()):
  q=dest/p.name;b=R.R.read(source,p.name);c=R.R.read(dest,p.name);ok(b==c);ok(stat.S_IMODE(q.lstat().st_mode)==0o600 and q.stat().st_nlink==1)
 parts=[];proof=R.C.verify_stream(lambda n:R.R.read(dest,n),tp,desc,parts.append)
 expected=bytes(range(128))*(rows*(2 if dtype=='<f8' else 1));ok(b''.join(parts)==expected and proof['raw_sha256']==R.sha(expected))
 inv=R.inspect(dest,R.sha(label.encode()),desc,tp)
 rawrows=[f for f in inv.files if f.kind=='chunk'];off=0
 for f in rawrows:
  ok(f.raw_offset==off and f.raw_size>0);frame=R.R.read(dest,f.name);body=frame[R.C.HEADER.size:-32];ok(R.sha(body)==f.raw_sha256);off+=len(body)
 ok(off==len(expected));observations.append({'dtype':dtype,'files':len(inv.files),'raw_bytes':off,'exact_mode_headers_order_whole_recovery':True})
# Real primary callback error + real final recovered-store close secondary;
# all actual partial output is retained, primary fatal is never replaced.
def mkdir(n):p=H/n;p.mkdir(mode=0o700);return p
smallsource=mkdir('fatal-source04');d=dict(schema_version=1,kind='mcm-batch-output-bytes',role='mcm-output',dtype='<f4',shape=[1,32],order='C',scope={k:'a'*64 for k in R.C.SCOPE},motifs=32,spent_samples=512)
with R.L.LocalStore(smallsource) as store:terminal=R.C.encode_stream(io.BytesIO(bytes(range(128))),d,store.put)
i=R.inspect(smallsource,'f'*64,d,terminal);route=R.route((i,),2)
for x,primary_type in enumerate((MemoryError,KeyboardInterrupt,SystemExit)):
 for y,secondary_type in enumerate((OSError,MemoryError,KeyboardInterrupt)):
  router=R.Router(mkdir('fatal-ledger-%d-%d'%(x,y)),route,*R.estimate(route));sp=tuple(mkdir('fatal-spool-%d-%d-%d'%(x,y,p.index)) for p in route.partitions);rec=(mkdir('fatal-recovered-%d-%d'%(x,y)),)
  oldinit=R.L.LocalStore.__init__;realclose=os.close;captured=[];closed=[];primary=primary_type('original callback');secondary=secondary_type('after real recovered close')
  def init(s,*a,**kw):oldinit(s,*a,**kw);captured.append(s.fd)
  def close(fd):
   realclose(fd)
   if captured and fd==captured[0] and not closed:closed.append(fd);raise secondary
  def send(*args):raise primary
  try:
   R.L.LocalStore.__init__=init;os.close=close
   try:router.run(sp,rec,send,None)
   except BaseException as error:ok(error is primary)
   else:raise AssertionError('fatal disappeared')
  finally:R.L.LocalStore.__init__=oldinit;os.close=realclose
  ok(router.failed and not router.finished and router.consumed==R.estimate(route));ok(len(closed)==1)
  try:os.fstat(closed[0])
  except OSError:ok(True)
  else:raise AssertionError('owned fd leaked')
  ok((router.root/'failed.json').is_file() and not (router.root/'complete.json').exists());router.close()
ok(all(n not in sys.modules for n in ('numpy','torch','pandas','tradingagents.research.lifecycle')))
(H/'INDEPENDENT04.json').write_text(json.dumps({'checks':checks,'observations':observations,'fatal_pairs':9,'actual_external_or_numerical_execution':False},sort_keys=True,indent=2)+'\n');print(checks,'checks passed')
