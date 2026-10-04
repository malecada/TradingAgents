import ast,hashlib,json,os,io
from pathlib import Path
import byte_bridge01 as B,codec01 as C,local_store01 as L,recovery04 as R,owned_io as IO
H=Path(__file__).resolve().parent;rows=[]
tree=ast.parse((H/'byte_bridge01.py').read_bytes());enc=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_encode');tr=next(x for x in enc.body if isinstance(x,ast.Try));tail=tr.body[-3:-1];assert isinstance(tail[0],ast.Assign) and tail[0].targets[0].id=='final_proof';code=compile(ast.Module(body=tail,type_ignores=[]),'<exact new utility tail>','exec')
for label,change in [('old-corrupt',True),('new-corrupt',True),('new-valid',False)]:
 root=H/label;root.mkdir(mode=0o700);dest=root/'codec';dest.mkdir(mode=0o700);raw=bytes(range(256));d={'schema_version':1,'kind':'mcm-batch-output-bytes','role':'score-batches','dtype':'<f8','shape':[1,32],'order':'C','scope':{k:B.digest(k.encode()) for k in C.SCOPE},'motifs':32,'spent_samples':512}
 with L.LocalStore(dest) as store:
  pin=C.encode_stream(io.BytesIO(raw),d,store.put);proof=store.verify(pin,d);done={'bytes':256,'sha256':B.digest(raw)};chunk=dest/'chunk-00000.bin';before=chunk.read_bytes();path=root/'complete.json';body=B.canonical({'kind':'opaque-utility-tail-only','terminal':pin});close=os.close;events=[]
  def inject(fd):
   s=os.fstat(fd);match=path.exists() and (s.st_dev,s.st_ino)==(path.stat().st_dev,path.stat().st_ino);close(fd)
   if change and match and not events:
    events.append(fd)
    with chunk.open('r+b') as f:f.seek(C.HEADER.size);f.write(bytes([before[C.HEADER.size]^1]));f.flush();os.fsync(f.fileno())
  os.close=inject
  try:B._write(R,IO,path,body)
  finally:os.close=close
  store.check();error=None
  if label.startswith('new'):
   try:exec(code,{'store':store,'terminal':pin,'descriptor':d,'proof':proof,'done':done,'require':B.require})
   except ValueError as e:error=str(e)
  assert (error is not None)==(label=='new-corrupt');assert len(events)==int(change)
  if label=='old-corrupt':
   try:C.verify_stream(lambda n:R.read(dest,n),pin,d)
   except ValueError:pass
   else:raise AssertionError('original witness did not corrupt')
  rows.append({'case':label,'summary_cleanup_completed':True,'mutation_count':len(events),'new_tail_refusal':error,'genuine_encode_executed':False})
(H/'BB1_CONTROLS01.json').write_text(json.dumps(rows,indent=2)+'\n');print('3 exact utility tail cases passed')
