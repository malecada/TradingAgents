import gzip,hashlib,json,os,sys
from pathlib import Path
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O.parent/'held-consumer-final-recovery-preparation04-2026-10-03'));import recovery04 as R
T=O/'framing';T.mkdir(mode=0o700);u=T/'original';u.mkdir(mode=0o700);p=u/'body';p.write_bytes(b'tiny opaque');p.chmod(0o600);m=R.scan(u);info=R.pack(u,m,T/'valid.tar.gz');valid=(T/'valid.tar.gz').read_bytes();plain=gzip.decompress(valid);cases={}
# Keep descriptor honest for each altered local byte fixture so parsing checks, not hash mismatch, decide refusal.
for label in ['checksum','type','footer']:
 if label=='footer':raw=valid[:-8]
 else:
  data=bytearray(plain)
  if label=='checksum':data[0]^=1
  else:
   data[156]=ord('2');data[148:156]=b'        ';data[148:156]=('%06o\0 '%sum(data[:512])).encode()
  raw=gzip.compress(bytes(data),mtime=0)
 path=T/(label+'.tar.gz');path.write_bytes(raw);path.chmod(0o600);out=T/label;out.mkdir(mode=0o700);descriptor=dict(info,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
 try:R.restore(path,descriptor,m,out)
 except (ValueError,OSError,EOFError) as e:cases[label]={'type':type(e).__name__,'reason':str(e),'retained_files':sorted(p.name for p in out.iterdir())}
 else:raise AssertionError('malformed accepted '+label)
(O/'FRAMING_CONTROLS03.json').write_bytes(R.encode({'tiny_only':True,'cases':cases,'actual_Root_capture':False}));print(json.dumps(cases))
