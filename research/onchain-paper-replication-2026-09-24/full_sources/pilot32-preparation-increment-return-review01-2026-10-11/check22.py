"""Independent declared full32increment22 returned-byte review; no subprocess/helper run."""
import datetime,hashlib,io,json,os,resource,signal,stat,tarfile
from pathlib import Path,PurePosixPath
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,384*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304));signal.alarm(45)
H=Path(__file__).resolve().parent;F=H.parent;R=F.parents[2];D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full32increment22';checks=[];refs={};streamed=0
SOURCE='1d074ddf77552d8c4cb897527bf37ea729f24e4f';EXPECTED=(3624960,'a15adc19299b7b140df0ed48bc7d00ef6085e5ffbb0698c3d0a34a5dbf2d045f')
def ck(ok,name):
 assert ok,name
 checks.append(name)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 p=Path(p);s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<2*1024**2;b=p.read_bytes();refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b)};return b
def js(p):return json.loads(read(p))
def stream(f,limit):
 global streamed
 n=0;h=hashlib.sha256()
 while b:=f.read(65536):
  n+=len(b);streamed+=len(b);assert n<=limit and streamed<384*1024**2;h.update(b)
 return n,h.hexdigest()
def digest(p,limit=64*1024**2):
 p=Path(p);before=p.lstat();assert stat.S_ISREG(before.st_mode) and before.st_size<=limit
 with p.open('rb') as f:result=stream(f,limit)
 after=p.lstat();assert all(getattr(before,k)==getattr(after,k) for k in ('st_dev','st_ino','st_size','st_mode','st_mtime_ns','st_ctime_ns'));return result
observation=js(H/'EXPECTED_RETURN22.json');ck(observation['exit_code']==0 and observation['source']==SOURCE,'Root actual recovery completion')
Q=F/'pilot32-preparation-increment-tools-review01-2026-10-11/TOOLS_REVIEW01.json';ck(sha(read(Q))=='e449b0ac0884767a09a59071664ca9250324651f6d12b5fd2b780f37a0eeedb0','accepted tools22 review reused');tools=js(Q)
mp=tools['helper_manifest'];ck(digest(R/mp['path'])==(mp['bytes'],mp['sha256']),'exact reviewed helpers manifest');manifest=js(R/mp['path'])
for name,pin in manifest['files'].items():ck(digest(D/name)==(pin['bytes'],pin['sha256']),'exact helper '+name)
selb=read(D/'SELECTION22.json');sel=json.loads(selb);capb=read(D/'CAPTURE22.json');cap=json.loads(capb);rec=js(D/'FRESH_GIT_RECOVERY22.json')
ck(sha(selb)==cap['selection']['sha256'] and sha(capb)==rec['capture']['sha256'],'actual selection/capture/recovery joins')
ck(cap['selection']['path']==str((D/'SELECTION22.json').relative_to(R)) and rec['capture']['path']==str((D/'CAPTURE22.json').relative_to(R)),'exact receipt paths')
ck(rec['source']==rec['actual_remote_head']==rec['actual_fetch_head']==SOURCE,'actual source/remote/fetch commit')
ck(cap['archive']['path']==str((D/'pilot-preparation-increment22.tar').relative_to(R)) and rec['returned_archive']['path']==str((D/'fresh-git-recovered-preparation22.tar').relative_to(R)),'exact archive paths')
for pin in (cap['archive'],rec['returned_archive']):ck((pin['bytes'],pin['sha256'])==EXPECTED and digest(R/pin['path'])==EXPECTED,'whole actual archive hash')
ops=js(D/'GIT_OPERATIONS22.json');names=['local_head','remote_get_url','remote_actual_branch_readback','local_archive_git_tree_join','fresh_bare_init','fresh_remote_add','set_promisor','set_tree_zero_filter','actual_external_commit_only_fetch','fetched_head_readback','actual_external_commit_body','actual_external_selected_blob_fetch','actual_external_archive_blob_return']
ck(ops==rec['operations'] and [o['operation'] for o in ops]==names,'exact13 actual operations')
for op in ops:
 ck(op['exit_code']==0,'operation success '+op['operation'])
 for kind in ('stdout','stderr'):ck(digest(D/(op['operation']+'.'+kind))==(op[kind+'_bytes'],op[kind+'_sha256']),'actual raw '+op['operation']+'.'+kind)
