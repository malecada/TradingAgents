import dataclasses as D,importlib,io,json,os,sys
from pathlib import Path
H=Path(__file__).resolve().parent;old=sys.argv[1]=='old';tag='old' if old else 'new';A=H.parent/('financial-batch-output-codec-spool-integration-preparation01-2026-10-04' if old else 'financial-batch-output-codec-spool-integration-preparation02-2026-10-04');sys.path.insert(0,str(A));R=importlib.import_module('router04' if old else 'router05')
def mkdir(n):p=H/(tag+'-'+n);p.mkdir(mode=0o700);return p
source=mkdir('source');raw=bytes(range(128));desc=dict(schema_version=1,kind='mcm-batch-output-bytes',role='mcm-output',dtype='<f4',shape=[1,32],order='C',scope={k:'a'*64 for k in R.C.SCOPE},motifs=32,spent_samples=512)
with R.L.LocalStore(source) as s:pin=R.C.encode_stream(io.BytesIO(raw),desc,s.put,chunk_bytes=32)
inv=R.inspect(source,'b'*64,desc,pin);types=[]
for field,value in [('mode',384.0),('ordinal',False),('raw_offset',-1.0),('raw_size',False)]:
 f=D.replace(inv.files[0],**{field:value});bad=D.replace(inv,files=(f,)+inv.files[1:])
 try:R.current(bad);refused=False
 except ValueError:refused=True
 assert refused is (not old);types.append({'field':field,'type':type(value).__name__,'refused':refused})
route=R.route((inv,),4);router=R.Router(mkdir('ledger'),route,*R.estimate(route));sp=tuple(mkdir('spool-%d'%p.index) for p in route.partitions);rr=(mkdir('recovered'),);rid=(rr[0].stat().st_dev,rr[0].stat().st_ino);memory={}
def send(env,b):memory[env.pin()]=b;m=env.spool_member;return R.RoutedAck(env.pin(),R.S.Ack(env.spool_plan_sha256,m.page,m.chunk,m.size,m.sha256,'c'*64))
def recover(env,a):return R.RoutedRecovery(env.pin(),a.ack,memory[env.pin()])
realclose=os.close;oldinit=R.L.LocalStore.__init__;fds=[];events=[]
def init(s,*a,**kw):oldinit(s,*a,**kw);fds.append(s.fd)
def close(fd):
 try:s=os.fstat(fd);chosen=(s.st_dev,s.st_ino)==rid
 except OSError:chosen=False
 realclose(fd)
 if fds and fd==fds[0] and chosen and not events:
  p=rr[0]/'chunk-00000.bin';b=p.read_bytes();p.write_bytes(b[:-1]+bytes([b[-1]^1]));events.append('one real final close then byte mutation')
try:
 R.L.LocalStore.__init__=init;os.close=close
 try:router.run(sp,rr,send,recover);refused=False
 except ValueError:refused=True
finally:R.L.LocalStore.__init__=oldinit;os.close=realclose
assert refused is (not old) and len(events)==1 and router.finished is old
if not old:assert router.failed and (router.root/'failed.json').is_file() and not (router.root/'complete.json').exists()
out={'IR1':types,'IR2':{'refused':refused,'failed':router.failed,'finished':router.finished,'complete_exists':(router.root/'complete.json').exists(),'events':events,'no_timed_race_claim':True}};router.close();(H/('RED_GREEN_'+tag+'.json')).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out,sort_keys=True))
