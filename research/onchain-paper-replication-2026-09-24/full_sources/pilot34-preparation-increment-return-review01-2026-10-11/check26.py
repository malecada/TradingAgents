"""Independent declared full34increment26 returned-byte review; no subprocess/helper run."""
import datetime,hashlib,io,json,os,resource,signal,stat,tarfile
from pathlib import Path,PurePosixPath
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,384*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304));signal.alarm(45)
H=Path(__file__).resolve().parent;F=H.parent;R=F.parents[2];D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full34increment26';checks=[];refs={};streamed=0
SOURCE='67335f5e1987f28219e75e8cb679ff339739d853';EXPECTED=(3799040,'a935c6c0ea3f6e21f7dae1588ff5c43b4b18bff7a7af7ecbc3715d7f6bd8c17e')
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
observation=js(D/'ROOT_ACTUAL_OPERATIONS26.json');ck(sha(read(D/'ROOT_ACTUAL_OPERATIONS26.json'))=='b6b1137ce7676210116484f43f07a63f4988121ca366a97ecf161ae75143df26' and observation['actual_operations'][-1]=={'name':'fresh_remote_recovery','session':89119,'terminal_chunk':'7f0e95','terminal_exit':0},'Root actual recovery completion')
Q=F/'pilot34-preparation-increment-tools-review01-2026-10-11/TOOLS_REVIEW01.json';ck(sha(read(Q))=='b66b1cf7f54a3a913ef543b45a4402e923fb327b6e9c9c1f17954fae3abf00bf','accepted tools24 review reused');tools=js(Q)
mp=tools['helper_manifest'];ck(sha(read(R/mp['path']))==mp['sha256'],'exact reviewed helpers manifest');manifest=js(R/mp['path'])
for name,pin in manifest['files'].items():ck(digest(D/name)==(pin['bytes'],pin['sha256']),'exact helper '+name)
selb=read(D/'SELECTION26.json');sel=json.loads(selb);capb=read(D/'CAPTURE26.json');cap=json.loads(capb);rec=js(D/'FRESH_GIT_RECOVERY26.json')
ck(sha(selb)==cap['selection']['sha256'] and sha(capb)==rec['capture']['sha256'],'actual selection/capture/recovery joins')
ck(cap['selection']['path']==str((D/'SELECTION26.json').relative_to(R)) and rec['capture']['path']==str((D/'CAPTURE26.json').relative_to(R)),'exact receipt paths')
ck(rec['source']==rec['actual_remote_head']==rec['actual_fetch_head']==SOURCE,'actual source/remote/fetch commit')
ck(cap['archive']['path']==str((D/'pilot-preparation-increment26.tar').relative_to(R)) and rec['returned_archive']['path']==str((D/'fresh-git-recovered-preparation26.tar').relative_to(R)),'exact archive paths')
for pin in (cap['archive'],rec['returned_archive']):ck((pin['bytes'],pin['sha256'])==EXPECTED and digest(R/pin['path'])==EXPECTED,'whole actual archive hash')
ops=js(D/'GIT_OPERATIONS26.json');names=['local_head','remote_get_url','remote_actual_branch_readback','local_archive_git_tree_join','fresh_bare_init','fresh_remote_add','set_promisor','set_tree_zero_filter','actual_external_commit_only_fetch','fetched_head_readback','actual_external_commit_body','actual_external_selected_blob_fetch','actual_external_archive_blob_return']
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
bare=Path(rec['fresh_bare']);ck(bare==R.parent/'onchain-pilot-recovery/real-pilot-full34-preparation-20261011-26.git' and bare.is_dir() and not bare.is_symlink() and not os.path.lexists(bare/'objects/info/alternates') and rec['no_alternates'] is True,'actual exact bare/no alternates metadata')
rows=sorted(sel['rows']+sel['directories'],key=lambda x:x['path']);index={r['path']:r for r in rows}
ck(len(index)==len(rows)==156 and len(sel['rows'])==sel['files']==cap['files']==137 and len(sel['directories'])==19 and sel['symlinks']==0,'247 regular31 directories')
ck(all(r['type']=='regular' for r in sel['rows']) and sum(r['bytes'] for r in sel['rows'])==sel['body_bytes']==cap['regular_bytes']==3533330,'exact3533330 body bytes')
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
 members=source.getmembers();ck(len(members)==156,'complete returned member roster')
 for m,r in zip(members,rows,strict=True):
  ck(m.name==r['path'] and m.mode==int(r['mode'],8),'typed exact name/mode '+m.name);ck(m.uid==m.gid==m.mtime==0 and m.uname==m.gname=='','normalized owner/time')
  n=tarfile.TarInfo(r['path']);n.mode=int(r['mode'],8);n.uid=n.gid=n.mtime=0
  if r['type']=='directory':ck(m.type==tarfile.DIRTYPE and m.size==0,'actual directory');n.type=tarfile.DIRTYPE;target.addfile(n)
  else:
   ck(m.type==tarfile.REGTYPE and m.size==r['bytes']<=64*1024**2,'actual regular extent');ck(stream(source.extractfile(m),64*1024**2)==(r['bytes'],r['sha256']),'returned body '+m.name);n.size=m.size;target.addfile(n,source.extractfile(m))
  typed.append({'path':m.name,'type':r['type'],'mode':r['mode'],'bytes':m.size})
