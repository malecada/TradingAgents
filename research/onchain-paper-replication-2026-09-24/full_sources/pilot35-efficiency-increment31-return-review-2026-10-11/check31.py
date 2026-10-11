"""Actual finite increment31 return verification; no extraction, helper or Git/network execution."""
import hashlib,json,os,resource,signal,stat,tarfile
from pathlib import Path,PurePosixPath
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(30)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';D=H/'full35outcome31';O=H/'full35increment30';refs={};counts={};streamed=0
SOURCE='cf4138dd4b902c1ec63bae7cf0116ad49da74be8'
EXPECTED=(2416640,'57dbe76279528352d21d85a915d9ee79c782e0962867f53c7793a991cae17396')
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
T=F/'pilot35-efficiency-increment31-tools-review-2026-10-11/TOOLS_REVIEW01.json'
ck(sha(read(T))=='120b49f691296583e555e397e1d2e074eb2bba6dc2a97dc4401139a406013bbb' and js(T)['decision']=='accepted','accepted tools review')
hm=js(D/'HELPERS_MANIFEST01.json');ck(sha(read(D/'HELPERS_MANIFEST01.json'))=='b37eb6ec7c50a3c09d815fe599864ffb5fe889dc398ceeae21c9e19366ece074','actual helper freeze')
for pin in hm['files']:ck(digest(R/pin['path'])==(pin['bytes'],pin['sha256']),'actual helper member',pin['path'])
selb=read(D/'SELECTION31.json');sel=json.loads(selb);capb=read(D/'CAPTURE31.json');cap=json.loads(capb);rec=js(D/'FRESH_GIT_RECOVERY31.json');ops=js(D/'GIT_OPERATIONS31.json');roster=js(D/'PROSPECTIVE_ROSTER01.json')
ck(sha(selb)==cap['selection']['sha256'] and sha(capb)==rec['capture']['sha256'],'selection capture return joins')
ck(cap['selection']['path']==str((D/'SELECTION31.json').relative_to(R)) and rec['capture']['path']==str((D/'CAPTURE31.json').relative_to(R)),'exact receipt paths')
ck(rec['source']==rec['actual_remote_head']==rec['actual_fetch_head']==SOURCE,'actual source remote fetch')
ck(cap['archive']['path']==str((D/'failed35-outcome-increment31.tar').relative_to(R)) and rec['returned_archive']['path']==str((D/'fresh-git-recovered-full35outcome31.tar').relative_to(R)),'fresh archive paths')
for pin in (cap['archive'],rec['returned_archive']):ck((pin['bytes'],pin['sha256'])==EXPECTED and digest(R/pin['path'])==EXPECTED,'actual original and returned archive')
names=['local_head','remote_get_url','remote_actual_branch_readback','local_archive_git_tree_join','fresh_bare_init','fresh_remote_add','set_promisor','set_tree_zero_filter','actual_external_commit_only_fetch','fetched_head_readback','actual_external_commit_body','actual_external_selected_blob_fetch','actual_external_archive_blob_return']
ck(ops==rec['operations'] and [o['operation'] for o in ops]==names,'exact13 original operations')
for op in ops:
 ck(op['exit_code']==0,'actual exits',op['operation'])
 for kind in ('stdout','stderr'):ck(digest(D/(op['operation']+'.'+kind))==(op[kind+'_bytes'],op[kind+'_sha256']),'actual raw operation body',op['operation']+'.'+kind)
ck(read(D/'local_head.stdout').decode().strip()==read(D/'fetched_head_readback.stdout').decode().strip()==SOURCE,'raw source/fetch')
ck(read(D/'remote_actual_branch_readback.stdout').decode().strip()==SOURCE+'\trefs/heads/research/onchain-paper-replication-2026-09-24','raw remote source')
ck(read(D/'remote_get_url.stdout').decode().strip()==rec['actual_external_source']=='git@github.com:malecada/TradingAgents.git','raw original remote')
ck(read(D/'local_archive_git_tree_join.stdout').decode().strip()==rec['local_commit_tree_join']==f"100644 blob {rec['archive_git_blob_oid']}\t{cap['archive']['path']}",'raw tree join')
commit=read(D/'actual_external_commit_body.stdout');ck(sha(commit)==rec['commit_body_sha256'] and hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==SOURCE,'commit exact object reencoding')
returned=R/rec['returned_archive']['path'];blob=hashlib.sha1(b'blob '+str(EXPECTED[0]).encode()+b'\0')
with returned.open('rb') as f:
 while b:=f.read(65536):blob.update(b)
