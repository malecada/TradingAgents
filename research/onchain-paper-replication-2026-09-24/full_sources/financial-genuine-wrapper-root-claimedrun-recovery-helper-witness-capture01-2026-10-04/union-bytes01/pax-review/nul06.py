import gzip,hashlib,io,json,sys,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-genuine-wrapper-claimedrun-witness-pax-framer-correction-preparation01-2026-10-04';sys.path.insert(0,str(A));import recovery_pax01 as N
from owned_io import CleanupFailure
out=io.BytesIO()
with gzip.GzipFile(fileobj=out,mode='wb',mtime=0,filename='') as gz:
 with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
  t=tarfile.TarInfo('a\x00b');t.mode=384;t.size=1;tf.addfile(t,io.BytesIO(b'x'))
raw=out.getvalue();p=H/'noncanonical-nul06.tar.gz';p.write_bytes(raw);m={'schema_version':1,'root_mode':448,'members':[{'path':'a','kind':'file','mode':384,'bytes':1,'sha256':hashlib.sha256(b'x').hexdigest()}]};info={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'manifest_sha256':hashlib.sha256(N.encode(m)).hexdigest()};flat=H/'nul06-flat';flat.mkdir(mode=0o700)
try:N.restore(p,info,m,flat)
except (ValueError,CleanupFailure) as e:q={'control':'Raw NUL terminates the name at a; full canonical reencoding must reject extra raw bytes b','exception':type(e).__name__,'message':str(e),'causes':[str(x) for x in getattr(e,'failures',())]}
else:raise AssertionError('raw noncanonical NUL unexpectedly restored')
(H/'NUL06.json').write_text(json.dumps(q,sort_keys=True,indent=2)+'\n');print('PASS full raw NUL canonical refusal')