ck((sink.n,sink.h.hexdigest())==EXPECTED,'complete independent PAX reencoding exact')
A=F/'pilot33-outcome-increment-return-review01-2026-10-11/REVIEW01.json';ck(sha(read(A))=='60606981c43543883e9ffd0dfd3ff76a7e03c1eea7cc039f986fdf27110585f8','accepted actual25 continuity');accepted=js(A)
base=js(R/sel['baseline_actual_recovery']['path']);ck(sha(read(R/sel['baseline_actual_recovery']['path']))==sel['baseline_actual_recovery']['sha256']=='e6aa5f63f63a7b8f567a36a6fcb598673a674c0a47bcd6520e55d26a4a9ce5c3','actual25 receipt')
ck(base['source']==sel['baseline_source']==accepted['source']=='905e1361b2d624e48ae554095d508df3ce680b81' and base['returned_archive']==accepted['archive'],'prior25 accepted archive continuity without replay')
reused=sel['exact_unchanged_prior_rows_reused'];ck(len(reused)==len(set(reused))==24 and not set(reused)&set(index),'exact disjoint prior25 reused roster')
basecap=js(R/base['capture']['path']);ck(sha(read(R/base['capture']['path']))==base['capture']['sha256'],'prior25 capture hash')
basebody=read(R/basecap['selection']['path']);ck(sha(basebody)==basecap['selection']['sha256'],'prior25 selection hash');baseindex={row['path']:row for row in json.loads(basebody)['rows']}
for name in reused:
 row=baseindex[name];ck(row['type']=='regular' and digest(R/name)==(row['bytes'],row['sha256']) and stat.S_IMODE((R/name).lstat().st_mode)==int(row['mode'],8),'current unchanged prior25 body '+name)
ck(set(sel['exact_already_recovered_duplicate_exclusions'])==set(tools['prior_archive_exclusions']) and not set(index)&set(tools['prior_archive_exclusions']),'exact three prior archive exclusions')
for name,pin in manifest['files'].items():ck(index[str((D/name).relative_to(R))]['sha256']==pin['sha256'],'returned reviewed helper '+name)
release_path=F/'pilot34-binding-release-review01-2026-10-11/RELEASE_REVIEW01.json';release=js(release_path);ck(sha(read(release_path))=='faec5b4da6f5fefc1cf5d8ae8f284721b1ab57cf285a79869df56f9923e7e035' and release['decision']=='accepted' and all(release['checks'].values()),'exact final accepted release review')
ck(index[str(release_path.relative_to(R))]['sha256']=='faec5b4da6f5fefc1cf5d8ae8f284721b1ab57cf285a79869df56f9923e7e035','returned release review body')
ck(release['source_count']==742 and release['input_count']==67,'accepted release scalar742sources67inputs; no source/input reopening')
for key in ('binding','binding_review','gate'):
 pin=release[key];row=index[pin['path']];ck((row['bytes'],row['sha256'])==(pin['bytes'],pin['sha256']),'returned final release join '+key)
