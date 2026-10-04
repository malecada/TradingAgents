import dataclasses as D,hashlib,io,json,os,sys
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-batch-output-codec-spool-integration-preparation01-2026-10-04';sys.path.insert(0,str(A));import router04 as R
assert R.sha((A/'router04.py').read_bytes())=='24bb42b49baba8ea330ced3864d28019a5b30745d5739de3cafc2cbea8a74454'
def mkdir(n):p=H/('run02-'+n);p.mkdir(mode=0o700);return p
source=mkdir('source');raw=bytes(range(128));desc=dict(schema_version=1,kind='mcm-batch-output-bytes',role='mcm-output',dtype='<f4',shape=[1,32],order='C',scope={k:'a'*64 for k in R.C.SCOPE},motifs=32,spent_samples=512)
with R.L.LocalStore(source) as s:pin=R.C.encode_stream(io.BytesIO(raw),desc,s.put,chunk_bytes=32)
inv=R.inspect(source,'b'*64,desc,pin)
# Value equality permits malformed literal mode type in a real reconstructed
# inventory; no owner/admission/research object is instantiated.
bad=D.replace(inv,files=tuple(D.replace(f,mode=float(f.mode)) for f in inv.files))
R.current(bad);route=R.route((bad,),4);router=R.Router(mkdir('type-ledger'),route,*R.estimate(route));sr=tuple(mkdir('type-spool-%d'%p.index) for p in route.partitions);rr=(mkdir('type-recovered'),);memory={}
def send(env,b):memory[env.pin()]=b;m=env.spool_member;return R.RoutedAck(env.pin(),R.S.Ack(env.spool_plan_sha256,m.page,m.chunk,m.size,m.sha256,'c'*64))
def recover(env,a):return R.RoutedRecovery(env.pin(),a.ack,memory[env.pin()])
router.run(sr,rr,send,recover);assert router.finished and type(router.route.inventories[0].files[0].mode)is float
results={'IR1':{'malformed_mode_type':'float','mode_value':bad.files[0].mode,'current_accepted':True,'router_finished':router.finished,'actual_recovered_mode':(rr[0]/'start.json').stat().st_mode&0o777,'files':len(inv.files)}};router.close()
# Final recovered directory is fully verified while its store FD is live. A
# controlled real-close operation then changes a recovered body before complete.
route=R.route((inv,),4);router=R.Router(mkdir('close-ledger'),route,*R.estimate(route));sr=tuple(mkdir('close-spool-%d'%p.index) for p in route.partitions);rr=(mkdir('close-recovered'),);rid=(rr[0].stat().st_dev,rr[0].stat().st_ino);realclose=os.close;events=[]
def close(fd):
 try:s=os.fstat(fd);chosen=(s.st_dev,s.st_ino)==rid
 except OSError:chosen=False
 realclose(fd)
 # R.read also briefly opens this directory. Trigger only after final complete
 # inspect has returned: that final LocalStore.close's caller is __cleanup lambda
 # and its fd is the persistent LocalStore descriptor, recorded via constructor.
 if fd==storefd[0] and chosen and not events:
  p=rr[0]/'chunk-00000.bin';b=p.read_bytes();p.write_bytes(b[:-1]+bytes([b[-1]^1]));events.append('recovered body corrupted after real final close')
storefd=[None];originalinit=R.L.LocalStore.__init__
def init(s,*args,**kw):originalinit(s,*args,**kw);storefd[0]=s.fd
try:
 R.L.LocalStore.__init__=init;os.close=close;router.run(sr,rr,send,recover)
finally:R.L.LocalStore.__init__=originalinit;os.close=realclose
assert router.finished and events
try:R.C.verify_stream(lambda n:R.R.read(rr[0],n),pin,desc)
except ValueError as e:after=str(e)
else:raise AssertionError('expected recovered corruption refusal')
results['IR2']={'router_finished':router.finished,'complete_marker':(router.root/'complete.json').is_file(),'close_events':events,'post_return_actual_byte_verification':after,'actual_timed_race_claim':False};router.close()
(H/'WITNESSES02.json').write_text(json.dumps(results,sort_keys=True,indent=2)+'\n');print(json.dumps(results,sort_keys=True))
