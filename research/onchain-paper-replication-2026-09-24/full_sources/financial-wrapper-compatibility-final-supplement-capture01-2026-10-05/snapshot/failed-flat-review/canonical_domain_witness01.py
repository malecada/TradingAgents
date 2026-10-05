from pathlib import Path
import gzip,hashlib,io,json,tarfile,ast
H=Path(__file__).resolve().parent;D=H.parent/'financial-wrapper-compatibility-baseline-root-remote02-2026-10-05';q=json.loads((D/'ROOT_REQUEST_BASELINE01.json').read_bytes());b=q['bundles'][0];arc=(D/'selected'/b['archive']['path']).read_bytes();m=json.loads((D/'selected'/b['manifest']['path']).read_bytes());sha=lambda x:hashlib.sha256(x).hexdigest()
assert sha(arc)==b['archive']['sha256']
source=(D/'utilities/recovery_pax01.py').read_bytes();assert sha(source)=='a054d5922899b53579f4220ff3b427dc050dff075cb5470b43ff55e621b97eb2'
tree=ast.parse(source);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='flat_tar_stream');assert 'format=tarfile.PAX_FORMAT' in ast.get_source_segment(source.decode(),fn)
with tarfile.open(fileobj=io.BytesIO(arc),mode='r:gz') as t:bodies={r.name:t.extractfile(r).read() for r in t if r.isfile()}
def stream(fmt):
 out=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=fmt) as tar:
   for r in m['members']:
    t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
    if r['kind']=='directory':t.type=tarfile.DIRTYPE;t.size=0;tar.addfile(t)
    else:body=bodies[r['path']];assert len(body)==r['bytes'] and sha(body)==r['sha256'];t.size=len(body);tar.addfile(t,io.BytesIO(body))
 return out.getvalue()
ustar=stream(tarfile.USTAR_FORMAT);pax=stream(tarfile.PAX_FORMAT);assert ustar==arc and pax!=arc
origraw=gzip.decompress(arc);paxraw=gzip.decompress(pax);first=next(i for i,(x,y) in enumerate(zip(origraw,paxraw)) if x!=y);off=first//512*512
result={'schema_version':1,'finding':'BR_PAX_CANONICAL_DOMAIN01','actual_failure_cause_unchanged':'outer bounded changing-directory census failed; child was killed before this later canonical re-encoding','source_sha256':sha(source),'function':'flat_tar_stream','line':175,'archive_sha256':sha(arc),'actual_ustar_bytes':len(arc),'independent_ustar_reencoding_exact':True,'pax_reencoding_sha256':sha(pax),'pax_bytes':len(pax),'pax_uncompressed_bytes':len(paxraw),'original_uncompressed_bytes':len(origraw),'first_raw_difference':first,'original_header_at_difference_hex':origraw[off:off+512].hex(),'pax_header_at_difference_hex':paxraw[off:off+512].hex(),'paths_over_100_bytes':[r['path'] for r in m['members'] if len(r['path'].encode())>100],'conclusion':'Original ExactSink comparison will refuse the otherwise complete USTAR baseline after PAX re-encoding; valid original archive bytes remain unchanged. A separately reviewed format-aware restoration successor is needed.','actual_restore_executed':False,'numerical_authority':False}
with (H/'CANONICAL_DOMAIN_WITNESS01.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if not k.endswith('_hex') and k!='paths_over_100_bytes'}))
