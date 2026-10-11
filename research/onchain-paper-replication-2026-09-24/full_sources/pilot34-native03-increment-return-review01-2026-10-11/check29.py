"""One finite actual nativeoutcome29 byte review, adapted from accepted check28.
No Git/network/selector/capture/recover or scientific decoding/execution.
EXPECTED_RETURN29.json must contain Root's actual source/archive and receipt pins.
"""
import hashlib,json,os,resource,signal,stat,tarfile
from pathlib import Path,PurePosixPath
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(30)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';D=H/'nativeoutcome29';O=H/'postnative28';refs={};counts={};streamed=0
def ck(v,category,detail=''):
 assert v,(category,detail)
 counts[category]=counts.get(category,0)+1
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 p=Path(p);s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<2*1024**2
 b=p.read_bytes();refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b)};return b
def js(p):return json.loads(read(p))
def stream(f,limit=64*1024**2):
 global streamed
 n=0;h=hashlib.sha256()
 while b:=f.read(65536):
  n+=len(b);streamed+=len(b);assert n<=limit and streamed<384*1024**2;h.update(b)
 return n,h.hexdigest()
def digest(p):
 p=Path(p);before=p.lstat();assert stat.S_ISREG(before.st_mode) and before.st_size<=64*1024**2
 with p.open('rb') as f:result=stream(f)
 after=p.lstat();assert all(getattr(before,k)==getattr(after,k) for k in ('st_dev','st_ino','st_size','st_mode','st_nlink','st_mtime_ns','st_ctime_ns'));return result
expected=js(P/'EXPECTED_RETURN29.json');SOURCE=expected['source'];EXPECTED=(expected['archive_bytes'],expected['archive_sha256'])
for name,digest_expected in expected['receipt_sha256'].items():ck(sha(read(D/name))==digest_expected,'actual supplied receipt pins',name)
A=F/'pilot34-postnative-increment-return-review01-2026-10-11/REVIEW01.json'
accepted=js(A);ck(sha(read(A))=='71e99df6ce8daf7226c2b91a42716cbbd35fd97d1bd6a9656365918f6d35259b','accepted28 return reused')
T=F/'pilot34-native03-increment-tools-review01-2026-10-11'/expected['tools_review_name'];ck(sha(read(T))==expected['tools_review_sha256'],'different-author actual tools acceptance')
tools=js(T);ck(tools['decision']=='accepted' and tools['baseline_source']=='7d7adf135f319530770c328cb19a7ec438364994','actual independent tools decision')
roster=js(D/'PROSPECTIVE_ROSTER01.json');hm=js(D/'HELPERS_MANIFEST01.json')
ck(sha(read(D/'HELPERS_MANIFEST01.json'))=='0e3aa221c7c75045c90b740cd3e25919ca5e2f523f18dd1322d2c232b4d10e1e','exact frozen29 manifest')
for name,pin in hm['files'].items():ck(digest(D/name)==(pin['bytes'],pin['sha256']),'frozen helper bodies',name)
selb=read(D/'SELECTION29.json');sel=json.loads(selb);capb=read(D/'CAPTURE29.json');cap=json.loads(capb);rec=js(D/'FRESH_GIT_RECOVERY29.json');ops=js(D/'GIT_OPERATIONS29.json');root=js(D/'ROOT_ACTUAL_OPERATIONS29.json')
ck(sha(selb)==cap['selection']['sha256'] and sha(capb)==rec['capture']['sha256'],'selection capture recovery joins')
ck(cap['selection']['path']==str((D/'SELECTION29.json').relative_to(R)) and rec['capture']['path']==str((D/'CAPTURE29.json').relative_to(R)),'selection capture paths')
ck(rec['source']==rec['actual_remote_head']==rec['actual_fetch_head']==SOURCE,'actual source remote fetch join')
ck(cap['archive']['path']==str((D/'native-outcome-increment29.tar').relative_to(R)) and rec['returned_archive']['path']==str((D/'fresh-git-recovered-nativeoutcome29.tar').relative_to(R)),'exact archive names')
for pin in (cap['archive'],rec['returned_archive']):ck((pin['bytes'],pin['sha256'])==EXPECTED and digest(R/pin['path'])==EXPECTED,'original and returned archive length hash')
names=['local_head','remote_get_url','remote_actual_branch_readback','local_archive_git_tree_join','fresh_bare_init','fresh_remote_add','set_promisor','set_tree_zero_filter','actual_external_commit_only_fetch','fetched_head_readback','actual_external_commit_body','actual_external_selected_blob_fetch','actual_external_archive_blob_return']
ck(ops==rec['operations'] and [o['operation'] for o in ops]==names,'exact thirteen operations')
for op in ops:
 ck(op['exit_code']==0,'actual operation exits',op['operation'])
 for kind in ('stdout','stderr'):ck(digest(D/(op['operation']+'.'+kind))==(op[kind+'_bytes'],op[kind+'_sha256']),'raw operation bytes',op['operation']+'.'+kind)
