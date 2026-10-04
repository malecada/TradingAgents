import ast,copy,hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent
A=H.parent/'financial-genuine-wrapper-claimedrun-final-union-recovery-preparation02-2026-10-04'
sys.path.insert(0,str(A));import restore_sharded01 as M
R=M.R;checks=[]
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def refused(fn,n):
 try:fn()
 except (ValueError,KeyError,TypeError,OSError):ok(True,n)
 else:raise AssertionError(n)
def sha(b):return hashlib.sha256(b).hexdigest()
ok(sha((A/'MANIFEST01.json').read_bytes())=='6381d52f220a8a2669e8bb03a4614601e3a41ed916863a77a95bff78a3d4897a','frozen source manifest')
manifest=json.loads((A/'MANIFEST01.json').read_bytes());print('schema',manifest.keys())
for row in manifest['members']:
 p=A/row['path'];st=p.lstat();mode=row['mode'];mode=int(mode,8) if isinstance(mode,str) else mode
 ok(stat.S_IMODE(st.st_mode)==mode,'mode '+row['path'])
 if row['kind']=='file':b=p.read_bytes();ok(len(b)==row['bytes'] and sha(b)==row['sha256'],'body '+row['path'])
 elif row['kind']=='directory':ok(p.is_dir() and not p.is_symlink(),'dir '+row['path'])
 else:ok(p.is_symlink() and os.readlink(p)==row['target'],'literal '+row['path'])
