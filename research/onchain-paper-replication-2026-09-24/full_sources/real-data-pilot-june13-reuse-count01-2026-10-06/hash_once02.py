"""Single authorized opaque integrity pass, no numerical imports or run authority."""
import ast,datetime,hashlib,json,math,os,stat,struct,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
MP=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-02/2022-06-13/decode_graph/graph/manifest.json'
EXPECTED='a7599cb4dce5a3d7b01614fe097026e70d48ecd63bb1c25518ccb05f41204d59'
def sig(s):return [s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def need(v,msg):
 if not v:raise ValueError(msg)
def exact(fd,n):
 out=bytearray()
 while len(out)<n:
  part=os.read(fd,n-len(out));need(part,'truncated header');out.extend(part)
 return bytes(out)
def header(fd,extent,name):
 prefix=exact(fd,8);need(prefix[:6]==b'\x93NUMPY' and prefix[6:] in (b'\x01\x00',b'\x02\x00'),'original NPY version required')
 width=2 if prefix[6:]==b'\x01\x00' else 4;lr=exact(fd,width);n=struct.unpack('<H' if width==2 else '<I',lr)[0]
 need(0<n<=10000 and 8+width+n<=extent,'bounded header required');body=exact(fd,n);need(body.endswith(b'\n'),'header newline')
 tree=ast.parse(body.decode('latin1').strip(),mode='eval');need(len(list(ast.walk(tree)))<=32 and isinstance(tree.body,ast.Dict),'bounded literal')
 keys=tree.body.keys;need(len(keys)==3 and all(isinstance(k,ast.Constant) and type(k.value) is str for k in keys) and {k.value for k in keys}=={'descr','fortran_order','shape'},'exact header keys')
 q=ast.literal_eval(tree);shape=q['shape'];need(q['fortran_order'] is False and type(shape) is tuple and len(shape)==2 and all(type(i) is int and 0<i<2**63 for i in shape),'shape differs')
 need((name=='node_features' and q['descr']=='<f8' and shape[1]==4) or (name=='edge_index' and q['descr']=='<i8' and shape[0]==2),'original descriptor differs')
 raw=prefix+lr+body;need(len(raw)+math.prod(shape)*8==extent,'header/extent differs')
 return raw,{'shape':list(shape),'descr':q['descr'],'fortran_order':False,'header_bytes':len(raw),'header_sha256':hashlib.sha256(raw).hexdigest(),'captured_header_hex':raw.hex()}
def put(name,value):
 with (HERE/name).open('x') as out:json.dump(value,out,sort_keys=True,indent=2);out.write('\n');out.flush();os.fsync(out.fileno())
start=time.monotonic();mr=MP.read_bytes();need(hashlib.sha256(mr).hexdigest()==EXPECTED,'manifest changed');m=json.loads(mr)
need(set(m['arrays'])=={'edge_aggregates','edge_features','edge_index','node_features','node_ids'},'five original arrays required')
put('PASS_STARTED02.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manifest_sha256':EXPECTED,'buffer_bytes':1048576,'scope':'exact five original arrays, one opaque pass; two headers captured in same stream'})
rows=[]
try:
 for name,a in sorted(m['arrays'].items()):
  p=MP.parent/a['path'];need(a['path']==name+'.npy' and p.resolve(strict=True)==p,'canonical original member required');pre=p.lstat()
  need(stat.S_ISREG(pre.st_mode) and pre.st_nlink==1 and pre.st_size==a['bytes'],'original regular extent/link mismatch')
  fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
  try:
   opened=os.fstat(fd);need(sig(pre)==sig(opened) and pre.st_mode==opened.st_mode,'open identity changed');h=hashlib.sha256();count=0;obs=None
   if name in ('node_features','edge_index'):
    raw,obs=header(fd,pre.st_size,name);h.update(raw);count+=len(raw)
   while True:
    chunk=os.read(fd,1048576)
    if not chunk:break
    count+=len(chunk);need(count<=pre.st_size,'body grew');h.update(chunk)
   post=os.fstat(fd);current=p.lstat();need(sig(pre)==sig(post)==sig(current) and pre.st_mode==post.st_mode==current.st_mode and p.resolve(strict=True)==p,'body identity changed')
   need(count==a['bytes'] and h.hexdigest()==a['sha256'],'original full body hash differs')
   row={'path':str(p.relative_to(ROOT)),'bytes':count,'sha256':h.hexdigest(),'mode':stat.S_IMODE(pre.st_mode),'stat_identity':sig(pre),'full_body_passes':1}
   if obs:row['header']=obs
   rows.append(row)
  finally:os.close(fd)
 need(MP.read_bytes()==mr,'manifest changed during pass');need(sum(r['bytes'] for r in rows)==474534176,'total differs')
 node=next(r for r in rows if r['path'].endswith('/node_features.npy'));edge=next(r for r in rows if r['path'].endswith('/edge_index.npy'))
 need(node['header']['shape'][0]==1768268 and edge['header']['shape'][1]==2518332,'historical count agreement differs')
 put('ORIGINAL_BODY_HASH02.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'decision':'pass','graph_manifest_sha256':EXPECTED,'graph_hash':m['graph_hash'],'buffer_bytes':1048576,'files':rows,'total_bytes':474534176,'full_body_passes':1,'elapsed_seconds':time.monotonic()-start,'nodes':node['header']['shape'][0],'directed_edges':edge['header']['shape'][1],'header_bytes_captured':sum(r.get('header',{}).get('header_bytes',0) for r in rows),'qualification':'Actual current opaque SHA-256 of every original member plus stable sampled path/descriptor identities and mode; two bounded original headers only. No payload values decoded, numerical modules, graph semantic recomputation, atomic writer exclusion, scientific completion or Owner/Binding authority.'})
 print(json.dumps({'decision':'pass','count':5,'bytes':474534176,'nodes':1768268,'edges':2518332,'elapsed_seconds':time.monotonic()-start}))
except BaseException as e:
 put('PASS_FAILED02.json',{'decision':'failed','completed_rows':rows,'error':type(e).__name__+': '+str(e),'no_automatic_retry':True});raise
