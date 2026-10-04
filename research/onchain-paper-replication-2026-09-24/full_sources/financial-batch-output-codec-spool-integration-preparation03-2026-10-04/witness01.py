import dataclasses as D,importlib.util,io,json,os,sys
from pathlib import Path
import router06 as new
P=Path(__file__).resolve().parent;oldpath=P.with_name('financial-batch-output-codec-spool-integration-preparation01-2026-10-04')/'router04.py'
spec=importlib.util.spec_from_file_location('original_router04',oldpath);old=importlib.util.module_from_spec(spec);sys.modules[spec.name]=old;spec.loader.exec_module(old)
results=[]
def mkdir(n):p=P/n;p.mkdir(mode=0o700);return p
for label,A in (('old',old),('new',new)):
 source=mkdir(label+'-source');raw=bytes(range(128));desc={'schema_version':1,'kind':'mcm-batch-output-bytes','role':'mcm-output','dtype':'<f4','shape':[1,32],'order':'C','scope':{k:'a'*64 for k in A.C.SCOPE},'motifs':32,'spent_samples':512}
 with A.L.LocalStore(source) as s:pin=A.C.encode_stream(io.BytesIO(raw),desc,s.put,chunk_bytes=32)
 inv=A.inspect(source,'b'*64,desc,pin)
 bad=D.replace(inv,files=tuple(D.replace(f,mode=float(f.mode)) for f in inv.files));error=None
 try:A.current(bad)
 except BaseException as e:error=e
 assert (error is None)==(label=='old')
 results.append({'source':label,'finding':'IR1','current_accepted':error is None,'error':None if error is None else str(error)})
 if label=='old':
  badroute=A.route((bad,),4);badrouter=A.Router(mkdir('old-malformed-ledger'),badroute,*A.estimate(badroute));bs=tuple(mkdir('old-malformed-spool-'+str(i)) for i in range(len(badroute.partitions)));br=(mkdir('old-malformed-recovery'),)
  mem={}
  def send(env,b):
   mem[env.pin()]=b;m=env.spool_member;return A.RoutedAck(env.pin(),A.S.Ack(env.spool_plan_sha256,m.page,m.chunk,m.size,m.sha256,'c'*64))
  def recover(env,ack):return A.RoutedRecovery(env.pin(),ack.ack,mem[env.pin()])
  badrouter.run(bs,br,send,recover);assert badrouter.finished;badrouter.close();results[-1]['full_old_pipeline_finished']=True
 route=A.route((inv,),4);router=A.Router(mkdir(label+'-close-ledger'),route,*A.estimate(route));sr=tuple(mkdir(label+'-close-spool-'+str(i)) for i in range(len(route.partitions)));rr=(mkdir(label+'-close-recovered'),)
 original=router.consumed;rid=(rr[0].stat().st_dev,rr[0].stat().st_ino);realclose=os.close;originalinit=A.L.LocalStore.__init__;storefd=[None];events=[];mem={}
 def send(env,b):
  mem[env.pin()]=b;m=env.spool_member;return A.RoutedAck(env.pin(),A.S.Ack(env.spool_plan_sha256,m.page,m.chunk,m.size,m.sha256,'c'*64))
 def recover(env,ack):return A.RoutedRecovery(env.pin(),ack.ack,mem[env.pin()])
 def init(s,*args,**kwargs):originalinit(s,*args,**kwargs);storefd[0]=s.fd
 def close(fd):
  try:s=os.fstat(fd);chosen=(s.st_dev,s.st_ino)==rid
  except OSError:chosen=False
  realclose(fd)
  if fd==storefd[0] and chosen and not events:
   p=rr[0]/'chunk-00000.bin';b=p.read_bytes();p.write_bytes(b[:-1]+bytes([b[-1]^1]));events.append('one-use corruption after real inode-qualified close')
 error=None
 try:
  A.L.LocalStore.__init__=init;os.close=close;router.run(sr,rr,send,recover)
 except BaseException as e:error=e
 finally:A.L.LocalStore.__init__=originalinit;os.close=realclose
 assert len(events)==1 and router.consumed==original
 assert router.finished==(label=='old') and (error is None)==(label=='old')
 assert (router.root/'complete.json').exists()==(label=='old')
 if label=='new':assert router.failed and (router.root/'failed.json').exists()
 try:A.C.verify_stream(lambda n:A.R.read(rr[0],n),pin,desc)
 except ValueError as e:after=str(e)
 else:raise AssertionError('missing corruption refusal')
 A.current(inv)
 results.append({'source':label,'finding':'IR2','finished':router.finished,'failed':router.failed,'error':None if error is None else str(error),'events':events,'actual_postrun_codec_refusal':after,'complete_marker':(router.root/'complete.json').exists(),'failed_marker':(router.root/'failed.json').exists(),'source_unchanged':True,'consumed_unchanged':True,'continuous_immunity_claim':False});router.close()
(P/'WITNESS01.json').write_text(json.dumps(results,sort_keys=True,indent=2)+'\n');print(len(results),'old/new witnesses passed')