ok(sha((A/'restore_sharded01.py').read_bytes())=='f0fa6231ed61dea322021e75578187c604633df21c3acee7eade4f0497e9cab7','exact adapter')
old=(A/'original-restore_union01.py').read_text();new=(A/'restore_sharded01.py').read_text();inv=json.loads((A/'INVERSE01.json').read_bytes());print('inverse schema',inv.keys())
for name,pin in M.PINS.items():ok(sha((A/name).read_bytes())==pin,'original primitive '+name)
fn=lambda s:{n.name:ast.get_source_segment(s,n) for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
for name in ('hashed','reference','contract','reserve','restore_ordinary','validate_expected_trees'):ok(fn(old)[name]==fn(new)[name],'unchanged '+name)
refused(lambda:M.request(json.loads((A/'REQUEST_TEMPLATE01.json').read_bytes())),'actual NULL request refuses')
expected=json.loads((A/'EXPECTED_ORIGINALS01.json').read_bytes());M.validate_expected_trees(expected['scope_trees']);ok(True,'exact original20 census')
for i in range(20):
 for kind in ('omit','extra','root','mode','body','link'):
  t=copy.deepcopy(expected['scope_trees']);rows=t[i]['members']
  if kind=='omit':rows.pop()
  elif kind=='extra':rows.append(copy.deepcopy(rows[-1]))
  elif kind=='root':t[i]['original_root']+='/redirect'
  elif kind=='mode':rows[0]['mode']^=1
  elif kind=='body':next(r for r in rows if r['kind']=='file')['sha256']='0'*64
  else:
   link=next((r for r in rows if r['kind']=='lexical-symlink'),None)
   if link is None:rows.append({'kind':'lexical-symlink','path':'extra','mode':511,'target':'literal'})
   else:link['target']+='changed'
  refused(lambda t=t:M.validate_expected_trees(t),'census '+str(i)+' '+kind)
# Real opaque author archives only, fresh reviewer-owned restoration, no request/release or Run.
root=A/'owned01';virtual=root/'tiny-virtual';m=R.scan(root/'shard-0000-source')
# Build complete tiny manifest from the two actual immutable shard manifests + empty dir metadata.
remote=root/'opaque-shard-input';prefix='research/opaque';rows={};shards=[]
for i in range(2):
 ident='shard-%04d'%i;mp=remote/'selected'/prefix/'shards'/(ident+'-manifest.json');sm=json.loads(mp.read_bytes());rows.update({r['path']:r for r in sm['members']})
rows['empty-retained']={'path':'empty-retained','kind':'directory','mode':448}
m={'schema_version':1,'root_mode':448,'members':[rows[k] for k in sorted(rows)]};plans=M.PLAN.partition(m)
for i,p in enumerate(plans):
 ident='shard-%04d'%i;ap=remote/'selected'/prefix/'shards'/(ident+'.tar.gz');mb=R.encode(p['manifest']);raw=ap.read_bytes()
 shards.append({**{k:v for k,v in p.items() if k!='manifest'},'id':ident,'manifest':{'path':'shards/'+ident+'-manifest.json','bytes':len(mb),'sha256':sha(mb)},'archive':{'path':'shards/'+ident+'.tar.gz','bytes':len(raw),'sha256':sha(raw),'manifest_sha256':sha(mb)}})
mb=R.encode(m);q={'manifest':{'path':prefix+'/union-manifest.json','bytes':len(mb),'sha256':sha(mb)},'shard_index':{'path':prefix+'/SHARD_INDEX01.json'},'expected_members':len(rows),'expected_files':261,'expected_logical_bytes':sum(r.get('bytes',0) for r in rows.values()),'expected_shards':2}
idx={'schema_version':1,'kind':'complete-final-union-shards-v1','virtual_manifest':{'path':'union-manifest.json','bytes':len(mb),'sha256':sha(mb)},'limits':{'logical_bytes':2097152,'typed_members':256,'archive_bytes':4194304},'regular_bodies':261,'shards':shards}
M.validate_index(q,m,R.encode(idx));ok(True,'independent index reconstruction')
for field in ('regular_paths','members','regular_bodies','logical_bytes','tar_bytes_bound'):
 bad=copy.deepcopy(idx)
 if field=='regular_paths':bad['shards'][0][field].pop()
 else:bad['shards'][0][field]+=1
 refused(lambda:M.validate_index(q,m,R.encode(bad)),'index mutation '+field)
for kind in ('duplicate','omit','reverse'):
 bad=copy.deepcopy(idx)
 if kind=='duplicate':bad['shards'].append(bad['shards'][0])
 elif kind=='omit':bad['shards'].pop()
 else:bad['shards'].reverse()
 refused(lambda:M.validate_index(q,m,R.encode(bad)),'shard '+kind)
out=H/'fresh-flat';M.reserve(out);progress={};files,result=M.restore_shards(remote,q,m,idx,plans,out,lambda:None,progress)
ok(len(files)==261 and len(result)==2,'real complete2shard261body restore')
for name,ref in files.items():ok(R.read(out/ref['shard'],ref['file'])==R.read(virtual,name),'real body '+name)
partial=H/'partial-flat';M.reserve(partial);bad=copy.deepcopy(idx);bad['shards'][1]['archive']['sha256']='0'*64;progress={}
refused(lambda:M.restore_shards(remote,q,m,bad,plans,partial,lambda:None,progress),'second corruption refuses')
ok(set(progress)=={'shard-0000'} and (partial/'shard-0001').is_dir(),'completed first/partial second retained')
for firstcls in (MemoryError,KeyboardInterrupt):
 for secondcls in (OSError,MemoryError,KeyboardInterrupt):
  fd=os.open(H/'fd-witness',os.O_CREAT|os.O_WRONLY,0o600);first=firstcls('original');second=secondcls('close');events=[]
  def close():os.close(fd);events.append('close');raise second
  def final():events.append('final')
  try:
   try:raise first
   finally:R._cleanup((close,final))
  except BaseException as e:ok(e is first,'actual first fatal retained')
  ok(events==['close','final'] and not Path('/proc/self/fd/'+str(fd)).exists(),'real fd closed and every cleanup')
ok(not any(k in sys.modules for k in ('numpy','torch','pandas','scipy')),'no numerical imports')
(H/'CHECKS01.json').write_text(json.dumps({'checks':len(checks),'names':checks,'actual_root_restore':False},indent=2)+'\n');print('PASS',len(checks))