# Only selected public bodies are joined; scientific/runtime input reference bodies are not opened.
for name,expected in release['evidence'].items():
 if name in index:ck(index[name]['sha256']==expected,'selected release evidence '+name)
entry=F/'real-data-pilot-full34-entry-preparation01-2026-10-11'
for name in ('gate01.json','preflight34_01.py','root_io34_01.py','BINDING01.json'):
 key=str((entry/name).relative_to(R));ck(key in index and digest(R/key)==(index[key]['bytes'],index[key]['sha256']),'actual current public caller retained '+name)
ck(all(op.get('exit_code',op.get('terminal_exit'))==0 for op in observation['actual_operations']),'postreturn actual Root operations zero exits')
ck(str((D/'ROOT_ACTUAL_OPERATIONS26.json').relative_to(R)) not in index,'postreturn packet not asserted archived')
ck(index['tradingagents/research/onchain_replication/compact_mcm.py']['sha256']=='abd86e24681f0df4ef3ca82cfb016662d9af5a46a38a32bafc65e7c92f2dacf8','actual installed scope correction selected')
ck(index[str((entry/'RELEASE_REVIEW01.json').relative_to(R))]['sha256']==sha(read(release_path)),'exact installed entry release selected')
ck(str((entry/'ADMISSION01.json').relative_to(R)) in index,'actual read-only admission body selected')
gate=js(entry/'gate01.json');experiment=gate['experiments']['eth-paper-real-data-end-to-end-resource-20261011-34'];budget=experiment['cumulative_budget_extension'];extension=js(R/budget['extension']['path']);ck(extension['cumulative_ceiling']==105,'actual105 ceiling')
for ref in [budget['extension'],budget['review'],extension['allocation']]:
 name=ref['path'];row=index[name] if name in index else baseindex[name]
 ck((name in index or name in reused) and row['sha256']==ref['sha256']==experiment['source_files'][name],'current105 exact selected-or-reused/sourcepin '+name)
for row in sel['rows']:
 p=R/row['path'];ck(digest(p)==(row['bytes'],row['sha256']) and stat.S_IMODE(p.lstat().st_mode)==int(row['mode'],8),'current selected frozen body '+row['path'])
for key in ['capture','git_operations','recovery']:
 pin=observation[key];ck(digest(R/pin['path'])==(pin['bytes'],pin['sha256']),'Root actual receipt '+key)
(H/'TYPED_MEMBERS26.json').write_text(json.dumps(typed,sort_keys=True,indent=2)+'\n')
out={'decision':'ACCEPT_ACTUAL_INCREMENT26_DECLARED_PUBLIC_PREPARATION_RETURN','source':SOURCE,'archive':rec['returned_archive'],'archive_git_blob_oid':rec['archive_git_blob_oid'],'regular':137,'directories':19,'regular_bytes':3533330,'whole_pax_reencoding_exact':True,'no_alternates_metadata_verified':True,'checks':checks,'references':refs,'streamed_bytes_accounted':streamed,'limitations':['Declared137 public bodies and19 typed directory names/modes only. No scientific/private/runtime/store completeness, POSIX reconstruction or deletion authority.','Original13 retained Git operations verified; no new network/Git operation or future remote availability proof.','Accepted prior25 return and232 tools checks reused; no historical matrix replay.','Public final caller/release byte joins only; no claim, numerical execution or admission decision.']}
(H/'REVIEW01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({'decision':out['decision'],'checks':len(checks),'review_sha256':sha((H/'REVIEW01.json').read_bytes())}))
