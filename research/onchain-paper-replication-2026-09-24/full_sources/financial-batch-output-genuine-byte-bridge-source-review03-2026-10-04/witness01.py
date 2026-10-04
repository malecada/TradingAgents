import ast,json,os,pathlib,sys
D=pathlib.Path(__file__).resolve().parent;P=D.parent/'financial-batch-output-genuine-byte-bridge-preparation03-2026-10-04';O=D.parent/'financial-batch-output-genuine-byte-bridge-preparation02-2026-10-04';sys.path.insert(0,str(P))
import byte_bridge01 as B,codec01 as C,local_store01 as L,recovery04 as R,owned_io as IO
def tail(p,new):
 e=next(n for n in ast.parse((p/'byte_bridge01.py').read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name=='_encode');t=next(n for n in e.body if isinstance(n,ast.Try));nodes=t.body[-6:-1]if new else t.body[-3:-1]
 assert ast.unparse(nodes[0]).startswith('codec_before = 'if new else 'final_proof = ')
 return compile(ast.Module(body=nodes,type_ignores=[]),'<literal utility tail '+p.name+'>','exec'),ast.unparse(ast.Module(body=nodes,type_ignores=[]))
newcode,newtext=tail(P,True);oldcode,oldtext=tail(O,False);rows=[]
for label,site in [('old-BB2','verify'),('new-BB2','verify'),('new-BB1','summary'),('new-intact',None),('new-last-boundary','boundary')]:
 root=D/label;root.mkdir(mode=0o700);dest=root/'codec';dest.mkdir(mode=0o700);summary=root/'complete.json'
 raw=bytes(range(256))*2;d={'schema_version':1,'kind':'mcm-batch-output-bytes','role':'score-batches','dtype':'<f8','shape':[2,32],'order':'C','scope':{k:B.digest(k.encode())for k in C.SCOPE},'motifs':32,'spent_samples':512}
 cur=B.Cursor([('raw',len(raw),B.digest(raw))],8,lambda n,o,c:raw[o:o+c],lambda:None)
 with L.LocalStore(dest)as store:
  pin=C.encode_stream(cur,d,store.put,chunk_bytes=256);proof=store.verify(pin,d);done=cur.completion();first=dest/'chunk-00000.bin';last=dest/'chunk-00001.bin';original=first.read_bytes();realclose=os.close;events=[]
  body=B.canonical({'kind':'opaque-utility-witness-not-research','terminal':pin})
  def close(fd):
   info=os.fstat(fd);target=last if site=='verify'else summary
   match=target.exists()and(info.st_dev,info.st_ino)==(target.stat().st_dev,target.stat().st_ino);realclose(fd)
   if match and not events:
    events.append({'fd':fd,'inode':info.st_ino})
    with first.open('r+b')as f:f.seek(C.HEADER.size);f.write(bytes([original[C.HEADER.size]^1]));f.flush();os.fsync(f.fileno())
  if site=='summary':os.close=close
  try:B._write(R,IO,summary,body)
  finally:os.close=realclose
  def opaque_boundary():
   # Utility readback only, never a replacement Owner/Target authority result.
   if site=='boundary':os.close=close
   try:assert R.read(root,'complete.json')==body;store.check()
   finally:
    if site=='boundary':os.close=realclose
  if site=='verify':os.close=close
  try:
   try:exec(oldcode if label=='old-BB2'else newcode,{'store':store,'terminal':pin,'descriptor':d,'proof':proof,'done':done,'require':B.require,'_codec_population':B._codec_population,'R':R,'boundary':opaque_boundary})
   except BaseException as e:failure=type(e).__name__+': '+str(e)
   else:failure=None
  finally:os.close=realclose
  assert (failure is None)==(label in ['old-BB2','new-intact'])
  assert len(events)==int(site is not None)
  try:C.verify_stream(lambda n:R.read(dest,n),pin,d)
  except ValueError as e:later=str(e)
  else:later=None
  assert (later is None)==(site is None)
  rows.append({'case':label,'refusal':failure,'independent_verify':later,'actual_one_use_closed_inode_events':events,'genuine_encode_executed':False})
with (D/'WITNESSES01.json').open('x')as f:json.dump({'cases':rows,'exact_old_tail':oldtext,'exact_new_tail':newtext,'boundary_callback_scope':'only actual opaque summary readback/store metadata; no genuine source authority simulated'},f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps(rows))