ck(read(D/'local_head.stdout').decode().strip()==read(D/'fetched_head_readback.stdout').decode().strip()==SOURCE,'raw local fetch source')
ck(read(D/'remote_actual_branch_readback.stdout').decode().strip()==SOURCE+'\trefs/heads/research/onchain-paper-replication-2026-09-24','raw remote branch')
ck(read(D/'remote_get_url.stdout').decode().strip()==rec['actual_external_source']=='git@github.com:malecada/TradingAgents.git','actual external source')
ck(read(D/'local_archive_git_tree_join.stdout').decode().strip()==rec['local_commit_tree_join']==f"100644 blob {rec['archive_git_blob_oid']}\t{cap['archive']['path']}",'actual commit regular tree join')
commit=read(D/'actual_external_commit_body.stdout');ck(sha(commit)==rec['commit_body_sha256'] and hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==SOURCE,'independent commit object reencoding')
returned=R/rec['returned_archive']['path'];blob=hashlib.sha1(b'blob '+str(EXPECTED[0]).encode()+b'\0')
with returned.open('rb') as f:
 while b:=f.read(65536):blob.update(b)
ck(blob.hexdigest()==rec['archive_git_blob_oid'],'independent returned blob object reencoding')
bare=Path(rec['fresh_bare']);ck(bare==R.parent/'onchain-pilot-recovery/real-pilot-native03-outcome-20261011-29.git' and bare.is_dir() and not bare.is_symlink() and not os.path.lexists(bare/'objects/info/alternates') and rec['no_alternates'] is True,'fresh bare no-alternates metadata only')
rows=sorted(sel['rows']+sel['directories'],key=lambda r:r['path']);index={r['path']:r for r in rows}
ck(len(index)==len(rows) and len(sel['rows'])==sel['files']==cap['files']==expected['files'] and len(sel['directories'])==cap['directories']==expected['directories'],'complete typed denominator')
ck(sum(r['type']=='symlink' for r in sel['rows'])==sel['symlinks']==expected['symlinks'] and sum(r['bytes'] for r in sel['rows'])==sel['body_bytes']==cap['regular_bytes']==expected['body_bytes'],'complete body symlink denominator')
ck(sel['actual_scope_states']==[] and sel['mandatory_public_roots']==roster['owned_public_roots'] and sel['prior_generated_files']==roster['prior_generated_files'],'no original scientific scope traversal and exact finite roots')
def public(name):
 p=PurePosixPath(name)
 return not p.is_absolute() and '..' not in p.parts and not {'.git','.venv','node_modules','keys','apis','real_pilot_runtime'}&set(p.parts) and p.name not in ('.env','connection.json','hf_token.txt') and not name.startswith(('research_runs/','research_artifacts/'))
for r in rows:ck(public(r['path']),'public names',r['path'])
class Sink:
 def __init__(self):self.n=0;self.h=hashlib.sha256()
 def write(self,b):self.n+=len(b);self.h.update(b);return len(b)
 def tell(self):return self.n
 def flush(self):pass
sink=Sink()
with tarfile.open(returned,'r:') as archive,tarfile.open(fileobj=sink,mode='w',format=tarfile.PAX_FORMAT) as target:
 members=archive.getmembers();ck(len(members)==len(rows),'complete member count')
 for m,r in zip(members,rows,strict=True):
  ck(m.name==r['path'] and m.mode==int(r['mode'],8) and m.uid==m.gid==m.mtime==0 and m.uname==m.gname=='','member order name mode normalized metadata',m.name)
  n=tarfile.TarInfo(r['path']);n.mode=int(r['mode'],8);n.uid=n.gid=n.mtime=0
  if r['type']=='directory':ck(m.type==tarfile.DIRTYPE and m.size==0,'typed directories',m.name);n.type=tarfile.DIRTYPE;target.addfile(n)
  elif r['type']=='symlink':ck(m.type==tarfile.SYMTYPE and m.size==0 and m.linkname==r['linkname'],'typed symlinks',m.name);n.type=tarfile.SYMTYPE;n.linkname=r['linkname'];target.addfile(n)
  else:
   ck(r['type']=='regular' and m.type==tarfile.REGTYPE and m.size==r['bytes']<=64*1024**2,'typed regular extents',m.name);ck(stream(archive.extractfile(m))==(r['bytes'],r['sha256']),'every opaque returned body',m.name);n.size=m.size;target.addfile(n,archive.extractfile(m))
