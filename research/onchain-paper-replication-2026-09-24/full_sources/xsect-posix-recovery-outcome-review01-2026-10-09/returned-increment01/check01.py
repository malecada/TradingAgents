import hashlib,json,os,stat,tarfile
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[4];F=P.parent.parent;D=F/'pilot-throughput23-and-xsect-recovery-increment01-2026-10-09';pins={}
def raw(p):
 b=p.read_bytes();pins[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def load(p):return json.loads(raw(p))
fresh=load(D/'FRESH_GIT_RECOVERY01.json');cap=load(D/'CAPTURE01.json');sel=load(D/'SELECTION01.json');ops=load(D/'GIT_OPERATIONS01.json')
assert fresh['capture']['sha256']==pins[str((D/'CAPTURE01.json').relative_to(R))] and cap['selection']['sha256']==pins[str((D/'SELECTION01.json').relative_to(R))]
assert ops==fresh['operations'] and len(ops)==13 and len({x['operation'] for x in ops})==13
for op in ops:
 assert op['exit_code']==0
 for stream in ['stdout','stderr']:
  b=raw(D/(op['operation']+'.'+stream));assert len(b)==op[stream+'_bytes'] and hashlib.sha256(b).hexdigest()==op[stream+'_sha256']
source=fresh['source'];assert source==fresh['actual_remote_head']==fresh['actual_fetch_head']==(D/'local_head.stdout').read_text().strip()==(D/'fetched_head_readback.stdout').read_text().strip();assert (D/'remote_actual_branch_readback.stdout').read_text().split()[0]==source
assert (D/'remote_get_url.stdout').read_text().strip()==fresh['actual_external_source']=='git@github.com:malecada/TradingAgents.git'
commit=raw(D/'actual_external_commit_body.stdout');assert hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==source;assert hashlib.sha256(commit).hexdigest()==fresh['commit_body_sha256']
join=(D/'local_archive_git_tree_join.stdout').read_text().strip();assert join==fresh['local_commit_tree_join'];assert join.split()==['100644','blob',fresh['archive_git_blob_oid'],cap['archive']['path']]
bare=Path(fresh['fresh_bare']);assert fresh['no_alternates'] and not (bare/'objects/info/alternates').exists() and not (bare/'objects/info/alternates').is_symlink();assert (bare/'FETCH_HEAD').read_text().split()[0]==source
returned=raw(R/fresh['returned_archive']['path']);assert returned==raw(D/'actual_external_archive_blob_return.stdout')==raw(R/cap['archive']['path']);assert len(returned)==fresh['returned_archive']['bytes']==cap['archive']['bytes']==6205440;assert hashlib.sha256(returned).hexdigest()==fresh['returned_archive']['sha256']==cap['archive']['sha256'];assert hashlib.sha1(b'blob '+str(len(returned)).encode()+b'\0'+returned).hexdigest()==fresh['archive_git_blob_oid']
rows={x['path']:x for x in sel['rows']};dirs={x['path']:x for x in sel['directories']};assert len(rows)==sel['files']==cap['files']==292 and len(dirs)==cap['directories']==43;assert sum(x['bytes'] for x in rows.values())==sel['body_bytes']==cap['regular_bytes']==5610259
seen=set()
with tarfile.open(R/fresh['returned_archive']['path'],'r:') as archive:
 for member in archive:
  assert member.name not in seen;seen.add(member.name);assert member.name in rows or member.name in dirs;row=(rows|dirs)[member.name];assert member.mode==int(row['mode'],8)
  if member.name in dirs:assert member.isdir() and not member.linkname
  else:
   assert member.isreg() and not member.linkname and member.size==row['bytes'];body=archive.extractfile(member).read();assert hashlib.sha256(body).hexdigest()==row['sha256'];actual=R/member.name;st=actual.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==member.mode;assert raw(actual)==body
assert seen==rows.keys()|dirs.keys()
for name,row in dirs.items():assert stat.S_ISDIR((R/name).lstat().st_mode) and stat.S_IMODE((R/name).lstat().st_mode)==int(row['mode'],8)
assert any(name.endswith('gate02.json') for name in rows) and not any(name.endswith('gate03.json') for name in rows)
prior=load(P.parent/'RESULT01.json');assert prior['decision']=='accepted_sampled_recovery_and_original_currentness'
contract=load(F/'xsect-posix-recovery-entry01-2026-10-09/CONTRACT_FINAL01.json');target=Path(contract['target_root']);st=target.lstat();assert stat.S_ISDIR(st.st_mode) and [st.st_dev,st.st_ino]==prior['fresh_current_root_pin'];assert target.resolve()==target and not target.is_relative_to(Path(contract['original_root']))
result={'decision':'accepted_exact_returned_public_increment','source':source,'files':292,'directories':43,'regular_bytes':5610259,'archive_bytes':6205440,'actual_operations':13,'no_alternates':True,'current_selected_bodies_unchanged':True,'scope':'Original23 gate02 and declared actual xsect recovery metadata only; corrected gate03/new final seal excluded.','generated_tree_exact_path':str(target),'generated_tree_current_root_pin':[st.st_dev,st.st_ino],'retirement_assessment':'Generated restore tree is a redundant verification copy under the reviewed preservation chain; exact Root-owned retirement can remove only this namespace after final identity/quiescence checks. No deletion performed or authority created. Original xsect/StorageBox backup/all old stores must remain.','no_raw_tree_rehash':True,'evidence':pins};(P/'RESULT01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='evidence'}))
