import json,hashlib,tarfile,subprocess,os
from pathlib import Path,PurePosixPath
O=Path(__file__).resolve().parent;W=O.parent;D=W.parent;R=D.parents[4]
def sha(b):return hashlib.sha256(b).hexdigest()
def get(p):return json.loads(p.read_bytes())
v=get(W/'FRESH_GIT_RECOVERY08.json');ops=get(W/'GIT_OPERATIONS08.json');c=get(D/'CAPTURE08.json');s=get(D/'SELECTION08.json')
assert v['source']=='91bd4bee8c1560d6464349e7f37b60d581b329f4' and len(ops)==19 and ops==v['operations']
for op in ops:
 assert op['exit_code']==0
 for k in ('stdout','stderr'):
  b=(W/(op['operation']+'.'+k)).read_bytes();assert len(b)==op[k+'_bytes'] and sha(b)==op[k+'_sha256']
assert v['capture']['sha256']==sha((D/'CAPTURE08.json').read_bytes()) and c['selection']['sha256']==sha((D/'SELECTION08.json').read_bytes())
commit=(W/'actual_external_commit_body.stdout').read_bytes();assert sha(commit)==v['commit_body_sha256'] and hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==v['source']
assert (W/'local_head.stdout').read_text().strip()==v['source']==v['actual_fetch_head']==v['actual_remote_head']
assert (W/'fetched_head_readback.stdout').read_text().strip()==v['source'] and (W/'remote_actual_branch_readback.stdout').read_text().split()[0]==v['source']
assert (W/'remote_get_url.stdout').read_text().strip()==v['actual_external_source']
assert (W/'local_archive_git_tree_join.stdout').read_text().strip()==v['local_commit_tree_join']=='100644 blob '+v['archive_git_blob_oid']+'\t'+c['archive']['path']
b=(R/v['returned_archive']['path']).read_bytes();assert b==(W/'actual_external_archive_blob_return.stdout').read_bytes()==(R/c['archive']['path']).read_bytes()
assert len(b)==2969600==c['archive']['bytes']==v['returned_archive']['bytes'] and sha(b)==c['archive']['sha256']==v['returned_archive']['sha256']=='6844438d2a30b4b90a6c197a315e6d911641b551ceceeb92907f948af02766ff'
assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==v['archive_git_blob_oid'] and not (Path(v['fresh_bare'])/'objects/info/alternates').exists()
rows=sorted(s['rows']+s['directories'],key=lambda x:x['path']);files=dirs=total=0
with tarfile.open(R/v['returned_archive']['path']) as t:
 members=t.getmembers();assert len(members)==len(rows)==147 and len({m.name for m in members})==147
 for m,row in zip(members,rows,strict=True):
  assert m.name==row['path'] and m.mode==int(row['mode'],8) and not PurePosixPath(m.name).is_absolute() and '..' not in PurePosixPath(m.name).parts
  if row['type']=='directory':assert m.isdir();dirs+=1
  else:
   assert row['type']=='regular' and m.isfile() and m.size==row['bytes'];f=t.extractfile(m);h=hashlib.sha256();n=0
   while z:=f.read(1048576):h.update(z);n+=len(z)
   f.close();assert n==row['bytes'] and h.hexdigest()==row['sha256'];files+=1;total+=n
assert (files,dirs,total)==(131,16,2716058)
env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0'}
def git(*a):return subprocess.check_output(['git',*a],cwd=R,env=env)
assert git('ls-tree',v['source'],'--',c['archive']['path']).decode().strip()==v['local_commit_tree_join']
for name in ('CAPTURE08.json','SELECTION08.json'):assert git('show',v['source']+':'+str((D/name).relative_to(R)))==(D/name).read_bytes()
extras=v['correction_bodies_actual_external_return'];assert len(extras)==2
for i,name in enumerate(('recover08_02.py','TOOLS_CORRECTION_REVIEW02.json')):
 e=extras[i];relative=str((D/name).relative_to(R));assert e['path']==relative
 line=(W/f'extra_local_tree_{i}.stdout').read_text().split();assert line[:2]==['100644','blob'] and line[2]==e['git_blob_oid'] and line[3]==relative
 body=(W/f'extra_external_return_{i}.stdout').read_bytes();assert body==(D/name).read_bytes()==git('show',v['source']+':'+relative)
 assert len(body)==e['bytes'] and sha(body)==e['sha256'] and hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==e['git_blob_oid']
 assert git('ls-tree',v['source'],'--',relative).decode().split()==line
 assert relative not in {row['path'] for row in s['rows']}
failed=get(D/'GIT_OPERATIONS08.json');assert len(failed)==4
for op in failed:
 for k in ('stdout','stderr'):
  z=(D/(op['operation']+'.'+k)).read_bytes();assert len(z)==op[k+'_bytes'] and sha(z)==op[k+'_sha256']
result={'decision':'accepted','scope':'Original immutable131-file full26 preparation archive PLUS exactly two separately returned correction bodies, at corrected recovery source91bd4bee8c1560d6464349e7f37b60d581b329f4','source':v['source'],'actual_git_operations_verified':19,'archive_regular_files':files,'archive_directories':dirs,'archive_regular_bytes':total,'archive_bytes':len(b),'archive_sha256':sha(b),'correction_bodies':extras,'archive_and_correction_scopes_distinct':True,'all_names_types_modes_regular_hashes_verified':True,'raw_remote_fetch_source_commit_archive_blob_and_extra_blob_joins_verified':True,'prior_failed_operations_preserved_and_verified':4,'recovery_receipt_sha256':sha((W/'FRESH_GIT_RECOVERY08.json').read_bytes()),'selection_sha256':sha((D/'SELECTION08.json').read_bytes()),'network':False,'extraction':False,'qualification':'Preservation only. Original wrong-mode helper and erroneous tools review remain in original archive; corrected helper and correction receipt are separately source-bound actual remote returns. No scientific completion, numerical launch, current resource capacity, current remote availability, POSIX reconstruction, or deletion authority.'}
(O/'RECOVERY_REVIEW01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
