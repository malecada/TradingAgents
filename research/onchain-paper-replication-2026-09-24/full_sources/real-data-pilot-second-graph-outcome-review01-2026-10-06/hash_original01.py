"""Exactly one opaque streaming pass over six terminal May9 original bodies."""
import ast,datetime,hashlib,json,os,stat,struct,time
from pathlib import Path
D=Path(__file__).resolve().parent;M=D.parents[3];ID='eth-paper-real-pilot-graph-20220509-20261005-01';SOURCE='b794d60df4e898d0832fee485ed4e6630b30f4df'
R=M/'research_runs'/ID;S=M/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/ID
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def metadata(p):
 p=Path(p);assert p.resolve()==p and p.lstat().st_size<=4*1024**2 and stat.S_ISREG(p.lstat().st_mode)
 raw=p.read_bytes();return json.loads(raw),sha(raw)
def sig(s):return [s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def npy_header(first,size):
 assert first[:6]==b'\x93NUMPY' and first[6:8] in (b'\x01\x00',b'\x02\x00')
 width=2 if first[6:8]==b'\x01\x00' else 4;length=struct.unpack('<H' if width==2 else '<I',first[8:8+width])[0]
 assert 0<length<=10000 and 8+width+length<=size
 offset=8+width+length;raw=first[8+width:offset];assert raw.endswith(b'\n')
 tree=ast.parse(raw.decode('latin1').strip(),mode='eval');assert len(list(ast.walk(tree)))<=32 and isinstance(tree.body,ast.Dict)
 assert len(tree.body.keys)==3 and all(isinstance(k,ast.Constant) for k in tree.body.keys) and {k.value for k in tree.body.keys}=={'descr','shape','fortran_order'}
 h=ast.literal_eval(tree);assert h['fortran_order'] is False and type(h['shape']) is tuple and all(type(n) is int and n>0 for n in h['shape'])
 return {'descr':h['descr'],'shape':list(h['shape']),'fortran_order':False,'header_bytes':offset,'header_sha256':sha(first[:offset]),'method':'bounded header captured during the sole opaque full-body hash pass'}
claim,claimsha=metadata(R/'claim.json');complete,terminalsha=metadata(R/'complete.json');index,indexsha=metadata(R/'outputs/artifact-index.json');manifest,manifestsha=metadata(S/'graph-2022-05-09/manifest.json')
assert claimsha==complete['claim_sha256']=='b9ac2065d853dafa23ed02216f6f929baed01209e6199130e6ec4801b1f77254' and claim['source']==complete['source']==SOURCE and complete['status']=='complete'
assert indexsha==complete['output_sha256']['artifact-index.json']=='db2fc69adf28438805e3952ae8943c0d2da56909ae771b5db4766c91d4c89dd2'
assert manifestsha==complete['cells'][1]['manifest_sha256']=='a05d237ea6803c323e13e8294d8dad9c89a1221a42b7df4a2e6550c054374aec'
assert set(manifest['arrays'])=={'node_features','node_ids','edge_index','edge_features','edge_aggregates'}
paths=[S/'aggregation/ledger.sqlite']
for name,a in sorted(manifest['arrays'].items()):
 assert a['path']==name+'.npy';p=S/'graph-2022-05-09'/a['path'];assert index[str(p.relative_to(M))]=={'bytes':a['bytes'],'sha256':a['sha256']};paths.append(p)
assert len(set(paths))==6
rows=[];began=time.monotonic()
with (D/'HASH_ONCE_STARTED01.json').open('x') as f:json.dump({'source':SOURCE,'claim_sha256':claimsha,'terminal_sha256':terminalsha,'index_sha256':indexsha,'paths':[str(p.relative_to(M)) for p in paths]},f)
try:
 for path in paths:
  assert path.resolve()==path;rel=str(path.relative_to(M));expected=index[rel]
  fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
  try:
   before=os.fstat(fd);assert stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size==expected['bytes'] and sig(before)==sig(path.lstat())
   digest=hashlib.sha256();count=0;header=None
   while True:
    raw=os.read(fd,1024**2)
    if not raw:break
    if count==0 and path.suffix=='.npy':header=npy_header(raw,before.st_size)
    digest.update(raw);count+=len(raw)
   assert count==expected['bytes'] and digest.hexdigest()==expected['sha256']
   after=os.fstat(fd);assert sig(before)==sig(after)==sig(path.lstat()) and stat.S_IMODE(before.st_mode)==stat.S_IMODE(path.lstat().st_mode)
   row={'path':rel,'bytes':count,'sha256':digest.hexdigest(),'mode':stat.S_IMODE(before.st_mode),'stat_identity':sig(before)}
   if header is not None:row['header']=header
   rows.append(row)
  finally:os.close(fd)
 result={'decision':'pass','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':SOURCE,'claim_sha256':claimsha,'terminal_sha256':terminalsha,'index_sha256':indexsha,'graph_manifest_sha256':manifestsha,'files':rows,'total_bytes':sum(r['bytes'] for r in rows),'elapsed_seconds':time.monotonic()-began,'full_body_passes':1,'buffer_bytes':1024**2,'qualification':'Opaque complete bytes streamed exactly once; only bounded original NPY headers parsed. No array values decoded, numerical imports or graph construction/semantic recomputation.'}
 with (D/'ORIGINAL_BODY_HASH01.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps({k:result[k] for k in ('decision','total_bytes','elapsed_seconds')}))
except BaseException as e:
 with (D/'HASH_FAILED01.json').open('x') as f:json.dump({'decision':'failed','completed_rows':rows,'error':repr(e)},f,indent=2)
 raise
