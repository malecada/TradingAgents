import gzip,io,json,sys,tarfile
from pathlib import Path
O=Path(__file__).resolve().parent;P=O.parent/'held-consumer-post-outcome-archive-preparation01-2026-10-03';sys.path.insert(0,str(P));import recovery04 as R
out=[]
for name,kind,size in [('oversized-pax',tarfile.XHDTYPE,8193),('symlink',tarfile.SYMTYPE,0),('sparse',tarfile.GNUTYPE_SPARSE,0),('large-file',tarfile.REGTYPE,R.FILE+1)]:
 t=tarfile.TarInfo('././@PaxHeader' if kind==tarfile.XHDTYPE else 'opaque');t.type=kind;t.size=size;raw=gzip.compress(t.tobuf(format=tarfile.USTAR_FORMAT),mtime=0);(O/(name+'.gz')).write_bytes(raw)
 try:list(R.framed_members(raw))
 except ValueError as e:out.append({'case':name,'refusal':str(e)})
 else:raise AssertionError(name)
assert all('truncated' not in r['refusal'] for r in out)
(O/'FRAMING03.json').write_text(json.dumps(out,indent=2)+'\n');print('4 raw-header refusals before missing payload')
