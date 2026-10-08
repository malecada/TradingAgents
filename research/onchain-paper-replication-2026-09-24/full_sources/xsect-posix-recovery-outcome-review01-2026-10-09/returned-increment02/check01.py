import hashlib,json,os,stat,tarfile
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[4];F=P.parent.parent;D=F/'pilot-throughput23-and-xsect-recovery-increment01-2026-10-09';pins={}
def raw(p):
 b=p.read_bytes();pins[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def load(p):return json.loads(raw(p))
fresh=load(D/'FRESH_GIT_RECOVERY02.json');cap=load(D/'CAPTURE02.json');sel=load(D/'SELECTION02.json');ops=load(D/'GIT_OPERATIONS02.json')
assert fresh['capture']['sha256']==pins[str((D/'CAPTURE02.json').relative_to(R))] and cap['selection']['sha256']==pins[str((D/'SELECTION02.json').relative_to(R))]
assert ops==fresh['operations'] and len(ops)==13 and len({x['operation'] for x in ops})==13
for op in ops:
 assert op['exit_code']==0
 for stream in ['stdout','stderr']:
  b=raw(D/(op['operation']+'02.'+stream));assert len(b)==op[stream+'_bytes'] and hashlib.sha256(b).hexdigest()==op[stream+'_sha256']
source=fresh['source'];assert source==fresh['actual_remote_head']==fresh['actual_fetch_head']==(D/'local_head02.stdout').read_text().strip()==(D/'fetched_head_readback02.stdout').read_text().strip();assert (D/'remote_actual_branch_readback02.stdout').read_text().split()[0]==source
assert (D/'remote_get_url02.stdout').read_text().strip()==fresh['actual_external_source']=='git@github.com:malecada/TradingAgents.git'
commit=raw(D/'actual_external_commit_body02.stdout');assert hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==source;assert hashlib.sha256(commit).hexdigest()==fresh['commit_body_sha256']
join=(D/'local_archive_git_tree_join02.stdout').read_text().strip();assert join==fresh['local_commit_tree_join'];assert join.split()==['100644','blob',fresh['archive_git_blob_oid'],cap['archive']['path']]
bare=Path(fresh['fresh_bare']);assert fresh['no_alternates'] and not (bare/'objects/info/alternates').exists() and not (bare/'objects/info/alternates').is_symlink();assert (bare/'FETCH_HEAD').read_text().split()[0]==source
returned=raw(R/fresh['returned_archive']['path']);assert returned==raw(D/'actual_external_archive_blob_return02.stdout')==raw(R/cap['archive']['path']);assert len(returned)==fresh['returned_archive']['bytes']==cap['archive']['bytes']==1116160;assert hashlib.sha256(returned).hexdigest()==fresh['returned_archive']['sha256']==cap['archive']['sha256'];assert hashlib.sha1(b'blob '+str(len(returned)).encode()+b'\0'+returned).hexdigest()==fresh['archive_git_blob_oid']
rows={x['path']:x for x in sel['rows']};dirs={x['path']:x for x in sel['directories']};assert len(rows)==sel['files']==cap['files']==34 and len(dirs)==cap['directories']==0;assert sum(x['bytes'] for x in rows.values())==sel['body_bytes']==cap['regular_bytes']==1051373
seen=set()
with tarfile.open(R/fresh['returned_archive']['path'],'r:') as archive:
 for member in archive:
  assert member.name not in seen;seen.add(member.name);assert member.name in rows or member.name in dirs;row=(rows|dirs)[member.name];assert member.mode==int(row['mode'],8)
  if member.name in dirs:assert member.isdir() and not member.linkname
  else:
   assert member.isreg() and not member.linkname and member.size==row['bytes'];body=archive.extractfile(member).read();assert hashlib.sha256(body).hexdigest()==row['sha256'];actual=R/member.name;st=actual.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==member.mode;assert raw(actual)==body
assert seen==rows.keys()|dirs.keys()
for name,row in dirs.items():assert stat.S_ISDIR((R/name).lstat().st_mode) and stat.S_IMODE((R/name).lstat().st_mode)==int(row['mode'],8)

assert source=='ba4b19dbab5d1ca8fa4bd1a30dadae12a6e8eb5b'
for name in ['gate03.json','preflight02.py','root_io02.py','BINDING02.json','RELEASE_REVIEW02.json']:
 assert any(p.endswith('/'+name) for p in rows),name
old=(D/'recover01.py').read_text();new=(D/'recover02.py').read_text()
for x,y in [('20261009-02.git','20261009-01.git'),('FRESH_GIT_RECOVERY02','FRESH_GIT_RECOVERY01'),("name+'02.'","name+'.'"),('GIT_OPERATIONS02','GIT_OPERATIONS01'),('CAPTURE02','CAPTURE01'),('fresh-git-recovered-correction02.tar','fresh-git-recovered-increment01.tar')]:new=new.replace(x,y)
assert new==old
ret=F/'xsect-generated-copy-retirement01-2026-10-09';terminal=load(ret/'ROOT_TERMINAL01.json');complete=load(ret/'COMPLETE01.json');assert terminal['actual_root_exit_code']==0 and terminal['exec_session']==28690 and terminal['actual_exit_tool_chunk']=='8195d4';assert terminal['complete_sha256']==pins[str((ret/'COMPLETE01.json').relative_to(R))];assert complete['original_retirement'] is False and complete['generated_target_absent'] and complete['deleted_generated_files']==3783
contract=load(F/'xsect-posix-recovery-entry01-2026-10-09/CONTRACT_FINAL01.json');assert not Path(contract['target_root']).exists() and not Path(contract['target_root']).is_symlink();assert Path(contract['original_root']).is_dir()
result={'decision':'accepted_exact_returned_correction','source':source,'files':34,'directories':0,'regular_bytes':1051373,'archive_bytes':1116160,'actual_operations':13,'no_alternates':True,'current_selected_bodies_unchanged':True,'literal_recovery_method_inverse':True,'generated_only_retirement_receipt_verified':True,'original_tree_present':True,'scope':'Corrected gate03/preflight02/root_io02/BINDING02/release and generated-only retirement public bodies; no current launch/capacity authority.','evidence':pins};(P/'RESULT01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='evidence'}))
