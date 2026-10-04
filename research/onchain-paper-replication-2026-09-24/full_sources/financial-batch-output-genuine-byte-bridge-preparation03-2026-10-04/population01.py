import io,json,os
from pathlib import Path
import byte_bridge01 as B,codec01 as C,local_store01 as L,recovery04 as R
H=Path(__file__).resolve().parent;rows=[]
for case in ('intact','changed','missing','extra','mode','replaced'):
 root=H/('population-'+case);root.mkdir(mode=0o700);dest=root/'codec';dest.mkdir(mode=0o700);raw=bytes(range(128));desc={'schema_version':1,'kind':'mcm-batch-output-bytes','role':'mcm-output','dtype':'<f4','shape':[1,32],'order':'C','scope':{k:B.digest(k.encode()) for k in C.SCOPE},'motifs':32,'spent_samples':512}
 with L.LocalStore(dest) as store:
  pin=C.encode_stream(io.BytesIO(raw),desc,store.put,chunk_bytes=32);before=B._codec_population(store,R);store.verify(pin,desc);p=dest/'chunk-00000.bin';body=p.read_bytes()
  if case=='changed':
   with p.open('r+b') as f:f.seek(C.HEADER.size);f.write(b'\xff');f.flush();os.fsync(f.fileno())
  elif case=='missing':p.rename(root/'retained-missing')
  elif case=='extra':(dest/'extra').write_bytes(b'x')
  elif case=='mode':p.chmod(0o640)
  elif case=='replaced':p.rename(root/'retained-replaced');p.write_bytes(body);p.chmod(0o600)
  error=None
  try:B.require(B._codec_population(store,R)==before,'changed complete population')
  except ValueError as e:error=str(e)
  assert bool(error)==(case!='intact');rows.append({'case':case,'refusal':error,'all_original_bytes_retained':True})
(H/'POPULATION01.json').write_text(json.dumps(rows,indent=2)+'\n');print('6 population cases')