ck(blob.hexdigest()==rec['archive_git_blob_oid'],'returned blob exact object reencoding')
bare=Path(rec['fresh_bare']);ck(bare==R.parent/'onchain-pilot-recovery/real-pilot-failed35-outcome-20261011-31.git' and bare.is_dir() and not bare.is_symlink() and not os.path.lexists(bare/'objects/info/alternates') and rec['no_alternates'] is True,'actual fresh bare no-alternates metadata')
rows=sorted(sel['rows']+sel['directories'],key=lambda r:r['path']);index={r['path']:r for r in rows}
ck(len(index)==len(rows) and len(sel['rows'])==sel['files']==cap['files']==256 and len(sel['directories'])==cap['directories']==55,'complete256body55directory denominator')
ck(sel['symlinks']==0 and all(r['type']=='regular' for r in sel['rows']) and sum(r['bytes'] for r in sel['rows'])==sel['body_bytes']==cap['regular_bytes']==1931762,'complete body totals')
raw_scopes=sel['actual_scope_states'];terminal=js(F/'pilot35-terminal-outcome-review-2026-10-11/REVIEW01.json')
ck(sha(read(F/'pilot35-terminal-outcome-review-2026-10-11/REVIEW01.json'))==sel['terminal_review']['sha256']=='7224646b35c3fe8094c19288ad81be7c1650be458b7a3723198e82bc1a86aba4','original terminal anchor')
ck(raw_scopes==terminal['incremental_raw_scopes']==roster['raw_scope_states'] and [r['exists'] for r in raw_scopes]==[True]*5+[False],'exact5 original scopes/sixth absent')
ck(sel['mandatory_public_roots']==roster['public_roots'] and len(roster['public_roots'])==18 and sel['prior_generated_files']==roster['prior_generated_files'],'exact finite public scope')
def public(name):
 p=PurePosixPath(name)
 return not p.is_absolute() and '..' not in p.parts and not {'.git','.venv','node_modules','keys','apis','real_pilot_runtime'}&set(p.parts) and p.name not in ('.env','connection.json','hf_token.txt','id_ed25519_storagebox_u676273') and (not name.startswith(('research_runs/','research_artifacts/')) or any((R/name).is_relative_to(R/r['path']) for r in raw_scopes if r['exists']))
# Ancestor directory entries under research_artifacts/runs are permitted, but
# no regular body outside the five exact raw subtrees is admitted.
for r in rows:
 if r['type']!='directory':ck(public(r['path']),'bounded public or exact opaque failed scope',r['path'])
 else:ck(not PurePosixPath(r['path']).is_absolute() and '..' not in PurePosixPath(r['path']).parts,'canonical directory name',r['path'])
class Sink:
 def __init__(self):self.n=0;self.h=hashlib.sha256()
 def write(self,b):self.n+=len(b);self.h.update(b);return len(b)
 def tell(self):return self.n
 def flush(self):pass
sink=Sink()
with tarfile.open(returned,'r:') as archive,tarfile.open(fileobj=sink,mode='w',format=tarfile.PAX_FORMAT) as target:
 members=archive.getmembers();ck(len(members)==len(rows),'complete tar denominator')
 for m,r in zip(members,rows,strict=True):
  ck(m.name==r['path'] and m.mode==int(r['mode'],8) and m.uid==m.gid==m.mtime==0 and m.uname==m.gname=='','exact typed name mode order',m.name)
  n=tarfile.TarInfo(r['path']);n.mode=int(r['mode'],8);n.uid=n.gid=n.mtime=0
  if r['type']=='directory':ck(m.type==tarfile.DIRTYPE and m.size==0,'directory type',m.name);n.type=tarfile.DIRTYPE;target.addfile(n)
  else:
   ck(m.type==tarfile.REGTYPE and m.size==r['bytes']<=64*1024**2,'regular extent',m.name);ck(stream(archive.extractfile(m))==(r['bytes'],r['sha256']),'every actual opaque body',m.name);n.size=m.size;target.addfile(n,archive.extractfile(m))
ck((sink.n,sink.h.hexdigest())==EXPECTED,'exact complete PAX bytes')
accepted_path=F/'pilot35-preparation-increment-return-review01-2026-10-11/REVIEW01.json';accepted=js(accepted_path)
ck(sha(read(accepted_path))==sel['baseline_accepted_review']['sha256']=='170c85ab7eb08000467d7eeec098e1feb153ce8675b687d99f959728767dfbed','prior30 accepted return')
base=js(O/'FRESH_GIT_RECOVERY30.json');ck(sha(read(O/'FRESH_GIT_RECOVERY30.json'))==sel['baseline_actual_recovery']['sha256']=='32023dba761dbdcfc0fccd9bb9749a5320bdd345efa26a22411ca58be0f15d62','actual30 lineage receipt')
ck(base['source']==sel['baseline_source']==accepted['source']=='dd0d8d4cda7bffa6e45629f00da5ce60412cbec1' and base['returned_archive']==accepted['archive'],'prior30 source/archive continuity')
bcapb=read(O/'CAPTURE30.json');ck(sha(bcapb)==base['capture']['sha256'],'prior capture hash');bcap=json.loads(bcapb);bselb=read(O/'SELECTION30.json');ck(sha(bselb)==bcap['selection']['sha256'],'prior selection hash');bsel=json.loads(bselb);oldrows={r['path']:r for r in bsel['rows']};reused=sel['exact_unchanged_prior_rows_reused']
ck(len(reused)==len(set(reused)) and not set(reused)&set(index) and set(reused)<=set(oldrows),'disjoint explicit reused rows')
for name in reused:
 r=oldrows[name];ck(public(name) and r['type']=='regular' and digest(R/name)==(r['bytes'],r['sha256']) and stat.S_IMODE((R/name).lstat().st_mode)==int(r['mode'],8),'actual unchanged reused body',name)
