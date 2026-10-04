import ast,json,os,pathlib,sys
D=pathlib.Path(__file__).resolve().parent;P=D.parent/'financial-batch-output-genuine-byte-bridge-preparation02-2026-10-04';sys.path.insert(0,str(P))
import byte_bridge01 as B,codec01 as C,local_store01 as L,recovery04 as R,owned_io as IO
tr=next(x for x in ast.parse((P/'byte_bridge01.py').read_bytes()).body if isinstance(x,ast.FunctionDef)and x.name=='_encode');attempt=next(x for x in tr.body if isinstance(x,ast.Try));tail=attempt.body[-3:-1]
assert ast.unparse(tail[0]).startswith('final_proof = store.verify')
code=compile(ast.Module(body=tail,type_ignores=[]),'<exact candidate final tail>','exec');records=[]
for label,when in [('old-BB1','summary'),('new-BB1','summary'),('new-intact',None),('new-BB2','final-verification')]:
 root=D/label;root.mkdir(mode=0o700);dest=root/'codec';dest.mkdir(mode=0o700)
 raw=bytes(range(256))*2;desc={'schema_version':1,'kind':'mcm-batch-output-bytes','role':'score-batches','dtype':'<f8','shape':[2,32],'order':'C','scope':{k:B.digest(k.encode())for k in C.SCOPE},'motifs':32,'spent_samples':512}
 cur=B.Cursor([('raw',len(raw),B.digest(raw))],8,lambda n,o,c:raw[o:o+c],lambda:None)
 with L.LocalStore(dest)as store:
  pin=C.encode_stream(cur,desc,store.put,chunk_bytes=256);proof=store.verify(pin,desc);done=cur.completion()
  first=dest/'chunk-00000.bin';last=dest/'chunk-00001.bin';before=first.read_bytes();s=first.stat();before_sig=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  summary=root/'complete.json';body=B.canonical({'kind':'opaque-tail-witness-only','terminal':pin});realclose=os.close;events=[]
  def close(fd):
   s=os.fstat(fd);target=summary if when=='summary' else last
   match=target.exists()and(s.st_dev,s.st_ino)==(target.stat().st_dev,target.stat().st_ino)
   realclose(fd)
   if match and not events:
    events.append({'closed_fd':fd,'dev':s.st_dev,'inode':s.st_ino})
    with first.open('r+b')as f:f.seek(C.HEADER.size);f.write(bytes([before[C.HEADER.size]^1]));f.flush();os.fsync(f.fileno())
  if when=='summary':os.close=close
  try:B._write(R,IO,summary,body)
  finally:os.close=realclose
  store.check();error=None
  if label!='old-BB1':
   if when=='final-verification':os.close=close
   try:exec(code,{'store':store,'terminal':pin,'descriptor':desc,'proof':proof,'done':done,'require':B.require})
   except BaseException as e:error=type(e).__name__+': '+str(e)
   finally:os.close=realclose
  try:C.verify_stream(lambda n:R.read(dest,n),pin,desc)
  except ValueError as e:independent=str(e)
  else:independent=None
  assert bool(error)==(label=='new-BB1')
  assert bool(independent)==(when is not None)
  assert len(events)==int(when is not None)
  s=first.stat();records.append({'case':label,'final_tail_accepted':error is None,'refusal':error,'subsequent_independent_verify':independent,'events':events,'pre_signature':before_sig,'post_signature':(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns),'exact_tail':ast.unparse(ast.Module(body=tail,type_ignores=[])),'genuine_encode_executed':False})
with (D/'WITNESSES01.json').open('x')as f:json.dump(records,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps(records))
