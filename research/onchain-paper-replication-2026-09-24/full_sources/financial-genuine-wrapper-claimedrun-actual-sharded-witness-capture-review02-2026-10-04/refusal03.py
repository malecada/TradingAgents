import gzip,hashlib,io,json,sys,tarfile,traceback
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;R=B/'financial-genuine-wrapper-root-claimedrun-sharded-witness-capture02-2026-10-04';sys.path.insert(0,str(B/'held-consumer-final-recovery-preparation04-2026-10-03'));import recovery04 as a
results=[]
for name in ['shards/shard-0035.tar.gz','shards/shard-0049.tar.gz']:
 raw=a.read(R,name);yielded=0
 try:
  for row in a.framed_members(raw):yielded+=1
 except ValueError as e:
  assert str(e)=='noncanonical raw member slash/type';results.append({'actual_archive':name,'sha256':hashlib.sha256(raw).hexdigest(),'yielded_before_refusal':yielded,'exception_type':type(e).__name__,'exception':str(e)})
 else:raise AssertionError('actual R4 did not refuse')
# Small independent canonical PAX reproduction, no real restore or Root write.
name='a'*99+'/file';out=io.BytesIO()
with gzip.GzipFile(fileobj=out,mode='wb',filename='',mtime=0) as gz:
 with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
  t=tarfile.TarInfo(name);t.mode=384;t.size=1;tf.addfile(t,io.BytesIO(b'x'))
raw=out.getvalue();(H/'tiny-canonical-pax03.tar.gz').write_bytes(raw)
try:list(a.framed_members(raw))
except ValueError as e:
 assert str(e)=='noncanonical raw member slash/type';results.append({'owned_tiny_sha256':hashlib.sha256(raw).hexdigest(),'full_path':name,'exception_type':type(e).__name__,'exception':str(e)})
else:raise AssertionError('tiny canonical did not reproduce')
# Standard bounded single-tiny parse confirms regular full path; no extraction.
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tf:
 rows=tf.getmembers();assert len(rows)==1 and rows[0].name==name and rows[0].isreg();assert tf.extractfile(rows[0]).read()==b'x'
(H/'REFUSAL03.json').write_text(json.dumps({'decision':'UNCHANGED_R4_COMPATIBILITY_WITHHELD','primitives_unchanged':True,'actual_restore_executed':False,'reproductions':results},sort_keys=True,indent=2)+'\n');print(json.dumps(results))