ck((sink.n,sink.h.hexdigest())==EXPECTED,'entire canonical PAX exact')
base=js(O/'FRESH_GIT_RECOVERY28.json');ck(sha(read(O/'FRESH_GIT_RECOVERY28.json'))==sel['baseline_actual_recovery']['sha256']==roster['baseline_recovery_sha256'] and sel['baseline_actual_recovery']['path']==str((O/'FRESH_GIT_RECOVERY28.json').relative_to(R)),'exact accepted28 baseline receipt')
ck(base['source']==sel['baseline_source']==accepted['source']==roster['baseline_source'] and base['returned_archive']==accepted['archive'],'accepted28 source archive continuity')
bcapb=read(O/'CAPTURE28.json');ck(sha(bcapb)==base['capture']['sha256'],'prior28 capture pin');bcap=json.loads(bcapb);bselb=read(O/'SELECTION28.json');ck(sha(bselb)==bcap['selection']['sha256'],'prior28 selection pin');bsel=json.loads(bselb);oldrows={r['path']:r for r in bsel['rows']};reused=sel['exact_unchanged_prior_rows_reused']
ck(len(reused)==len(set(reused)) and not set(reused)&set(index) and set(reused)<=set(oldrows),'disjoint explicit reused27 rows')
for name in reused:
 r=oldrows[name];ck(public(name) and r['type']=='regular' and digest(R/name)==(r['bytes'],r['sha256']) and stat.S_IMODE((R/name).lstat().st_mode)==int(r['mode'],8),'actual unchanged reused27 body',name)
ck(sel['prior_inherited_reuse_preserved_by_receipt']==bsel['exact_unchanged_prior_rows_reused'] and len(sel['prior_inherited_reuse_preserved_by_receipt'])==accepted['reused_prior27_rows']==8 and sel['earlier_inherited_reuse_preserved_by_receipt']==bsel['prior_inherited_reuse_preserved_by_receipt'] and len(sel['earlier_inherited_reuse_preserved_by_receipt'])==accepted['inherited_rows_reused_by_accepted27']==67,'eight plus67 inherited rows preserved via accepted28 only')
exclusions={str((O/n).relative_to(R)) for n in ('post-native-increment28.tar','fresh-git-recovered-postnative28.tar','actual_external_archive_blob_return.stdout')};ck(set(sel['exact_already_recovered_duplicate_exclusions'])==exclusions and not exclusions&set(index),'three exact unchanged27 alias exclusions')
for name in exclusions:ck(digest(R/name)==(base['returned_archive']['bytes'],base['returned_archive']['sha256']),'excluded27 aliases remain exact',name)
available=dict(oldrows);available.update(index)
Q=F/'pilot34-native-owner-qualification03-2026-10-11';command=js(Q/'COMMAND03.json');command_name=str((Q/'COMMAND03.json').relative_to(R));prior_command_pin=oldrows[command_name]
ck((prior_command_pin['bytes'],prior_command_pin['sha256'])==(refs[command_name]['bytes'],refs[command_name]['sha256']),'unchanged accepted28 command binds earlier role references')
earlier_roles={str(Path(pin['path']).relative_to(R)):pin for pin in command['role_references'].values()}
def required(path,pin):
 name=str(path.relative_to(R))
 if name not in available:
  r=earlier_roles[name];ck((r['bytes'],r['sha256'])==(pin['bytes'],pin['sha256']),'earlier role bound by unchanged command and accepted28 proof',name);return
 r=available[name];ck(r['type']=='regular' and (r['bytes'],r['sha256'])==(pin['bytes'],pin['sha256']),'selected or prior28 required body',name)
for name,pin in hm['files'].items():required(D/name,pin)
for pin in [command['script'],command['candidate_manifest'],*command['role_references'].values()]:required(Path(pin['path']),pin)
opts=dict(zip(command['argv'][3::2],command['argv'][4::2]))
for role in ('owner','kernel','policy'):
 path=Path(opts['--'+role]);raw=read(path);required(path,{'bytes':len(raw),'sha256':opts['--'+role+'-sha256']})
for path in [T,Q/'COMMAND03.json',F/'pilot34-native-owner-qualification03-entry-review01-2026-10-11/REVIEW01.json',A]:required(path,refs.get(str(path.relative_to(R))) or {'bytes':len(read(path)),'sha256':sha(read(path))})
for reference in expected['new_acceptance_references']:
 path=R/reference['path'];ck(sha(read(path))==reference['sha256'],'actual new outcome and integration review pin',reference['path']);required(path,{'bytes':len(read(path)),'sha256':reference['sha256']})
for relative in roster['fixed_public_names']+roster['main_source_names']:
 ck(relative in index and index[relative]['type']=='regular','all five Main and fixed coordination bodies selected',relative)
for name in roster['prior_generated_files']:
 relative=str((O/name).relative_to(R));ck(relative in index or relative in reused or relative in exclusions,'finite prior28 receipts retained or exact alias excluded',name)