ck(read(D/'local_head.stdout').decode().strip()==read(D/'fetched_head_readback.stdout').decode().strip()==SOURCE,'raw local/fetch identities')
ck(read(D/'remote_actual_branch_readback.stdout').decode().strip()==SOURCE+'\trefs/heads/research/onchain-paper-replication-2026-09-24','raw remote branch identity')
ck(read(D/'remote_get_url.stdout').decode().strip()==rec['actual_external_source']=='git@github.com:malecada/TradingAgents.git','raw external source identity')
ck(read(D/'local_archive_git_tree_join.stdout').decode().strip()==rec['local_commit_tree_join']==f"100644 blob {rec['archive_git_blob_oid']}\t{cap['archive']['path']}",'actual committed regular archive join')
commit=read(D/'actual_external_commit_body.stdout');ck(sha(commit)==rec['commit_body_sha256'] and hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==SOURCE,'independent commit object encoding')
returned=R/rec['returned_archive']['path'];blob=hashlib.sha1(b'blob '+str(EXPECTED[0]).encode()+b'\0')
with returned.open('rb') as f:
 while b:=f.read(65536):blob.update(b)
ck(blob.hexdigest()==rec['archive_git_blob_oid'],'independent blob object encoding')
bare=Path(rec['fresh_bare']);ck(bare==R.parent/'onchain-pilot-recovery/real-pilot-full32-preparation-20261011-22.git' and bare.is_dir() and not bare.is_symlink() and not os.path.lexists(bare/'objects/info/alternates') and rec['no_alternates'] is True,'actual exact bare/no alternates metadata')
rows=sorted(sel['rows']+sel['directories'],key=lambda x:x['path']);index={r['path']:r for r in rows}
ck(len(index)==len(rows)==195 and len(sel['rows'])==sel['files']==cap['files']==172 and len(sel['directories'])==23 and sel['symlinks']==0,'227 regular31 directories')
ck(all(r['type']=='regular' for r in sel['rows']) and sum(r['bytes'] for r in sel['rows'])==sel['body_bytes']==cap['regular_bytes']==3291274,'exact3291274 body bytes')
ck(sel['actual_scope_states']==tools['explicit_scopes']==[],'no empirical scopes')
for row in rows:
 p=PurePosixPath(row['path']);ck(not p.is_absolute() and '..' not in p.parts and not {'.git','.venv','node_modules','keys','apis','real_pilot_runtime'}&set(p.parts) and p.name not in ('.env','connection.json','hf_token.txt') and not row['path'].startswith(('research_runs/','research_artifacts/')),'safe public typed path '+row['path'])
class Sink:
 def __init__(self):self.n=0;self.h=hashlib.sha256()
 def write(self,b):self.n+=len(b);self.h.update(b);return len(b)
 def tell(self):return self.n
 def flush(self):pass
sink=Sink();typed=[]
with tarfile.open(returned,'r:') as source,tarfile.open(fileobj=sink,mode='w',format=tarfile.PAX_FORMAT) as target:
 members=source.getmembers();ck(len(members)==195,'complete returned member roster')
 for m,r in zip(members,rows,strict=True):
  ck(m.name==r['path'] and m.mode==int(r['mode'],8),'typed exact name/mode '+m.name);ck(m.uid==m.gid==m.mtime==0 and m.uname==m.gname=='','normalized owner/time')
  n=tarfile.TarInfo(r['path']);n.mode=int(r['mode'],8);n.uid=n.gid=n.mtime=0
  if r['type']=='directory':ck(m.type==tarfile.DIRTYPE and m.size==0,'actual directory');n.type=tarfile.DIRTYPE;target.addfile(n)
  else:
   ck(m.type==tarfile.REGTYPE and m.size==r['bytes']<=64*1024**2,'actual regular extent');ck(stream(source.extractfile(m),64*1024**2)==(r['bytes'],r['sha256']),'returned body '+m.name);n.size=m.size;target.addfile(n,source.extractfile(m))
  typed.append({'path':m.name,'type':r['type'],'mode':r['mode'],'bytes':m.size})
