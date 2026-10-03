from pathlib import Path,PurePosixPath
import ast,copy,gzip,hashlib,io,json,os,stat,subprocess,tarfile
R=Path(__file__).resolve().parent;ROOT=R.parents[3];A=R.parent/'held-consumer-final-baseline-root-remote-recovery02-2026-10-03';OLD=R.parent/'held-consumer-final-baseline-root-remote-recovery01-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes());COMMIT='d9ebc6cb0be3b3b5f7247ff486e44455136b21ef'
assert (ROOT/'AGENTS.md').exists()
receipt=J(A/'REMOTE_RECOVERY02.json');assert H((A/'REMOTE_RECOVERY02.json').read_bytes())=='e4c0d191f87816717e3239c627421d5096e79466f4234a85ed6d4cdaf610ea9d';selection=J(A/'SELECTED_BODIES02.json');assert H((A/'SELECTED_BODIES02.json').read_bytes())==receipt['selection_sha256']=='d55e093c8dccc7c1e13dbb8f78bc515b6968c74f8c668ed03de42ab3925975f1'
rows=selection['rows'];assert len(rows)==receipt['selected_count']==137 and sum(r['bytes'] for r in rows)==receipt['selected_logical_bytes']==7566383 and selection['remote_commit']==receipt['remote_commit']==COMMIT
assert [r['path'] for r in rows]==sorted(set(r['path'] for r in rows));repo=Path(receipt['fresh_git_root']);assert repo==A/'fresh-origin02.git' and not (repo/'objects/info/alternates').exists();env=dict(os.environ);env.update(GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL='',GIT_TERMINAL_PROMPT='0',GIT_NO_REPLACE_OBJECTS='1')
def git(args,cap=4194304):
 p=subprocess.run(['git',*args],cwd=repo,env=env,capture_output=True,timeout=15);assert p.returncode==0 and len(p.stdout)<=cap and len(p.stderr)<=65536;return p.stdout
assert git(['cat-file','-t',COMMIT])==b'commit\n';assert git(['config','--get','remote.origin.url']).decode().strip()==receipt['origin']=='git@github.com:malecada/TradingAgents.git'
tree=git(['ls-tree','-r','-z',COMMIT,'--',*[r['path'] for r in rows]]);assert tree.endswith(b'\0');objects={}
for line in tree.split(b'\0')[:-1]:
 left,name=line.split(b'\t');mode,kind,oid=left.decode().split();assert kind=='blob' and mode in ('100644','100755');objects[name.decode()]=(mode,oid)
assert set(objects)=={r['path'] for r in rows};saved=set();recrows={r['path']:r for r in receipt['selected_blobs']};assert len(recrows)==137
for row in rows:
 name=row['path'];assert str(PurePosixPath(name))==name and not name.startswith('/') and '..' not in PurePosixPath(name).parts
 p=A/'selected'/name;s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==row['bytes']<=4194304;raw=p.read_bytes();assert H(raw)==row['sha256'];mode,oid=objects[name];rr=recrows[name];assert rr==dict(row,git_mode=mode,git_object=oid)
 assert git(['cat-file','blob',oid])==raw==(ROOT/name).read_bytes();assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid;saved.add(name)
actual=set()
for p,ds,fs in os.walk(A/'selected',followlinks=False):
 for n in ds:assert stat.S_ISDIR((Path(p)/n).lstat().st_mode)
 for n in fs:actual.add((Path(p)/n).relative_to(A/'selected').as_posix())
