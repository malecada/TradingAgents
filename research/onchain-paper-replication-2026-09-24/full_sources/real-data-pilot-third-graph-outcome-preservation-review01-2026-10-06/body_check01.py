from pathlib import Path
import ast,hashlib,json,os,stat,math
R=Path.cwd();N='eth-paper-real-pilot-graph-20220516-20261005-01';O=Path(__file__).parent
I=R/'research_runs'/N/'outputs/artifact-index.json';idx=json.loads(I.read_bytes());rows=[]
def ident(s):return [s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
for name,v in sorted(idx.items()):
 if not name.endswith(('.npy','ledger.sqlite')):continue
 p=R/name;s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==v['bytes'];sha=hashlib.sha256();prefix=b'';count=0
 with p.open('rb') as stream:
  assert ident(os.fstat(stream.fileno()))==ident(s)
  while chunk:=stream.read(1024*1024):
   if not prefix:prefix=chunk[:65536]
   sha.update(chunk);count+=len(chunk)
  assert ident(os.fstat(stream.fileno()))==ident(s)
 assert ident(p.lstat())==ident(s) and count==s.st_size and sha.hexdigest()==v['sha256']
 row={'path':name,'bytes':count,'sha256':sha.hexdigest(),'stat_identity':ident(s),'mode':stat.S_IMODE(s.st_mode)}
 if name.endswith('.npy'):
  assert prefix[:6]==b'\x93NUMPY';version=list(prefix[6:8]);length_bytes=2 if version==[1,0] else 4;assert version in ([1,0],[2,0],[3,0]);offset=8+length_bytes;length=int.from_bytes(prefix[8:offset],'little');assert length+offset<=len(prefix)
  meta=ast.literal_eval(prefix[offset:offset+length].decode('utf-8' if version==[3,0] else 'latin1'));assert set(meta)=={'descr','fortran_order','shape'} and meta['fortran_order'] is False
  dtype=meta['descr'];assert isinstance(dtype,str) and dtype[1] in 'fiuUS';item=int(dtype[2:])*(4 if dtype[1]=='U' else 1);assert offset+length+math.prod(meta['shape'])*item==count
  row['npy_header']={'version':version,'header_bytes':offset+length,**meta}
 rows.append(row);print(name.rsplit('/',1)[-1],count,flush=True)
assert len(rows)==6 and sum(r['bytes'] for r in rows)==3855665024
out={'decision':'pass','index_sha256':hashlib.sha256(I.read_bytes()).hexdigest(),'files':rows,'total_bytes':sum(r['bytes'] for r in rows),'one_streaming_pass_per_body':True,'headers_captured_same_pass':5,'numerical_imports':False,'raw_daily_body_reads':False}
(O/'BODY_HASH01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