ck(sel['prior_inherited_reuse_preserved_by_receipt']==bsel['exact_unchanged_prior_rows_reused'] and sel['earlier_inherited_reuse_preserved_by_receipt']==bsel['prior_inherited_reuse_preserved_by_receipt'],'inherited reuse exact lineage')
exclusions={str((O/n).relative_to(R)) for n in ('full35-preparation-increment30.tar','fresh-git-recovered-full35increment30.tar','actual_external_archive_blob_return.stdout')};ck(set(sel['exact_already_recovered_duplicate_exclusions'])==exclusions and not exclusions&set(index),'three exact alias exclusions')
for name in exclusions:ck(digest(R/name)==(base['returned_archive']['bytes'],base['returned_archive']['sha256']),'actual exact excluded alias',name)
for r in sel['rows']:
 p=R/r['path'];s=p.lstat();ck(stat.S_IMODE(s.st_mode)==int(r['mode'],8) and s.st_nlink==1 and digest(p)==(r['bytes'],r['sha256']),'every frozen local selected body/mode',r['path'])
for r in sel['directories']:
 p=R/r['path'];ck(p.is_dir() and not p.is_symlink() and p.resolve()==p and stat.S_IMODE(p.stat().st_mode)==int(r['mode'],8),'every frozen directory mode',r['path'])
census=[]
scopes=[F/n for n in roster['public_roots']]+[R/r['path'] for r in raw_scopes if r['exists']]
for scope in scopes:
 found={}
 for parent,dirs,files in os.walk(scope,followlinks=False):
  p=Path(parent);s=p.lstat();found[str(p.relative_to(R))]=('directory',stat.S_IMODE(s.st_mode))
  for child in dirs+files:
   cp=p/child;st=cp.lstat()
   if stat.S_ISREG(st.st_mode):found[str(cp.relative_to(R))]=('regular',stat.S_IMODE(st.st_mode))
   elif stat.S_ISLNK(st.st_mode):found[str(cp.relative_to(R))]=('symlink',stat.S_IMODE(st.st_mode))
   else:assert stat.S_ISDIR(st.st_mode)
 expected={n:(r['type'],int(r['mode'],8)) for n,r in index.items() if (R/n).is_relative_to(scope)}
 expected.update({n:(oldrows[n]['type'],int(oldrows[n]['mode'],8)) for n in reused if (R/n).is_relative_to(scope)})
 ck(found==expected,'complete current scope name/type/mode census',str(scope.relative_to(R)))
 census.append({'root':str(scope.relative_to(R)),'regular':sum(t=='regular' for t,m in found.values()),'directories':sum(t=='directory' for t,m in found.values())})
for r in raw_scopes:
 if not r['exists']:ck(not os.path.lexists(R/r['path']),'original sixth scope still absent')
snapshot=js(R/sel['engineering_source_snapshot']['path']);ck(sha(read(R/sel['engineering_source_snapshot']['path']))==sel['engineering_source_snapshot']['sha256'],'snapshot hash retained')
for row in snapshot['files']:ck(row['path'] in index and index[row['path']]['sha256']==row['sha256'],'all23 snapshot source/test bytes recovered',row['path'])
for name in roster['prior_generated_files']:
 n=str((O/name).relative_to(R));ck(n in index or n in reused or n in exclusions,'every33 predecessor receipt accounted',name)
out={'decision':'ACCEPT_ACTUAL_INCREMENT31_DECLARED_RETURN','source':SOURCE,'archive':rec['returned_archive'],'archive_git_blob_oid':rec['archive_git_blob_oid'],'regular_files':256,'directories':55,'regular_bytes':1931762,'symlinks':0,'operation_count':13,'reused_prior30_rows':len(reused),'scope_census':census,'whole_pax_reencoding_exact':True,'category_checks':counts,'references':refs,'streamed_bytes_accounted':streamed,'limitations':['Only declared increment31 and explicit inherited30 lineage; no installed runtime/private/other-store/POSIX/deletion authority.','Opaque failed35 bodies authenticated without scientific decoding or execution.','Later fixture-signature correction and fixture-fix directory are outside31; not recovered or current source closure evidence here.','No Git/network/helper/capture/recovery execution; original raw13 operation evidence inspected.','Postcapture operation receipts and this review need later preservation; no future availability guarantee.']}
with (P/'REVIEW01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'decision':out['decision'],'checks':sum(counts.values()),'sha256':sha((P/'REVIEW01.json').read_bytes())}))