census=[]
for name in roster['owned_public_roots']:
 scope=F/name;found={};empty=[]
 for basepath,dirs,files in os.walk(scope,followlinks=False):
  p=Path(basepath);s=p.lstat();assert stat.S_ISDIR(s.st_mode);found[str(p.relative_to(R))]=('directory',stat.S_IMODE(s.st_mode))
  if not dirs and not files:empty.append(str(p.relative_to(R)))
  for child in dirs+files:
   cp=p/child;st=cp.lstat()
   if stat.S_ISLNK(st.st_mode):found[str(cp.relative_to(R))]=('symlink',stat.S_IMODE(st.st_mode))
   elif stat.S_ISREG(st.st_mode):found[str(cp.relative_to(R))]=('regular',stat.S_IMODE(st.st_mode))
   else:assert stat.S_ISDIR(st.st_mode)
 selected={n:(r['type'],int(r['mode'],8)) for n,r in index.items() if (R/n).is_relative_to(scope)}
 selected.update({n:(oldrows[n]['type'],int(oldrows[n]['mode'],8)) for n in reused if (R/n).is_relative_to(scope)})
 ck(found==selected,'exact public scope names types modes census',name)
 census.append({'root':name,'regular':sum(t=='regular' for t,m in found.values()),'directories':sum(t=='directory' for t,m in found.values()),'symlinks':sum(t=='symlink' for t,m in found.values()),'empty_directories':empty})
for r in sel['rows']:
 p=R/r['path'];s=p.lstat();ck(stat.S_IMODE(s.st_mode)==int(r['mode'],8),'current selected modes',r['path'])
 if r['type']=='regular':ck(s.st_nlink==1 and digest(p)==(r['bytes'],r['sha256']),'every current original selected body',r['path'])
 else:ck(stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['linkname'],'current selected symlink',r['path'])
# Exact actual Root receipt schema/fields are supplied after actual operations;
# do not invent old schema fields when the original receipt changes shape.
for key,fields in expected['root_operation_fields'].items():
 ck(all(root[key][field]==value for field,value in fields.items()),'actual Root retained operation',key)
ck(root['capture']['archive_bytes']==root['fresh_recovery']['archive_bytes']==EXPECTED[0] and root['capture']['archive_sha256']==root['fresh_recovery']['archive_sha256']==EXPECTED[1] and root['fresh_recovery']['source']==root['commit']['head']==SOURCE,'Root actual archive source joins')
commit_stdout=read(D/root['commit']['raw_stdout']).decode();commit_stderr=read(D/root['commit']['raw_stderr']);ck(commit_stdout.startswith('[research/onchain-paper-replication-2026-09-24 '+SOURCE[:9]+'] ') and (' '+str(root['commit']['changed_paths'])+' files changed,') in commit_stdout and commit_stderr==b'','original Root commit raw outputs')
ck(SOURCE[:9] in root['push']['output'] and 'research/onchain-paper-replication-2026-09-24 -> research/onchain-paper-replication-2026-09-24' in root['push']['output'],'Root actual push raw output')
staging=js(D/root['initial_staging']['receipt']);ck(root['initial_staging']['chunk_id']=='5490ee' and root['initial_staging']['exit_code']==1 and str((D/root['initial_staging']['receipt']).relative_to(R)) not in index,'original staging refusal retained separately outside capture')
out={'decision':'ACCEPT_ACTUAL_NATIVEOUTCOME29_DECLARED_RETURN','source':SOURCE,'archive':rec['returned_archive'],'archive_git_blob_oid':rec['archive_git_blob_oid'],'files':sel['files'],'directories':len(sel['directories']),'symlinks':sel['symlinks'],'regular_bytes':sel['body_bytes'],'reused_prior28_rows':len(reused),'inherited_prior27_rows_by_accepted28':8,'earlier_inherited_rows_by_accepted28':67,'scope_census':census,'whole_pax_reencoding_exact':True,'operation_count':13,'check_category_counts':counts,'references':refs,'streamed_bytes_accounted':streamed,'limitations':['Only declared public nativeoutcome29 increment; no original failed34 scientific scope traversal or earlier archive replay.','Opaque bodies authenticated by hash, never decoded as science or loaded. No installed runtime/private/whole-store/POSIX reconstruction/deletion claim.','No new Git/network operation. Original raw13 outputs authenticated; no future availability promise.','Post-capture Root actual-operation receipt and this review require later preservation.','No numerical qualification, genuine Owner/Binding, financial outcome or unconditional launch authority.']}
with (P/'REVIEW01.json').open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({k:out[k] for k in ('decision','source','archive','files','directories','symlinks','regular_bytes','reused_prior28_rows','inherited_prior27_rows_by_accepted28','earlier_inherited_rows_by_accepted28','operation_count')},sort_keys=True))