ck((sink.n,sink.h.hexdigest())==EXPECTED,'complete independent PAX reencoding exact')
A=F/'pilot31-outcome-increment-return-review01-2026-10-11/REVIEW01.json';ck(sha(read(A))=='f7366927d229e02ec62a1f7940ddb10ec8ea5bab8ef75003295520eda13d260f','accepted actual19 continuity');accepted=js(A)
base=js(R/sel['baseline_actual_recovery']['path']);ck(sha(read(R/sel['baseline_actual_recovery']['path']))==sel['baseline_actual_recovery']['sha256']=='e6829503c04eb32c2bfdece6cfd4547eb63b2eb7fc7648b60e3c68c6c3390ab9','actual19 receipt')
ck(base['source']==sel['baseline_source']==accepted['source']=='607e2727366f7891bf72525cbe02258ae7c6dd3c' and base['returned_archive']==accepted['archive'],'prior21 accepted archive continuity without replay')
ck(sel['exact_unchanged_prior_rows_reused']==[] and set(sel['exact_already_recovered_duplicate_exclusions'])==set(tools['prior_archive_exclusions']) and not set(index)&set(tools['prior_archive_exclusions']),'zero reused rows; exact three prior archive exclusions')
for name,pin in manifest['files'].items():ck(index[str((D/name).relative_to(R))]['sha256']==pin['sha256'],'returned reviewed helper '+name)
release_path=F/'pilot32-final-entry-review01-2026-10-11/RELEASE_REVIEW01.json';release=js(release_path);ck(sha(read(release_path))==observation['release_sha256'] and release['decision']=='accepted' and all(release['checks'].values()),'exact final accepted release review')
ck(index[str(release_path.relative_to(R))]['sha256']==observation['release_sha256'],'returned release review body')
ck(release['source_count']==620 and release['input_count']==67,'accepted release scalar620sources67inputs; no source/input reopening')
for key in ('binding','binding_review','gate'):
 pin=release[key];row=index[pin['path']];ck((row['bytes'],row['sha256'])==(pin['bytes'],pin['sha256']),'returned final release join '+key)
# Only selected public bodies are joined; scientific/runtime input reference bodies are not opened.
for name,expected in release['evidence'].items():
 if name in index:ck(index[name]['sha256']==expected,'selected release evidence '+name)
entry=F/'real-data-pilot-full32-entry-preparation01-2026-10-11'
for name in ('gate01.json','preflight32_02.py','root_io32_02.py','BINDING01.json'):
 key=str((entry/name).relative_to(R));ck(key in index and digest(R/key)==(index[key]['bytes'],index[key]['sha256']),'actual current public caller retained '+name)
packet_path=D/'ROOT_ACTUAL_OPERATIONS22.json';packet=js(packet_path);ck(sha(read(packet_path))=='363dea3aef8ccdfde9e6f6fb815c97d0c8d46a99ea6c4052c56296fbfc815aae' and packet['actual_source']==SOURCE and all(op['exit_code']==0 for op in packet['operations']),'postreturn actual Root operations local evidence')
for key in ('selection','capture','fresh_recovery'):
 pin=packet[key];ck(digest(R/pin['path'])==(pin['bytes'],pin['sha256']),'postreturn packet exact receipt '+key)
ck(str(packet_path.relative_to(R)) not in index,'postreturn packet not claimed archived')
(H/'TYPED_MEMBERS22.json').write_text(json.dumps(typed,sort_keys=True,indent=2)+'\n')
out={'decision':'ACCEPT_ACTUAL_INCREMENT22_DECLARED_PUBLIC_PREPARATION_RETURN','source':SOURCE,'archive':rec['returned_archive'],'archive_git_blob_oid':rec['archive_git_blob_oid'],'regular':172,'directories':23,'regular_bytes':3291274,'whole_pax_reencoding_exact':True,'no_alternates_metadata_verified':True,'checks':checks,'references':refs,'streamed_bytes_accounted':streamed,'limitations':['Declared172 public bodies and23 typed directory names/modes only. No scientific/private/runtime/store completeness, POSIX reconstruction or deletion authority.','Original13 retained Git operations verified; no new network/Git operation or future remote availability proof.','Accepted prior21 return and300 tools checks reused; no historical matrix replay.','Public final caller/release byte joins only; no claim, numerical execution or admission decision.']}
(H/'REVIEW01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({'decision':out['decision'],'checks':len(checks),'review_sha256':sha((H/'REVIEW01.json').read_bytes())}))
