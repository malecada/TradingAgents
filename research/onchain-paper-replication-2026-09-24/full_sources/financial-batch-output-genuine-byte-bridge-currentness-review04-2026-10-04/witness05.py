import ast,json,os,pathlib,sys,hashlib,time
D=pathlib.Path(__file__).resolve().parent;P=D.parent/'financial-batch-output-genuine-byte-bridge-preparation03-2026-10-04';sys.path.insert(0,str(P))
import byte_bridge01 as B,codec01 as C,local_store01 as L,recovery04 as R,owned_io as IO
src=(P/'byte_bridge01.py').read_bytes();e=next(n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef)and n.name=='_encode');t=next(n for n in e.body if isinstance(n,ast.Try));nodes=t.body[-6:-1]
assert ast.unparse(nodes[0]).startswith('codec_before = ')
code=compile(ast.Module(body=nodes,type_ignores=[]),'<exact bridge03 final opaque utility tail>','exec');text=ast.unparse(ast.Module(body=nodes,type_ignores=[]));(D/'EXACT_TAIL05.py').write_text(text+'\n')
rows=[]
for i in range(4):
 root=D/('intact-%03d'%i);root.mkdir(mode=0o700);dest=root/'codec';dest.mkdir(mode=0o700);summary=root/'complete.json';site='none'
 raw=b'opaque0123456789'*16;d={'schema_version':1,'kind':'mcm-batch-output-bytes','role':'score-batches','dtype':'<f8','shape':[1,32],'order':'C','scope':{k:B.digest(k.encode())for k in C.SCOPE},'motifs':32,'spent_samples':512}
 cur=B.Cursor([('raw',len(raw),B.digest(raw))],8,lambda n,o,c:raw[o:o+c],lambda:None)
 with L.LocalStore(dest)as store:
  pin=C.encode_stream(cur,d,store.put,chunk_bytes=256);proof=store.verify(pin,d);done=cur.completion();first=dest/'chunk-00000.bin';last=first;original=first.read_bytes();events=[];realclose=os.close
  body=B.canonical({'kind':'opaque-tail-not-research','terminal':pin});B._write(R,IO,summary,body)
  # Legitimate identical-byte rewrite immediately before the sampled final tail.
  # No timestamp reset: this establishes a fresh real fingerprint with unchanged
  # original byte proof. Half the cases omit even this extra same-byte write.
  rewrite=(i//2)%2==0
  if rewrite:
   with first.open('r+b')as f:f.write(original);f.flush();os.fsync(f.fileno())
  before_hash=B.digest(original)
  def close(fd):
   info=os.fstat(fd);target=last if site=='verify'else summary;s=target.stat();match=(info.st_dev,info.st_ino)==(s.st_dev,s.st_ino);realclose(fd)
   if match and not events:
    events.append({'fd':fd,'dev':info.st_dev,'inode':info.st_ino,'site':site,'before_mutation':R.sig(first.stat())})
    with first.open('r+b')as f:f.seek(C.HEADER.size);f.write(bytes([original[C.HEADER.size]^1]));f.flush();os.fsync(f.fileno())
    events[-1]['after_mutation']=R.sig(first.stat())
  def boundary():
   if site=='boundary':os.close=close
   try:assert R.read(root,'complete.json')==body;store.check()
   finally:
    if site=='boundary':os.close=realclose
  ns={'store':store,'terminal':pin,'descriptor':d,'proof':proof,'done':done,'require':B.require,'_codec_population':B._codec_population,'R':R,'boundary':boundary}
  if site=='verify':os.close=close
  try:
   try:exec(code,ns)
   except BaseException as err:failure=repr(err)
   else:failure=None
  finally:os.close=realclose
  before=ns.get('codec_before');after=B._codec_population(store,R);after_hash=B.digest(first.read_bytes())
  try:C.verify_stream(lambda n:R.read(dest,n),pin,d)
  except BaseException as err:independent=repr(err)
  else:independent=None
  assert len(events)==0 and before_hash==after_hash and independent is None and failure is None
  rows.append({'case':i,'site':site,'identical_byte_write_before_sample':rewrite,'tail_accepted':failure is None,'refusal':failure,'actual_before_population':before,'tail_before_population':ns.get('codec_before'),'actual_after_population':after,'all_population_equal':before==after==ns.get('codec_before'),'original_first_frame_sha256':before_hash,'current_first_frame_sha256':after_hash,'independent_verify_refusal':independent,'close_events':events,'original_proof':proof,'original_cursor_completion':done,'genuine_encode_executed':False})
(D/'WITNESSES05.json').write_bytes(json.dumps({'source_sha256':B.digest(src),'cases':rows,'accepted_intact':sum(x['tail_accepted']for x in rows),'boundary_scope':'real opaque summary readback/store checks only; not genuine Owner/Target boundary','no_timestamp_reset':True},sort_keys=True,separators=(',',':')).encode())
print(json.dumps({'cases':len(rows),'accepted_intact':sum(x['tail_accepted']for x in rows),'accepted_equal_population':sum(x['tail_accepted']and x['all_population_equal']for x in rows),'accepted_by_site':{s:sum(x['tail_accepted']and x['site']==s for x in rows)for s in ('verify','boundary')}}))
