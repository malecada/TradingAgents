import ast,json,os,pathlib,sys
D=pathlib.Path(__file__).resolve().parent;P=D.parent/'financial-batch-output-genuine-byte-bridge-preparation02-2026-10-04';sys.path.insert(0,str(P))
import byte_bridge01 as B,codec01 as C,local_store01 as L,recovery04 as R,owned_io as IO
enc=next(n for n in ast.parse((P/'byte_bridge01.py').read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name=='_encode');tr=next(n for n in enc.body if isinstance(n,ast.Try));code=compile(ast.Module(body=tr.body[-3:-1],type_ignores=[]),'<exact source tail>','exec');out=[]
for label in ['proof','bytes','hash','terminal','descriptor','extra','readfatal','closefatal']:
 root=D/('tail-'+label);root.mkdir(mode=0o700);raw=b'x'*256;d={'schema_version':1,'kind':'mcm-batch-output-bytes','role':'score-batches','dtype':'<f8','shape':[1,32],'order':'C','scope':{k:B.digest(k.encode())for k in C.SCOPE},'motifs':32,'spent_samples':512}
 cur=B.Cursor([('raw',256,B.digest(raw))],8,lambda n,o,c:raw[o:o+c],lambda:None)
 with L.LocalStore(root)as store:
  pin=C.encode_stream(cur,d,store.put);proof=store.verify(pin,d);done=cur.completion()
  if label=='proof':proof=dict(proof,representation_complete=True)
  elif label=='bytes':done=dict(done,bytes=255)
  elif label=='hash':done=dict(done,sha256='0'*64)
  elif label=='terminal':pin='0'*64
  elif label=='descriptor':d=dict(d,dtype='<f4')
  elif label=='extra':(root/'extra').write_bytes(b'x')
  read,close=os.read,os.close;primary=MemoryError('actual verifier IO fatal');secondary=RuntimeError('after actual verifier descriptor close');closed=[]
  def readfail(*a):raise primary
  def closefail(fd):
   close(fd);closed.append(fd)
   if len(closed)==1:raise primary if label=='closefatal' else secondary
  if label=='readfatal':os.read=readfail;os.close=closefail
  if label=='closefatal':os.close=closefail
  try:
   try:exec(code,{'store':store,'terminal':pin,'descriptor':d,'proof':proof,'done':done,'require':B.require})
   except BaseException as e:failure=e
   else:raise AssertionError('bad final tail accepted '+label)
  finally:os.read=read;os.close=close
  if label.endswith('fatal'):
   assert failure is primary and len(closed)==2 and store.poisoned
   for fd in closed:
    try:os.fstat(fd)
    except OSError:pass
    else:raise AssertionError('FD not drained')
  out.append({'case':label,'refusal':type(failure).__name__,'genuine_encode':False,'closed_fds':closed})
with (D/'TAIL_CONTROLS01.json').open('x')as f:json.dump(out,f,indent=2);f.write('\n')
print('8 exact final-tail refusal/fatal controls passed')