assert actual==saved
ops=receipt['operations'];assert len(ops)==285 and all(o['exit']==0 and o['cleanup_failures']==[] for o in ops)
remote=next(o for o in ops if o['operation']=='ls-remote');assert remote['stdout_sha256']==H((COMMIT+'\t'+receipt['branch']+'\n').encode());fetches=[o for o in ops if o['operation']=='fetch'];assert len(fetches)==2;assert not any(Path('/proc',str(o['pid'])).exists() for o in ops)
# Final FETCH_HEAD holds explicitly fetched blob refs, not original source commit.
fh=(repo/'FETCH_HEAD').read_bytes();assert fh and all(line.split(b'\t')[0].decode() in {v[1] for v in objects.values()} for line in fh.splitlines())
fail=J(OLD/'FAILED01.json');assert H((OLD/'FAILED01.json').read_bytes())=='c5bc47634a4434844c6155277a9e7a4c1d6188518e37c96215c24e951d5abaa3';assert fail['status']=='failed-original-attempt' and fail['error']=='streaming response bound' and fail['operations'][-1]['stdout_bytes']==8396800 and fail['operations'][-1]['cleanup_failures']==[];assert not list((OLD/'selected').rglob('*')) if (OLD/'selected').exists() else True
# Independently read only raw TAR headers/extensions to locate exact actual failure.
base='research/onchain-paper-replication-2026-09-24/full_sources/held-consumer-final-baseline-root-capture01-2026-10-03';bundle=A/'selected'/base/'bundle01';q=J(A/'selected'/base/'REQUEST01.json');raw=(bundle/'capsule.tar.gz').read_bytes();assert H(raw)=='bcbc44160e09beba8b50e28188393cce6a3e9f90af9062fd90e4026f2ce74dbd';preceding_files=[];cause=None;total=0
with gzip.GzipFile(fileobj=io.BytesIO(raw),mode='rb') as z:
 def take(n):
  global total
  assert 0<=n<=4194304;parts=[]
  while n:
   b=z.read(min(65536,n));assert b;parts.append(b);n-=len(b);total+=len(b);assert total<=192*1024**2
  return b''.join(parts)
 pending=None
 while True:
  h=take(512);assert h!=bytes(512);t=tarfile.TarInfo.frombuf(h,'utf8','strict')
  if t.type==tarfile.XHDTYPE:
   assert t.size<=8192;body=take(t.size);take((-t.size)%512);pos=0;values={}
   while pos<len(body):
    s=body.index(b' ',pos);n=int(body[pos:s]);k,v=body[s+1:pos+n-1].split(b'=',1);values[k]=v.decode();pos+=n
   assert set(values)=={b'path'};pending=values[b'path']
   if pending!=str(PurePosixPath(pending)):
    nexthead=take(512);nextinfo=tarfile.TarInfo.frombuf(nexthead,'utf8','strict');assert pending.endswith('/') and nextinfo.isdir() and nextinfo.size==0
    name=pending[:-1];entry=next(r for r in q['capsule_manifest']['members'] if r['path']==name);assert entry['kind']=='directory';cause={'pax_path':pending,'next_header_type':'directory','next_size':0,'original_manifest_entry':entry,'preceding_regular_bodies':len(preceding_files),'pax_body_sha256':H(body),'next_header_sha256':H(nexthead)};break
   continue
  name=pending if pending is not None else t.name.rstrip('/') if t.isdir() else t.name;pending=None
  assert t.type in (tarfile.REGTYPE,tarfile.DIRTYPE) and 0<=t.size<=4194304;body=take(t.size);take((-t.size)%512)
  if t.isfile():preceding_files.append((name,H(body),len(body)))
assert cause is not None
# Actual partial mapping order/content, no final or metadata seal fabricated.
flat=A/'flat02';names={p.name for p in flat.iterdir()};expected={f'capsule-{i:05d}.body' for i in range(len(preceding_files))};assert names==expected
for i,(name,h,n) in enumerate(preceding_files):
 p=flat/f'capsule-{i:05d}.body';s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600 and s.st_size==n and H(p.read_bytes())==h
assert not list((A/'flat01').iterdir()) and not (flat/'recovery.json').exists()
f1=J(A/'FLAT_FAILURE01.json');f2=J(A/'FLAT_TERMINAL02.json');assert f1['exit']==f2['exit']==1 and f1['flat01_entries']==0 and f2['recovery_sha256'] is None;assert H((A/'FLAT02.stderr').read_bytes())==f2['stderr_sha256'] and b'pending=path_name' in (A/'FLAT02.stderr').read_bytes();assert H((A/'FLAT01.stderr').read_bytes())==f1['stderr_sha256']
# Actual source-only path predicate reproduces the precise rejection without recovery.
source=R.parent/'held-consumer-final-recovery-preparation03-2026-10-03/recovery03.py';assert H(source.read_bytes())=='785b957f93e22b18b1d3c00a73cacc75b6028bab9566d737b40903dcffc4964e';tree=ast.parse(source.read_bytes());defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('require','path_name')];ns={'PurePosixPath':PurePosixPath};exec(compile(ast.Module(body=defs,type_ignores=[]),'<actual-path-predicate>','exec'),ns)
try:ns['path_name'](cause['pax_path'])
except ValueError as e:assert str(e)=='unsafe member path'
else:raise AssertionError('actual failure not reproduced')
assert ns['path_name'](cause['pax_path'][:-1])==cause['original_manifest_entry']['path']
result={'schema_version':1,'decision':'accepted_actual_selected_remote_bytes_flat_recovery_failed','remote_commit':COMMIT,'remote_receipt_sha256':H((A/'REMOTE_RECOVERY02.json').read_bytes()),'selected_count':137,'selected_bytes':7566383,'offline_commit_tree_blob_body_equality':True,'operation_count':len(ops),'actual_remote_ls_readback_hash_join':True,'final_fetch_head_is_blob_union':True,'recorded_operation_pids_absent':True,'flat01_empty_failed':True,'flat02_exact_partial_bodies':len(preceding_files),'flat02_failure_cause':cause,'flat_recovery_accepted':False,'recovered_git_proved':False,'native_approved':False}
(R/'ORIGIN_FAILURE_READBACK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print('PASS offline137actualremoteGit+saved+original body joins; actualfailed01 preserved;flat01empty;flat02exactpartial',len(preceding_files),'cause',cause['pax_path'])
