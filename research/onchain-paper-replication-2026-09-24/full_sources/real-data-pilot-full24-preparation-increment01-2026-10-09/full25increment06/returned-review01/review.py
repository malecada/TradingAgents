import hashlib,json,tarfile,datetime
from pathlib import Path,PurePosixPath
O=Path(__file__).resolve().parent;D=O.parent;R=D.parents[4]
def sha(b):return hashlib.sha256(b).hexdigest()
def read(n):return json.loads((D/n).read_bytes())
s=read('SELECTION06.json');c=read('CAPTURE06.json');v=read('FRESH_GIT_RECOVERY06.json');ops=read('GIT_OPERATIONS06.json')
assert v['source']=='bbf426dbf1a7d52bb6dfe2617988760968507b0f'
assert v['capture']['sha256']==sha((D/'CAPTURE06.json').read_bytes())
assert c['selection']['sha256']==sha((D/'SELECTION06.json').read_bytes())
assert ops==v['operations'] and len(ops)==13
for op in ops:
 assert op['exit_code']==0
 for k in ('stdout','stderr'):
  b=(D/(op['operation']+'.'+k)).read_bytes();assert len(b)==op[k+'_bytes'] and sha(b)==op[k+'_sha256']
commit=(D/'actual_external_commit_body.stdout').read_bytes()
assert sha(commit)==v['commit_body_sha256']
assert hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==v['source']
assert (D/'local_head.stdout').read_text().strip()==v['source']
assert (D/'fetched_head_readback.stdout').read_text().strip()==v['source']==v['actual_fetch_head']
assert (D/'remote_actual_branch_readback.stdout').read_text().split()[0]==v['source']==v['actual_remote_head']
assert (D/'remote_get_url.stdout').read_text().strip()==v['actual_external_source']
assert (D/'local_archive_git_tree_join.stdout').read_text().strip()==v['local_commit_tree_join']
assert v['local_commit_tree_join']=='100644 blob '+v['archive_git_blob_oid']+'\t'+c['archive']['path']
returned=R/v['returned_archive']['path'];b=returned.read_bytes()
assert b==(D/'actual_external_archive_blob_return.stdout').read_bytes()
assert b==(R/c['archive']['path']).read_bytes()
assert len(b)==v['returned_archive']['bytes']==c['archive']['bytes'] and sha(b)==v['returned_archive']['sha256']==c['archive']['sha256']
assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==v['archive_git_blob_oid']
assert not (Path(v['fresh_bare'])/'objects/info/alternates').exists()
rows=sorted(s['rows']+s['directories'],key=lambda r:r['path']);regular=symlinks=dirs=body=0
with tarfile.open(returned,'r') as t:
 members=t.getmembers();assert len(members)==len(rows)==len({m.name for m in members})
 for m,r in zip(members,rows,strict=True):
  assert m.name==r['path'] and m.mode==int(r['mode'],8)
  p=PurePosixPath(m.name);assert not p.is_absolute() and '..' not in p.parts
  if r['type']=='directory':assert m.isdir();dirs+=1
  elif r['type']=='symlink':assert m.issym() and m.linkname==r['linkname'];symlinks+=1
  else:
   assert m.isfile() and m.size==r['bytes'];f=t.extractfile(m);h=hashlib.sha256();size=0
   while chunk:=f.read(1048576):h.update(chunk);size+=len(chunk)
   f.close();assert size==r['bytes'] and h.hexdigest()==r['sha256'];regular+=1;body+=size
assert regular+symlinks==s['files']==169 and symlinks==s['symlinks']==0 and body==s['body_bytes']==c['regular_bytes']
result={'decision':'accepted','scope':'Actual returned full24 preparation increment at bbf426dbf1a7d52bb6dfe2617988760968507b0f only; full25 selected preparation only; no numerical admission','source':v['source'],'raw_git_operations_verified':13,'selection_non_directory_entries':169,'regular_files':regular,'symlinks':symlinks,'directories':dirs,'regular_bytes':body,'archive_bytes':len(b),'archive_sha256':sha(b),'selection_sha256':sha((D/'SELECTION06.json').read_bytes()),'capture_sha256':sha((D/'CAPTURE06.json').read_bytes()),'recovery_sha256':sha((D/'FRESH_GIT_RECOVERY06.json').read_bytes()),'raw_commit_git_oid_verified':True,'raw_archive_git_blob_oid_verified':True,'raw_source_tree_join_verified':True,'raw_remote_head_and_fetch_head_joined':True,'no_alternates_observed':True,'all_member_names_types_modes_regular_hashes_and_symlink_targets_verified':True,'network_performed':False,'extraction_performed':False,'qualification':'Authenticates recorded fresh external Git return and every selected archive member without extraction or symlink dereference. No current remote re-fetch, full working-tree coverage, POSIX reconstruction, source installation, scientific admission, post-capture audit recovery, or deletion authority. Later delta must be preserved separately from this genuine return.'}
(O/'RECOVERY_REVIEW01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
